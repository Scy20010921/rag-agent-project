import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from pydantic import BaseModel
from app.schemas.chat import ChatRequest
from app.agents.graph import build_chat_graph
from app.agents.tools import TOOLS
from app.core.session_store import (
    create_session, list_sessions, get_session, delete_session,
    save_message, load_messages,
)

router = APIRouter(prefix="/v1/chat", tags=["chat"])


# ---- Pydantic schemas for REST ----

class CreateSessionRequest(BaseModel):
    title: str = "新对话"


# ---- 会话 REST API ----

@router.get("/sessions")
async def api_list_sessions():
    """获取所有会话列表"""
    return {"sessions": list_sessions()}


@router.post("/sessions")
async def api_create_session(req: CreateSessionRequest):
    """创建新会话，返回 session_id"""
    import uuid
    sid = str(uuid.uuid4())
    session = create_session(sid, title=req.title)
    return session


@router.get("/sessions/{session_id}/messages")
async def api_load_messages(session_id: str):
    """加载指定会话的所有消息"""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    msgs = load_messages(session_id)
    return {"session": session, "messages": msgs}


@router.delete("/sessions/{session_id}")
async def api_delete_session(session_id: str):
    """删除指定会话"""
    delete_session(session_id)
    return {"ok": True}


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


# ==================== WebSocket 端点 ====================

@router.websocket("/ws")
async def chat_ws(websocket: WebSocket):
    await websocket.accept()

    stream_task: asyncio.Task | None = None
    stop_event = asyncio.Event()
    messages_history: list = []
    # 当前 WebSocket 连接绑定的会话 ID
    current_session_id: str | None = None
    # 当前连接的用户 ID（前端生成，用于用户文档隔离）
    current_user_id: str = ""

    async def run_stream(messages: list, model_type: str, system_prompt: str = "", user_id: str = "") -> str:
        graph = build_chat_graph()
        # 如果用户设置了 system prompt，且当前开启深度思考，拼入用户的第一条消息而不是单独 SystemMessage
        # 避免多轮对话中 SystemMessage 出现在非首位导致千问 API 报错
        msgs_for_llm = list(messages)
        if system_prompt and model_type == "qwen_api":
            msgs_for_llm = [HumanMessage(content=f"[系统指令]\n{system_prompt}")] + msgs_for_llm
        elif system_prompt:
            msgs_for_llm = [SystemMessage(content=system_prompt)] + msgs_for_llm
        initial_state = {
            "messages": msgs_for_llm,
            "model_type": model_type,
            "user_id": user_id,  # 传给 retrieve 节点用于用户文档检索
        }
        full_response = ""
        has_sent_thinking = False
        try:
            async for event in graph.astream_events(initial_state, version="v2"):
                if stop_event.is_set():
                    await websocket.send_json({"event": "stopped", "data": "用户停止了生成"})
                    return full_response

                if event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        # 第一个 token 时推送"正在思考"状态
                        if not has_sent_thinking:
                            has_sent_thinking = True
                            await websocket.send_json({
                                "event": "status",
                                "data": "正在思考..."
                            })
                        full_response += chunk.content
                        await websocket.send_json({
                            "event": "chunk",
                            "data": chunk.content
                        })

                # 工具调用开始
                elif event["event"] == "on_tool_start":
                    tool_input = event["data"].get("input", {})
                    # 推送"正在调用工具"状态
                    await websocket.send_json({
                        "event": "status",
                        "data": f"🔧 正在调用工具: {event['name']}"
                    })
                    await websocket.send_json({
                        "event": "tool_start",
                        "data": {
                            "name": event["name"],
                            "input": str(tool_input)[:200],
                        }
                    })

                # 工具调用结束
                elif event["event"] == "on_tool_end":
                    tool_output = event["data"].get("output", "")
                    await websocket.send_json({
                        "event": "status",
                        "data": f"✅ 工具 {event['name']} 执行完成"
                    })
                    await websocket.send_json({
                        "event": "tool_end",
                        "data": {
                            "name": event["name"],
                            "output": str(tool_output)[:500],
                        }
                    })

                elif event["event"] == "on_chain_end" and event["name"] == "LangGraph":
                    await websocket.send_json({"event": "done", "data": "[DONE]"})
                    return full_response

            await websocket.send_json({"event": "done", "data": "[DONE]"})
            return full_response
        except asyncio.CancelledError:
            await websocket.send_json({"event": "stopped", "data": "生成已取消"})
            return full_response
        except Exception as e:
            await websocket.send_json({"event": "error", "data": str(e)})
            return full_response

    async def _run_and_record(coro, history: list, session_id: str | None):
        response = await coro
        if response:
            history.append(AIMessage(content=response))
            # 持久化 AI 回复
            if session_id:
                save_message(session_id, "assistant", response)

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type", "")

            if msg_type == "chat":
                # 记录用户 ID
                uid = msg.get("user_id", "")
                if uid:
                    current_user_id = uid
                if stream_task and not stream_task.done():
                    stop_event.set()
                    try:
                        await stream_task
                    except asyncio.CancelledError:
                        pass

                # 区分：切换会话（load）还是新消息（chat）
                sid = msg.get("session_id")
                if sid and sid != current_session_id:
                    # 切换到指定会话
                    current_session_id = sid
                    messages_history.clear()
                    if get_session(sid):
                        db_msgs = load_messages(sid)
                        for m in db_msgs:
                            if m["role"] == "user":
                                messages_history.append(HumanMessage(content=m["content"]))
                            else:
                                messages_history.append(AIMessage(content=m["content"]))
                        # 把历史消息推给前端
                        await websocket.send_json({"event": "history", "data": db_msgs})

                # 如果不带 message 字段，只是加载历史，不调 LLM
                if not msg.get("message"):
                    continue

                # 如果还没有 session_id，自动创建
                if not current_session_id:
                    import uuid
                    current_session_id = str(uuid.uuid4())
                    create_session(current_session_id)
                    await websocket.send_json({
                        "event": "session_created",
                        "data": {"session_id": current_session_id}
                    })

                # 用户消息加入历史 + 持久化
                user_content = msg["message"]
                messages_history.append(HumanMessage(content=user_content))
                save_message(current_session_id, "user", user_content)

                model_type = msg.get("model_type", "ollama")
                system_prompt = msg.get("system_prompt", "")
                stop_event.clear()
                stream_task = asyncio.create_task(
                    _run_and_record(
                        run_stream(list(messages_history), model_type, system_prompt, current_user_id),
                        messages_history,
                        current_session_id,
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
        if stream_task and not stream_task.done():
            stop_event.set()