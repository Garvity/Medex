"""Provision and index the normalized medical corpus into Qdrant."""
import json
from pathlib import Path

import requests

from core.config import get_settings
from retrieval.qdrant_retriever import QdrantHybridRetriever


def ensure_dataset(dataset_path: Path, dataset_url: str | None) -> Path:
    if dataset_path.exists():
        return dataset_path
    if not dataset_url:
        raise FileNotFoundError(
            f"Medical corpus not found at {dataset_path}. Set MEDICAL_DATASET_URL or copy the normalized JSON corpus there."
        )
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(dataset_url, timeout=120)
    response.raise_for_status()
    dataset_path.write_bytes(response.content)
    return dataset_path


def ingest_dataset(dataset_path: str | None = None, batch_size: int = 64, start: int = 0) -> None:
    """Download (when necessary) and index normalized records, optionally resuming at ``start``."""
    if start < 0:
        raise ValueError("start must be zero or a positive document offset.")
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1.")

    settings = get_settings()
    source = ensure_dataset(Path(dataset_path or settings.medical_dataset_path), settings.medical_dataset_url)
    documents = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(documents, list) or not documents:
        raise ValueError(f"{source} is not a non-empty normalized medical document list.")

    retriever = QdrantHybridRetriever()
    for offset in range(start, len(documents), batch_size):
        retriever.upsert_documents(documents[offset : offset + batch_size])
        print(f"Indexed {min(offset + batch_size, len(documents))}/{len(documents)} documents")
    print(f"Knowledge base ready: {retriever.knowledge_base_status()}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download and index the medical corpus into Qdrant.")
    parser.add_argument("dataset", nargs="?", help="Optional path to medical_rag_dataset.json")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--start", type=int, default=0, help="Document offset at which to resume ingestion.")
    args = parser.parse_args()
    ingest_dataset(args.dataset, args.batch_size, args.start)
