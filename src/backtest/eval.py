from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import pandas as pd

from src.backtest.returns import compute_forward_returns, load_price_cache
from src.backtest.stats import bootstrap_mean_ci, permutation_pvalue_ic, spearman_ic


@dataclass(frozen=True)
class EvalResult:
    merged_rows: int
    ic_spearman_1d: float
    ic_perm_pvalue: float
    events_n: int
    event_mean_1d: float
    event_mean_3d: float
    event_mean_1d_ci_lo: float
    event_mean_1d_ci_hi: float
    event_mean_3d_ci_lo: float
    event_mean_3d_ci_hi: float


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
        return EvalResult(
            merged_rows=0, ic_spearman_1d=0.0, events_n=0, event_mean_1d=0.0, event_mean_3d=0.0
        )

    ic = spearman_ic(eval_df["avg_compound"], eval_df["fwd_ret_1d"])
    p_ic = permutation_pvalue_ic(eval_df["avg_compound"], eval_df["fwd_ret_1d"], n_perm=1000)

    events = eval_df[(eval_df["volume_z"] >= 1.0) & (eval_df["docs"] >= 10)].copy()
    events_n = int(len(events))

    m1, lo1, hi1 = bootstrap_mean_ci(events["fwd_ret_1d"]) if events_n else (0.0, 0.0, 0.0)
    m3, lo3, hi3 = bootstrap_mean_ci(events["fwd_ret_3d"]) if events_n else (0.0, 0.0, 0.0)

    return EvalResult(
        merged_rows=int(len(eval_df)),
        ic_spearman_1d=float(ic) if ic == ic else 0.0,
        ic_perm_pvalue=float(p_ic),
        events_n=events_n,
        event_mean_1d=float(m1),
        event_mean_3d=float(m3),
        event_mean_1d_ci_lo=float(lo1),
        event_mean_1d_ci_hi=float(hi1),
        event_mean_3d_ci_lo=float(lo3),
        event_mean_3d_ci_hi=float(hi3),
    )


def write_day5_report(result, eval_df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # ---- Dataset summary (from eval_df) ----
    tickers = sorted(eval_df["ticker"].dropna().unique().tolist()) if "ticker" in eval_df.columns else []
    n_tickers = len(tickers)

    if "date" in eval_df.columns:
        d = pd.to_datetime(eval_df["date"], errors="coerce").dropna()
        min_date = d.min().date().isoformat() if len(d) else ""
        max_date = d.max().date().isoformat() if len(d) else ""
    else:
        min_date, max_date = "", ""

    # ---- Interpretation (short + readable) ----
    ic = result.ic_spearman_1d
    p = result.ic_perm_pvalue

    if p < 0.05:
        ic_read = "statistically significant"
    else:
        ic_read = "not statistically significant"

    interpretation_lines = [
        "## Interpretation",
        (
            f"The sentiment feature shows a {ic:.4f} Spearman IC with next-day returns "
            f"and is {ic_read} (perm p-value = {p:.4f})."
        ),
        (
            f"On burst days (high volume_z), the event study suggests average forward returns of "
            f"{result.event_mean_1d:.6f} (1D) and {result.event_mean_3d:.6f} (3D). "
            "Use this as a directional signal quality check, not a guarantee of predictability."
        ),
        "",
    ]

    lines = [
        "# Day 5 Results — Signal Evaluation",
        "",
        "What this measures:",
        "- **IC (Spearman, 1D):** rank correlation between daily sentiment and next-day return.",
        "- **Event study:** average forward returns on **news-burst** days (volume_z ≥ 1.0, docs ≥ 10).",
        "",
        "## Dataset",
        f"- merged_rows: {result.merged_rows}",
        f"- tickers: {n_tickers}" + (f" ({', '.join(tickers)})" if n_tickers <= 20 else ""),
        f"- date_span: {min_date} → {max_date}" if min_date and max_date else "- date_span: (unknown)",
        "",
        "## Summary",
        f"- ic_spearman_1d: {result.ic_spearman_1d:.4f}",
        f"- ic_perm_pvalue: {result.ic_perm_pvalue:.4f}",
        f"- events_n: {result.events_n}",
        f"- event_mean_1d: {result.event_mean_1d:.6f} (95% CI [{result.event_mean_1d_ci_lo:.6f}, {result.event_mean_1d_ci_hi:.6f}])",
        f"- event_mean_3d: {result.event_mean_3d:.6f} (95% CI [{result.event_mean_3d_ci_lo:.6f}, {result.event_mean_3d_ci_hi:.6f}])",
        "",
        *interpretation_lines,
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")


def write_merged_csv(eval_df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    eval_df.to_csv(out_path, index=False)
