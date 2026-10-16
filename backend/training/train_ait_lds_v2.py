"""
AIT-LDS Training Pipeline for Smart-Log  (v2 — post-audit fixes)
=================================================================
Changes from v1:
  FIX 1: All 22 attacker labels now mapped to is_anomaly=1 (was only 3).
          Uses ait_label_config.ANOMALOUS_LABELS as single source of truth.
  FIX 2: Deduplication of rotated log files before train/val split.
          Conflict resolution: any line labeled anomalous in any file → anomalous.
  FIX 3: severity_level removed from feature schema (constant = 6, std ≈ 0).
          LogParser.extract_features() already updated to omit it.

Workflow:
  1. Load and label-join log files from gather/ using labels/ JSON annotations
  2. Extract features via updated LogParser.extract_features()
  3. Deduplicate by raw line MD5 with conflict resolution
  4. Train on FOX (primary); cross-evaluate on RUSSELLMITCHELL + SANTOS
  5. Also train per-dataset models for each scenario
  6. Save models via ModelRegistry (INACTIVE by default)

Usage:
  python -m backend.training.train_ait_lds_v2 [--dry-run]
"""

import os
import sys
import json
import time
import hashlib
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import (
    classification_report, confusion_matrix,
    precision_score, recall_score, f1_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split

# ── Path setup ────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.feature_engineering.log_parser import LogParser
from backend.preprocessing.pipeline import PreprocessingBundle
from backend.models.random_forest.rf_classifier import RandomForestModelWrapper
from backend.models.xgboost.xgb_classifier import XGBoostModelWrapper
from backend.models.registry import ModelRegistry
from backend.database.db import init_db
from backend.training.ait_label_config import (
    ANOMALOUS_LABELS, UNCERTAIN_LABELS, ALL_FEATURES,
    NUMERICAL_FEATURES, CATEGORICAL_FEATURES,
    classify_labels, DEDUP_KEY,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ait_lds_v2")

DATASETS_ROOT   = PROJECT_ROOT / "backend" / "datasets"
DATASETS        = ["fox", "russellmitchell", "santos"]
EXCLUDED        = "HDFS_v1"
MAX_LINES_PER_FILE = None   # None = read all
RANDOM_STATE    = 42


# ── File discovery ────────────────────────────────────────────────────────────
def discover_log_files(dataset_dir: Path) -> List[Tuple[Path, str]]:
    gather_dir = dataset_dir / "gather"
    if not gather_dir.exists():
        return []
    results = []
    for p in sorted(gather_dir.rglob("*")):
        if not p.is_file():
            continue
        name = p.name
        size = p.stat().st_size
        if size > 50 * 1024 * 1024:
            continue
        if name.endswith(".journal") or name.endswith(".journal~") or name.startswith("."):
            continue
        if name.startswith("auth"):
            ltype = "auth"
        elif name.startswith("syslog"):
            ltype = "syslog"
        elif name == "audit.log":
            ltype = "audit"
        elif ("access" in name or "error" in name) and name.endswith(".log"):
            ltype = "apache"
        elif name.startswith("openvpn"):
            ltype = "openvpn"
        elif name.startswith("dnsmasq"):
            ltype = "dnsmasq"
        else:
            continue
        results.append((p, ltype))
    return results


def find_label_file(labels_dir: Path, log_path: Path, gather_dir: Path) -> Optional[Path]:
    try:
        rel = log_path.relative_to(gather_dir)
        candidate = labels_dir / rel
        if candidate.exists():
            return candidate
    except ValueError:
        pass
    return None


def load_label_index(label_path: Optional[Path]) -> Dict[int, List[str]]:
    """Returns {0-indexed-line: [label_str, ...]}"""
    index: Dict[int, List[str]] = {}
    if not label_path or not label_path.exists():
        return index
    with open(label_path, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
                index[int(obj["line"]) - 1] = obj.get("labels", [])
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
    return index


# ── Dataset loader ────────────────────────────────────────────────────────────
def load_dataset(dataset_name: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load, parse, feature-extract, label-join, and deduplicate one AIT dataset.
    Returns (DataFrame, stats_dict).
    """
    assert dataset_name != EXCLUDED
    ds_dir     = DATASETS_ROOT / dataset_name
    labels_dir = ds_dir / "labels"
    gather_dir = ds_dir / "gather"

    log_files = discover_log_files(ds_dir)
    logger.info(f"[{dataset_name}] {len(log_files)} processable log files")

    stats = dict(
        files_processed=0, files_with_label=0,
        raw_lines=0, blank_skipped=0,
        parse_errors=0, feature_errors=0,
        pre_dedup_records=0,
        dedup_removed=0, dedup_conflicts=0,
        anomalous=0, normal=0, uncertain_records=0,
    )

    # ── Phase 1: Read all records into a raw list ──
    raw_records = []

    for log_path, log_type in log_files:
        label_file  = find_label_file(labels_dir, log_path, gather_dir)
        label_index = load_label_index(label_file)
        if label_file:
            stats["files_with_label"] += 1

        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                for line_idx, raw_line in enumerate(f):
                    if MAX_LINES_PER_FILE and line_idx >= MAX_LINES_PER_FILE:
                        break
                    stats["raw_lines"] += 1
                    raw_stripped = raw_line.rstrip("\n\r")
                    if not raw_stripped.strip():
                        stats["blank_skipped"] += 1
                        continue

                    try:
                        parsed = LogParser.parse_line(raw_stripped)
                    except Exception:
                        stats["parse_errors"] += 1
                        continue

                    try:
                        features = LogParser.extract_features(parsed)
                    except Exception:
                        stats["feature_errors"] += 1
                        continue

                    attack_labels = label_index.get(line_idx, [])
                    is_anomaly, uncertain = classify_labels(attack_labels)

                    line_hash = hashlib.md5(
                        raw_stripped.encode("utf-8", errors="replace")
                    ).hexdigest()

                    rec = {k: features.get(k) for k in ALL_FEATURES}
                    rec["raw_line_md5"]    = line_hash
                    rec["raw_log"]         = raw_stripped[:300]
                    rec["source_file"]     = str(log_path.relative_to(ds_dir))
                    rec["log_type"]        = log_type
                    rec["line_idx"]        = line_idx
                    rec["attack_labels"]   = ",".join(attack_labels) if attack_labels else ""
                    rec["uncertain_labels"]= ",".join(uncertain)     if uncertain     else ""
                    rec["is_anomaly"]      = is_anomaly

                    raw_records.append(rec)
        except Exception as e:
            logger.warning(f"  Read error {log_path.name}: {e}")
            continue

        stats["files_processed"] += 1

    if not raw_records:
        raise ValueError(f"No records loaded from '{dataset_name}'")

    df_raw = pd.DataFrame(raw_records)
    stats["pre_dedup_records"] = len(df_raw)

    # ── Phase 2: Deduplicate ──────────────────────────────────────────────────
    # Group by MD5; within each group, if any row is anomalous, mark all as
    # anomalous (conservative: trust the labeled copy).
    # If different anomalous labels clash → flag as duplicate_conflict.
    groups = df_raw.groupby("raw_line_md5")
    deduped_rows = []

    for md5_hash, grp in groups:
        if len(grp) == 1:
            row = grp.iloc[0].to_dict()
            row["duplicate_conflict"] = False
            deduped_rows.append(row)
            continue

        stats["dedup_removed"] += len(grp) - 1

        # Best row: prefer anomalous over normal
        anom_rows = grp[grp["is_anomaly"] == 1]
        norm_rows = grp[grp["is_anomaly"] == 0]

        if len(anom_rows) == 0:
            # All normal — keep first
            row = grp.iloc[0].to_dict()
            row["duplicate_conflict"] = False
        elif len(norm_rows) == 0:
            # All anomalous — keep first anomalous; check label consistency
            row = anom_rows.iloc[0].to_dict()
            label_set = set(anom_rows["attack_labels"].unique())
            row["duplicate_conflict"] = len(label_set) > 1
            if row["duplicate_conflict"]:
                stats["dedup_conflicts"] += 1
        else:
            # Conflict: some copies are normal, some anomalous.
            # Conservative: mark as anomalous, flag conflict.
            row = anom_rows.iloc[0].to_dict()
            row["is_anomaly"] = 1
            row["duplicate_conflict"] = True
            stats["dedup_conflicts"] += 1

        deduped_rows.append(row)

    df = pd.DataFrame(deduped_rows)

    # ── Fill missing feature values ────────────────────────────────────────────
    for col in NUMERICAL_FEATURES:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    for col in CATEGORICAL_FEATURES:
        if col not in df.columns:
            df[col] = "unknown"
        df[col] = df[col].fillna("unknown").astype(str)

    stats["anomalous"]        = int(df["is_anomaly"].sum())
    stats["normal"]           = int((df["is_anomaly"] == 0).sum())
    stats["uncertain_records"] = int((df["uncertain_labels"] != "").sum())
    stats["final_records"]    = len(df)
    stats["anomaly_rate_pct"] = round(df["is_anomaly"].mean() * 100, 3)

    logger.info(
        f"[{dataset_name}] Records: raw={stats['pre_dedup_records']:,} "
        f"→ deduped={stats['final_records']:,} "
        f"(removed={stats['dedup_removed']:,}, conflicts={stats['dedup_conflicts']}) "
        f"| Anomalous={stats['anomalous']:,} ({stats['anomaly_rate_pct']}%)"
    )
    return df, stats


# ── Metrics ───────────────────────────────────────────────────────────────────
def compute_metrics(y_true, y_pred, y_proba=None):
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel() if cm.shape == (2, 2) else (cm[0,0], 0, 0, cm[1,1])
    fpr = round(fp / (fp + tn), 4) if (fp + tn) > 0 else 0.0
    m = dict(
        precision=round(precision_score(y_true, y_pred, zero_division=0), 4),
        recall=round(recall_score(y_true, y_pred, zero_division=0), 4),
        f1_score=round(f1_score(y_true, y_pred, zero_division=0), 4),
        false_positive_rate=fpr,
        true_negatives=int(tn), false_positives=int(fp),
        false_negatives=int(fn), true_positives=int(tp),
        confusion_matrix=cm.tolist(),
        classification_report=classification_report(
            y_true, y_pred, target_names=["Normal", "Anomaly"],
            output_dict=True, zero_division=0,
        ),
    )
    if y_proba is not None:
        try:
            m["roc_auc"] = round(roc_auc_score(y_true, y_proba), 4)
        except Exception:
            m["roc_auc"] = None
    return m


def train_one(model_wrapper, X_tr, y_tr, X_val, y_val, algo):
    logger.info(f"  Training {algo} on {len(X_tr):,} samples...")
    t0 = time.time()
    model_wrapper.fit(X_tr, y_tr)
    elapsed = round(time.time() - t0, 1)
    y_pred = model_wrapper.predict(X_val)
    y_proba = None
    try:
        proba = model_wrapper.predict_proba(X_val)
        y_proba = proba[:, 1] if proba.shape[1] > 1 else proba[:, 0]
    except Exception:
        pass
    m = compute_metrics(y_val, y_pred, y_proba)
    m["training_duration_seconds"] = elapsed
    m["train_samples"] = int(len(X_tr))
    m["val_samples"]   = int(len(X_val))
    logger.info(
        f"  [{algo}] {elapsed}s | F1={m['f1_score']} "
        f"Prec={m['precision']} Rec={m['recall']} FPR={m['false_positive_rate']}"
    )
    return model_wrapper, m


def cross_eval(model_wrapper, preprocessor, df_test, dataset_name):
    X = preprocessor.transform(df_test[ALL_FEATURES])
    y = df_test["is_anomaly"].values
    y_pred = model_wrapper.predict(X)
    y_proba = None
    try:
        p = model_wrapper.predict_proba(X)
        y_proba = p[:, 1] if p.shape[1] > 1 else p[:, 0]
    except Exception:
        pass
    m = compute_metrics(y, y_pred, y_proba)
    m.update(eval_dataset=dataset_name, eval_samples=int(len(y)),
             eval_anomaly_rate=round(float(y.mean()) * 100, 3))
    logger.info(
        f"  [cross-eval on {dataset_name}] F1={m['f1_score']} "
        f"Prec={m['precision']} Rec={m['recall']} FPR={m['false_positive_rate']}"
    )
    return m


def make_model_id(algo_key, dataset):
    return f"ait_{dataset}_{algo_key}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"


# ── Main ──────────────────────────────────────────────────────────────────────
def run_training(dry_run: bool = False):
    logger.info("=" * 70)
    logger.info("AIT-LDS Training Pipeline v2 — Smart-Log")
    logger.info(f"dry_run={dry_run} | ANOMALOUS_LABELS={len(ANOMALOUS_LABELS)} labels")
    logger.info("=" * 70)

    init_db()

    # Load datasets
    datasets, ds_stats = {}, {}
    for ds in DATASETS:
        df, stats = load_dataset(ds)
        datasets[ds]  = df
        ds_stats[ds]  = stats

    if dry_run:
        logger.info("[DRY RUN] Data loaded. Stopping before training.")
        return datasets, ds_stats, {}

    saved_models = {}

    # Train on FOX, cross-eval on RUSSELL + SANTOS
    df_fox = datasets["fox"]
    X_fox, y_fox = df_fox[ALL_FEATURES], df_fox["is_anomaly"].values
    X_tr, X_val, y_tr, y_val = train_test_split(
        X_fox, y_fox, test_size=0.2, random_state=RANDOM_STATE, stratify=y_fox
    )
    preprocessor_fox = PreprocessingBundle.infer_and_create(X_tr, ALL_FEATURES)
    X_tr_t  = preprocessor_fox.fit_transform(X_tr)
    X_val_t = preprocessor_fox.transform(X_val)

    algos = [
        ("Random Forest", RandomForestModelWrapper, "random_forest"),
        ("XGBoost",       XGBoostModelWrapper,       "xgboost"),
    ]

    for algo_name, Cls, algo_key in algos:
        logger.info(f"\n=== {algo_name} on FOX ===")
        hp = {"n_estimators": 150, "max_depth": 15, "random_state": RANDOM_STATE}
        if algo_key == "xgboost":
            hp.update(n_estimators=200, max_depth=8, learning_rate=0.1,
                      scale_pos_weight=max(1, int((y_tr == 0).sum() / max((y_tr == 1).sum(), 1))))
        mid = make_model_id(algo_key, "fox")
        wrapper = Cls(model_id=mid, hyperparameters=hp)
        wrapper, val_m = train_one(wrapper, X_tr_t, y_tr, X_val_t, y_val, algo_name)
        cross_evals = {ds: cross_eval(wrapper, preprocessor_fox, datasets[ds], ds)
                       for ds in ["russellmitchell", "santos"]}
        full_m = {"val_on_fox": val_m, "cross_eval": cross_evals,
                  "training_duration_seconds": val_m["training_duration_seconds"]}
        dm = {"dataset_id": f"ait_fox_{algo_key}_v2",
              "dataset_name": "AIT-LDS FOX (v2 fixed labels)",
              "label_mapping": {"normal": "0", "anomaly": "1"},
              "source_datasets": ["fox"],
              "anomalous_labels": sorted(ANOMALOUS_LABELS),
              "pipeline_version": "v2"}
        meta = ModelRegistry.save_model(wrapper, preprocessor_fox, full_m, dm, version="2.0.0")
        logger.info(f"  Saved model_id={meta['model_id']} (INACTIVE)")
        saved_models[f"fox_{algo_key}"] = meta

    # Per-dataset models for RUSSELL + SANTOS
    for ds in ["russellmitchell", "santos"]:
        df_ds = datasets[ds]
        X_ds, y_ds = df_ds[ALL_FEATURES], df_ds["is_anomaly"].values
        X_tr_d, X_val_d, y_tr_d, y_val_d = train_test_split(
            X_ds, y_ds, test_size=0.2, random_state=RANDOM_STATE, stratify=y_ds
        )
        prep_ds = PreprocessingBundle.infer_and_create(X_tr_d, ALL_FEATURES)
        X_tr_dt  = prep_ds.fit_transform(X_tr_d)
        X_val_dt = prep_ds.transform(X_val_d)
        for algo_name, Cls, algo_key in algos:
            logger.info(f"\n=== {algo_name} on {ds} ===")
            hp = {"n_estimators": 150, "max_depth": 15, "random_state": RANDOM_STATE}
            if algo_key == "xgboost":
                hp.update(n_estimators=200, max_depth=8, learning_rate=0.1,
                          scale_pos_weight=max(1, int((y_tr_d==0).sum()/max((y_tr_d==1).sum(),1))))
            mid = make_model_id(algo_key, ds)
            wrapper = Cls(model_id=mid, hyperparameters=hp)
            wrapper, val_m = train_one(wrapper, X_tr_dt, y_tr_d, X_val_dt, y_val_d, algo_name)
            full_m = {"val_on_own_split": val_m,
                      "training_duration_seconds": val_m["training_duration_seconds"]}
            dm = {"dataset_id": f"ait_{ds}_{algo_key}_v2",
                  "dataset_name": f"AIT-LDS {ds.upper()} (v2)",
                  "label_mapping": {"normal": "0", "anomaly": "1"},
                  "source_datasets": [ds],
                  "anomalous_labels": sorted(ANOMALOUS_LABELS),
                  "pipeline_version": "v2"}
            meta = ModelRegistry.save_model(wrapper, prep_ds, full_m, dm, version="2.0.0")
            logger.info(f"  Saved model_id={meta['model_id']} (INACTIVE)")
            saved_models[f"{ds}_{algo_key}"] = meta

    logger.info(f"\nDone. {len(saved_models)} models saved (all INACTIVE).")
    return datasets, ds_stats, saved_models


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run_training(dry_run=args.dry_run)
