from pathlib import Path

import pandas as pd

from src.features.daily_features import build_and_save_daily_features


def test_daily_features_builder_writes_expected_columns(tmp_path: Path):
    # Minimal synthetic "articles" shaped like what our pipeline expects.
    # (Only fields that typical pipelines use: title + seendate; extras are fine.)
    ticker_to_articles = {
        "aapl.us": [
            {"title": "Apple shares rise after earnings", "seendate": "2025-12-20 00:00:00"},
            {"title": "Apple announces new product", "seendate": "2025-12-20 12:00:00"},
        ],
        "msft.us": [
            {"title": "Microsoft releases update", "seendate": "2025-12-21 00:00:00"},
        ],
    }

    out_path = tmp_path / "daily_features.csv"
    res = build_and_save_daily_features(ticker_to_articles=ticker_to_articles, out_path=out_path)

    assert out_path.exists()
    df = pd.read_csv(out_path)

    expected_cols = {"ticker", "date", "docs", "avg_compound", "pos_frac", "neg_frac", "volume_z"}
    assert expected_cols.issubset(set(df.columns))
    assert res.rows_written >= 1
