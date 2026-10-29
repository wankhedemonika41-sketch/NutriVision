import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.analysis.health_features import build_features
from app.analysis.health_scoring import compute_health_score, to_per_100g

CSV = ROOT / "packaged_foods_india.csv"
OUT = ROOT / "ml" / "data" / "training_data.csv"

COLUMN_MAP = {
    "Calories_kcal": "calories",
    "Carbohydrates_g": "carbohydrates",
    "Proteins_g": "protein",
    "Total_Fat_g": "total_fat",
    "Saturated_Fat_g": "saturated_fat",
    "Trans_Fat_g": "trans_fat",
    "Sugar_g": "sugar",
    "Sodium_mg": "sodium",
    "Dietary_Fiber_g": "fiber",
    "Cholesterol_mg": "cholesterol",
}


def main():
    df = pd.read_csv(CSV, encoding="utf-8-sig")

    for col in list(COLUMN_MAP) + ["Serving_Size_g"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    rows, skipped = [], 0

    for _, r in df.iterrows():
        nutrition = {
            new: (None if pd.isna(r[old]) else float(r[old]))
            for old, new in COLUMN_MAP.items()
        }
        serving = None if pd.isna(r["Serving_Size_g"]) else r["Serving_Size_g"]
        per100 = to_per_100g(nutrition, serving)

        # calories, sugar, sodium zaroori hain
        if any(per100.get(k) is None for k in ("calories", "sugar", "sodium")):
            skipped += 1
            continue

        features = build_features(per100, r["Ingredients"], r["Category"])
        result = compute_health_score(features)

        rows.append({
            "name": str(r["Item name"]).strip(),
            "category": r["Category"],
            **features,
            "health_score": result["score"],
            "grade": result["grade"],
        })

    out = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)

    print(f"Saved {len(out)} rows to {OUT}  (skipped {skipped})")
    print("\nGrade distribution:")
    print(out["grade"].value_counts().sort_index())
    print("\nScore by category (mean):")
    print(out.groupby("category")["health_score"].mean().round(1).sort_values())


if __name__ == "__main__":
    main()