import pandas as pd
import json
import re

df = pd.read_csv("processed_drugs.csv")

documents = []

def clean_text(text):
    if pd.isna(text):
        return ""
    
    # remove section numbers like "1 INDICATIONS", "5 WARNINGS"
    text = re.sub(r'\b\d+(\.\d+)?\s+[A-Z ]+', '', str(text))
    
    # remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

for _, row in df.iterrows():

    purpose = clean_text(row["purpose"])
    warnings = clean_text(row["warnings"])
    side_effects = clean_text(row["side_effects"])
    interactions = clean_text(row["interactions"])

    doc = f"""
Drug: {row['drug_name']}

Purpose:
{purpose}

Warnings:
{warnings}

Side Effects:
{side_effects}

Drug Interactions:
{interactions}
"""

    documents.append({
        "drug_name": row["drug_name"],
        "text": doc.strip()
    })

with open("drug_rag_clean.json", "w", encoding="utf-8") as f:
    json.dump(documents, f, indent=2)

print("Created", len(documents), "clean RAG documents")