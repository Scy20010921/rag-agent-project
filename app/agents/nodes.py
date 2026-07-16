from typing import Dict, Any, AsyncGenerator
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from app.core.llm_factory import get_llm_by_type


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
    # 这里仍然用 invoke，因为 astream_events 会在路由层监听模型流
    response = await llm.ainvoke(messages)  # 注意异步调用
    return {"messages": [response]}