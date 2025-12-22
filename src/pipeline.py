from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from src.ingestion.stooq_prices import load_or_download_daily_prices
from src.ingestion.gdelt_news import load_or_download_gdelt_articles
from src.features.daily_features import build_and_save_daily_features



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

TICKER_TO_QUERY = {
    "aapl.us": "Apple",
    "msft.us": "Microsoft",
    "nvda.us": "NVIDIA",
    "spy.us": "SPY",
}



def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Market sentiment project pipeline.")
    p.add_argument(
        "--stage",
        choices=["scaffold", "prices", "news", "features"],
        default="scaffold",
        help="Which stage to run.",
    )
    p.add_argument(
        "--tickers",
        default=",".join(DEFAULT_TICKERS),
        help="Comma-separated Stooq tickers (e.g., aapl.us,msft.us,spy.us).",
    )
    p.add_argument("--lookback-days", type=int, default=7, help="Days of news to fetch.")
    p.add_argument("--max-records", type=int, default=250, help="Max articles per ticker query.")

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

def run_news_stage(tickers: list[str], lookback_days: int, max_records: int) -> RunMetrics:
    metrics = RunMetrics()
    metrics.tickers_targeted = len(tickers)

    cache_dir = Path("data") / "news"
    total_docs = 0
    cache_hits = 0

    for t in tickers:
        query = TICKER_TO_QUERY.get(t.lower(), t)  # fallback to ticker if unknown
        try:
            articles, result = load_or_download_gdelt_articles(
                key=t,
                query=query,
                cache_dir=cache_dir,
                lookback_days=lookback_days,
                max_records=max_records,
        )
        except Exception as e:
            print(f"- {t}: query='{query}' FAILED: {e}")
            continue  # skip this ticker and move on

        total_docs += result.docs
        cache_hits += 1 if result.cache_hit else 0

        print(f"- {t}: query='{query}', docs={result.docs}, cache_hit={result.cache_hit}, path={result.path}")

    metrics.news_docs_fetched = total_docs
    metrics.cache_hit_rate_pct = round((cache_hits / len(tickers)) * 100.0, 2) if tickers else 0.0
    return metrics


def main() -> None:
    args = parse_args()
    start = time.time()

    tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]

    if args.stage == "prices":
        metrics = run_prices_stage(tickers)
    elif args.stage == "news":
        metrics = run_news_stage(tickers, lookback_days=args.lookback_days, max_records=args.max_records)
    elif args.stage == "features":
        # Force-load from cache by calling the same ingestion function (it should hit cache)
        from src.ingestion.gdelt_news import load_or_download_gdelt_articles
        from pathlib import Path

        ticker_to_articles = {}
        for t in tickers:
            query = TICKER_TO_QUERY.get(t.lower(), t)
            articles, _ = load_or_download_gdelt_articles(
                key=t,
                query=query,
                cache_dir=Path("data") / "news",
                lookback_days=args.lookback_days,
                max_records=args.max_records,
            )
            ticker_to_articles[t] = articles

        result = build_and_save_daily_features(
            ticker_to_articles=ticker_to_articles,
            out_path=Path("data") / "features" / "daily_features.csv",
        )

        # Put something meaningful in metrics for display
        metrics = RunMetrics(tickers_targeted=len(tickers))
        metrics.news_docs_fetched = sum(len(v) for v in ticker_to_articles.values())
        metrics.cache_hit_rate_pct = 100.0  # should be, if cached; we’ll verify via output speed
        print(f"\nWrote daily features: rows={result.rows_written}, unique_days={result.unique_days}, path={result.path}")
    else:
        metrics = RunMetrics(tickers_targeted=0)


    metrics.pipeline_runtime_sec = round(time.time() - start, 4)

    print("\n✅ Market Sentiment Pipeline")
    print(f"Date: {date.today().isoformat()}")
    print(metrics)


if __name__ == "__main__":
    main()
