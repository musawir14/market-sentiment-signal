from pathlib import Path

import pandas as pd


def test_daily_features_file_exists_and_has_expected_columns():
    path = Path("data/features/daily_features.csv")
    assert path.exists(), "Run: python -m src.pipeline --stage features first"

    df = pd.read_csv(path)
    expected = {"ticker", "date", "docs", "avg_compound", "pos_frac", "neg_frac", "volume_z"}
    assert expected.issubset(set(df.columns))

    # Basic sanity checks
    assert len(df) > 0
    assert (df["docs"] >= 0).all()
