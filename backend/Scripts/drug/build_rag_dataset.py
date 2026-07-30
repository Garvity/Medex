import pandas as pd
import json
import re

INPUT_FILE = "processed_drugs.csv"
OUTPUT_FILE = "drug_rag_final.json"

MAX_CHUNK_LENGTH = 800


def clean_text(text):
    if pd.isna(text):
        return ""

    text = str(text)

    # remove numbering like (5.1) etc
    text = re.sub(r"\(\s*\d+(\.\d+)?\s*\)", "", text)

    # remove excessive spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def split_into_chunks(text, max_len=MAX_CHUNK_LENGTH):

    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current = ""

    for sentence in sentences:

        if len(current) + len(sentence) < max_len:
            current += " " + sentence
        else:
            chunks.append(current.strip())
            current = sentence

    if current:
        chunks.append(current.strip())

    return chunks


df = pd.read_csv(INPUT_FILE)

rag_docs = []

for _, row in df.iterrows():

    drug = str(row["drug_name"]).strip()

    sections = {
        "purpose": row.get("purpose", ""),
        "warnings": row.get("warnings", ""),
        "side_effects": row.get("side_effects", ""),
        "drug_interactions": row.get("interactions", "")
    }

    for section, text in sections.items():

        text = clean_text(text)

        if len(text) < 20:
            continue

        chunks = split_into_chunks(text)

        for chunk in chunks:

            rag_docs.append({
                "drug_name": drug,
                "section": section,
                "text": chunk
            })


with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(rag_docs, f, indent=2)


print("RAG dataset created")
print("Total chunks:", len(rag_docs))