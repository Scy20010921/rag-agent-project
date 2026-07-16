from typing import TypedDict, List, Annotated, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from app.agents.nodes import call_model

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    model_type: Literal["ollama", "qwen_api"]

def build_chat_graph():
    graph = StateGraph(AgentState)
    graph.add_node("call_model", call_model)  # 异步节点会自动识别
    graph.set_entry_point("call_model")
    graph.add_edge("call_model", END)
    return graph.compile()