import json
import pandas as pd

input_file = "drug_labels.json"
output_file = "processed_drugs.csv"

rows = []

with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

for record in data["results"]:

    # Drug name
    drug_name = None
    if "openfda" in record and "brand_name" in record["openfda"]:
        drug_name = record["openfda"]["brand_name"][0]

    # Purpose
    purpose = " ".join(record.get("indications_and_usage", []))

    # Warnings
    warnings = " ".join(record.get("warnings_and_cautions", []))

    # Side effects
    side_effects = " ".join(record.get("adverse_reactions", []))

    # Drug interactions
    interactions = " ".join(record.get("drug_interactions", []))

    rows.append({
        "drug_name": drug_name,
        "purpose": purpose,
        "warnings": warnings,
        "side_effects": side_effects,
        "interactions": interactions
    })

df = pd.DataFrame(rows)

# Clean dataset
df = df.dropna(subset=["drug_name"])
df = df.drop_duplicates(subset=["drug_name"])

df.to_csv(output_file, index=False)

print("Dataset created with", len(df), "drugs")