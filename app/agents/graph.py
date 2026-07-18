from typing import TypedDict, List, Annotated, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from app.agents.nodes import call_model, retrieve
from app.agents.tools import TOOLS
from langgraph.prebuilt import ToolNode
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    model_type: Literal["ollama", "qwen_api"]

def _should_continue(state: AgentState) -> Literal["tool_execute", "__end__"]:
    """
    条件路由：最后一条消息是否包含 tool_calls。
    有 → 去工具节点执行；无 → 结束。
    """
    messages = state.get("messages", [])
    if not messages:
        return "__end__"
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tool_execute"
    return "__end__"

def build_chat_graph():
    """
    RAG Agent 图：
    retrieve → call_model → (tool_calls?) → tool_execute → call_model → ... → END
    retrieve 节点内部会先检查知识库是否为空——空则跳过检索直接走 call_model。
       """
    # 工具执行节点：LangGraph 内置 ToolNode，自动匹配 tool_call 名称
    tool_node = ToolNode(TOOLS)

    graph = StateGraph(AgentState)

    # 检索节点
    graph.add_node("retrieve", retrieve)
    # 模型节点
    graph.add_node("call_model", call_model)
    # 工具执行节点
    graph.add_node("tool_execute", tool_node)

    graph.set_entry_point("retrieve")
    # retrieve → call_model
    graph.add_edge("retrieve", "call_model")

    # call_model 之后按条件路由
    graph.add_conditional_edges(
        "call_model",
        _should_continue,
        {"tool_execute": "tool_execute", "__end__": END}
    )

    # 工具执行完后回到 call_model，让 LLM 处理工具结果
    graph.add_edge("tool_execute", "call_model")

    return graph.compile()
    # graph = StateGraph(AgentState)
    # graph.add_node("call_model", call_model)  # 异步节点会自动识别
    # graph.set_entry_point("call_model")
    # graph.add_edge("call_model", END)
    # return graph.compile()