from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.core.llm_factory import get_llm_by_type
from app.core.vector_store import search
from app.core.reranker import rerank
import json

async def call_model(state: Dict[str, Any]) -> Dict[str, Any]:
    messages = state.get("messages", [])
    model_type = state.get("model_type", "ollama")
    if not messages:
        return {"messages": []}

    llm = get_llm_by_type(model_type)
    response = await llm.ainvoke(messages)
    return {"messages": [response]}


async def retrieve(state: Dict[str, Any]) -> Dict[str, Any]:
    messages = state.get("messages", [])
    user_id = state.get("user_id", "")
    if not messages:
        return {"messages": []}

    query = ""
    ctx_lines = []
    found_current = False
    for m in reversed(messages):
        if isinstance(m, HumanMessage) and not found_current:
            query = m.content
            found_current = True
        elif len(ctx_lines) < 4:
            role = "用户" if isinstance(m, HumanMessage) else "AI"
            ctx_lines.append("[{}]: {}".format(role, m.content[:200]))
    ctx_lines.reverse()

    if not query:
        return {"messages": []}

    if ctx_lines:
        search_query = "对话历史:\n" + "\n".join(ctx_lines[-4:]) + "\n\n当前问题: " + query
    else:
        search_query = query

    results = search(search_query, user_id=user_id, k=10)
    if not results:
        return {"messages": []}

    candidates = [r for r in results if r["score"] < 1.5]
    if not candidates:
        return {"messages": []}

    ranked = rerank(query, candidates, top_k=3)
    if not ranked:
        return {"messages": []}

    context_parts = []
    for r in ranked:
        source = r["metadata"].get("filename", "未知文档")
        score = r.get("rerank_score", 0)
        context_parts.append("[来源: {} | 相关度: {:.2f}]\n{}".format(source, score, r["content"]))
    context = "\n\n---\n\n".join(context_parts)

    last_msg = messages[-1]
    if isinstance(last_msg, HumanMessage):
        enhanced = (
            "[系统指令]\n"
            "你是一个知识库助手。基于以下文档片段和对话历史回答用户问题。\n"
            "如果片段中没有相关信息，请如实告知，不要编造。\n\n"
            "检索到的相关文档片段:\n"
            + context +
            "\n\n[用户问题]\n"
            + last_msg.content
        )
        return {"messages": [HumanMessage(content=enhanced)]}
    return {"messages": []}


async def supervisor(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    总管节点：判断用户意图。
    返回字典，包含 intent 字段。
    """
    messages = state.get("messages", [])
    if not messages:
        return {"intent": "chat"}  # 默认走闲聊

    last_msg = messages[-1]
    query = last_msg.content if isinstance(last_msg, HumanMessage) else ""

    # 1. 极速兜底关键词（不经过 LLM，省时省钱）
    chat_keywords = ["你是谁", "你好", "天气", "计算", "搜索", "今天", "讲个笑话"]
    if any(kw in query for kw in chat_keywords):
        # 注意：这里如果包含“计算”或“搜索”，虽然走了 chat，但 call_model 有工具，依然能执行。
        return {"intent": "chat"}

    # 强制知识库关键词
    knowledge_keywords = ["根据文档", "知识库", "公司政策", "手册", "查阅", "参考", "报告"]
    if any(kw in query for kw in knowledge_keywords):
        return {"intent": "knowledge"}

    # 2. 智能路由：用 LLM 判断（只调用一次，不给大模型加 system prompt 检索干扰）
    # 为了节省资源，这里复用现有的 llm，但用极简 prompt
    from app.core.llm_factory import get_llm_by_type
    model_type = state.get("model_type", "ollama")
    llm = get_llm_by_type(model_type)

    sys_prompt = SystemMessage(
        content="你是一个路由器。判断用户是否需要查询知识库（如文档、内部数据、特定事实）。"
                "如果需要查知识库返回 'knowledge'，否则返回 'chat'。"
                "只返回一个单词，不要有其他内容。"
    )
    try:
        response = await llm.ainvoke([sys_prompt, last_msg])
        intent = response.content.strip().lower()
        if "knowledge" in intent:
            return {"intent": "knowledge"}
    except Exception:
        pass
    # 默认走闲聊（避免死循环）
    return {"intent": "chat"}