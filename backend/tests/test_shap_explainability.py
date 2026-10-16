import pytest
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
from backend.explainability.shap_engine import ShapExplainabilityEngine

# SYNTHETIC TEST FIXTURE: Simple binary dataset
@pytest.fixture
def synthetic_shap_dataset():
    np.random.seed(42)
    X = np.random.randn(50, 4)
    # Feature 0 positively correlates with anomaly
    y = (X[:, 0] > 0.3).astype(int)
    feature_names = ["feat_error_count", "feat_entropy", "feat_msg_len", "feat_rate"]
    return X, y, feature_names

def test_shap_instance_explanation_random_forest(synthetic_shap_dataset):
    X, y, feature_names = synthetic_shap_dataset

    rf = RandomForestClassifier(n_estimators=10, random_state=42)
    rf.fit(X, y)

    sample_row = X[0]
    explanation = ShapExplainabilityEngine.explain_instance(
        model=rf,
        transformed_row=sample_row,
        feature_names=feature_names,
        algorithm="random_forest"
    )

    assert explanation["available"] is True
    assert explanation["base_value"] is not None
    assert len(explanation["contributions"]) == 4
    # Ensure sorted by absolute contribution
    abs_contribs = [c["abs_contribution"] for c in explanation["contributions"]]
    assert abs_contribs == sorted(abs_contribs, reverse=True)
    # Directions are marked
    for c in explanation["contributions"]:
        assert c["direction"] in ["anomaly", "normal", "neutral"]

def test_shap_instance_explanation_xgboost(synthetic_shap_dataset):
    X, y, feature_names = synthetic_shap_dataset

    xgb_clf = xgb.XGBClassifier(n_estimators=10, random_state=42, eval_metric="logloss")
    xgb_clf.fit(X, y)

    sample_row = X[0]
    explanation = ShapExplainabilityEngine.explain_instance(
        model=xgb_clf,
        transformed_row=sample_row,
        feature_names=feature_names,
        algorithm="xgboost"
    )

    assert explanation["available"] is True
    assert explanation["base_value"] is not None
    assert len(explanation["contributions"]) == 4

def test_shap_global_importance(synthetic_shap_dataset):
    X, y, feature_names = synthetic_shap_dataset

    rf = RandomForestClassifier(n_estimators=10, random_state=42)
    rf.fit(X, y)

    global_rank = ShapExplainabilityEngine.compute_global_importance(rf, X[:20], feature_names)
    assert len(global_rank) == 4
    assert "mean_abs_shap" in global_rank[0]
