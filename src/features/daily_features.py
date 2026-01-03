from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from src.features.sentiment import score_title


@dataclass(frozen=True)
class FeatureBuildResult:
    rows_written: int
    unique_days: int
    path: Path


def _to_date(seendate: str) -> str:
    if seendate is None:
        return ""
    s = str(seendate).strip()
    if not s:
        return ""

    # Case 1: compact numeric format (YYYYMMDDHHMMSS)
    if s.isdigit() and len(s) == 14:
        try:
            dt = datetime.strptime(s, "%Y%m%d%H%M%S")
            return dt.date().isoformat()
        except ValueError:
            pass

    # Case 2: common timestamp strings
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.date().isoformat()
        except ValueError:
            pass

    # Case 3: fallback parser (handles odd formats)
    try:
        dt = pd.to_datetime(s, errors="coerce")
        if pd.isna(dt):
            return ""
        return dt.date().isoformat()
    except Exception:
        return ""


def articles_to_daily_features(ticker: str, articles: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for a in articles:
        title = a.get("title", "") or ""
        seendate = a.get("seendate", "") or ""
        day = _to_date(seendate)
        if not day:
            continue

        s = score_title(title)
        rows.append(
            {
                "ticker": ticker.lower(),
                "date": day,
                "title": title,
                "compound": s.compound,
                "pos": s.pos,
                "neu": s.neu,
                "neg": s.neg,
            }
        )

    if not rows:
        return pd.DataFrame(columns=["ticker", "date", "title", "compound", "pos", "neu", "neg"])

    df = pd.DataFrame(rows)
    return df


def build_and_save_daily_features(
    ticker_to_articles: Dict[str, List[Dict[str, Any]]],
    out_path: Path,
) -> FeatureBuildResult:
    """
    Produces daily aggregated features and writes to CSV.
    Also adds a simple 'volume_z' burst score per ticker.
    """
    all_rows = []
    for t, articles in ticker_to_articles.items():
        all_rows.append(articles_to_daily_features(t, articles))

    if not all_rows:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame().to_csv(out_path, index=False)
        return FeatureBuildResult(rows_written=0, unique_days=0, path=out_path)

    raw = pd.concat(all_rows, ignore_index=True)

    daily = (
        raw.groupby(["ticker", "date"], as_index=False)
        .agg(
            docs=("compound", "size"),
            avg_compound=("compound", "mean"),
            pos_frac=("pos", "mean"),
            neg_frac=("neg", "mean"),
        )
        .sort_values(["ticker", "date"])
        .reset_index(drop=True)
    )

    # Burst feature: z-score of docs vs rolling 5-day mean/std (per ticker)
    daily["volume_z"] = 0.0
    for t, g in daily.groupby("ticker", as_index=False):
        idx = g.index
        roll_mean = g["docs"].rolling(window=5, min_periods=2).mean()
        roll_std = g["docs"].rolling(window=5, min_periods=2).std(ddof=0)
        z = (g["docs"] - roll_mean) / roll_std.replace(0, pd.NA)
        daily.loc[idx, "volume_z"] = z.fillna(0.0).astype(float)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    daily.to_csv(out_path, index=False)

    return FeatureBuildResult(
        rows_written=len(daily),
        unique_days=int(daily["date"].nunique()) if len(daily) else 0,
        path=out_path,
    )
