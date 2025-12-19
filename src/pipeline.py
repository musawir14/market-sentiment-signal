from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from src.ingestion.stooq_prices import load_or_download_daily_prices


@dataclass
class RunMetrics:
    tickers_targeted: int = 0
    pipeline_runtime_sec: float = 0.0
    cache_hit_rate_pct: float = 0.0
    news_docs_fetched: int = 0
    price_rows_fetched: int = 0


DEFAULT_TICKERS = [
    "aapl.us",
    "msft.us",
    "nvda.us",
    "spy.us",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Market sentiment project pipeline.")
    p.add_argument(
        "--stage",
        choices=["scaffold", "prices"],
        default="scaffold",
        help="Which stage to run.",
    )
    p.add_argument(
        "--tickers",
        default=",".join(DEFAULT_TICKERS),
        help="Comma-separated Stooq tickers (e.g., aapl.us,msft.us,spy.us).",
    )
    return p.parse_args()


def run_prices_stage(tickers: list[str]) -> RunMetrics:
    metrics = RunMetrics()
    metrics.tickers_targeted = len(tickers)

    cache_dir = Path("data") / "prices"
    total_rows = 0
    cache_hits = 0

    for t in tickers:
        df, result = load_or_download_daily_prices(ticker=t, cache_dir=cache_dir)
        total_rows += result.rows
        cache_hits += 1 if result.cache_hit else 0
        # Helpful print for debugging / proof on GitHub
        print(f"- {t}: rows={result.rows}, cache_hit={result.cache_hit}, path={result.path}")

    metrics.price_rows_fetched = total_rows
    metrics.cache_hit_rate_pct = round((cache_hits / len(tickers)) * 100.0, 2) if tickers else 0.0
    return metrics


def main() -> None:
    args = parse_args()
    start = time.time()

    tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]

    if args.stage == "prices":
        metrics = run_prices_stage(tickers)
    else:
        # Day 1 scaffold
        metrics = RunMetrics(tickers_targeted=0)

    metrics.pipeline_runtime_sec = round(time.time() - start, 4)

    print("\n✅ Market Sentiment Pipeline")
    print(f"Date: {date.today().isoformat()}")
    print(metrics)


if __name__ == "__main__":
    main()
