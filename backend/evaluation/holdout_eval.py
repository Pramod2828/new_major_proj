import os
import sys
import json
import logging
from pathlib import Path
# Ensure project root is on PYTHONPATH for relative imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))
from typing import List, Dict, Any

import pandas as pd
from sklearn.model_selection import train_test_split

# Project imports
from backend.training.train_ait_lds import load_dataset, RANDOM_STATE, evaluate_cross_dataset
from backend.models.registry import ModelRegistry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("holdout_evaluation")

def main():
    logger.info("Loading FOX dataset...")
    df_fox, stats = load_dataset("fox")
    logger.info(f"FOX loaded: {len(df_fox)} records, {stats.get('anomalous_lines',0)} anomalies")

    X = df_fox
    y = df_fox["is_anomaly"].values
    _, X_holdout, _, y_holdout = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    holdout_df = X_holdout.reset_index(drop=True)
    logger.info(f"Holdout set: {len(holdout_df)} records (stratified)")

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    all_models = ModelRegistry.list_models()
    target_models = [m for m in all_models if m["algorithm"] in ["Random Forest", "XGBoost"]]
    if not target_models:
        logger.error("No Random Forest or XGBoost model entries found in the registry.")
        return

    results: List[Dict[str, Any]] = []
    for meta in target_models:
        model_id = meta["model_id"]
        logger.info(f"Loading model bundle {model_id} ({meta['algorithm']})")
        bundle = ModelRegistry.load_bundle(model_id)
        if not bundle:
            logger.error(f"Failed to load bundle for {model_id}")
            continue
        model_wrapper = bundle["model"]
        preprocessor = bundle["preprocessor"]
        metrics = evaluate_cross_dataset(model_wrapper, preprocessor, holdout_df, "fox_holdout")
        metrics["model_id"] = model_id
        metrics["algorithm"] = meta["algorithm"]
        results.append(metrics)
        out_path = output_dir / f"{model_id}_holdout_metrics.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Metrics written to {out_path}")

    summary_csv = output_dir / "holdout_summary.csv"
    with open(summary_csv, "w", encoding="utf-8") as f:
        f.write("model_id,algorithm,samples,anomaly_rate,precision,recall,f1_score,false_positive_rate\n")
        for m in results:
            f.write(
                f"{m['model_id']},{m['algorithm']},{m['eval_samples']},{m['eval_anomaly_rate']},"
                f"{m['precision']},{m['recall']},{m['f1_score']},{m['false_positive_rate']}\n"
            )
    logger.info(f"Summary CSV written to {summary_csv}")

if __name__ == "__main__":
    main()
