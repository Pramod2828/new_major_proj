import os, sys, json, sqlite3
from pathlib import Path
# Add project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from backend.config import Config

def main():
    db_path = Config.DATABASE_PATH
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = cur.fetchall()
    cur.execute('PRAGMA table_info(models)')
    cols = cur.fetchall()
    result = {'tables': tables, 'model_columns': cols}
    out_path = Path(__file__).with_name('db_inspect.json')
    out_path.write_text(json.dumps(result, indent=2))
    print('Wrote', out_path)

if __name__ == '__main__':
    main()
