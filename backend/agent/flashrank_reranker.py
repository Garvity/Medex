from functools import lru_cache

from flashrank import Ranker, RerankRequest

from retrieval.qdrant_retriever import RetrievedDocument


@lru_cache
def get_ranker() -> Ranker:
    return Ranker(model_name="ms-marco-MiniLM-L-12-v2")


def rerank(query: str, documents: list[RetrievedDocument], limit: int = 5) -> list[RetrievedDocument]:
    if not documents:
        return []
    result = get_ranker().rerank(
        RerankRequest(query=query, passages=[{"id": document.id, "text": document.text} for document in documents])
    )
    by_id = {document.id: document for document in documents}
    reranked: list[RetrievedDocument] = []
    for item in result[:limit]:
        document = by_id[str(item["id"])]
        document.score = float(item.get("score", document.score))
        reranked.append(document)
    return reranked
