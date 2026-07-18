from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.core.llm_factory import get_llm_by_type
from app.agents.tools import TOOLS
from app.core.vector_store import search


async def call_model(state: Dict[str, Any]) -> Dict[str, Any]:
    """异步节点：调用 LLM（绑定工具）并返回消息。"""
    messages = state.get("messages", [])
    model_type = state.get("model_type", "ollama")
    if not messages:
        return {"messages": []}

    llm = get_llm_by_type(model_type)
    llm_with_tools = llm.bind_tools(TOOLS)
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}


async def retrieve(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    检索节点：检查 Chroma 向量库是否有与用户查询相关的文档片段。
    如果知识库空或检索结果不相关，跳过 RAG 走纯对话模式。
    """
    messages = state.get("messages", [])
    user_id = state.get("user_id", "")
    if not messages:
        return {"messages": []}

    # 取最后一条人类消息作为查询
    query = ""
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            query = m.content
            break

    if not query:
        return {"messages": []}

    # 检索
    results = search(query, user_id=user_id, k=3)
    if not results:
        return {"messages": []}

    # 相关性过滤：score 越低越相关。超过阈值 = 语义差距太大，丢弃
    RELEVANCE_THRESHOLD = 0.8
    relevant = [r for r in results if r["score"] < RELEVANCE_THRESHOLD]
    if not relevant:
        return {"messages": []}

    # 拼接检索上下文
    context_parts = []
    for r in relevant:
        source = r["metadata"].get("filename", "未知文档")
        snippet = r["content"]
        context_parts.append(f"[来源: {source}]\n{snippet}")
    context = "\n\n---\n\n".join(context_parts)

    # 把 RAG 上下文拼入最后一条人类消息，用醒目的角色标记包裹，
    # 避免 SystemMessage 在多轮对话中出现在非首位导致千问 API 报错
    last_msg = messages[-1]
    if isinstance(last_msg, HumanMessage):
        enhanced_content = f"""[系统指令]
你是一个知识库助手。请基于以下检索到的文档片段回答用户的问题。
如果片段中没有相关信息，请如实告知用户，不要编造。

检索到的相关文档片段:
{context}

请根据上述片段回答用户的问题。

[用户问题]
{last_msg.content}"""
        return {"messages": [HumanMessage(content=enhanced_content)]}
    return {"messages": []}