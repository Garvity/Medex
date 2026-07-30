"""Index the merged medical corpus into Qdrant after dataset normalization."""
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from retrieval.ingest import ingest_dataset


if __name__ == "__main__":
    ingest_dataset(str(ROOT_DIR / "medical_rag_dataset.json"))
