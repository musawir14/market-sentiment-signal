from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class SimResult:
    n_signal_days: int
    n_trades: int
    sharpe_annual: float
    max_drawdown: float
    out_portfolio_csv: Path


def _annualized_sharpe(daily_rets: pd.Series) -> float:
    r = pd.to_numeric(daily_rets, errors="coerce").dropna()
    if len(r) < 2:
        return 0.0
    mu = r.mean()
    sd = r.std(ddof=0)
    if sd == 0 or pd.isna(sd):
        return 0.0
    return float((mu / sd) * (252**0.5))


def _max_drawdown(equity: pd.Series) -> float:
    eq = pd.to_numeric(equity, errors="coerce").dropna()
    if eq.empty:
        return 0.0
    running_max = eq.cummax()
    dd = (eq / running_max) - 1.0
    return float(dd.min())


def build_signals(
    df: pd.DataFrame,
    sent_thresh: float = 0.05,
    vol_thresh: float = 1.0,
    min_docs: int = 10,
) -> pd.DataFrame:
    """
    Create a discrete signal per (ticker, date).
      +1 if avg_compound >= sent_thresh AND volume_z >= vol_thresh AND docs >= min_docs
      -1 if avg_compound <= -sent_thresh AND volume_z >= vol_thresh AND docs >= min_docs
       0 otherwise
    """
    out = df.copy()
    out["signal"] = 0

    long_mask = (
        (out["avg_compound"] >= sent_thresh)
        & (out["volume_z"] >= vol_thresh)
        & (out["docs"] >= min_docs)
    )
    short_mask = (
        (out["avg_compound"] <= -sent_thresh)
        & (out["volume_z"] >= vol_thresh)
        & (out["docs"] >= min_docs)
    )

    out.loc[long_mask, "signal"] = 1
    out.loc[short_mask, "signal"] = -1
    return out


def simulate_equal_weight_portfolio(
    merged_df: pd.DataFrame,
    out_dir: Path,
    sent_thresh: float = 0.05,
    vol_thresh: float = 1.0,
    min_docs: int = 10,
    slippage_bps: float = 2.0,
) -> SimResult:
    """
    Inputs: merged_df with columns at least:
      ticker, date, docs, avg_compound, volume_z, fwd_ret_1d

    We:
      1) build signals on date t from features on date t
      2) apply a 1-day execution delay (signal executed next day):
         signal_exec(t+1) = signal(t)
      3) portfolio return on day d = average(signal_exec * fwd_ret_1d) across tickers with signal_exec != 0
      4) subtract slippage per trade (bps converted to decimal)

    Writes:
      - out_dir/portfolio_daily.csv (tracked? you can track in report/ if small; otherwise keep in data/)
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    df = merged_df.copy()
    df["ticker"] = df["ticker"].astype(str).str.lower()
    df["date"] = df["date"].astype(str)

    # Build base signals on the same day as the features
    df = build_signals(df, sent_thresh=sent_thresh, vol_thresh=vol_thresh, min_docs=min_docs)

    # Apply 1-day delay per ticker: signal_exec(date d) = signal(date d-1)
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)
    df["signal_exec"] = df.groupby("ticker")["signal"].shift(1).fillna(0).astype(int)

    # Trade indicator: a non-zero executed signal counts as a trade for that ticker-day
    df["trade"] = (df["signal_exec"] != 0).astype(int)

    # PnL per ticker-day (using next-day return relative to the feature day)
    # If signal_exec is on day d, we use fwd_ret_1d from day d (close(d+1)/close(d)-1)
    df["gross_pnl"] = df["signal_exec"] * df["fwd_ret_1d"]

    # Slippage: subtract bps for each executed trade (per ticker-day)
    slip = slippage_bps / 10000.0
    df["net_pnl"] = df["gross_pnl"] - (df["trade"] * slip)

    # Portfolio daily return: equal-weight average across tickers that traded that day
    traded = df[(df["trade"] == 1) & (df["fwd_ret_1d"].notna())].copy()
    if traded.empty:
        out_path = out_dir / "portfolio_daily.csv"
        pd.DataFrame(columns=["date", "portfolio_ret", "n_positions"]).to_csv(out_path, index=False)
        return SimResult(0, 0, 0.0, 0.0, out_path)

    port = (
        traded.groupby("date", as_index=False)
        .agg(
            portfolio_ret=("net_pnl", "mean"),
            n_positions=("net_pnl", "size"),
        )
        .sort_values("date")
        .reset_index(drop=True)
    )

    port["equity"] = (1.0 + port["portfolio_ret"]).cumprod()

    sharpe = _annualized_sharpe(port["portfolio_ret"])
    mdd = _max_drawdown(port["equity"])

    out_path = out_dir / "portfolio_daily.csv"
    port.to_csv(out_path, index=False)

    n_signal_days = int((df["signal"] != 0).sum())
    n_trades = int(traded["trade"].sum())

    return SimResult(
        n_signal_days=n_signal_days,
        n_trades=n_trades,
        sharpe_annual=sharpe,
        max_drawdown=mdd,
        out_portfolio_csv=out_path,
    )
