import hashlib
import uuid
from dataclasses import dataclass
from typing import Any

import httpx
from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient, models

from core.config import get_settings


class KnowledgeBaseNotReady(RuntimeError):
    """Raised when Qdrant has not been populated with the curated medical corpus."""


@dataclass
class RetrievedDocument:
    id: str
    text: str
    name: str
    section: str
    source_type: str
    score: float = 0.0

    def citation(self) -> dict[str, str | float]:
        return {
            "id": self.id,
            "name": self.name,
            "section": self.section,
            "type": self.source_type,
            "score": round(self.score, 4),
        }


class JinaEmbedder:
    def __init__(self) -> None:
        self.settings = get_settings()

    def embed(self, texts: list[str], task: str) -> list[list[float]]:
        if not self.settings.jina_api_key:
            raise RuntimeError("JINA_API_KEY must be configured before retrieval can run.")
        response = httpx.post(
            "https://api.jina.ai/v1/embeddings",
            headers={"Authorization": f"Bearer {self.settings.jina_api_key}"},
            json={
                "model": self.settings.jina_embedding_model,
                "input": texts,
                "task": task,
                "dimensions": self.settings.jina_embedding_dimensions,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        return [item["embedding"] for item in response.json()["data"]]


class QdrantHybridRetriever:
    """Dense Jina + sparse BM25 retrieval fused with reciprocal-rank fusion."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = QdrantClient(url=self.settings.qdrant_url)
        self.embedder = JinaEmbedder()
        self.sparse_model: SparseTextEmbedding | None = None

    @property
    def collection_name(self) -> str:
        return self.settings.qdrant_collection

    def ensure_collection(self) -> None:
        if self.client.collection_exists(self.collection_name):
            return
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config={
                "dense": models.VectorParams(
                    size=self.settings.jina_embedding_dimensions,
                    distance=models.Distance.COSINE,
                )
            },
            sparse_vectors_config={"sparse": models.SparseVectorParams()},
        )

    def knowledge_base_status(self) -> dict[str, int | bool]:
        if not self.client.collection_exists(self.collection_name):
            return {"collection_exists": False, "points_count": 0}
        info = self.client.get_collection(self.collection_name)
        return {"collection_exists": True, "points_count": int(info.points_count or 0)}

    def _sparse_vector(self, text: str) -> models.SparseVector:
        if self.sparse_model is None:
            self.sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
        embedding = next(iter(self.sparse_model.embed([text])))
        return models.SparseVector(indices=list(embedding.indices), values=list(embedding.values))

    def retrieve(self, query: str, limit: int = 8) -> list[RetrievedDocument]:
        status = self.knowledge_base_status()
        if not status["collection_exists"] or not status["points_count"]:
            raise KnowledgeBaseNotReady(
                "The medical knowledge base has not been indexed. Start Qdrant and run "
                "`python -m retrieval.ingest` after configuring JINA_API_KEY."
            )
        dense = self.embedder.embed([query], task="retrieval.query")[0]
        response = self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                models.Prefetch(query=dense, using="dense", limit=limit * 4),
                models.Prefetch(query=self._sparse_vector(query), using="sparse", limit=limit * 4),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=limit,
            with_payload=True,
        )
        documents: list[RetrievedDocument] = []
        for point in response.points:
            payload = point.payload or {}
            documents.append(
                RetrievedDocument(
                    id=str(point.id),
                    text=str(payload.get("text", "")),
                    name=str(payload.get("name", "Unknown")),
                    section=str(payload.get("section", "overview")),
                    source_type=str(payload.get("type", "unknown")),
                    score=float(point.score),
                )
            )
        return documents

    def upsert_documents(self, documents: list[dict[str, Any]]) -> None:
        self.ensure_collection()
        texts = [str(document["text"]) for document in documents]
        dense_vectors = self.embedder.embed(texts, task="retrieval.passage")
        points = []
        for document, dense in zip(documents, dense_vectors, strict=True):
            source_hash = document.get("id") or hashlib.sha256(
                f"{document.get('type')}|{document.get('name')}|{document.get('section')}|{document['text']}".encode()
            ).hexdigest()
            source_id = str(uuid.uuid5(uuid.NAMESPACE_URL, str(source_hash)))
            points.append(
                models.PointStruct(
                    id=source_id,
                    vector={"dense": dense, "sparse": self._sparse_vector(document["text"])},
                    payload={
                        "text": document["text"],
                        "name": document.get("name", "Unknown"),
                        "section": document.get("section", "overview"),
                        "type": document.get("type", "unknown"),
                    },
                )
            )
        self.client.upsert(collection_name=self.collection_name, points=points, wait=True)
