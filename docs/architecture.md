# Smart-Log: Architecture & Technical Design

## 1. System Overview

**Smart-Log** is an automated syslog anomaly detection system engineered specifically for enterprise server security monitoring. The application operates on a dataset-independent philosophy: rather than assuming hardcoded schemas from academic benchmarks (such as HDFS, Thunderbird, or AIT-LDS), it provides an end-to-end configurable machine learning framework capable of ingesting arbitrary server log structures, inspecting schema distributions, training dual supervised classifiers (**Random Forest** and **XGBoost**), explaining predictions via **SHAP TreeExplainer**, and persisting operational telemetry in **SQLite**.

```
                           ┌──────────────────────────────────────────────┐
                           │            React 18 + Vite (SOC UI)          │
                           │ Tailwind CSS • Recharts • Lucide • TypeScript│
                           └──────────────────────┬───────────────────────┘
                                                  │ REST API (/api/*)
                                                  ▼
                           ┌──────────────────────────────────────────────┐
                           │             Flask Backend Core               │
                           │      CORS Restricted • Error Handlers        │
                           └───────┬──────────────────────────────┬───────┘
                                   │                              │
                   ┌───────────────▼──────────────┐  ┌────────────▼──────────────┐
                   │  Dataset Ingestion Engine    │  │   Live Inference Engine   │
                   │ • CSV / JSON / JSONL Loader  │  │ • RFC 3164 / 5424 Parser  │
                   │ • Schema Inspector           │  │ • Feature Vectorizer      │
                   │ • Leakage-Safe Validator     │  │ • Active Model Evaluator  │
                   └───────────────┬──────────────┘  └────────────┬──────────────┘
                                   │                              │
                   ┌───────────────▼──────────────┐               │
                   │     Preprocessing Pipeline   │               │
                   │ • Train-only Median Imputer  │               │
                   │ • Train-only Standard Scaler │               │
                   │ • One-Hot Encoder (Unknowns) │               │
                   └───────────────┬──────────────┘               │
                                   │                              │
         ┌─────────────────────────┴───────────────────────┐      │
         ▼                                                 ▼      ▼
┌──────────────────┐                             ┌──────────────────┐
│  Random Forest   │                             │     XGBoost      │
│  Classifier (RF) │                             │ Classifier (XGB) │
└────────┬─────────┘                             └────────┬─────────┘
         │                                                │
         └─────────────────────────┬──────────────────────┘
                                   ▼
                   ┌──────────────────────────────┐
                   │       Model Registry         │
                   │ • Joblib Bundles (.joblib)   │
                   │ • Schema & Transformer Cache │
                   │ • Atomic Activation Switch   │
                   └───────────────┬──────────────┘
                                   │
                                   ├──────────────────────────────┐
                                   ▼                              ▼
                   ┌──────────────────────────────┐ ┌───────────────────────────┐
                   │    SHAP Explainability       │ │     Reporting Engine      │
                   │ • TreeExplainer Attributions │ │ • Executive Audit PDF     │
                   │ • Per-Record Impact Vector   │ │ • RFC 4180 CSV Export     │
                   │ • Global Feature Weights     │ └───────────────────────────┘
                   └───────────────┬──────────────┘
                                   │
                                   ▼
                   ┌──────────────────────────────┐
                   │    SQLite Storage Layer      │
                   │ datasets • configs • models  │
                   │ predictions • audit_logs     │
                   └──────────────────────────────┘
```

---

## 2. Core Architectural Principles

### 2.1 Dataset-Independent Ingestion
The system treats datasets as external inputs with unknown column names and label conventions. The dataset manager inspects data types, missing value percentages, and unique values to identify candidate target columns, but never silently assigns a target label. The user explicitly maps values to binary classes:
- **Normal Class (0)**
- **Anomaly Class (1)** (Defined as positive class across all metrics)

### 2.2 Strict Target Leakage Prevention
To prevent data contamination:
- The target ground-truth column is forbidden from appearing in the feature columns list.
- Preprocessing transformers (imputers, scalers, encoders) are fitted **only** on the training split `X_train`.
- Validation and test splits are transformed using the already-fitted preprocessor.
- Unseen categorical levels in test data are gracefully ignored via `OneHotEncoder(handle_unknown='ignore')`.

### 2.3 Dual Supervised Classifier Parity
Random Forest and XGBoost are trained on identical data splits and evaluated on the identical held-out test split, enabling objective, measured comparisons across Accuracy, Precision, Recall, F1-Score, False Positive Rate (FPR), and ROC-AUC.

### 2.4 Separation of Training and Live Inference
- **Training Pipeline**: Requires ground-truth labels, performs stratified train/val/test splitting, fits transformers, trains models, evaluates test performance, and writes versioned artifacts to the Model Registry.
- **Inference Pipeline**: Operates on live unlabelled logs (RFC 3164, RFC 5424, or JSON), extracts candidate features, verifies feature schema compatibility against the active model, executes inference, generates SHAP explanations, and records telemetry in SQLite.
