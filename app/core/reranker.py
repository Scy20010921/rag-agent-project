"""
交叉编码器重排序模块。
使用 BAAI/bge-reranker-v2-m3 对向量检索结果进行精排。
"""
from sentence_transformers import CrossEncoder

MODEL_NAME = "BAAI/bge-reranker-v2-m3"
_reranker = None


def _get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(MODEL_NAME)
    return _reranker


def rerank(query: str, documents: list[dict], top_k: int = 3) -> list[dict]:
    """
    对向量检索结果进行重排序。
    参数:
        query: 用户查询文本
        documents: 向量检索结果列表，每项需包含 'content' 字段
        top_k: 最终返回几条结果
    返回: 按相关性从高到低排序的结果，每项新增 'rerank_score' 字段
    """
    if len(documents) <= 1:
        return documents

    model = _get_reranker()
    pairs = [(query, d["content"]) for d in documents]
    scores = model.predict(pairs)

    for d, score in zip(documents, scores):
        d["rerank_score"] = float(score)

    documents.sort(key=lambda x: x["rerank_score"], reverse=True)
    return documents[:top_k]