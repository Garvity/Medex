import pandas as pd
import json

INPUT_FILE = "foods.csv"

df = pd.read_csv(INPUT_FILE)

rag_entries = []

for _, row in df.iterrows():

    food = str(row["Food Items"])

    nutrients = []

    if pd.notna(row.get("Energy kcal")):
        nutrients.append(f"{row['Energy kcal']} kcal energy")

    if pd.notna(row.get("Carbs")):
        nutrients.append(f"{row['Carbs']} g carbohydrates")

    if pd.notna(row.get("Protein(g)")):
        nutrients.append(f"{row['Protein(g)']} g protein")

    if pd.notna(row.get("Fat(g)")):
        nutrients.append(f"{row['Fat(g)']} g fat")

    if pd.notna(row.get("Fibre(g)")):
        nutrients.append(f"{row['Fibre(g)']} g fiber")

    if pd.notna(row.get("Calcium(mg)")):
        nutrients.append(f"{row['Calcium(mg)']} mg calcium")

    if len(nutrients) == 0:
        continue

    description = f"{food} contains " + ", ".join(nutrients) + "."

    rag_entries.append({
        "type": "nutrition",
        "name": food,
        "section": "nutrition",
        "text": description
    })

with open("nutrition_rag.json", "w", encoding="utf-8") as f:
    json.dump(rag_entries, f, indent=2)

print("Nutrition dataset created")
print("Total foods processed:", len(rag_entries))