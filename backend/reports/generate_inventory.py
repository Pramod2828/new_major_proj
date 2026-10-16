import os, json, sys
PROJECT_ROOT = r"C:/Users/Admin/OneDrive/Desktop/new major project"
sys.path.insert(0, PROJECT_ROOT)
from backend.training.train_ait_lds import load_dataset, ALL_FEATURES
from backend.models.registry import ModelRegistry
from sklearn.model_selection import train_test_split

datasets = ['fox', 'russellmitchell', 'santos']
inventory = {}

total_unique_records = 0
for ds in datasets:
    df, stats = load_dataset(ds)
    pre_duplicate = len(df) + stats.get('exact_duplicates_removed', 0) + stats.get('conflicting_records_removed', 0)
    inventory[ds] = {
        'pre_duplicate_records': pre_duplicate,
        'post_duplicate_records': len(df),
        'exact_duplicates_removed': stats.get('exact_duplicates_removed', 0),
        'conflicting_groups': stats.get('conflicting_groups', 0),
        'conflicting_records_removed': stats.get('conflicting_records_removed', 0),
    }
    X = df[ALL_FEATURES]
    y = df['is_anomaly'].values
    X_tr, X_val, y_tr, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    inventory[ds]['train_records'] = len(X_tr)
    inventory[ds]['val_records'] = len(X_val)
    total_unique_records += len(df)

models = ModelRegistry.list_models()
model_info = []
for m in models:
    model_info.append({
        'model_id': m.get('id'),
        'algorithm': m.get('algorithm'),
        'dataset_id': m.get('dataset_id'),
        'dataset_name': m.get('dataset_name'),
        'is_active': m.get('is_active'),
        'artifact_path': m.get('artifact_path'),
        'metrics': m.get('metrics', {}),
    })

train_samples_total = sum(m.get('metrics', {}).get('train_samples', 0) for m in model_info)
val_samples_total = sum(m.get('metrics', {}).get('val_samples', 0) for m in model_info)

result = {
    'datasets': inventory,
    'models': model_info,
    'summary': {
        'total_unique_project_records': total_unique_records,
        'total_records_used_for_training': train_samples_total,
        'total_validation_records_across_runs': val_samples_total,
        'mock_test_records': 'NOT VERIFIED'
    }
}

os.makedirs('backend/reports', exist_ok=True)
output_path = 'backend/reports/model_dataset_inventory.json'
with open(output_path, 'w') as f:
    json.dump(result, f, indent=2)
print(json.dumps(result, indent=2))
