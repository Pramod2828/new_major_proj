import pytest
import pandas as pd
from backend.training.train_ait_lds import handle_duplicates

def test_duplicate_handling_exact_and_conflict():
    # Create synthetic dataframe with duplicate rows and conflicting labels
    data = [
        {"feature1": 1, "feature2": 2, "is_anomaly": 0},
        {"feature1": 1, "feature2": 2, "is_anomaly": 0},  # exact duplicate
        {"feature1": 3, "feature2": 4, "is_anomaly": 0},
        {"feature1": 3, "feature2": 4, "is_anomaly": 1},  # conflict same features diff label
        {"feature1": 5, "feature2": 6, "is_anomaly": 1},
    ]
    df = pd.DataFrame(data)
    cleaned_df, stats = handle_duplicates(df)
    # Expect one exact duplicate removed, one conflicting group (2 records) removed
    assert stats["exact_duplicates_removed"] == 1
    assert stats["conflicting_groups"] == 1
    assert stats["conflicting_records_removed"] == 2
    # Remaining records should be those without duplicates/conflicts
    assert len(cleaned_df) == 2
    # Verify remaining features are as expected
    remaining = cleaned_df.to_dict(orient="records")
    assert {"feature1": 1, "feature2": 2, "is_anomaly": 0} in remaining
    assert {"feature1": 5, "feature2": 6, "is_anomaly": 1} in remaining
