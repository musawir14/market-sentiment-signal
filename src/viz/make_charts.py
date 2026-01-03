from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update(
    {
        "figure.figsize": (9, 4.5),
        "font.size": 11,
        "axes.titlesize": 14,
        "axes.labelsize": 12,
    }
)

REPORT_DIR = Path("report")
FIG_DIR = REPORT_DIR / "figures"


def plot_equity_curve():
    path = REPORT_DIR / "portfolio_daily.csv"
    if not path.exists():
        print(f"Missing {path}. Run simulate stage first.")
        return

    df = pd.read_csv(path)
    df = df.dropna(subset=["equity"])
    if df.empty:
        print("No equity data to plot (equity column is empty).")
        return

    df["date"] = pd.to_datetime(df["date"])

    plt.figure()
    plt.plot(df["date"], df["equity"])
    plt.title("Equity Curve (Simulation)")
    plt.xlabel("Date")
    plt.ylabel("Equity ($1 start)")
    plt.axhline(1.0, linestyle="--", linewidth=1)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    out = FIG_DIR / "equity_curve.png"
    plt.savefig(out, dpi=200)
    plt.close()
    print(f"Wrote {out}")


def plot_scatter_sentiment_vs_return():
    path = REPORT_DIR / "day6_merged_table.csv"
    if not path.exists():
        print(f"Missing {path}.")
        return

    df = pd.read_csv(path)
    df = df.dropna(subset=["avg_compound", "fwd_ret_1d"])
    if df.empty:
        print("No data for scatter plot (avg_compound or fwd_ret_1d missing).")
        return

    plt.figure()
    plt.scatter(df["avg_compound"], df["fwd_ret_1d"], alpha=0.6)
    plt.axhline(0.0, linestyle="--", linewidth=1)
    plt.title("Daily Sentiment vs Next-Day Return")
    plt.xlabel("avg_compound (sentiment)")
    plt.ylabel("fwd_ret_1d")
    plt.tight_layout()

    out = FIG_DIR / "sentiment_vs_return.png"
    plt.savefig(out, dpi=200)
    plt.close()
    print(f"Wrote {out}")


def _extract_event_study_numbers(md_text: str):
    """
    Parses from bullet lines in day5_results.md, e.g.
    - events_n: 9
    - event_mean_1d: 0.004464  (95% CI [-0.001589, 0.010647])
    - event_mean_3d: -0.001841 (95% CI [-0.001841, -0.001841])
    """
    # n
    m_n = re.search(r"events_n:\s*(\d+)", md_text)
    if not m_n:
        return None
    n = int(m_n.group(1))

    # mean + CI for 1d
    m1 = re.search(
        r"event_mean_1d:\s*([-\d.]+).*?\[\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\]",
        md_text,
    )
    # mean + CI for 3d
    m3 = re.search(
        r"event_mean_3d:\s*([-\d.]+).*?\[\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\]",
        md_text,
    )

    if not (m1 and m3):
        return None

    mean1, lo1, hi1 = float(m1.group(1)), float(m1.group(2)), float(m1.group(3))
    mean3, lo3, hi3 = float(m3.group(1)), float(m3.group(2)), float(m3.group(3))
    return n, (mean1, lo1, hi1), (mean3, lo3, hi3)


def plot_event_study_bar():
    path = REPORT_DIR / "day5_results.md"
    if not path.exists():
        print(f"Missing {path}. Run eval stage first.")
        return

    text = path.read_text(encoding="utf-8")
    parsed = _extract_event_study_numbers(text)
    if not parsed:
        print("Could not parse event study numbers from day5_results.md.")
        print("Make sure the report contains the 'Event study (burst days): ... (CI [...])' line.")
        return

    n, (m1, lo1, hi1), (m3, lo3, hi3) = parsed

    labels = ["1D", "3D"]
    means = [m1, m3]
    # asymmetric errors: [[lower_errors...],[upper_errors...]]
    yerr = [[m1 - lo1, m3 - lo3], [hi1 - m1, hi3 - m3]]

    plt.figure()
    plt.bar(labels, means, yerr=yerr, capsize=6)
    plt.title(f"Event Study: Avg Forward Return on Burst Days (n={n})")
    plt.xlabel("Horizon")
    plt.ylabel("Mean forward return")
    plt.axhline(0.0, linestyle="--", linewidth=1)
    plt.tight_layout()

    out = FIG_DIR / "event_study.png"
    plt.savefig(out, dpi=200)
    plt.close()
    print(f"Wrote {out}")


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    plot_equity_curve()
    plot_scatter_sentiment_vs_return()
    plot_event_study_bar()


if __name__ == "__main__":
    main()
