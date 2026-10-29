from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xgboost as xgb

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "backend" / "app" / "ml_models" / "health_model.joblib"
DATA = ROOT / "ml" / "data" / "training_data.csv"
OUT = ROOT / "ml" / "reports"


def main():
    bundle = joblib.load(MODEL)
    model = bundle["regressor"]
    cols = bundle["feature_columns"]
    X = pd.read_csv(DATA)[cols]

    # TreeSHAP values from XGBoost itself (last column = bias term)
    contribs = model.get_booster().predict(xgb.DMatrix(X), pred_contribs=True)
    shap_values = contribs[:, :-1]

    OUT.mkdir(parents=True, exist_ok=True)

    mean_abs = np.abs(shap_values).mean(axis=0)
    order = np.argsort(mean_abs)[-12:]          # top 12 features

    # 1) importance bar chart
    plt.figure(figsize=(8, 5))
    plt.barh([cols[i] for i in order], mean_abs[order], color="#2563eb")
    plt.xlabel("Mean |SHAP value| (impact on health score)")
    plt.title("Feature importance (SHAP)")
    plt.tight_layout()
    plt.savefig(OUT / "shap_importance.png", dpi=150)
    plt.close()

    # 2) beeswarm-style summary plot
    rng = np.random.default_rng(42)
    plt.figure(figsize=(9, 6))
    scatter = None
    for row, i in enumerate(order):
        values = X.iloc[:, i].to_numpy(dtype=float)
        span = values.max() - values.min()
        norm = (values - values.min()) / span if span > 0 else np.zeros_like(values)
        y = row + rng.uniform(-0.25, 0.25, size=len(values))
        scatter = plt.scatter(shap_values[:, i], y, c=norm,
                              cmap="coolwarm", s=8, vmin=0, vmax=1)
    plt.yticks(range(len(order)), [cols[i] for i in order])
    plt.axvline(0, color="grey", linewidth=0.8)
    plt.xlabel("SHAP value (impact on health score)")
    plt.title("SHAP summary (red = high feature value)")
    plt.colorbar(scatter, label="Feature value (low to high)")
    plt.tight_layout()
    plt.savefig(OUT / "shap_summary.png", dpi=150)
    plt.close()

    print("Saved plots in", OUT)


if __name__ == "__main__":
    main()