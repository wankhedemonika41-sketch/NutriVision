from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from app.analysis.health_features import FEATURE_LABELS, build_features
from app.analysis.health_scoring import (
    compute_health_score, grade_for, risk_flags, to_per_100g,
)


MODEL_PATH = Path(__file__).resolve().parents[1] / "ml_models" / "health_model.joblib"

DISCLAIMER = (
    "Indicative score based on nutrient and ingredient content per 100 g. "
    "It is general information, not medical advice."
)


@lru_cache(maxsize=1)
def _load_model():
    if not MODEL_PATH.exists():
        return None
    import joblib
    return joblib.load(MODEL_PATH)


def warm_up():
    """
    Load the model in the background when the server starts, so the first
    real request does not have to wait for xgboost and scikit-learn to load.
    """
    import threading

    def work():
        try:
            _load_model()
        except Exception:
            pass          # a missing/broken model is handled later, per request

    threading.Thread(target=work, daemon=True, name="model-warm-up").start()


def _explain(bundle, X):
    """TreeSHAP contributions from XGBoost (last column is the bias term)."""
    import xgboost as xgb

    booster = bundle["regressor"].get_booster()
    values = booster.predict(xgb.DMatrix(X), pred_contribs=True)[0][:-1]

    pairs = sorted(zip(bundle["feature_columns"], values),
                   key=lambda p: abs(p[1]), reverse=True)

    reasons = []
    for name, value in pairs[:6]:
        if abs(value) < 0.5:
            continue
        reasons.append({
            "feature": name,
            "label": FEATURE_LABELS.get(name, name),
            "impact": round(float(value), 1),
            "direction": "raises" if value > 0 else "lowers",
        })
    return reasons


def compute_health(product, nutrition, already_per_100g=False, explain=True):
    """
    product / nutrition are plain dicts (same as build_report).

    explain=False skips the "why this score" reasons. The recommendations
    feature uses it, because it scores a whole category of products.
    """

    if not nutrition:
        return None

    per100 = to_per_100g(nutrition, product.get("serving_size"), already_per_100g)

    if any(per100.get(k) is None for k in ("calories", "sugar", "sodium")):
        return {
            "available": False,
            "reason": "Calories, sugar and sodium are needed to calculate a score.",
        }

    features = build_features(per100, product.get("ingredients"), product.get("category"))
    rule = compute_health_score(features)

    result = {
        "available": True,
        "score": rule["score"],
        "rule_score": rule["score"],
        "method": "rule-based",
        "reasons": [],
        "risks": risk_flags(features),
        "per_100g": per100,
        "disclaimer": DISCLAIMER,
    }

    bundle = _load_model()
    if bundle is not None:
        X = pd.DataFrame([features])[bundle["feature_columns"]]
        predicted = float(np.clip(bundle["regressor"].predict(X)[0], 0, 100))
        result["score"] = round(predicted, 1)
        result["method"] = f"ML ({bundle['model_name']})"
        if explain:
            result["reasons"] = _explain(bundle, X)

    grade, label = grade_for(result["score"])
    result["grade"] = grade
    result["label"] = label
    return result