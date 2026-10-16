"""
AIT-LDS Training Pipeline for Smart-Log
========================================
Trains Random Forest and XGBoost classifiers on the three AIT Log Data Set
scenarios: fox, russellmitchell, santos.

Workflow:
  1. Load and label-join log files from gather/ using labels/ JSON annotations
  2. Extract features via existing LogParser.extract_features()
  3. Train on FOX (primary), evaluate cross-dataset on RUSSELLMITCHELL + SANTOS
  4. Train per-dataset models for each of the three datasets
  5. Save all models via ModelRegistry (inactive by default)
  6. Report full metrics: precision, recall, F1, confusion matrix, FPR

Usage:
  python -m backend.training.train_ait_lds [--dry-run]
"""

import os
import sys
import json
import time
import logging
import argparse
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import (
    classification_report, confusion_matrix, precision_score,
    recall_score, f1_score, roc_auc_score
)
from sklearn.model_selection import train_test_split

import os
import sys
from pathlib import Path

# Correct project root determination using Config
from backend.config import Config

# Repository root is the parent of the backend directory
REPO_ROOT = Config.BASE_DIR.parent
# Ensure the repository root is in sys.path for imports
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Dataset root directory
DATASETS_ROOT = REPO_ROOT / "backend" / "datasets"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ait_lds_training")

# ── Constants ─────────────────────────────────────────────────────────────────
# Removed duplicate definition; using DATASETS_ROOT defined above
EXCLUDED_DATASET = "HDFS_v1"  # Never touched

# Log files to use from each dataset's gather/ directory
LOG_SOURCES = [
    # (gather_subpath_pattern, log_type)
    # These paths are resolved against each host's gather folder
    ("*/logs/auth.log*",       "auth"),
    ("*/logs/syslog*",         "syslog"),
    ("*/logs/audit/audit.log", "audit"),
    ("*/logs/apache2/*.log*",  "apache_access"),
    ("*/logs/openvpn.log*",    "openvpn"),
]

# Max lines to sample per log file to cap RAM usage (None = all)
MAX_LINES_PER_FILE = 100_000

# Feature columns used for training (numerical + categorical)
NUMERICAL_FEATURES = [
    "message_length", "token_count", "digit_ratio", "entropy",
    "severity_level", "has_error", "has_warning", "has_auth",
    "has_failed_auth", "has_denied", "has_ip",
]
CATEGORICAL_FEATURES = ["service"]
ALL_FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES


