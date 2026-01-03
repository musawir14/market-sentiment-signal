from pathlib import Path

import pandas as pd

from src.features.daily_features import build_and_save_daily_features


def test_build_and_save_daily_features_writes_expected_columns(tmp_path: Path):
    # Minimal fake "GDELT-like" articles. If your parser expects different keys,
    # update these keys to match what articles_to_daily_features() reads.
    ticker_to_articles = {
        "aapl.us": [
            {"seendate": "2025-12-20T12:00:00Z", "title": "Apple shares rise on earnings"},
            {"seendate": "2025-12-20T15:00:00Z", "title": "Apple announces new product"},
        ],
        "msft.us": [
            {"seendate": "2025-12-20T13:00:00Z", "title": "Microsoft releases update"},
        ],
    }

    out_path = tmp_path / "daily_features.csv"
    res = build_and_save_daily_features(ticker_to_articles=ticker_to_articles, out_path=out_path)

    assert out_path.exists()
    df = pd.read_csv(out_path)

    expected_cols = {"ticker", "date", "docs", "avg_compound", "pos_frac", "neg_frac", "volume_z"}
    assert expected_cols.issubset(df.columns)

    # Basic sanity checks
    assert res.rows_written == len(df)
    assert len(df) > 0
