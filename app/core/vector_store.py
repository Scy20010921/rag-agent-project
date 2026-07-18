"""
Chroma 向量存储封装。
按 scope 隔离 collection：
- public 文档 → "rag_public"
- user 私有文档 → "rag_user_{user_id}"
单例缓存 embedding 和 vectorstore 实例。
"""
import os
import time
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_community.embeddings import DashScopeEmbeddings
from app.core.config import settings

_embedding = None
_stores = {}  # {collection_name: Chroma} 缓存

# 文档数量缓存：避免每次检索都查 MySQL
_doc_count_cache = {"value": -1, "ts": 0}  # -1 表示未初始化
_CACHE_TTL = 10  # 秒


def _get_embedding():
    global _embedding
    if _embedding is not None:
        return _embedding
    if settings.embedding_provider == "ollama":
        _embedding = OllamaEmbeddings(
            model=settings.embedding_model,
            base_url=settings.ollama_base_url,
        )
    elif settings.embedding_provider == "dashscope":
        _embedding = DashScopeEmbeddings(
            model=settings.embedding_model or "text-embedding-v3",
            dashscope_api_key=settings.dashscope_api_key,
        )
    else:
        raise ValueError(f"不支持的 embedding 类型: {settings.embedding_provider}")
    return _embedding


def _get_collection_name(scope: str, user_id: str = "") -> str:
    if scope == "public":
        return "rag_public"
    elif scope == "user":
        return f"rag_user_{user_id}"
    raise ValueError(f"无效 scope: {scope}")


def get_vectorstore(scope: str = "public", user_id: str = "") -> Chroma:
    col_name = _get_collection_name(scope, user_id)
    if col_name in _stores:
        return _stores[col_name]
    embedding = _get_embedding()
    os.makedirs(settings.chroma_persist_dir, exist_ok=True)
    store = Chroma(
        collection_name=col_name,
        embedding_function=embedding,
        persist_directory=settings.chroma_persist_dir,
    )
    _stores[col_name] = store
    return store


def _has_documents() -> bool:
    """带缓存的检查知识库是否有文档"""
    global _doc_count_cache
    now = time.time()
    if _doc_count_cache["value"] >= 0 and (now - _doc_count_cache["ts"]) < _CACHE_TTL:
        return _doc_count_cache["value"] > 0
    try:
        from app.core.doc_store import list_documents
        docs = list_documents()
        count = len(docs)
        _doc_count_cache = {"value": count, "ts": now}
        return count > 0
    except Exception:
        return True  # 连接失败时不阻塞对话


def invalidate_doc_cache():
    """上传/删除文档后调用，强制下次检索时刷新缓存"""
    global _doc_count_cache
    _doc_count_cache = {"value": -1, "ts": 0}


def add_chunks(document_id: int, filename: str, chunks: list[str], scope: str = "public", user_id: str = ""):
    if not chunks:
        return
    store = get_vectorstore(scope, user_id)
    col_name = _get_collection_name(scope, user_id)
    ids = [f"{col_name}_{document_id}_{i}" for i in range(len(chunks))]
    metadatas = [
        {"document_id": document_id, "chunk_index": i, "filename": filename, "scope": scope}
        for i in range(len(chunks))
    ]
    store.add_texts(texts=chunks, ids=ids, metadatas=metadatas)
    invalidate_doc_cache()


def search(query: str, user_id: str = "", k: int = 3) -> list[dict]:
    """检索：同时查 public + 用户的私有 collection"""
    # 快速检查：没有文档直接返回空
    if not _has_documents():
        return []

    collections = [("public", "")]
    if user_id:
        collections.append(("user", user_id))

    all_results = []
    for scope, uid in collections:
        try:
            store = get_vectorstore(scope, uid)
            results = store.similarity_search_with_score(query, k=k)
            for doc, score in results:
                all_results.append({
                    "content": doc.page_content,
                    "score": score,
                    "metadata": doc.metadata,
                })
        except Exception as e:
            print(f"[VECTOR] 检索 {scope} 失败: {e}", flush=True)

    all_results.sort(key=lambda x: x["score"])
    return all_results[:k]


def delete_document_chunks(document_id: int, scope: str = "public", user_id: str = ""):
    store = get_vectorstore(scope, user_id)
    try:
        results = store.get(where={"document_id": document_id})
        if results and results["ids"]:
            store.delete(ids=results["ids"])
    except Exception as e:
        print(f"[VECTOR] 删除失败: {e}", flush=True)
    invalidate_doc_cache()