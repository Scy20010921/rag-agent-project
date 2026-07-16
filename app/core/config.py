import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # DashScope (千问百炼)
    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", "")
    qwen_model_name: str = os.getenv("QWEN_MODEL_NAME", "qwen-plus")

    # Ollama
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model_name: str = os.getenv("OLLAMA_MODEL_NAME", "qwen2.5")


settings = Settings()