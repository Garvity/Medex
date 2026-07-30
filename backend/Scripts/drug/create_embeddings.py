"""Index the processed drug RAG JSON into the shared Qdrant hybrid collection."""
import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from retrieval.qdrant_retriever import QdrantHybridRetriever


if __name__ == "__main__":
    source = Path(__file__).with_name("drug_rag_final.json")
    raw_documents = json.loads(source.read_text(encoding="utf-8"))
    documents = [
        {
            "type": "drug",
            "name": document.get("name") or document.get("drug_name", "Unknown"),
            "section": document.get("section", "overview"),
            "text": document["text"],
        }
        for document in raw_documents
    ]
    retriever = QdrantHybridRetriever()
    for offset in range(0, len(documents), 64):
        retriever.upsert_documents(documents[offset : offset + 64])
    print(f"Indexed {len(documents)} drug chunks into Qdrant.")
