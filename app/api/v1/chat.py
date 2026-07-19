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
from app.core.llm_factory import get_llm_by_type

router = APIRouter(prefix="/v1/chat", tags=["chat"])


# ---- Pydantic schemas ----

class CreateSessionRequest(BaseModel):
    title: str = "新对话"


# ---- 上下文压缩配置 ----

MAX_CONTEXT_CHARS = 4000   # 超过 4000 字触发摘要
SUMMARY_KEEP_LAST = 2      # 保留最后 2 轮不动


async def _summarize_history(messages: list, model_type: str) -> str:
    """合并历史对话为一小段摘要，保留关键事实。"""
    history_text = ""
    for m in messages[:-SUMMARY_KEEP_LAST]:
        role = "用户" if isinstance(m, HumanMessage) else "AI"
        history_text += f"[{role}]: {m.content}\n"
    prompt = f"请将以下对话历史总结为一小段摘要，保留关键事实和决策：\n\n{history_text}\n\n摘要:"
    llm = get_llm_by_type(model_type)
    resp = await llm.ainvoke([HumanMessage(content=prompt)])
    return resp.content.strip()


# ---- 会话 REST API ----

@router.get("/sessions")
async def api_list_sessions():
    return {"sessions": list_sessions()}


@router.post("/sessions")
async def api_create_session(req: CreateSessionRequest):
    import uuid
    sid = str(uuid.uuid4())
    session = create_session(sid, title=req.title)
    return session


@router.get("/sessions/{session_id}/messages")
async def api_load_messages(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    msgs = load_messages(session_id)
    return {"session": session, "messages": msgs}


@router.delete("/sessions/{session_id}")
async def api_delete_session(session_id: str):
    delete_session(session_id)
    return {"ok": True}


# ==================== SSE 端点（保留） ====================

@router.post("/stream")
async def chat_stream(request: ChatRequest):
    graph = build_chat_graph()
    initial_state = {
        "messages": [HumanMessage(content=request.message)],
        "model_type": request.model_type,
        "user_id": "",
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
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    )


# ==================== WebSocket 端点 ====================

@router.websocket("/ws")
async def chat_ws(websocket: WebSocket):
    await websocket.accept()

    stream_task: asyncio.Task | None = None
    stop_event = asyncio.Event()
    messages_history: list = []
    current_session_id: str | None = None
    current_user_id: str = ""

    async def run_stream(messages: list, model_type: str, system_prompt: str = "", user_id: str = "") -> str:
        graph = build_chat_graph()
        msgs_for_llm = list(messages)

        # 上下文窗口管理：只对 Ollama 本地模型启用
        if model_type == "ollama":
            total_chars = sum(len(m.content) for m in msgs_for_llm if hasattr(m, "content"))
            if total_chars > MAX_CONTEXT_CHARS and len(msgs_for_llm) > SUMMARY_KEEP_LAST + 2:
                summary = await _summarize_history(msgs_for_llm, model_type)
                msgs_for_llm = (
                    [SystemMessage(content=f"[对话历史摘要] {summary}")]
                    + msgs_for_llm[-SUMMARY_KEEP_LAST:]
                )

        if system_prompt:
            msgs_for_llm = [SystemMessage(content=system_prompt)] + msgs_for_llm

        initial_state = {
            "messages": msgs_for_llm,
            "model_type": model_type,
            "user_id": user_id,
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
                        if not has_sent_thinking:
                            has_sent_thinking = True
                            await websocket.send_json({"event": "status", "data": "正在思考..."})
                        full_response += chunk.content
                        await websocket.send_json({"event": "chunk", "data": chunk.content})

                elif event["event"] == "on_tool_start":
                    tool_input = event["data"].get("input", {})
                    await websocket.send_json({"event": "status", "data": f"🔧 正在调用工具: {event['name']}"})
                    await websocket.send_json({"event": "tool_start", "data": {"name": event["name"], "input": str(tool_input)[:200]}})

                elif event["event"] == "on_tool_end":
                    tool_output = event["data"].get("output", "")
                    await websocket.send_json({"event": "status", "data": f"✅ 工具 {event['name']} 执行完成"})
                    await websocket.send_json({"event": "tool_end", "data": {"name": event["name"], "output": str(tool_output)[:500]}})

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
            if session_id:
                save_message(session_id, "assistant", response)

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type", "")

            if msg_type == "chat":
                uid = msg.get("user_id", "")
                if uid:
                    current_user_id = uid

                if stream_task and not stream_task.done():
                    stop_event.set()
                    try:
                        await stream_task
                    except asyncio.CancelledError:
                        pass

                sid = msg.get("session_id")
                if sid and sid != current_session_id:
                    current_session_id = sid
                    messages_history.clear()
                    if get_session(sid):
                        db_msgs = load_messages(sid)
                        for m in db_msgs:
                            messages_history.append(
                                HumanMessage(content=m["content"])
                                if m["role"] == "user"
                                else AIMessage(content=m["content"])
                            )
                        await websocket.send_json({"event": "history", "data": db_msgs})

                if not msg.get("message"):
                    continue

                if not current_session_id:
                    import uuid
                    current_session_id = str(uuid.uuid4())
                    create_session(current_session_id)
                    await websocket.send_json({"event": "session_created", "data": {"session_id": current_session_id}})

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