# Smart-Log: Testing Strategy & Automated Test Suite

## 1. Testing Philosophy

Smart-Log maintains a rigorous automated test suite covering all tiers of the application:
1. **No Fabricated Benchmarks**: Unit tests utilize small, clearly designated synthetic mock fixtures strictly to verify mathematical invariants, code paths, and boundary conditions. These fixtures are never treated as the actual project dataset or published as benchmark metrics.
2. **Defensive Validation**: Tests explicitly verify that missing features, unapproved datasets, target leakages, or unmapped classes immediately throw clear, informative errors rather than silently fabricating results.

---

## 2. Test Suite Architecture

| Test Module | Coverage Areas |
|---|---|
| [`test_dataset_and_validation.py`](file:///c:/Users/Admin/OneDrive/Desktop/new%20major%20project/backend/tests/test_dataset_and_validation.py) | CSV and JSON dataset loading, memory-safe parsing, structural inspection (nulls, types, candidate targets), target leakage detection, and missing class validation. |
| [`test_feature_and_preprocessing.py`](file:///c:/Users/Admin/OneDrive/Desktop/new%20major%20project/backend/tests/test_feature_and_preprocessing.py) | RFC 3164 and RFC 5424 syslog parsing, JSON log parsing, candidate feature extraction, and `PreprocessingBundle` leak-free fitting on training data and transformation on test data with unseen categories. |
| [`test_models_and_evaluation.py`](file:///c:/Users/Admin/OneDrive/Desktop/new%20major%20project/backend/tests/test_models_and_evaluation.py) | `RandomForestModelWrapper` and `XGBoostModelWrapper` training and probability predictions, evaluation metric calculations (Accuracy, Precision, Recall, F1, FPR, Confusion Matrix, ROC-AUC), and `ModelRegistry` `.joblib` serialization and atomic activation. |
| [`test_shap_explainability.py`](file:///c:/Users/Admin/OneDrive/Desktop/new%20major%20project/backend/tests/test_shap_explainability.py) | SHAP `TreeExplainer` per-prediction attributions for Random Forest and XGBoost, base value extraction, feature direction indicators (`anomaly` vs `normal`), and global feature importance ranking. |
| [`test_api_endpoints.py`](file:///c:/Users/Admin/OneDrive/Desktop/new%20major%20project/backend/tests/test_api_endpoints.py) | Flask REST endpoints: `/api/health`, `/api/system/status`, `/api/training/guard` (asserting training is locked until approval), `/api/inference/predict-logs` (asserting error when no active model is configured), and `/api/reports/csv` & `/api/reports/pdf` binary downloads. |

---

## 3. Running the Backend Tests

Execute pytest with verbose output:

```bash
pytest backend/tests -v
```

Expected Output:
```
backend/tests/test_api_endpoints.py::test_api_health PASSED
backend/tests/test_api_endpoints.py::test_api_system_status PASSED
backend/tests/test_api_endpoints.py::test_training_guard_initial_state PASSED
backend/tests/test_api_endpoints.py::test_inference_without_active_model PASSED
backend/tests/test_api_endpoints.py::test_reports_csv_export_endpoint PASSED
backend/tests/test_api_endpoints.py::test_reports_pdf_export_endpoint PASSED
backend/tests/test_dataset_and_validation.py::test_dataset_loader_csv PASSED
backend/tests/test_dataset_and_validation.py::test_dataset_loader_json PASSED
backend/tests/test_dataset_and_validation.py::test_dataset_inspector PASSED
backend/tests/test_dataset_and_validation.py::test_dataset_validator_success PASSED
backend/tests/test_dataset_and_validation.py::test_dataset_validator_target_leakage PASSED
backend/tests/test_dataset_and_validation.py::test_dataset_validator_missing_class PASSED
backend/tests/test_feature_and_preprocessing.py::test_rfc_3164_syslog_parsing PASSED
backend/tests/test_feature_and_preprocessing.py::test_json_log_parsing PASSED
backend/tests/test_feature_and_preprocessing.py::test_feature_extraction PASSED
backend/tests/test_feature_and_preprocessing.py::test_preprocessing_pipeline_fit_and_transform PASSED
backend/tests/test_models_and_evaluation.py::test_random_forest_training PASSED
backend/tests/test_models_and_evaluation.py::test_xgboost_training PASSED
backend/tests/test_models_and_evaluation.py::test_evaluation_metrics_calculations PASSED
backend/tests/test_models_and_evaluation.py::test_model_registry_save_and_activate PASSED
backend/tests/test_shap_explainability.py::test_shap_instance_explanation_random_forest PASSED
backend/tests/test_shap_explainability.py::test_shap_instance_explanation_xgboost PASSED
backend/tests/test_shap_explainability.py::test_shap_global_importance PASSED

============================= 23 passed in 0.91s ==============================
```

---

## 4. Running the Frontend Typecheck and Build

Execute Vite production build in the `frontend/` directory:

```bash
cd frontend
npm run build
```

Expected Output:
```
vite building client environment for production...
✓ 2493 modules transformed.
✓ built in ~2s
```
