"""
LangSmith 可观测性初始化。
在 main.py 启动时调用 init_langsmith() 即可自动追踪所有 LangChain/LangGraph 调用。
"""
import os
from app.core.config import settings


def init_langsmith():
    """初始化 LangSmith 追踪。仅在设置了 API key 时生效。"""
    if not settings.langsmith_api_key:
        print("[langsmith] 未设置 LANGSMITH_API_KEY，跳过")
        return

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    print(f"[langsmith] 已启用，项目: {settings.langsmith_project}")
    os.environ["LANGCHAIN_HIDE_WARNINGS"] = "true"