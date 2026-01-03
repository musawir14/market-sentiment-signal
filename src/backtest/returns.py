from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_price_cache(ticker: str, cache_dir: Path) -> pd.DataFrame:
    """
    Load cached Stooq prices for ticker. Must exist.
    Returns df with Date (datetime) and Close (float).
    """
    path = cache_dir / f"{ticker.lower()}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing price cache for {ticker}: {path}")

    df = pd.read_csv(path)
    if "Date" not in df.columns or "Close" not in df.columns:
        raise ValueError(f"Unexpected price columns for {ticker}: {df.columns.tolist()}")

    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df = df.dropna(subset=["Close"])
    return df[["Date", "Close"]]


def compute_forward_returns(price_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create forward returns:
      fwd_ret_1d(t) = Close(t+1)/Close(t) - 1
      fwd_ret_3d(t) = Close(t+3)/Close(t) - 1
    """
    df = price_df.copy()
    df["date"] = df["Date"].dt.date.astype(str)

    close = df["Close"]
    df["fwd_ret_1d"] = (close.shift(-1) / close) - 1.0
    df["fwd_ret_3d"] = (close.shift(-3) / close) - 1.0

    return df[["date", "fwd_ret_1d", "fwd_ret_3d"]]
