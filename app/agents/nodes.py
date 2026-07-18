from typing import Dict, Any, AsyncGenerator
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage,SystemMessage
from app.core.llm_factory import get_llm_by_type
from app.agents.tools import TOOLS
from app.core.vector_store import search
async def call_model(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    异步节点：调用 LLM 并返回完整消息（用于非流式状态更新）。
    但我们将通过 astream_events 在路由层捕获 token 流，所以这里保持常规 invoke。
    """
    messages = state.get("messages", [])
    model_type = state.get("model_type", "ollama")
    if not messages:
        return {"messages": []}

    llm = get_llm_by_type(model_type)
    # bind_tools：让 LLM 知道有哪些工具可用
    llm_with_tools = llm.bind_tools(TOOLS)
    # 这里仍然用 invoke，因为 astream_events 会在路由层监听模型流
    response = await llm_with_tools.ainvoke(messages)
    # response = await llm.ainvoke(messages)  # 注意异步调用
    return {"messages": [response]}


async def retrieve(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    检索节点：从用户最后一条消息中提取查询，检索 Chroma 向量库，
    将检索到的相关片段拼入 system prompt 后返回。
    修改 state 中的 messages，在最前面插入一条带检索上下文的 system message。
    """
    messages = state.get("messages", [])
    if not messages:
        return {"messages": []}

        # 知识库空 → 跳过检索
    from app.core.doc_store import list_documents
    if not list_documents():
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
    results = search(query, k=3)

    if not results:
        return {"messages": []}

    # 拼接检索上下文
    context_parts = []
    for r in results:
        source = r["metadata"].get("filename", "未知文档")
        context_parts.append(f"[来源: {source}]\n{r['content']}")
    context = "\n\n---\n\n".join(context_parts)

    rag_prompt = f"""你是一个知识库助手。请基于以下检索到的文档片段回答用户的问题。
                如果片段中没有相关信息，请如实告知用户，不要编造。
                
                检索到的相关文档片段:
                {context}
                
                请根据上述片段回答用户的问题。"""

    # 在消息列表最前面插入 system message
    return {"messages": [SystemMessage(content=rag_prompt)]}