from pathlib import Path

import pandas as pd

from src.features.daily_features import build_and_save_daily_features


def test_build_and_save_daily_features_writes_expected_columns(tmp_path: Path):
    # Minimal fake articles (match the keys your pipeline uses from GDELT)
    ticker_to_articles = {
        "aapl.us": [
            {"seendate": "2026-01-01", "title": "Apple rises on earnings beat", "snippet": "Strong iPhone demand"},
            {"seendate": "2026-01-01", "title": "Apple dips after guidance", "snippet": "Concerns about margins"},
        ],
        "msft.us": [
            {"seendate": "2026-01-02", "title": "Microsoft announces new product", "snippet": "Cloud growth continues"},
        ],
    }

    out_path = tmp_path / "daily_features.csv"
    res = build_and_save_daily_features(ticker_to_articles=ticker_to_articles, out_path=out_path)

    assert out_path.exists()
    df = pd.read_csv(out_path)

    expected_cols = {
        "ticker",
        "date",
        "docs",
        "avg_compound",
        "pos_frac",
        "neg_frac",
        "volume_z",
    }
    assert expected_cols.issubset(set(df.columns))

    # Sanity checks
    assert res.rows_written == len(df)
    assert res.unique_days >= 1
