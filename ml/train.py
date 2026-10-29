import json
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, r2_score
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from xgboost import XGBRegressor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.analysis.health_features import FEATURE_COLUMNS

DATA = ROOT / "ml" / "data" / "training_data.csv"
MODEL_OUT = ROOT / "backend" / "app" / "ml_models" / "health_model.joblib"
REPORT_DIR = ROOT / "ml" / "reports"


def regression_experiment(X, y):
    models = {
        "LinearRegression": LinearRegression(),
        "DecisionTree": DecisionTreeRegressor(max_depth=8, random_state=42),
        "RandomForest": RandomForestRegressor(
            n_estimators=300, random_state=42, n_jobs=-1),
        "XGBoost": XGBRegressor(
            n_estimators=300, max_depth=4, learning_rate=0.05,
            subsample=0.9, random_state=42),
    }
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    results = {}
    for name, model in models.items():
        cv = cross_val_score(model, X, y, cv=kf, scoring="r2")
        model.fit(X_tr, y_tr)
        pred = model.predict(X_te)
        results[name] = {
            "cv_r2": round(float(cv.mean()), 4),
            "test_r2": round(float(r2_score(y_te, pred)), 4),
            "test_mae": round(float(mean_absolute_error(y_te, pred)), 3),
        }
    return models, results


def classification_experiment(X, y_grade):
    models = {
        "LogisticRegression": make_pipeline(
            StandardScaler(), LogisticRegression(max_iter=3000)),
        "DecisionTree": DecisionTreeClassifier(max_depth=6, random_state=42),
        "RandomForest": RandomForestClassifier(
            n_estimators=300, random_state=42, n_jobs=-1),
    }
    stratify = y_grade if y_grade.value_counts().min() >= 5 else None
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y_grade, test_size=0.2, random_state=42, stratify=stratify)

    results = {}
    for name, model in models.items():
        model.fit(X_tr, y_tr)
        pred = model.predict(X_te)
        results[name] = {
            "accuracy": round(float(accuracy_score(y_te, pred)), 4),
            "f1_weighted": round(float(f1_score(y_te, pred, average="weighted")), 4),
        }
    return results


def main():
    df = pd.read_csv(DATA)
    X = df[FEATURE_COLUMNS]
    y = df["health_score"]

    print(f"Training rows: {len(df)}, features: {len(FEATURE_COLUMNS)}\n")

    reg_models, reg_results = regression_experiment(X, y)
    print("== Health Score regression ==")
    print(pd.DataFrame(reg_results).T, "\n")

    clf_results = classification_experiment(X, df["grade"])
    print("== Grade classification (A/B/C/D) ==")
    print(pd.DataFrame(clf_results).T, "\n")

    # Deployment ke liye sirf tree models (SHAP ke liye)
    best_name = "XGBoost"   # deploy XGBoost: built-in SHAP explanations (no numba needed)
    print("Deploying:", best_name)

    final = clone(reg_models[best_name]).fit(X, y)   # poore data par refit

    importance = pd.Series(final.feature_importances_, index=FEATURE_COLUMNS)
    print("\nTop features:")
    print(importance.sort_values(ascending=False).head(8).round(3))

    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump({
        "regressor": final,
        "feature_columns": FEATURE_COLUMNS,
        "model_name": best_name,
    }, MODEL_OUT)

    (REPORT_DIR / "metrics.json").write_text(json.dumps({
        "regression": reg_results,
        "classification": clf_results,
        "deployed": best_name,
        "rows": len(df),
    }, indent=2))

    print("\nSaved model  ->", MODEL_OUT)
    print("Saved report ->", REPORT_DIR / "metrics.json")


if __name__ == "__main__":
    main()