def handle_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Public utility to detect and remove exact duplicate records and conflicting-label groups.

    Works with any dataframe by using all non‑label columns as feature keys when the
    predefined ``ALL_FEATURES`` list is not applicable (e.g., synthetic test data).
    Returns cleaned DataFrame and a dict with statistics:
        - exact_duplicates_removed
        - conflicting_groups
        - conflicting_records_removed
    """
    stats_dup: Dict[str, Any] = {
        "exact_duplicates_removed": 0,
        "conflicting_groups": 0,
        "conflicting_records_removed": 0,
    }
    # Identify feature columns: prefer the known feature list, but fall back to any
    # column that is not the label column ``is_anomaly``.
    feature_cols = [col for col in ALL_FEATURES if col in df.columns]
    if not feature_cols:
        feature_cols = [c for c in df.columns if c != "is_anomaly"]
    # Subset for duplicate detection includes the label column.
    subset_cols = feature_cols + ["is_anomaly"] if "is_anomaly" in df.columns else feature_cols
    # Exact duplicate removal based on all feature columns + label.
    dup_mask = df.duplicated(subset=subset_cols, keep='first')
    stats_dup["exact_duplicates_removed"] = int(dup_mask.sum())
    df = df[~dup_mask]

    # Conflicting groups: same feature values but differing labels.
    if feature_cols:
        grp = df.groupby(feature_cols)["is_anomaly"].nunique()
        conflict_features = grp[grp > 1].index
        stats_dup["conflicting_groups"] = len(conflict_features)
        if len(conflict_features) > 0:
            conflict_mask = df.set_index(feature_cols).index.isin(conflict_features)
            stats_dup["conflicting_records_removed"] = int(conflict_mask.sum())
            df = df[~conflict_mask]
    return df, stats_dup

# Attack-phase labels that indicate a line is anomalous
ATTACK_PHASE_LABELS = {
    "foothold", "escalate", "crack_passwords", "attacker_vpn",
    "scan", "exploit", "lateral_movement", "exfiltration",
    "persistence", "collection", "command_and_control"
}

RANDOM_STATE = 42


# ── Label Loading ─────────────────────────────────────────────────────────────

def load_label_index(label_file_path: Path) -> Dict[int, List[str]]:
    """
    Parse a labels/*.log JSON-lines file.
    Each line: {"line": <1-indexed int>, "labels": ["foothold", ...], "rules": {...}}
    Returns dict: {0-indexed_line_number -> [label_str, ...]}
    """
    label_index: Dict[int, List[str]] = {}
    if not label_file_path.exists():
        return label_index
    try:
        with open(label_file_path, "r", encoding="utf-8", errors="replace") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                    # "line" in AIT-LDS is 1-indexed
                    line_no = int(obj["line"])          # 1-indexed
                    labels = obj.get("labels", [])
                    label_index[line_no - 1] = labels   # store as 0-indexed
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
    except Exception as e:
        logger.warning(f"Could not load label file {label_file_path}: {e}")
    return label_index


def find_label_file(labels_dir: Path, gather_log_path: Path, gather_dir: Path) -> Optional[Path]:
    """
    Find the matching labels/ file for a given gather/ log file.
    Mapping: gather/<host>/logs/<...>/file.log -> labels/<host>/logs/<...>/file.log
    """
    try:
        rel = gather_log_path.relative_to(gather_dir)
        candidate = labels_dir / rel
        if candidate.exists():
            return candidate
        # Try with .2, .3 suffix stripped
        stem = candidate.stem
        for suffix in ["", ".1", ".2", ".3"]:
            c = candidate.with_name(stem.rstrip(".123") + suffix)
            if c.exists():
                return c
    except ValueError:
        pass
    return None


# ── Log File Discovery ────────────────────────────────────────────────────────

def discover_log_files(dataset_dir: Path) -> List[Path]:
    """
    Find all readable text log files under gather/ that match our source types.
    Excludes binary journal files and huge suricata eve.json files (>50MB).
    """
    gather_dir = dataset_dir / "gather"
    if not gather_dir.exists():
        return []

    found = []
    for p in gather_dir.rglob("*"):
        if not p.is_file():
            continue
        name = p.name
        # Include only known log types
        if not (
            name.startswith("auth") or
            name.startswith("syslog") or
            name == "audit.log" or
            (("access" in name or "error" in name) and name.endswith(".log")) or
            name.startswith("openvpn")
        ):
            continue
        # Skip huge files (>50MB uncompressed) and binary journal files
        try:
            size = p.stat().st_size
            if size > 50 * 1024 * 1024:
                logger.debug(f"Skipping large file ({size//1024//1024}MB): {p.name}")
                continue
        except OSError:
            continue
        # Skip binary journal files
        if name.endswith(".journal") or name.endswith(".journal~"):
            continue
        found.append(p)

    return sorted(found)


# ── Dataset Loading ───────────────────────────────────────────────────────────

def load_dataset(
    dataset_name: str,
    max_lines_per_file: int = MAX_LINES_PER_FILE
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load all log files from a dataset, join labels, extract features.
    Returns (DataFrame with features + label column, metadata dict).
    """
    assert dataset_name != EXCLUDED_DATASET, "HDFS_v1 must not be used in this workflow"
    dataset_dir = DATASETS_ROOT / dataset_name
    labels_dir = dataset_dir / "labels"
    gather_dir = dataset_dir / "gather"

    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")

    log_files = discover_log_files(dataset_dir)
    logger.info(f"[{dataset_name}] Found {len(log_files)} log files to process")

    records = []
    stats = {
        "files_processed": 0,
        "total_lines": 0,
        "labeled_lines": 0,
        "anomalous_lines": 0,
        "normal_lines": 0,
        "parse_errors": 0,
        "files_with_labels": 0,
    }

    for log_path in log_files:
        label_file = find_label_file(labels_dir, log_path, gather_dir)
        label_index = load_label_index(label_file) if label_file else {}
        has_labels = len(label_index) > 0
        if has_labels:
            stats["files_with_labels"] += 1

        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                for line_idx, raw_line in enumerate(f):
                    if max_lines_per_file and line_idx >= max_lines_per_file:
                        break
                    raw_line = raw_line.rstrip("\n\r")
                    if not raw_line.strip():
                        continue

                    stats["total_lines"] += 1

                    # Parse log line
                    try:
                        parsed = LogParser.parse_line(raw_line)
                        features = LogParser.extract_features(parsed)
                    except Exception:
                        stats["parse_errors"] += 1
                        continue

                    # Determine label
                    attack_labels = label_index.get(line_idx, [])
                    is_anomaly = int(
                        any(lbl in ATTACK_PHASE_LABELS for lbl in attack_labels)
                    )

                    if attack_labels:
                        stats["labeled_lines"] += 1
                    if is_anomaly:
                        stats["anomalous_lines"] += 1
                    else:
                        stats["normal_lines"] += 1

                    record = {
                        "source_file": str(log_path.relative_to(dataset_dir)),
                        "line_idx": line_idx,
                        "raw_log": raw_line[:512],  # truncate for storage
                        "attack_labels": ",".join(attack_labels) if attack_labels else "",
                        "is_anomaly": is_anomaly,
                    }
                    record.update({k: v for k, v in features.items() if k in ALL_FEATURES})
                    records.append(record)

        except Exception as e:
            logger.warning(f"  Could not read {log_path}: {e}")
            continue

        stats["files_processed"] += 1

    if not records:
        raise ValueError(f"No records loaded from dataset '{dataset_name}'")

    df = pd.DataFrame(records)

    # -----------------------------------
    # Duplicate & Conflicting-label handling
    # -----------------------------------
    def _handle_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Detect and remove exact duplicate records and conflicting-label groups.

        Returns cleaned DataFrame and a dict with stats:
            - exact_duplicates_removed: int
            - conflicting_groups: int
            - conflicting_records_removed: int
        """
        stats_dup: Dict[str, Any] = {
            "exact_duplicates_removed": 0,
            "conflicting_groups": 0,
            "conflicting_records_removed": 0,
        }
        # Identify exact duplicates (including label) based on ALL_FEATURES + is_anomaly
        dup_mask = df.duplicated(subset=ALL_FEATURES + ["is_anomaly"], keep='first')
        stats_dup["exact_duplicates_removed"] = int(dup_mask.sum())
        df = df[~dup_mask]

        # Identify conflicting groups: same feature values but differing is_anomaly
        grp = df.groupby(ALL_FEATURES)["is_anomaly"].nunique()
        conflict_features = grp[grp > 1].index
        stats_dup["conflicting_groups"] = len(conflict_features)
        if len(conflict_features) > 0:
            # Build mask of rows belonging to any conflicting group
            conflict_mask = df.set_index(ALL_FEATURES).index.isin(conflict_features)
            stats_dup["conflicting_records_removed"] = int(conflict_mask.sum())
            df = df[~conflict_mask]
        return df, stats_dup

    # Apply duplicate handling and merge stats
    df, dup_stats = _handle_duplicates(df)
    stats.update(dup_stats)
    # Update total_records after cleaning
    stats["total_records"] = len(df)
    stats["anomaly_rate"] = round(df["is_anomaly"].mean() * 100, 2)


    # Ensure all feature columns exist (fill missing with defaults)
    for col in NUMERICAL_FEATURES:
        if col not in df.columns:
            df[col] = 0
    for col in CATEGORICAL_FEATURES:
        if col not in df.columns:
            df[col] = "unknown"

    stats["total_records"] = len(df)
    stats["anomaly_rate"] = round(df["is_anomaly"].mean() * 100, 2)

    logger.info(
        f"[{dataset_name}] Loaded {len(df):,} records | "
        f"Anomalous: {stats['anomalous_lines']:,} ({stats['anomaly_rate']}%) | "
        f"Files with labels: {stats['files_with_labels']}/{stats['files_processed']}"
    )

    return df, stats


# ── Training Helpers ──────────────────────────────────────────────────────────

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_proba: Optional[np.ndarray] = None) -> Dict[str, Any]:
    """Compute full classification metrics including FPR."""
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel() if cm.shape == (2, 2) else (cm[0,0], 0, 0, cm[1,1])

    fpr = round(fp / (fp + tn), 4) if (fp + tn) > 0 else 0.0

    metrics = {
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
        "recall":    round(recall_score(y_true, y_pred, zero_division=0), 4),
        "f1_score":  round(f1_score(y_true, y_pred, zero_division=0), 4),
        "false_positive_rate": fpr,
        "true_negatives":  int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_positives":  int(tp),
        "confusion_matrix": cm.tolist(),
        "classification_report": classification_report(
            y_true, y_pred, target_names=["Normal", "Anomaly"], output_dict=True, zero_division=0
        )
    }
    if y_proba is not None:
        try:
            metrics["roc_auc"] = round(roc_auc_score(y_true, y_proba), 4)
        except Exception:
            metrics["roc_auc"] = None
    return metrics


def train_model(
    model_wrapper,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    algorithm: str
) -> Tuple[Any, Dict[str, Any]]:
    """Fit model and return trained wrapper + validation metrics."""
    logger.info(f"  Training {algorithm} on {len(X_train):,} samples...")
    t0 = time.time()
    model_wrapper.fit(X_train, y_train)
    elapsed = round(time.time() - t0, 1)

    y_pred = model_wrapper.predict(X_val)
    y_proba = None
    if hasattr(model_wrapper, "predict_proba"):
        try:
            proba = model_wrapper.predict_proba(X_val)
            y_proba = proba[:, 1] if proba.shape[1] > 1 else proba[:, 0]
        except Exception:
            pass

    metrics = compute_metrics(y_val, y_pred, y_proba)
    metrics["training_duration_seconds"] = elapsed
    metrics["train_samples"] = int(len(X_train))
    metrics["val_samples"] = int(len(X_val))
    metrics["train_anomaly_rate"] = round(float(y_train.mean()) * 100, 2)
    metrics["val_anomaly_rate"] = round(float(y_val.mean()) * 100, 2)

    logger.info(
        f"  [{algorithm}] Done in {elapsed}s | "
        f"Val F1={metrics['f1_score']} Prec={metrics['precision']} "
        f"Rec={metrics['recall']} FPR={metrics['false_positive_rate']}"
    )
    return model_wrapper, metrics


def evaluate_cross_dataset(model_wrapper, preprocessor, df_test: pd.DataFrame, dataset_name: str) -> Dict[str, Any]:
    """Evaluate a trained model on a held-out dataset (no re-fitting)."""
    X_test = preprocessor.transform(df_test[ALL_FEATURES])
    y_test = df_test["is_anomaly"].values

    y_pred = model_wrapper.predict(X_test)
    y_proba = None
    if hasattr(model_wrapper, "predict_proba"):
        try:
            proba = model_wrapper.predict_proba(X_test)
            y_proba = proba[:, 1] if proba.shape[1] > 1 else proba[:, 0]
        except Exception:
            pass

    metrics = compute_metrics(y_test, y_pred, y_proba)
    metrics["eval_dataset"] = dataset_name
    metrics["eval_samples"] = int(len(y_test))
    metrics["eval_anomaly_rate"] = round(float(y_test.mean()) * 100, 2)

    logger.info(
        f"  Cross-eval on [{dataset_name}]: {len(y_test):,} samples | "
        f"F1={metrics['f1_score']} Prec={metrics['precision']} "
        f"Rec={metrics['recall']} FPR={metrics['false_positive_rate']}"
    )
    return metrics


def make_model_id(algorithm: str, dataset: str) -> str:
    """Generate deterministic model ID."""
    base = f"ait_{dataset}_{algorithm}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    return base.lower().replace(" ", "_")


def run_training(dry_run: bool = False):
    """Main training entry point."""
    logger.info("=" * 70)
    logger.info("AIT-LDS Training Pipeline — Smart-Log")
    logger.info(f"Project root: {PROJECT_ROOT}")
    logger.info(f"Datasets root: {DATASETS_ROOT}")
    logger.info(f"Dry run: {dry_run}")
    logger.info("=" * 70)

    # Initialize database
    init_db()

    # ── Step 1: Load all three datasets ──────────────────────────────────────
    logger.info("\n── Step 1: Loading datasets ──")
    datasets = {}
    dataset_stats = {}

    for ds_name in ["fox", "russellmitchell", "santos"]:
        logger.info(f"\nLoading dataset: {ds_name}")
        try:
            df, stats = load_dataset(ds_name)
            datasets[ds_name] = df
            dataset_stats[ds_name] = stats
        except Exception as e:
            logger.error(f"Failed to load {ds_name}: {e}")
            raise

    # ── Step 2: Class imbalance summary ──────────────────────────────────────
    logger.info("\n── Step 2: Class distribution ──")
    for ds_name, df in datasets.items():
        total = len(df)
        n_anom = df["is_anomaly"].sum()
        logger.info(f"  {ds_name}: {total:,} total | {n_anom:,} anomalous ({round(n_anom/total*100,2)}%) | {total-n_anom:,} normal")

    if dry_run:
        logger.info("\n[DRY RUN] Stopping before training. Data loading successful.")
        return datasets, dataset_stats, {}

    # ── Step 3: Train on FOX (primary), cross-eval on RUSSELL + SANTOS ───────
    logger.info("\n── Step 3: Train on FOX, cross-evaluate on RUSSELLMITCHELL + SANTOS ──")

    df_fox = datasets["fox"]

    # Train/val split on FOX only (no leakage from other datasets)
    X_fox = df_fox[ALL_FEATURES]
    y_fox = df_fox["is_anomaly"].values

    X_tr, X_val, y_tr, y_val = train_test_split(
        X_fox, y_fox, test_size=0.2, random_state=RANDOM_STATE, stratify=y_fox
    )
    logger.info(f"  FOX train: {len(X_tr):,} | val: {len(X_val):,}")

    # Fit preprocessor on TRAIN ONLY
    preprocessor_fox = PreprocessingBundle.infer_and_create(X_tr, ALL_FEATURES)
    X_tr_t  = preprocessor_fox.fit_transform(X_tr)
    X_val_t  = preprocessor_fox.transform(X_val)

    saved_models = {}

    for algo, ModelCls, algo_key in [
        ("Random Forest", RandomForestModelWrapper, "random_forest"),
        ("XGBoost",       XGBoostModelWrapper,       "xgboost"),
    ]:
        logger.info(f"\n  === {algo} (trained on FOX) ===")
        model_id = make_model_id(algo_key, "fox")

        hp = {"n_estimators": 150, "max_depth": 15, "random_state": RANDOM_STATE}
        if algo_key == "xgboost":
            pos_weight = max(1, int((y_tr == 0).sum() / max((y_tr == 1).sum(), 1)))
            hp["scale_pos_weight"] = pos_weight
            hp["n_estimators"] = 200
            hp["max_depth"] = 8
            hp["learning_rate"] = 0.1

        wrapper = ModelCls(model_id=model_id, hyperparameters=hp)
        wrapper, val_metrics = train_model(wrapper, X_tr_t, y_tr, X_val_t, y_val, algo)

        # Cross-dataset evaluation (no re-fitting, use same preprocessor)
        cross_evals = {}
        for cross_ds in ["russellmitchell", "santos"]:
            logger.info(f"  Cross-eval [{algo}] on {cross_ds}")
            ce_metrics = evaluate_cross_dataset(wrapper, preprocessor_fox, datasets[cross_ds], cross_ds)
            cross_evals[cross_ds] = ce_metrics

        # Save model (inactive by default)
        full_metrics = {
            "val_on_fox": val_metrics,
            "cross_eval": cross_evals,
            "training_duration_seconds": val_metrics["training_duration_seconds"]
        }
        dataset_meta = {
            "dataset_id": f"ait_fox_{algo_key}",
            "dataset_name": "AIT-LDS FOX scenario",
            "label_mapping": {"normal": "0", "anomaly": "1"},
            "source_datasets": ["fox"],
            "cross_eval_datasets": ["russellmitchell", "santos"],
            "attack_phase_labels": sorted(ATTACK_PHASE_LABELS),
            "log_sources": ["auth.log", "syslog", "audit.log", "apache_access.log", "openvpn.log"],
            "train_stats": dataset_stats["fox"]
        }

        meta = ModelRegistry.save_model(wrapper, preprocessor_fox, full_metrics, dataset_meta, version="1.0.0")
        logger.info(f"  Saved [{algo}|FOX] model_id={meta['model_id']} (INACTIVE)")
        saved_models[f"fox_{algo_key}"] = meta

    # ── Step 4: Per-dataset models ────────────────────────────────────────────
    logger.info("\n── Step 4: Train per-dataset models (FOX already done above) ──")

    for ds_name in ["russellmitchell", "santos"]:
        logger.info(f"\n  === Per-dataset training on {ds_name} ===")
        df_ds = datasets[ds_name]
        X_ds = df_ds[ALL_FEATURES]
        y_ds = df_ds["is_anomaly"].values

        X_tr_d, X_val_d, y_tr_d, y_val_d = train_test_split(
            X_ds, y_ds, test_size=0.2, random_state=RANDOM_STATE, stratify=y_ds
        )
        logger.info(f"  {ds_name} train: {len(X_tr_d):,} | val: {len(X_val_d):,}")

        preprocessor_ds = PreprocessingBundle.infer_and_create(X_tr_d, ALL_FEATURES)
        X_tr_dt  = preprocessor_ds.fit_transform(X_tr_d)
        X_val_dt = preprocessor_ds.transform(X_val_d)

        for algo, ModelCls, algo_key in [
            ("Random Forest", RandomForestModelWrapper, "random_forest"),
            ("XGBoost",       XGBoostModelWrapper,       "xgboost"),
        ]:
            model_id = make_model_id(algo_key, ds_name)

            hp = {"n_estimators": 150, "max_depth": 15, "random_state": RANDOM_STATE}
            if algo_key == "xgboost":
                pos_weight = max(1, int((y_tr_d == 0).sum() / max((y_tr_d == 1).sum(), 1)))
                hp["scale_pos_weight"] = pos_weight
                hp["n_estimators"] = 200
                hp["max_depth"] = 8
                hp["learning_rate"] = 0.1

            wrapper = ModelCls(model_id=model_id, hyperparameters=hp)
            wrapper, val_metrics = train_model(wrapper, X_tr_dt, y_tr_d, X_val_dt, y_val_d, algo)

            full_metrics = {
                "val_on_own_split": val_metrics,
                "training_duration_seconds": val_metrics["training_duration_seconds"]
            }
            dataset_meta = {
                "dataset_id": f"ait_{ds_name}_{algo_key}",
                "dataset_name": f"AIT-LDS {ds_name.upper()} scenario",
                "label_mapping": {"normal": "0", "anomaly": "1"},
                "source_datasets": [ds_name],
                "attack_phase_labels": sorted(ATTACK_PHASE_LABELS),
                "log_sources": ["auth.log", "syslog", "audit.log", "apache_access.log", "openvpn.log"],
                "train_stats": dataset_stats[ds_name]
            }

            meta = ModelRegistry.save_model(wrapper, preprocessor_ds, full_metrics, dataset_meta, version="1.0.0")
            logger.info(f"  Saved [{algo}|{ds_name}] model_id={meta['model_id']} (INACTIVE)")
            saved_models[f"{ds_name}_{algo_key}"] = meta

    logger.info("\n── Training Complete ──")
    logger.info(f"Saved {len(saved_models)} models (all INACTIVE by default)")
    for key, meta in saved_models.items():
        logger.info(f"  {key}: {meta['model_id']}")

    return datasets, dataset_stats, saved_models


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AIT-LDS Training Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Load data only, no training")
    args = parser.parse_args()
    run_training(dry_run=args.dry_run)
