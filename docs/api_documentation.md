# Smart-Log: REST API Documentation

Base URL: `http://127.0.0.1:5000/api`

---

## 1. System & Telemetry Endpoints

### `GET /api/health`
Check service health and SQLite connectivity.
- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "service": "Smart-Log Backend API",
  "version": "1.0.0",
  "database": true
}
```

### `GET /api/system/status`
Retrieve hardware telemetry, storage metrics, and active model overview.
- **Response `200 OK`**:
```json
{
  "active_model": { "id": "rf_123", "name": "Random Forest", "algorithm": "random_forest", "version": "1.0.0" },
  "counts": { "datasets": 2, "models": 2, "total_predictions": 50, "anomalies_flagged": 8 },
  "system_resources": { "cpu_usage_percent": 14.2, "memory_usage_percent": 62.1, "memory_available_mb": 6144.5 }
}
```

### `GET /api/dashboard/stats`
Telemetry statistics for the SOC dashboard widgets.
- **Response `200 OK`**:
```json
{
  "total_processed": 50,
  "anomalies_flagged": 8,
  "normal_count": 42,
  "anomaly_rate": 16.0,
  "active_model": { ... },
  "recent_activity": [ ... ],
  "has_data": true
}
```

---

## 2. Dataset Management Endpoints

### `POST /api/datasets/upload`
Upload CSV, JSON, or JSONL dataset file.
- **Form Data**: `file` (multipart/form-data)
- **Response `201 Created`**:
```json
{
  "success": true,
  "dataset_id": "ds_4a71b2",
  "filename": "server_auth_logs.csv",
  "rows": 1000,
  "columns": 8,
  "format": "csv",
  "inspection": { ... }
}
```

### `GET /api/datasets`
List all uploaded datasets and their configuration/approval status.

### `GET /api/datasets/<id>/inspect`
Full column inspection, null percentages, candidate target distributions, and sample preview records.

### `POST /api/datasets/<id>/configure`
Save target label mappings, feature list, and split ratios.
- **Body**:
```json
{
  "target_column": "label",
  "normal_value": "Normal",
  "anomaly_value": "Anomaly",
  "feature_columns": ["msg_len", "entropy", "error_count"],
  "train_ratio": 0.70,
  "val_ratio": 0.15,
  "test_ratio": 0.15,
  "stratified": true
}
```

### `POST /api/datasets/<id>/validate`
Execute leak-prevention and class-distribution validation.

### `POST /api/datasets/<id>/approve`
Explicitly approve validated dataset configuration, unlocking model training.

---

## 3. Model Training & Comparison Endpoints

### `GET /api/training/guard`
Checks if any dataset has been validated and approved.
- **Response `200 OK`**:
```json
{
  "can_train": true,
  "message": "Training is permitted on approved datasets."
}
```

### `POST /api/training/train`
Triggers supervised training on approved training splits.
- **Body**:
```json
{
  "dataset_id": "ds_4a71b2",
  "algorithms": ["random_forest", "xgboost"],
  "rf_params": { "n_estimators": 100, "max_depth": 15, "class_weight": "balanced" },
  "xgb_params": { "n_estimators": 100, "max_depth": 6, "learning_rate": 0.1 }
}
```

### `GET /api/models`
List all trained models with test evaluation metrics.

### `POST /api/models/<id>/activate`
Atomically sets specified model as the active inference model.

### `GET /api/models/compare`
Returns side-by-side metric comparison, confusion matrices, and ROC/PR points.

---

## 4. Live Inference & SHAP Endpoints

### `POST /api/inference/predict-logs`
Run inference on array of raw log strings.
- **Body**: `{ "logs": ["<34>Oct 11 22:14:15 srv1 sshd[123]: Failed password..."], "compute_shap": true }`

### `POST /api/inference/predict-file`
Upload raw syslog text file for batch processing.

### `GET /api/inference/history`
Query historical predictions with optional filters (`is_anomaly=true`, `limit=50`).

### `GET /api/inference/<id>`
Fetch full prediction record with raw log, extracted features, and SHAP attributions.

---

## 5. Reports & Export Endpoints

### `GET /api/reports/pdf`
Downloads executive audit report in PDF format (`Content-Type: application/pdf`).

### `GET /api/reports/csv`
Downloads prediction history in tabular CSV format (`Content-Type: text/csv`).
