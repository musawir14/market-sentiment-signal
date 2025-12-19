from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import pandas as pd


@dataclass(frozen=True)
class PriceIngestResult:
    ticker: str
    rows: int
    cache_hit: bool
    path: Path


def stooq_daily_url(ticker: str) -> str:
    """
    Stooq daily CSV endpoint.
    Example ticker formats: 'aapl.us', 'msft.us', 'spy.us'
    """
    t = ticker.strip().lower()
    return f"https://stooq.com/q/d/l/?s={t}&i=d"


def load_or_download_daily_prices(
    ticker: str,
    cache_dir: Path,
) -> Tuple[pd.DataFrame, PriceIngestResult]:
    """
    Loads cached daily prices if present; otherwise downloads from Stooq and caches.
    Returns a DataFrame with columns: Date, Open, High, Low, Close, Volume
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{ticker.strip().lower()}.csv"

    if cache_path.exists() and cache_path.stat().st_size > 0:
        df = pd.read_csv(cache_path)
        df = _clean_prices_df(df)
        return df, PriceIngestResult(ticker=ticker, rows=len(df), cache_hit=True, path=cache_path)

    url = stooq_daily_url(ticker)
    df = pd.read_csv(url)
    df = _clean_prices_df(df)

    # Cache to disk
    df.to_csv(cache_path, index=False)

    return df, PriceIngestResult(ticker=ticker, rows=len(df), cache_hit=False, path=cache_path)


def _clean_prices_df(df: pd.DataFrame) -> pd.DataFrame:
    if "Date" not in df.columns:
        # Stooq sometimes returns an empty/invalid response; be explicit.
        raise ValueError("Stooq response missing 'Date' column (ticker may be invalid or unavailable).")

    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    # Ensure sorted ascending by date
    df = df.sort_values("Date").reset_index(drop=True)

    # Keep only expected columns if present
    keep = [c for c in ["Date", "Open", "High", "Low", "Close", "Volume"] if c in df.columns]
    df = df[keep]

    # Drop rows where Close is missing (common sanity check)
    if "Close" in df.columns:
        df = df.dropna(subset=["Close"])

    return df
