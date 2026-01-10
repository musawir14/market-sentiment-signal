from __future__ import annotations

import re
from pathlib import Path

REPORT_DIR = Path("report")
FIG_DIR = REPORT_DIR / "figures"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _extract_ic_and_p(md: str) -> tuple[float | None, float | None]:
    m = re.search(r"ic_spearman_1d:\s*([-\d.]+)", md)
    ic = float(m.group(1)) if m else None
    mp = re.search(r"ic_perm_pvalue:\s*([-\d.]+)", md)
    p = float(mp.group(1)) if mp else None
    return ic, p


def _extract_events_n(md: str) -> int | None:
    m = re.search(r"events_n:\s*(\d+)", md)
    return int(m.group(1)) if m else None


def _extract_best_sweep_config(csv_path: Path) -> str | None:
    if not csv_path.exists():
        return None

    # quick + dependency-free parsing
    lines = csv_path.read_text(encoding="utf-8").strip().splitlines()
    if len(lines) < 2:
        return None

    header = lines[0].split(",")
    rows = [dict(zip(header, r.split(","))) for r in lines[1:]]

    # pick: highest trades, then highest total_return
    def key(r):
        return (int(float(r["trades"])), float(r["total_return"]))

    best = max(rows, key=key)
    return (
        f"sent={best['sent_thresh']}, vol={best['vol_thresh']}, "
        f"min_docs={best['min_docs']}, slip_bps={best['slippage_bps']} "
        f"(trades={best['trades']}, total_return={float(best['total_return']):.4f})"
    )


def write_latest_results(tickers: list[str]) -> Path:
    day5 = _read_text(REPORT_DIR / "day5_results.md")
    ic, p = _extract_ic_and_p(day5)
    events_n = _extract_events_n(day5)

    best_cfg = _extract_best_sweep_config(REPORT_DIR / "day8_sweep.csv")

    out = REPORT_DIR / "latest_results.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("## Results (latest run)")
    lines.append("")
    lines.append(f"- tickers: {len(tickers)}")
    if ic is not None:
        if p is not None:
            lines.append(f"- IC (Spearman, 1D): {ic:.4f} (perm p={p:.4f})")
        else:
            lines.append(f"- IC (Spearman, 1D): {ic:.4f}")
    if events_n is not None:
        lines.append(f"- event study burst days: n={events_n}")
    if best_cfg:
        lines.append(f"- best sweep config: {best_cfg}")
    lines.append("")
    lines.append("### Charts")
    lines.append("")
    lines.append("![Equity curve](report/figures/equity_curve.png)")
    lines.append("![Sentiment vs return](report/figures/sentiment_vs_return.png)")
    lines.append("![Event study](report/figures/event_study.png)")
    lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    return out
