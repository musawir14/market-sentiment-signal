from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from pathlib import Path

import pandas as pd

from src.backtest.sim import simulate_equal_weight_portfolio


@dataclass(frozen=True)
class SweepRow:
    sent_thresh: float
    vol_thresh: float
    min_docs: int
    slippage_bps: int
    trades: int
    sharpe_ann: float
    max_drawdown: float
    total_return: float


def _safe_float(x, default=0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def run_sweep(
    merged_table_path: str | Path,
    sent_thresh_grid=(0.02, 0.05, 0.08, 0.10),
    vol_thresh_grid=(0.5, 1.0, 1.5, 2.0),
    min_docs_grid=(5, 10, 20),
    slippage_bps_grid=(0, 2, 5),
) -> pd.DataFrame:
    merged_table_path = Path(merged_table_path)
    df = pd.read_csv(merged_table_path)

    rows: list[dict] = []

    for sent_thresh, vol_thresh, min_docs, slippage_bps in product(
        sent_thresh_grid, vol_thresh_grid, min_docs_grid, slippage_bps_grid
    ):
        res = simulate_equal_weight_portfolio(
            merged_df=df,
            out_dir=Path("report"),  # it will overwrite portfolio_daily.csv each run (fine for now)
            sent_thresh=float(sent_thresh),
            vol_thresh=float(vol_thresh),
            min_docs=int(min_docs),
            slippage_bps=float(slippage_bps),
        )

        port = pd.read_csv(res.out_portfolio_csv)
        # Some parameter combos might produce a file without 'equity' (e.g., no valid days).
        # If equity is missing, rebuild it from portfolio_ret.
        if "equity" not in port.columns:
            if "portfolio_ret" in port.columns and len(port) > 0:
                port["equity"] = (1.0 + port["portfolio_ret"].fillna(0.0)).cumprod()
            else:
                port["equity"] = []  # empty / no data

        port = port.dropna(subset=["equity"])
        total_return = float(port["equity"].iloc[-1] - 1.0) if len(port) else 0.0

        rows.append(
            dict(
                sent_thresh=float(sent_thresh),
                vol_thresh=float(vol_thresh),
                min_docs=int(min_docs),
                slippage_bps=int(slippage_bps),
                trades=int(res.n_trades),
                sharpe_ann=float(res.sharpe_annual),
                max_drawdown=float(res.max_drawdown),
                total_return=total_return,
            )
        )

    return pd.DataFrame(rows)


def write_sweep_report(df: pd.DataFrame, out_csv: Path, out_md: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)

    # Filter: ignore configs that barely trade (too noisy)
    df2 = df.copy()
    df2["abs_sharpe"] = df2["sharpe_ann"].abs()
    df2 = df2.sort_values(["trades", "abs_sharpe"], ascending=[False, True])

    best = df2.sort_values(["trades", "total_return"], ascending=[False, False]).head(10)

    lines = []
    lines.append("# Day 8 — Parameter Sweep (Sensitivity)")
    lines.append("")
    lines.append(
        "This report sweeps simulator parameters to show sensitivity of results to thresholds."
    )
    lines.append("")
    lines.append(f"- rows_tested: {len(df)}")
    lines.append(f"- trades_range: {int(df['trades'].min())} → {int(df['trades'].max())}")
    lines.append("")
    lines.append("## Top configs (by trades, then total return)")
    lines.append("")
    lines.append(
        "| sent_thresh | vol_thresh | min_docs | slippage_bps | trades | total_return | sharpe_ann | max_drawdown |"
    )
    lines.append("|---:|---:|---:|---:|---:|---:|---:|---:|")
    for _, r in best.iterrows():
        lines.append(
            f"| {r['sent_thresh']:.2f} | {r['vol_thresh']:.1f} | {int(r['min_docs'])} | {int(r['slippage_bps'])} | "
            f"{int(r['trades'])} | {r['total_return']:.4f} | {r['sharpe_ann']:.4f} | {r['max_drawdown']:.4f} |"
        )

    lines.append("")
    lines.append("## Notes")
    lines.append("- Very low trade counts can make Sharpe unstable (one bad day dominates).")
    lines.append(
        "- This sweep is a sanity check and helps pick reasonable defaults for a longer lookback window."
    )
    lines.append("")

    out_md.write_text("\n".join(lines), encoding="utf-8")


def main():
    merged_path = Path("report") / "day6_merged_table.csv"
    out_csv = Path("report") / "day8_sweep.csv"
    out_md = Path("report") / "day8_sweep.md"

    if not merged_path.exists():
        raise FileNotFoundError(f"Missing {merged_path}. Run simulate stage first.")

    df = run_sweep(merged_path)
    write_sweep_report(df, out_csv=out_csv, out_md=out_md)
    print(f"Wrote {out_csv}")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
