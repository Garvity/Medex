"""Retrieval evaluation for the Qdrant hybrid pipeline.

Run after indexing a dataset: ``python tests/evaluation.py``.
"""
import json
from pathlib import Path

from retrieval.qdrant_retriever import QdrantHybridRetriever


def reciprocal_rank(documents: list, expected_type: str) -> float:
    for index, document in enumerate(documents, start=1):
        if document.source_type == expected_type:
            return 1 / index
    return 0.0


def dcg(documents: list, expected_type: str) -> float:
    return sum((1.0 / __import__("math").log2(index + 1)) for index, document in enumerate(documents, start=1) if document.source_type == expected_type)


def evaluate(k: int = 5) -> dict[str, float]:
    golden_path = Path(__file__).with_name("golden_queries.json")
    examples = json.loads(golden_path.read_text(encoding="utf-8"))
    retriever = QdrantHybridRetriever()
    top1 = recall_at_k = mrr = ndcg = 0.0

    for example in examples:
        documents = retriever.retrieve(example["query"], limit=k)
        expected = example["expected_type"]
        top1 += float(bool(documents and documents[0].source_type == expected))
        recall_at_k += float(any(document.source_type == expected for document in documents))
        mrr += reciprocal_rank(documents, expected)
        ideal = 1.0
        ndcg += dcg(documents, expected) / ideal

    total = len(examples)
    metrics = {
        "top1_accuracy": round(top1 / total, 4),
        f"recall_at_{k}": round(recall_at_k / total, 4),
        "mrr": round(mrr / total, 4),
        f"ndcg_at_{k}": round(ndcg / total, 4),
    }
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    evaluate()
