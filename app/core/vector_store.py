"""
Chroma 向量存储封装。
collection "rag_documents"，metadata 记录 document_id/chunk_index/filename。
embedding 可选 Ollama (nomic-embed-text) 或 DashScope。
"""
import os
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_community.embeddings import DashScopeEmbeddings
from app.core.config import settings
_embedding = None
_vectorstore = None

def _get_embedding():
    global _embedding
    if _embedding is not None:
        return _embedding
    """获取 embedding 实例"""
    if settings.embedding_provider == "ollama":
        return OllamaEmbeddings(
            model=settings.embedding_model,
            base_url=settings.ollama_base_url,
        )
    elif settings.embedding_provider == "dashscope":
        return DashScopeEmbeddings(
            model=settings.embedding_model or "text-embedding-v3",
            dashscope_api_key=settings.dashscope_api_key,
        )
    else:
        raise ValueError(f"不支持的 embedding 类型: {settings.embedding_provider}")


def get_vectorstore() -> Chroma:
    """获取 Chroma 集合"""
    embedding = _get_embedding()
    os.makedirs(settings.chroma_persist_dir, exist_ok=True)
    return Chroma(
        collection_name=settings.chroma_collection_name,
        embedding_function=embedding,
        persist_directory=settings.chroma_persist_dir,
    )


def add_chunks(document_id: int, filename: str, chunks: list[str]):
    """批量添加分段到 Chroma"""
    if not chunks:
        return
    store = get_vectorstore()
    ids = [f"{document_id}_{i}" for i in range(len(chunks))]
    metadatas = [
        {"document_id": document_id, "chunk_index": i, "filename": filename}
        for i in range(len(chunks))
    ]
    store.add_texts(texts=chunks, ids=ids, metadatas=metadatas)


def search(query: str, k: int = 3) -> list[dict]:
    """检索最相关的 k 个分段"""
    store = get_vectorstore()
    results = store.similarity_search_with_score(query, k=k)
    return [
        {
            "content": doc.page_content,
            "score": score,
            "metadata": doc.metadata,
        }
        for doc, score in results
    ]


def delete_document_chunks(document_id: int):
    """删除文档的所有分段（按 metadata 过滤）"""
    store = get_vectorstore()
    # Chroma 不支持直接按 metadata delete，需要先查再删
    results = store.get(where={"document_id": document_id})
    if results and results["ids"]:
        store.delete(ids=results["ids"])