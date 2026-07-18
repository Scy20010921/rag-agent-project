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

    # Embedding (Ollama: nomic-embed-text / DashScope: text-embedding-v3)
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "ollama")  # "ollama" or "dashscope"
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

    # MySQL
    mysql_host: str = os.getenv("MYSQL_HOST", "localhost")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user: str = os.getenv("MYSQL_USER", "root")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "")
    mysql_database: str = os.getenv("MYSQL_DATABASE", "rag_agent")

    # Chroma
    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
    chroma_collection_name: str = os.getenv("CHROMA_COLLECTION", "rag_documents")

    # Document processing
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "500"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "100"))

    # LangSmith (可观测性)
    langsmith_api_key: str = os.getenv("LANGSMITH_API_KEY", "")
    langsmith_project: str = os.getenv("LANGSMITH_PROJECT", "rag-agent")


settings = Settings()