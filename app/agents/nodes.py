from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.core.llm_factory import get_llm_by_type
from app.agents.tools import TOOLS
from app.core.vector_store import search


async def call_model(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    异步节点：调用 LLM（绑定工具）并返回消息。
    """
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
    检索节点：从用户最后一条消息中提取查询，检索 Chroma 向量库。
    知识库为空时直接跳过。使用缓存避免每次查询 MySQL。
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

    # 检索（public + 用户私有）
    # search 内部会先检查是否有文档，无文档快速返回空列表
    results = search(query, user_id=user_id, k=3)

    if not results:
        return {"messages": []}

    # 拼接检索上下文
    context_parts = []
    for r in results:
        source = r["metadata"].get("filename", "未知文档")
        snippet = r["content"][:300]  # 每段限制 300 字，避免撑爆上下文
        context_parts.append(f"[来源: {source}]\n{snippet}")
    context = "\n\n---\n\n".join(context_parts)

    rag_prompt = f"""你是一个知识库助手。请基于以下检索到的文档片段回答用户的问题。
如果片段中没有相关信息，请如实告知用户，不要编造。

检索到的相关文档片段:
{context}

请根据上述片段回答用户的问题。"""

    return {"messages": [SystemMessage(content=rag_prompt)]}