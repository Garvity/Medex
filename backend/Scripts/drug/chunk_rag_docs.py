import json

with open("drug_rag_clean.json", "r", encoding="utf-8") as f:
    data = json.load(f)

chunks = []

for item in data:

    drug = item["drug_name"]
    text = item["text"]

    parts = text.split("\n\n")

    for part in parts:
        if ":" in part:
            section = part.split(":")[0].strip()
        else:
            section = "general"

        chunks.append({
            "drug_name": drug,
            "section": section,
            "text": part.strip()
        })

with open("drug_rag_chunks.json", "w", encoding="utf-8") as f:
    json.dump(chunks, f, indent=2)

print("Created", len(chunks), "RAG chunks")