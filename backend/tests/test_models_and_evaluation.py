import pytest
import numpy as np
import pandas as pd
from backend.models.random_forest.rf_classifier import RandomForestModelWrapper
from backend.models.xgboost.xgb_classifier import XGBoostModelWrapper
from backend.evaluation.metrics import EvaluationMetrics
from backend.models.registry import ModelRegistry
from backend.preprocessing.pipeline import PreprocessingBundle

# SYNTHETIC TEST FIXTURE: Mocked numeric features and labels
@pytest.fixture
def synthetic_train_test_data():
    np.random.seed(42)
    # 60 train samples, 20 test samples, 4 features
    X_train = np.random.randn(60, 4)
    y_train = np.array([0] * 45 + [1] * 15)  # Imbalanced
    X_test = np.random.randn(20, 4)
    y_test = np.array([0] * 15 + [1] * 5)
    return X_train, y_train, X_test, y_test

def test_random_forest_training(synthetic_train_test_data):
    X_train, y_train, X_test, y_test = synthetic_train_test_data

    rf = RandomForestModelWrapper(model_id="test_rf_1", hyperparameters={"n_estimators": 10, "random_state": 42})
    rf.fit(X_train, y_train)

    preds = rf.predict(X_test)
    probs = rf.predict_proba(X_test)

    assert len(preds) == len(y_test)
    assert probs.shape == (len(y_test), 2)
    assert set(preds).issubset({0, 1})

def test_xgboost_training(synthetic_train_test_data):
    X_train, y_train, X_test, y_test = synthetic_train_test_data

    xgb_wrapper = XGBoostModelWrapper(model_id="test_xgb_1", hyperparameters={"n_estimators": 10, "random_state": 42})
    xgb_wrapper.fit(X_train, y_train)

    preds = xgb_wrapper.predict(X_test)
    probs = xgb_wrapper.predict_proba(X_test)

    assert len(preds) == len(y_test)
    assert probs.shape == (len(y_test), 2)
    assert set(preds).issubset({0, 1})

def test_evaluation_metrics_calculations():
    y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    y_pred = np.array([0, 0, 0, 1, 0, 1, 1, 1])
    y_prob = np.array([0.1, 0.2, 0.3, 0.7, 0.4, 0.8, 0.9, 0.95])

    metrics = EvaluationMetrics.evaluate(y_true, y_pred, y_prob)

    assert metrics["accuracy"] == 0.75
    assert metrics["precision"] == 0.75  # 3 TP out of 4 predicted positive
    assert metrics["recall"] == 0.75     # 3 TP out of 4 actual positive
    assert metrics["false_positive_rate"] == 0.25  # 1 FP out of 4 actual negative
    assert metrics["confusion_matrix"]["tp"] == 3
    assert metrics["confusion_matrix"]["fp"] == 1
    assert metrics["confusion_matrix"]["tn"] == 3
    assert metrics["confusion_matrix"]["fn"] == 1
    assert metrics["roc_auc"] is not None

def test_model_registry_save_and_activate(test_temp_dir, test_db_path, synthetic_train_test_data):
    X_train, y_train, X_test, y_test = synthetic_train_test_data

    # Train a mock RF
    rf = RandomForestModelWrapper(model_id="reg_test_rf", hyperparameters={"n_estimators": 5, "random_state": 42})
    rf.fit(X_train, y_train)

    df_dummy = pd.DataFrame(X_train, columns=[f"f_{i}" for i in range(4)])
    bundle = PreprocessingBundle.infer_and_create(df_dummy, df_dummy.columns.tolist())
    bundle.fit_transform(df_dummy)

    metrics = {"accuracy": 0.95, "f1_score": 0.90}
    meta = {"dataset_id": "mock_ds", "dataset_name": "Mock Dataset"}

    # Save
    saved_info = ModelRegistry.save_model(rf, bundle, metrics, meta)
    assert saved_info["model_id"] == "reg_test_rf"

    # Load bundle
    loaded_bundle = ModelRegistry.load_bundle("reg_test_rf")
    assert loaded_bundle["name"] == rf.name
    assert loaded_bundle["algorithm"] == "random_forest"

    # Activate
    ModelRegistry.activate_model("reg_test_rf")
    active = ModelRegistry.get_active_model()
    assert active is not None
    assert active["id"] == "reg_test_rf"
    assert active["is_active"] is True
