from pydantic import BaseModel
from typing import Optional, Literal

class ChatRequest(BaseModel):
    message: str
    model_type: Literal["ollama", "qwen_api"] = "ollama"  # 默认走本地
    session_id: Optional[str] = None  # 预留多轮会话

class ChatChunkResponse(BaseModel):
    event: str  # "chunk" | "done"
    data: str   # 流式输出的文本片段