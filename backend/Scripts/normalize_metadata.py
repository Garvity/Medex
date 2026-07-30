import json

INPUT_FILE = "medical_rag_dataset.json"
OUTPUT_FILE = "medical_rag_dataset_clean.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

clean_data = []

for doc in data:

    new_doc = {}

    # ---- Determine type ----
    if "drug_name" in doc:
        new_doc["type"] = "drug"
        new_doc["name"] = doc["drug_name"]

    elif doc.get("type") == "disease":
        new_doc["type"] = "disease"
        new_doc["name"] = doc.get("name")

    elif doc.get("type") == "nutrition":
        new_doc["type"] = "nutrition"
        new_doc["name"] = doc.get("name")

    elif doc.get("type") == "guideline":
        new_doc["type"] = "guideline"
        new_doc["name"] = doc.get("name")

    else:
        new_doc["type"] = "unknown"
        new_doc["name"] = doc.get("name", "unknown")

    # keep section and text unchanged
    new_doc["section"] = doc.get("section")
    new_doc["text"] = doc.get("text")

    clean_data.append(new_doc)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(clean_data, f, indent=2)

print("Metadata normalized")
print("Total documents:", len(clean_data))
