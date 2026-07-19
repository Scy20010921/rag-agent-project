from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from app.core.llm_factory import get_llm_by_type
from app.agents.tools import TOOLS
from app.core.vector_store import search


async def call_model(state: Dict[str, Any]) -> Dict[str, Any]:
    """异步节点：调用 LLM 并返回消息。"""
    messages = state.get("messages", [])
    model_type = state.get("model_type", "ollama")
    if not messages:
        return {"messages": []}

    llm = get_llm_by_type(model_type)
    if model_type == "ollama":
        llm_with_tools = llm.bind_tools(TOOLS)
    else:
        llm_with_tools = llm
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}


async def retrieve(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    对话感知检索：把最近 4 轮对话 + 当前问题拼成一个上下文感知查询，
    避免"它怎么样"这类指代词无法匹配文档内容。
    """
    messages = state.get("messages", [])
    user_id = state.get("user_id", "")
    if not messages:
        return {"messages": []}

    # 构造上下文感知查询
    query = ""
    ctx_lines = []
    found_current = False
    for m in reversed(messages):
        if isinstance(m, HumanMessage) and not found_current:
            query = m.content
            found_current = True
        elif len(ctx_lines) < 4:
            role = "用户" if isinstance(m, HumanMessage) else "AI"
            ctx_lines.append(f"[{role}]: {m.content[:200]}")
    ctx_lines.reverse()

    if not query:
        return {"messages": []}

    if ctx_lines:
        search_query = "对话历史:\n" + "\n".join(ctx_lines[-4:]) + f"\n\n当前问题: {query}"
    else:
        search_query = query

    # 检索
    results = search(search_query, user_id=user_id, k=5)
    if not results:
        return {"messages": []}

    # 相关性过滤
    RELEVANCE_THRESHOLD = 0.8
    relevant = [r for r in results if r["score"] < RELEVANCE_THRESHOLD][:3]
    if not relevant:
        return {"messages": []}

    # 拼接上下文
    context_parts = []
    for r in relevant:
        source = r["metadata"].get("filename", "未知文档")
        context_parts.append(f"[来源: {source}]\n{r['content']}")
    context = "\n\n---\n\n".join(context_parts)

    last_msg = messages[-1]
    if isinstance(last_msg, HumanMessage):
        enhanced = f"""[系统指令]
你是一个知识库助手。基于以下文档片段和对话历史回答用户问题。
如果片段中没有相关信息，请如实告知，不要编造。

检索到的相关文档片段:
{context}

[用户问题]
{last_msg.content}"""
        return {"messages": [HumanMessage(content=enhanced)]}
    return {"messages": []}