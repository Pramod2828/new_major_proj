import json, os, sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.training.train_ait_lds import load_dataset
from backend.config import Config
from backend.models.registry import ModelRegistry
import sqlite3
from sklearn.model_selection import train_test_split

results = {}
for ds in ['fox', 'russellmitchell', 'santos']:
    try:
        df, stats = load_dataset(ds)
    except Exception as e:
        results[ds] = {'error': str(e)}
        continue
    raw_records = stats.get('total_lines')
    processed_records = len(df)
    exact_duplicates = stats.get('exact_duplicates_removed', 0)
    conflicting_groups = stats.get('conflicting_groups', 0)
    conflicting_records = stats.get('conflicting_records_removed', 0)
    X_train, X_val, y_train, y_val = train_test_split(
        df, df['is_anomaly'], test_size=0.2, random_state=42, stratify=df['is_anomaly']
    )
    results[ds] = {
        'raw_records': raw_records,
        'processed_records': processed_records,
        'exact_duplicates_removed': exact_duplicates,
        'conflicting_groups': conflicting_groups,
        'conflicting_records_removed': conflicting_records,
        'train_count': len(X_train),
        'val_count': len(X_val)
    }

# DB query
db_path = Config.DATABASE_PATH
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute('SELECT id, name, algorithm, dataset_id, is_active, artifact_path FROM models')
model_rows = cur.fetchall()
models_info = []
for row in model_rows:
    model_id, name, algorithm, dataset_id, is_active, artifact_path = row
    models_info.append({
        'model_id': name,  # model identifier stored in 'name' column
        'algorithm': algorithm,
        'dataset_id': dataset_id,
        'active': bool(is_active),
        'artifact_path': artifact_path
    })
active_models = [m for m in models_info if m['active']]
active_model = active_models[0] if active_models else None
reg_test_meta = None
for m in models_info:
    if m['model_id'] == 'reg_test_rf':
        bundle = ModelRegistry.load_bundle(m['model_id'])
        reg_test_meta = bundle.get('metadata')
        break

output = {
    'dataset_stats': results,
    'models': models_info,
    'active_model': active_model,
    'reg_test_rf_meta': reg_test_meta
}
# Write to file for inspection
out_path = Path(__file__).with_name('verify_output.json')
out_path.write_text(json.dumps(output, indent=2))
print('Wrote output to', out_path)
