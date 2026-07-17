import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage,SystemMessage
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
    # 启动器 使用websocket 必须使用
    await websocket.accept()
    #当前正在执行的流式生成任务（异步协程）。用于：① 任务取消（用户点击停止时）；② 任务状态检查（防止重复启动）
    stream_task: asyncio.Task | None = None
    #一个停止信号事件。当用户点击“停止生成”时，设置该事件，流式生成协程内部定期检查该事件，收到信号后优雅退出
    stop_event = asyncio.Event()
    # 当前会话的消息历史记录（用户+助手消息）。用于：① 上下文连续对话；② 会话恢复时重放历史
    messages_history: list = []
    # 当前 WebSocket 连接绑定的会话 ID
    current_session_id: str | None = None

#传入对话历史和模型名称
    async def run_stream(messages: list, model_type: str, system_prompt: str = "") -> str:
        graph = build_chat_graph() #构建好的 LangGraph 图
        # 如果有 system prompt，插入到消息列表最前面
        msgs_for_llm = list(messages)
        if system_prompt:
            msgs_for_llm = [SystemMessage(content=system_prompt)] + msgs_for_llm
        initial_state = {
            "messages": msgs_for_llm, # 对话历史（LangChain 格式）
            "model_type": model_type, # "ollama" 或 "qwen_api"
        }
        full_response = ""      #累积完整的回复内容，最后会返回给调用方（用于存储）
        has_sent_thinking = False
        try:

            # graph.astream_events(initial_state, version="v2") 会持续产生事件，直到图执行完毕。常见事件类型
            # on_chain_start 某个节点开始执行 on_chat_model_stream LLM 生成了一个 token on_tool_start 工具开始调用（如果有） on_chain_end 某个节点（包括整个图）执行完成
            async for event in graph.astream_events(initial_state, version="v2"):
                # 1️⃣ 检查停止信号（每次事件循环都检查）用户点击了“停止生成”
                if stop_event.is_set():
                    await websocket.send_json({"event": "stopped", "data": "用户停止了生成"})
                    return full_response
                # 2️⃣ 处理流式文本块（token 生成）
                #如果LLM 生成了一个 token
                if event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    #chunk类容为content='你好' additional_kwargs={} response_metadata={} id='lc_run--019f6fb8-7304-7002-807d-a6ad177e3c73' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
                    #content='！' additional_kwargs={} response_metadata={} id='lc_run--019f6fb8-7304-7002-807d-a6ad177e3c73' tool_calls=[] invalid_tool_calls=[] tool_call_chunks=[]
                    # hasattr(chunk, "content") 检查 chunk 这个对象有没有 content 属性（防止某些事件对象没有该字段）
                    # chunk.content 取 content 属性的值，然后在 if 上下文中做真值判断
                    if hasattr(chunk, "content") and chunk.content:
                        # 第一个 token 时推送"正在思考"状态
                        if not has_sent_thinking:
                            has_sent_thinking = True
                            await websocket.send_json({
                                "event": "status",
                                "data": "正在思考..."
                            })
                        # #累积完整的回复内容，最后会返回给调用方（用于存储）
                        full_response += chunk.content
                        #把 LLM 生成的每一个文本块（token），实时通过 WebSocket 推送给前端，让前端实现“打字机效果”。
                        #前端会怎么处理？
                        # ws.onmessage = (event) => {
                        #     const json = JSON.parse(event.data);
                        #
                        #     if (json.event === 'chunk') {
                        #         // 把收到的文本片段追加到正在显示的对话气泡上
                        #         currentAssistantMessage += json.data;
                        #         updateChatBubble(currentAssistantMessage);
                        #     }
                        # }
                        #用户体验： AI 的回复是一个字一个字地蹦出来的（类似 ChatGPT），而不是等全部生成完再一次性显示。
                        await websocket.send_json({
                            "event": "chunk",
                            "data": chunk.content
                        })
                # 工具调用开始 → 通知前端显示"正在调用 xxx"
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
                    # 工具调用结束 → 通知前端显示结果
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
                # 3️⃣ 处理图结束（LangGraph 执行完成）
                #on_chain_end 某个节点（包括整个图）执行完成
                #当 LangGraph 图执行完成时，发送 "done" 事件通知前端“所有内容已传输完毕”，然后返回完整的回复内容。
                elif event["event"] == "on_chain_end" and event["name"] == "LangGraph":
                    await websocket.send_json({"event": "done", "data": "[DONE]"})
                    return full_response
        # 这两行代码是 run_stream 函数的“最后一道防线”，作用是：
        # 当 LangGraph 流式事件循环正常结束（但没有触发 on_chain_end 事件）时，手动发送 done 事件告诉前端生成已完成，然后返回完整的回复内容。
            await websocket.send_json({"event": "done", "data": "[DONE]"})
            return full_response
        except asyncio.CancelledError:
            await websocket.send_json({"event": "stopped", "data": "生成已取消"})
            return full_response
        except Exception as e:
            await websocket.send_json({"event": "error", "data": str(e)})
            return full_response

    async def _run_and_record(coro, history: list, session_id: str | None):
        response = await coro       ## ① 等待流式生成完成
        if response:                # # ② 如果有回复内容
            history.append(AIMessage(content=response)) ## ③ 存入内存历史
            # 持久化 AI 回复
            if session_id:      ## ④ 如果有会话 ID
                save_message(session_id, "assistant", response)  # ⑤ 存入数据库
    try:
        print("1")
        while True:
            raw = await websocket.receive_text()
            # raw输出为{"type":"chat","message":"await websocket.accept()的作用","session_id":"e1cac807-5f34-4d7b-9832-cac3c1857388","model_type":"ollama"}
            msg = json.loads(raw)
            # msg被转换后为{'type': 'chat', 'message': 'await websocket.accept()的作用', 'session_id': 'e1cac807-5f34-4d7b-9832-cac3c1857388', 'model_type': 'ollama'}
            #websocket.receive_text() 收回来的是一个纯粹的文本字符串（str 类型）。如果你不转成字典，就只能得到一个长长的字符串，没法直接用 msg.get("type") 或 msg["message"] 去取值。
            msg_type = msg.get("type", "")
            # msg_type是取出msg的type里面的值 比如chat
            # 如何是chat则判断
            if msg_type == "chat":
                # 如果 stream_task 这个任务存在，并且它还没有执行完毕（还在运行中）
                if stream_task and not stream_task.done():
                    #  先发送停止信号，然后等待任务完全退出 将当前任务停止
                    stop_event.set()
                    try:
                        # 等待任务彻底结束（确保清理工作完成）
                        await stream_task
                    except asyncio.CancelledError:
                        pass

                # 区分：切换会话（load）还是新消息（chat）
                # 拿到当前会话的id
                sid = msg.get("session_id")
                # 判断是否有sid 并且传过来的id和当前连接绑定的id不同 则执行下面 不管怎么样都会走这个连接 可能是前端每次连接都清空了current的id
                #每次发消息 → 建立连接 → 消息完成 → 断开连接 → 下次再重连
                if sid and sid != current_session_id:
                    # 将获取的sid 赋值给当前连接绑定的id
                    current_session_id = sid
                    # 清空当前 WebSocket 连接内存中缓存的消息历史列表。
                    messages_history.clear()
                    # ① 检查 sid 对应的会话是否存在
                    if get_session(sid):
                        # ② 从数据库加载消息列表
                        db_msgs = load_messages(sid)
                        # ③ 遍历每条消息
                        for m in db_msgs:
                            # 如何数据中的role==user
                            if m["role"] == "user":
                                #将数据库里面的用户值添加给messages_history 而且还是转换后的
                                #数据库为[{"role": "user", "content": "你好，我是小明"},]
                                #转换后为[HumanMessage(content="你好，我是小明")]
                                messages_history.append(HumanMessage(content=m["content"]))
                                # 将数据库里面的AI值添加给messages_history 而且还是转换后的
                            else:
                                messages_history.append(AIMessage(content=m["content"]))
                        # 把历史消息推给前端
                        #websocket.send_json() FastAPI 提供的方法，自动把 Python 字典转成 JSON 字符串并通过 WebSocket 发出去
                        #{"event": "history", "data": db_msgs}	要发送的数据体
                        # 将json数据传给前端
                        #messages_history是LangChain对象列表 给ai看的 db_msgs是字典列表 传给前端的json格式
                        # messages_history  [HumanMessage(content="你好")] 字典列表
                        # db_msgs  [{"role": "user", "content": "你好"}] LangChain 对象列表
                        await websocket.send_json({"event": "history", "data": db_msgs})

                # 如果不带 message 字段，只是加载历史，不调 LLM
                if not msg.get("message"):
                    continue

                # 如果还没有 session_id，自动创建
                # 当用户发起对话但还没有会话 ID 时，后端自动创建一个新会话，生成唯一 ID，保存到数据库，并告知前端这个新 ID。
                if not current_session_id:   # ① 检查当前连接是否已绑定会话
                    import uuid             # ② 导入 UUID 生成库
                    current_session_id = str(uuid.uuid4())   # ③ 生成一个随机唯一 ID（如 "e1cac807-..."）
                    create_session(current_session_id)       # ④ 在数据库中创建该会话记录
                    await websocket.send_json({              # ⑤ 把新 ID 推送给前端
                        "event": "session_created",
                        "data": {"session_id": current_session_id}
                    })

                # 用户消息加入历史 + 持久化
                # 用户输入的消息 加入进去 输入什么就是什么
                user_content = msg["message"]
                #把用户刚发送的消息，转换成 LangChain 的 HumanMessage 对象，并添加到内存中的 messages_history 列表里，用于后续 LLM 推理时的上下文
                messages_history.append(HumanMessage(content=user_content))
                #把用户刚发送的消息，保存到数据库中，实现聊天记录的持久化存储。
                save_message(current_session_id, "user", user_content)

                # 从请求中获取模型类型（默认为 "ollama"），清空停止信号，然后创建一个异步任务来执行 LLM 流式生成，并自动记录 AI 回复到历史中。
                #从前端发来的字典中取 model_type 字段，如果没有则默认 "ollama"
                model_type = msg.get("model_type", "ollama")
                system_prompt = msg.get("system_prompt", "")
                print(system_prompt)
                #把停止信号重置为 False（未触发状态）
                stop_event.clear()
                #asyncio.create_task()创建一个异步任务，并立即开始执行（不阻塞当前代码）
                stream_task = asyncio.create_task(
                    #_run_and_record 包装函数：先执行生成，成功后把 AI 回复存到 messages_history 和数据库
                    _run_and_record(
                        run_stream(list(messages_history), model_type, system_prompt), # 参数1：协程对象
                        messages_history,            # 参数2：历史列表（引用）
                        current_session_id,         # 参数3：会话ID
                    )
                )
            # 判断前端发来的是 "stop" 类型消息（用户点击了停止按钮）
            elif msg_type == "stop":
                # 检查是否有任务在运行（有任务且未完成）
                if stream_task and not stream_task.done():
                    # 发送停止信号，告诉生成协程“该退出了”
                    stop_event.set()
                    try:
                        #  等待任务真正退出（确保清理完成）
                        await stream_task
                    except asyncio.CancelledError:
                        pass
                    # 清空任务引用，表示“当前没有正在运行的任务”
                    stream_task = None

    except WebSocketDisconnect:
        if stream_task and not stream_task.done():
            stop_event.set()