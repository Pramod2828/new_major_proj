# Smart-Log: Dataset Integration & Configuration Guide

This guide details the procedure for integrating any labelled server log dataset into **Smart-Log** once your target dataset is selected.

---

## 1. Supported File Formats

Smart-Log includes a modular dataset ingestion engine supporting:

| Format | Extensions | Format Requirements |
|---|---|---|
| **CSV** | `.csv` | Header row with column names; UTF-8 or Latin-1 encoded; comma-delimited. |
| **JSON** | `.json` | Array of record objects, or object with `"records"` / `"data"` list. |
| **JSONL** | `.jsonl` | Line-delimited JSON with one JSON object per line. |

---

## 2. Ingestion & Inspection Workflow

When a file is uploaded via the **Dataset Manager** (`/datasets`), the backend performs the following steps:

1. **Format Validation**: Ensures file format is `.csv`, `.json`, or `.jsonl` and does not exceed the 100MB limit.
2. **Metadata Extraction**: Calculates record counts, column counts, and file size.
3. **Type Inference**: Categorizes columns into:
   - Numerical (`int64`, `float64`)
   - Categorical (`object`, `string`, `bool`)
4. **Missing Value Analysis**: Computes exact null count and percentage for every column.
5. **Candidate Target Heuristics**: Flags low-cardinality columns (2–10 unique values) or columns with names like `label`, `class`, `anomaly`, `status`, `attack`, `tag`.
6. **Heuristic Candidate Timestamps & Messages**: Flags timestamp and text columns for reference.
7. **Sample Preview**: Generates clean preview records for the UI table.

---

## 3. Configuration Specification

Before any model training is permitted, the dataset schema must be explicitly configured:

### 3.1 Target Label Mapping
- **Target Column**: Select the column containing ground-truth classifications.
- **Normal Value**: Enter the exact string representation denoting benign activity (e.g., `0`, `Normal`, `Benign`, `false`). This maps to **Class 0**.
- **Anomaly Value**: Enter the exact string representation denoting suspicious or malicious activity (e.g., `1`, `Anomaly`, `Attack`, `true`). This maps to **Class 1** (the positive evaluation class).

### 3.2 Feature Selection & Leakage Prevention
- Select one or more feature columns for input to the ML algorithms.
- **CRITICAL**: The target ground truth column is **strictly forbidden** from the feature list. If selected, validation fails with a `CRITICAL LEAKAGE` error.

### 3.3 Split Ratios
- **Train Split**: Default `0.70` (70%). Must be $\ge 0.50$.
- **Validation Split**: Default `0.15` (15%). Used for early stopping and validation monitoring.
- **Test Split**: Default `0.15` (15%). Completely held-out set used strictly for final model evaluation and comparison.
- **Stratified Sampling**: Enabled by default to preserve class imbalance ratios across all splits.

---

## 4. Pre-Training Validation Checks

When clicking **"Save Configuration & Validate"**, the backend runs `DatasetValidator`:

- [x] Target column exists in the dataset.
- [x] Both Normal and Anomaly values exist in the target column.
- [x] Normal and Anomaly values are distinct.
- [x] Unmapped target values are detected and flagged.
- [x] At least one feature column is selected.
- [x] No target leakage exists.
- [x] Minimum dataset size is satisfied ($\ge 20$ valid records, $\ge 2$ instances of each class).
- [x] Split ratios sum to $1.0$.

Once validation passes, click **"Approve for Training"** to unlock the **Training Center**.
