import json, os, sqlite3
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.training.train_ait_lds import load_dataset, ALL_FEATURES
from backend.config import Config
from backend.models.registry import ModelRegistry


def get_dataset_stats(name):
    df, stats = load_dataset(name)
    # Approximate raw records before cleaning. If stats contain total_records before cleaning use it, otherwise infer.
    raw = stats.get('total_records')
    if raw is None:
        raw = len(df) + stats.get('exact_duplicates_removed', 0) + stats.get('conflicting_records_removed', 0)
    processed = len(df)
    exact_dup = stats.get('exact_duplicates_removed', 0)
    conflict_groups = stats.get('conflicting_groups', 0)
    conflict_records = stats.get('conflicting_records_removed', 0)
    # Train/validation split (80/20 stratified)
    X = df[ALL_FEATURES]
    y = df['is_anomaly'].values
    from sklearn.model_selection import train_test_split
    X_tr, X_val, y_tr, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    return {
        "raw_records": raw,
        "processed_records": processed,
        "exact_duplicates_removed": exact_dup,
        "conflicting_groups": conflict_groups,
        "conflicting_records_removed": conflict_records,
        "train_records": len(X_tr),
        "val_records": len(X_val),
    }

def query_active_model():
    db_path = Config.DATABASE_PATH
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Show schema
    cur.execute('PRAGMA table_info(models)')
    schema = cur.fetchall()
    # All models
    cur.execute('SELECT id, is_active FROM models')
    all_models = cur.fetchall()
    # Active model id
    cur.execute('SELECT id FROM models WHERE is_active=1')
    row = cur.fetchone()
    active_id = row[0] if row else None
    conn.close()
    return schema, all_models, active_id

def generate_inventory():
    datasets = ["fox", "russellmitchell", "santos"]
    inventory = {}
    total_unique = 0
    for ds in datasets:
        stats = get_dataset_stats(ds)
        inventory[ds] = stats
        total_unique += stats["processed_records"]
    # Model information from registry
    models = ModelRegistry.list_models()
    model_info = []
    for m in models:
        model_info.append({
            "model_id": m.get('id'),
            "algorithm": m.get('algorithm'),
            "dataset_id": m.get('dataset_id'),
            "is_active": m.get('is_active'),
            "artifact_path": m.get('artifact_path'),
            "metrics": m.get('metrics', {}),
        })
    summary = {
        "total_unique_project_records": total_unique,
        "total_records_used_for_training": sum(m.get('metrics', {}).get('train_samples', 0) for m in model_info),
        "total_validation_records_across_runs": sum(m.get('metrics', {}).get('val_samples', 0) for m in model_info),
        "mock_test_records": "NOT VERIFIED"
    }
    result = {"datasets": inventory, "models": model_info, "summary": summary}
    out_path = Path('backend/reports/model_dataset_inventory.json')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2)
    return result, out_path

if __name__ == '__main__':
    schema, all_models, active_id = query_active_model()
    print('=== DB Schema (models) ===')
    for col in schema:
        print(col)
    print('\n=== All models ===')
    for mid, act in all_models:
        print(f'id={mid}, active={act}')
    print(f'\nActive model ID: {active_id}')
    result, out_path = generate_inventory()
    print('\n=== Inventory generated at', out_path, '===')
    print(json.dumps(result, indent=2))
