
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage,AIMessage
from app.schemas.chat import ChatRequest
from app.agents.graph import build_chat_graph

router = APIRouter(prefix="/v1/chat", tags=["chat"])


# ==================== SSE 端点（保留） ====================

@router.post("/stream")
async def chat_stream(request: ChatRequest):
    graph = build_chat_graph()
    initial_state = {
        "messages": [HumanMessage(content=request.message)],
        "model_type": request.model_type,
    }

    async def event_generator():
        async for event in graph.astream_events(initial_state, version="v2"):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if hasattr(chunk, "content") and chunk.content:
                    yield f"data: {json.dumps({'event': 'chunk', 'data': chunk.content})}\n\n"
            elif event["event"] == "on_chain_end" and event["name"] == "LangGraph":
                yield f"data: {json.dumps({'event': 'done', 'data': '[DONE]'})}\n\n"

        yield f"data: {json.dumps({'event': 'done', 'data': '[DONE]'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ==================== WebSocket 端点（支持暂停） ====================

@router.websocket("/ws")
async def chat_ws(websocket: WebSocket):
    await websocket.accept()
    messages_history = []
    # 当前正在运行的流式任务，None 表示没有在生成
    stream_task: asyncio.Task | None = None
    # 取消信号：set 表示用户请求停止
    stop_event = asyncio.Event()

    async def run_stream(messages: list, model_type: str) -> str:
        """
        运行 LangGraph 流式生成，逐 token 推送。
        参数 messages 为完整对话历史（含本轮用户消息）。
        返回 AI 回复的完整文本（被暂停时返回已生成的部分）。
        """
        graph = build_chat_graph()
        initial_state = {
            "messages":messages,
            "model_type": model_type,
        }
        # 新增：打印传给 LLM 的消息数量和最后一条用户消息
        user_msgs = [m for m in messages if isinstance(m, HumanMessage)]
        print(f"[run_stream] 消息总数: {len(messages)}, 用户消息数: {len(user_msgs)}")
        print(f"[run_stream] 最近用户消息: {user_msgs[-1].content if user_msgs else '无'}")
        full_response = ""
        try:
            async for event in graph.astream_events(initial_state, version="v2"):
                # 每次迭代检查是否被取消
                if stop_event.is_set():
                    await websocket.send_json({"event": "stopped", "data": "用户停止了生成"})
                    return full_response

                if event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        full_response += chunk.content
                        await websocket.send_json({
                            "event": "chunk",
                            "data": chunk.content
                        })
                elif event["event"] == "on_chain_end" and event["name"] == "LangGraph":
                    await websocket.send_json({"event": "done", "data": "[DONE]"})
                    return  full_response

            # 兜底 done
            await websocket.send_json({"event": "done", "data": "[DONE]"})
            return full_response
        except asyncio.CancelledError:
            await websocket.send_json({"event": "stopped", "data": "生成已取消"})
            return full_response
        except Exception as e:
            await websocket.send_json({"event": "error", "data": str(e)})
            return full_response

    async def _run_and_record(coro, history: list):
        """
        运行流式生成协程，并在完成后把 AI 回复追加到对话历史。
        这样主循环可以立即回到 receive_text() 而不用等待流结束。
        """
        response = await coro
        if response:
            history.append(AIMessage(content=response))
    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type", "")

            if msg_type == "chat":
                # 如果有正在跑的流，先停掉 （旧回复已由 _run_and_record 存入历史）
                if stream_task and not stream_task.done():
                    stop_event.set()
                    try:
                        await stream_task
                    except asyncio.CancelledError:
                        pass
                        # 把本轮用户消息追加到历史
                messages_history.append(HumanMessage(content=msg["message"]))
                print(f"[WS] 历史长度: {len(messages_history)}")  # 临时加的调试日志
                model_type = msg.get("model_type", "ollama")
                # 重置状态，启动新的流
                stop_event.clear()
                stream_task = asyncio.create_task(
                    _run_and_record(
                        run_stream(list(messages_history), model_type),
                        messages_history,
                    )
                )

            elif msg_type == "stop":
                if stream_task and not stream_task.done():
                    stop_event.set()
                    try:
                        await stream_task
                    except asyncio.CancelledError:
                        pass
                    stream_task = None

    except WebSocketDisconnect:
        # 客户端断开，取消正在跑的任务
        if stream_task and not stream_task.done():
            stop_event.set()