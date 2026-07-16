
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
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

    # 当前正在运行的流式任务，None 表示没有在生成
    stream_task: asyncio.Task | None = None
    # 取消信号：set 表示用户请求停止
    stop_event = asyncio.Event()

    async def run_stream(message: str, model_type: str):
        """运行 LangGraph 流式生成，逐 token 推送"""
        graph = build_chat_graph()
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "model_type": model_type,
        }
        try:
            async for event in graph.astream_events(initial_state, version="v2"):
                # 每次迭代检查是否被取消
                if stop_event.is_set():
                    await websocket.send_json({"event": "stopped", "data": "用户停止了生成"})
                    return

                if event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        await websocket.send_json({
                            "event": "chunk",
                            "data": chunk.content
                        })
                elif event["event"] == "on_chain_end" and event["name"] == "LangGraph":
                    await websocket.send_json({"event": "done", "data": "[DONE]"})
                    return

            # 兜底 done
            await websocket.send_json({"event": "done", "data": "[DONE]"})
        except asyncio.CancelledError:
            await websocket.send_json({"event": "stopped", "data": "生成已取消"})
        except Exception as e:
            await websocket.send_json({"event": "error", "data": str(e)})

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type", "")

            if msg_type == "chat":
                # 如果有正在跑的流，先停掉
                if stream_task and not stream_task.done():
                    stop_event.set()
                    stream_task.cancel()
                    try:
                        await stream_task
                    except asyncio.CancelledError:
                        pass

                # 重置状态，启动新的流
                stop_event.clear()
                stream_task = asyncio.create_task(
                    run_stream(msg["message"], msg.get("model_type", "ollama"))
                )

            elif msg_type == "stop":
                if stream_task and not stream_task.done():
                    stop_event.set()
                    stream_task.cancel()
                    try:
                        await stream_task
                    except asyncio.CancelledError:
                        pass
                    stream_task = None

    except WebSocketDisconnect:
        # 客户端断开，取消正在跑的任务
        if stream_task and not stream_task.done():
            stop_event.set()
            stream_task.cancel()