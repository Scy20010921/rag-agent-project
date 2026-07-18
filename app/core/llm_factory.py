from langchain_ollama import ChatOllama
from langchain_community.chat_models import ChatTongyi  # 千问百炼官方LangChain集成
from app.core.config import settings

def get_ollama_llm(temperature: float = 0.7):
    """获取本地 Ollama LLM 实例"""
    return ChatOllama(
        model=settings.ollama_model_name,
        base_url=settings.ollama_base_url,
        temperature=temperature,
        streaming=True,  # 开启流式
    )

def get_qwen_api_llm(temperature: float = 0.7):
    return ChatTongyi(
        model=settings.qwen_model_name,
        dashscope_api_key=settings.dashscope_api_key,
        temperature=temperature,
        streaming=True,
        model_kwargs={
            "result_format": "message"
        }
    )

def get_llm_by_type(model_type: str, temperature: float = 0.7):
    """工厂方法：根据类型字符串返回对应 LLM 实例"""
    if model_type == "ollama":
        return get_ollama_llm(temperature)
    elif model_type == "qwen_api":
        return get_qwen_api_llm(temperature)
    else:
        raise ValueError(f"不支持的模型类型: {model_type}")