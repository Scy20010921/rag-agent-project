from typing import TypedDict, List, Annotated, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from app.agents.nodes import call_model, retrieve, supervisor
from app.agents.tools import TOOLS
from langgraph.prebuilt import ToolNode
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    model_type: Literal["ollama", "qwen_api"]
    intent: str  # 新增：用于存储路由结果

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

def route_supervisor(state: AgentState) -> Literal["retrieve", "call_model"]:
    """总管路由逻辑"""
    intent = state.get("intent", "chat")
    if intent == "knowledge":
        print("[Router] 🧠 路由到知识库 Agent (检索)")
        return "retrieve"
    else:
        print("[Router] 💬 路由到闲聊 Agent (跳过检索)")
        return "call_model"

def build_chat_graph():
    """
    多 Agent 图结构：
    supervisor → (条件路由)
        ├── knowledge → retrieve → call_model → (工具循环) → END
        └── chat     → call_model → (工具循环) → END
    """
    # 工具执行节点：LangGraph 内置 ToolNode，自动匹配 tool_call 名称
    tool_node = ToolNode(TOOLS)

    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor)  # 总管
    graph.add_node("retrieve", retrieve)  # 知识库专用
    graph.add_node("call_model", call_model)  # 通用 LLM
    # 工具执行节点
    graph.add_node("tool_execute", tool_node)

    # 入口
    graph.set_entry_point("supervisor")

    # call_model 之后按条件路由
    # 总管条件路由
    graph.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "retrieve": "retrieve",
            "call_model": "call_model"
        }
    )

    # 知识库链路
    graph.add_edge("retrieve", "call_model")

    # call_model 之后的条件路由（工具循环）
    graph.add_conditional_edges(
        "call_model",
        _should_continue,
        {"tool_execute": "tool_execute", "__end__": END}
    )

    # 工具执行完后回到 call_model
    graph.add_edge("tool_execute", "call_model")

    return graph.compile()
    # graph = StateGraph(AgentState)
    # graph.add_node("call_model", call_model)  # 异步节点会自动识别
    # graph.set_entry_point("call_model")
    # graph.add_edge("call_model", END)
    # return graph.compile()