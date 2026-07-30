import pandas as pd
import json

INPUT_FILE = "Diseases_Symptoms.csv"

df = pd.read_csv(INPUT_FILE)

rag_entries = []

for _, row in df.iterrows():

    disease = row["Name"]

    symptoms = str(row["Symptoms"])
    treatments = str(row["Treatments"])

    if len(symptoms) > 5:
        rag_entries.append({
            "type": "disease",
            "name": disease,
            "section": "symptoms",
            "text": symptoms
        })

    if len(treatments) > 5:
        rag_entries.append({
            "type": "disease",
            "name": disease,
            "section": "treatment",
            "text": treatments
        })

with open("disease_rag.json", "w", encoding="utf-8") as f:
    json.dump(rag_entries, f, indent=2)

print("Disease RAG dataset created")
print("Total diseases:", df.shape[0])
print("Total chunks:", len(rag_entries))