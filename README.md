# Smart-Log: Automated Syslog Anomaly Detection for Server Security

A full-stack, dataset-independent security operations application for detecting anomalies in server syslogs using **Random Forest** and **XGBoost** supervised classifiers with **SHAP explainability**, SQLite persistence, and executive PDF/CSV reporting.

---

## 1. Project Highlights

- **Dataset-Independent Architecture**: Built without assumptions regarding specific academic datasets (no HDFS, AIT-LDS, or Thunderbird hardcoding). Ready for dataset integration via an interactive data inspection and label mapping interface.
- **Dual Supervised Machine Learning**:
  - `RandomForestClassifier` (scikit-learn) with configurable trees, depth, split constraints, and class weighting.
  - `XGBClassifier` (XGBoost) with configurable estimators, learning rate, subsample ratios, scale_pos_weight, and validation monitoring.
- **Leakage-Safe Preprocessing**: Imputers, scalers, and encoders are fitted **strictly on training splits**. The target ground truth column is barred from feature inputs.
- **Objective Evaluation**: Evaluates Accuracy, Precision, Recall, F1-Score, False Positive Rate (FPR), Confusion Matrix, and ROC/PR curves on identical held-out test splits.
- **SHAP TreeExplainer**: Computes exact mathematical feature contributions (+ pushing towards Anomaly in red/amber, - pushing towards Normal in cyan/blue) and global feature importance.
- **Production Safety Guards**: Training is disabled until an ingested dataset configuration has been validated and approved. Inference requires an active validated model with compatible feature schemas.
- **SOC Dark Interface**: High-density cybersecurity dashboard built with React, Vite, TypeScript, Tailwind CSS, and Recharts.

---

## 2. Technology Stack

- **Backend**: Python 3.11, Flask REST API, Flask-CORS, scikit-learn, XGBoost, SHAP, pandas, NumPy, joblib, ReportLab.
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Recharts, Lucide React, Framer Motion.
- **Persistence**: SQLite with foreign keys, transactional integrity, and parameterized queries.
- **Reports**: ReportLab executive PDF generator and RFC 4180 CSV exporter.

---

## 3. Project Structure

```
new major project/
├── backend/
│   ├── api/                     # REST API Blueprints
│   │   ├── system_api.py        # Health, system status, dashboard stats
│   │   ├── dataset_api.py       # Ingest, inspect, configure, validate, approve
│   │   ├── training_api.py      # Training guard, training trigger
│   │   ├── model_api.py         # Listing, compare, activation
│   │   ├── inference_api.py     # Live log prediction, history, SHAP
│   │   └── reports_api.py       # PDF & CSV download endpoints
│   ├── database/                # SQLite connection and schema
│   │   ├── schema.sql
│   │   └── db.py
│   ├── dataset/                 # Dataset ingestion & validation
│   │   ├── loader.py            # CSV, JSON, JSONL loader
│   │   ├── inspector.py         # Type inference, nulls, candidate targets
│   │   └── validator.py         # Target leakage prevention & split bounds
│   ├── preprocessing/           # Leak-free ColumnTransformer pipeline
│   │   └── pipeline.py
│   ├── feature_engineering/     # Modular log parsers & feature extractors
│   │   └── log_parser.py        # RFC 3164, RFC 5424, ISO, JSON parser
│   ├── models/                  # Supervised Classifiers & Registry
│   │   ├── base.py              # Abstract wrapper interface
│   │   ├── random_forest/       # RandomForestClassifier wrapper
│   │   ├── xgboost/             # XGBClassifier wrapper
│   │   └── registry.py          # .joblib bundles, versioning, activation
│   ├── evaluation/              # Comprehensive metrics calculator
│   │   └── metrics.py
│   ├── explainability/          # SHAP TreeExplainer integration
│   │   └── shap_engine.py
│   ├── services/                # Application coordination services
│   │   ├── training_service.py
│   │   └── inference_service.py
│   ├── reports/                 # PDF and CSV generator
│   │   ├── pdf_generator.py
│   │   └── csv_exporter.py
│   ├── collectors/              # Syslog stream adapter interface
│   │   └── stream_adapter.py
│   ├── tests/                   # Pytest test suite (23 unit tests)
│   ├── app.py                   # Flask entrypoint & CORS configuration
│   ├── config.py                # Configuration management
│   └── requirements.txt         # Pinned backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── layouts/             # AppLayout with SOC dark navigation
│   │   ├── pages/               # 9 Full SOC pages
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── DatasetsPage.tsx
│   │   │   ├── TrainingPage.tsx
│   │   │   ├── ModelsPage.tsx
│   │   │   ├── AnalysisPage.tsx
│   │   │   ├── SHAPPage.tsx
│   │   │   ├── HistoryPage.tsx
│   │   │   ├── ReportsPage.tsx
│   │   │   └── SettingsPage.tsx
│   │   ├── services/            # Typed REST API client
│   │   └── types/               # TypeScript definitions
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── docs/                        # Complete technical documentation
│   ├── architecture.md
│   ├── dataset_integration.md
│   ├── model_training.md
│   ├── api_documentation.md
│   └── testing.md
├── .env.example
├── .gitignore
└── README.md
```

---

## 4. Setup & Running Instructions

### 4.1 Backend Setup

1. **Install Dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Initialize Database & Start Backend Server**:
   ```bash
   python backend/app.py
   ```
   The Flask API will start on `http://127.0.0.1:5000`.
   Verify health at `http://127.0.0.1:5000/api/health`.

### 4.2 Frontend Setup

1. **Install Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Start Vite Development Server**:
   ```bash
   npm run dev
   ```
   Open your browser to `http://localhost:5173`.
   Requests to `/api/*` are automatically proxied to the Flask backend.

---

## 5. Verification & Testing

### 5.1 Run Automated Backend Unit Tests
```bash
pytest backend/tests -v
```
All 23 unit tests run in $< 1\text{s}$ covering dataset loading, leakage validation, preprocessing fit/transform consistency, Random Forest & XGBoost training, evaluation metrics, SHAP TreeExplainer attributions, SQLite persistence, and API endpoints.

### 5.2 Run Frontend Build
```bash
cd frontend
npm run build
```
Executes TypeScript typechecking and builds production assets into `frontend/dist/`.

---

## 6. How to Integrate Your Dataset (When Selected)

1. Open the web interface at `http://localhost:5173` and navigate to **Dataset Manager**.
2. Click **"Import Dataset File"** to upload your CSV, JSON, or JSONL log dataset.
3. The schema inspector will display row counts, column types, and missing value percentages.
4. In Step 1, select your target ground-truth column and specify which string value represents **Normal (0)** and which represents **Anomaly (1)**.
5. In Step 2, select the input feature columns (the target column is automatically excluded to prevent leakage).
6. Click **"Save Configuration & Validate"**.
7. If validation succeeds, click **"Approve for Training"**.
8. Navigate to **Training Center**, configure your desired Random Forest and XGBoost hyperparameters, and click **"Start Supervised Training"**.
9. In **Model Comparison**, review side-by-side metrics on the held-out test split, and click **"Set as Active"** on your preferred model.
10. Navigate to **Live Log Analysis** to paste or upload raw syslogs for instant anomaly classification, scoring, and per-record SHAP explanations.
