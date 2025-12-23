from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

from src.backtest.returns import load_price_cache, compute_forward_returns


@dataclass(frozen=True)
class EvalResult:
    merged_rows: int
    ic_spearman_1d: float
    events_n: int
    event_mean_1d: float
    event_mean_3d: float


def _spearman(x: pd.Series, y: pd.Series) -> float:
    df = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(df) < 5:
        return 0.0
    return float(df["x"].corr(df["y"], method="spearman"))


def build_eval_table(
    tickers: List[str],
    features_path: Path,
    prices_cache_dir: Path,
) -> pd.DataFrame:
    """
    Load daily_features.csv and merge with forward returns for each ticker-day.
    """
    feats = pd.read_csv(features_path)
    if feats.empty:
        raise ValueError("daily_features.csv is empty. Run Day 4 again.")

    feats = feats.copy()
    feats["ticker"] = feats["ticker"].astype(str).str.lower()
    feats["date"] = feats["date"].astype(str)

    merged_all = []
    for t in tickers:
        tl = t.lower()
        sub = feats[feats["ticker"] == tl].copy()
        if sub.empty:
            continue

        px = load_price_cache(ticker=tl, cache_dir=prices_cache_dir)
        fwd = compute_forward_returns(px)
        fwd["ticker"] = tl

        m = sub.merge(fwd, on=["ticker", "date"], how="left")
        merged_all.append(m)

    if not merged_all:
        return pd.DataFrame()

    out = pd.concat(merged_all, ignore_index=True)
    return out


def run_signal_eval(eval_df: pd.DataFrame) -> EvalResult:
    """
    Compute:
    - Spearman IC between avg_compound and fwd_ret_1d
    - Simple event study on "news burst" days (volume_z >= 1.0)
    """
    if eval_df.empty:
        return EvalResult(merged_rows=0, ic_spearman_1d=0.0, events_n=0, event_mean_1d=0.0, event_mean_3d=0.0)

    ic = _spearman(eval_df["avg_compound"], eval_df["fwd_ret_1d"])

    events = eval_df[(eval_df["volume_z"] >= 1.0) & (eval_df["docs"] >= 10)].copy()
    events_n = int(len(events))

    event_mean_1d = float(events["fwd_ret_1d"].dropna().mean()) if events_n else 0.0
    event_mean_3d = float(events["fwd_ret_3d"].dropna().mean()) if events_n else 0.0

    return EvalResult(
        merged_rows=int(len(eval_df)),
        ic_spearman_1d=float(ic) if ic == ic else 0.0,
        events_n=events_n,
        event_mean_1d=event_mean_1d if event_mean_1d == event_mean_1d else 0.0,
        event_mean_3d=event_mean_3d if event_mean_3d == event_mean_3d else 0.0,
    )


def write_day5_report(result: EvalResult, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        "\n".join(
            [
                "# Day 5 Results — Signal Evaluation",
                "",
                "What this measures:",
                "- **IC (Spearman, 1D):** rank correlation between daily sentiment and next-day return.",
                "- **Event study:** average forward returns on **news-burst** days (volume_z ≥ 1.0, docs ≥ 10).",
                "",
                "## Summary",
                f"- merged_rows: {result.merged_rows}",
                f"- ic_spearman_1d: {result.ic_spearman_1d:.4f}",
                f"- events_n: {result.events_n}",
                f"- event_mean_1d: {result.event_mean_1d:.6f}",
                f"- event_mean_3d: {result.event_mean_3d:.6f}",
                "",
            ]
        ),
        encoding="utf-8",
    )

def write_merged_csv(eval_df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    eval_df.to_csv(out_path, index=False)
