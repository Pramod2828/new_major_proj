import sys
import os
from pathlib import Path
# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.training.train_ait_lds import load_dataset
from backend.config import Config
import sqlite3

def get_active_models():
    db_path = Config.DATABASE_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = lambda c,row: {col[0]: row[idx] for idx, col in enumerate(c.description)}
    cur = conn.cursor()
    cur.execute('SELECT id, is_active FROM models')
    all_models = cur.fetchall()
    cur.execute('SELECT id, is_active FROM models WHERE is_active=1')
    active = cur.fetchall()
    return all_models, active

if __name__ == '__main__':
    datasets = ['fox', 'russellmitchell', 'santos']
    for ds in datasets:
        df, stats = load_dataset(ds)
        print(f"=== Dataset {ds} ===")
        for k, v in stats.items():
            print(f"{k}: {v}")
        print(f"Total records after cleaning: {len(df)}")
        print()
    all_models, active_models = get_active_models()
    print("=== All models ===")
    for m in all_models:
        print(m)
    print("=== Active models ===")
    for m in active_models:
        print(m)
