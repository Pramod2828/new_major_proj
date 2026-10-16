import os, sqlite3, json, sys
from pathlib import Path
# Add project root to sys.path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))
import config
db_path = os.environ.get('DATABASE_PATH', config.Config.DATABASE_PATH)
print('DB path:', db_path)
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute('SELECT id, name, algorithm, artifact_path, is_active FROM models')
rows = cur.fetchall()
print('All models:')
for r in rows:
    print(dict(r))
cur.execute('SELECT id, name, algorithm, artifact_path FROM models WHERE is_active=1')
active = cur.fetchall()
print('Active models:')
for r in active:
    print(dict(r))
conn.close()
