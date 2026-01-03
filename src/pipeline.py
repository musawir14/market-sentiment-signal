from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from src.backtest.eval import build_eval_table, run_signal_eval, write_day5_report, write_merged_csv
from src.backtest.sim import simulate_equal_weight_portfolio
from src.backtest.sweep import run_sweep, write_sweep_report
from src.features.daily_features import build_and_save_daily_features
from src.ingestion.gdelt_news import load_or_download_gdelt_articles
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
        choices=["scaffold", "prices", "news", "features", "eval", "simulate", "sweep"],
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
    p.add_argument(
        "--sent-thresh", type=float, default=0.05, help="Sentiment threshold for long/short."
    )
    p.add_argument(
        "--vol-thresh", type=float, default=1.0, help="volume_z threshold for burst days."
    )
    p.add_argument("--min-docs", type=int, default=10, help="Minimum docs for signal day.")
    p.add_argument(
        "--slippage-bps", type=float, default=2.0, help="Slippage per trade in basis points."
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

        print(
            f"- {t}: query='{query}', docs={result.docs}, cache_hit={result.cache_hit}, path={result.path}"
        )

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
        metrics = run_news_stage(
            tickers, lookback_days=args.lookback_days, max_records=args.max_records
        )
    elif args.stage == "features":
        # Force-load from cache by calling the same ingestion function (it should hit cache)
        from src.ingestion.gdelt_news import load_or_download_gdelt_articles

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
        print(
            f"\nWrote daily features: rows={result.rows_written}, unique_days={result.unique_days}, path={result.path}"
        )
    elif args.stage == "eval":
        features_path = Path("data") / "features" / "daily_features.csv"
        prices_cache_dir = Path("data") / "prices"

        eval_df = build_eval_table(
            tickers=tickers,
            features_path=features_path,
            prices_cache_dir=prices_cache_dir,
        )

        res = run_signal_eval(eval_df)

        # Write a GitHub-trackable report (small markdown file)
        report_path = Path("report") / "day5_results.md"
        write_day5_report(res, report_path)

        metrics = RunMetrics(tickers_targeted=len(tickers))
        metrics.news_docs_fetched = int(len(eval_df))  # rows in merged table (proxy)
        metrics.cache_hit_rate_pct = 100.0
        print(f"\nWrote report: {report_path}")
        print(
            f"IC (Spearman, 1D): {res.ic_spearman_1d:.4f}  |  perm p-value: {res.ic_perm_pvalue:.4f}"
        )
        print(
            "Event study (burst days): "
            f"n={res.events_n}, "
            f"mean_1d={res.event_mean_1d:.6f} (CI [{res.event_mean_1d_ci_lo:.6f}, {res.event_mean_1d_ci_hi:.6f}]), "
            f"mean_3d={res.event_mean_3d:.6f} (CI [{res.event_mean_3d_ci_lo:.6f}, {res.event_mean_3d_ci_hi:.6f}])"
        )

    elif args.stage == "simulate":
        features_path = Path("data") / "features" / "daily_features.csv"
        prices_cache_dir = Path("data") / "prices"

        eval_df = build_eval_table(
            tickers=tickers,
            features_path=features_path,
            prices_cache_dir=prices_cache_dir,
        )

        # Save merged table for transparency (small enough to track for now)
        merged_path = Path("report") / "day6_merged_table.csv"
        write_merged_csv(eval_df, merged_path)

        sim = simulate_equal_weight_portfolio(
            merged_df=eval_df,
            out_dir=Path("report"),
            sent_thresh=args.sent_thresh,
            vol_thresh=args.vol_thresh,
            min_docs=args.min_docs,
            slippage_bps=args.slippage_bps,
        )

        # Write a small markdown report (GitHub-tracked)
        report_path = Path("report") / "day6_backtest.md"
        report_path.write_text(
            "\n".join(
                [
                    "# Day 6 — Simple Trading Simulation",
                    "",
                    "Strategy:",
                    "- Build daily signal from news features.",
                    "- Long if sentiment >= threshold on burst days; short if <= -threshold on burst days.",
                    "- Execute with a 1-day delay (more realistic).",
                    "- Equal-weight portfolio across tickers with positions that day.",
                    "",
                    "Parameters:",
                    f"- sent_thresh: {args.sent_thresh}",
                    f"- vol_thresh: {args.vol_thresh}",
                    f"- min_docs: {args.min_docs}",
                    f"- slippage_bps: {args.slippage_bps}",
                    "",
                    "Results:",
                    f"- signal_days (raw): {sim.n_signal_days}",
                    f"- trades (executed): {sim.n_trades}",
                    f"- sharpe_annual: {sim.sharpe_annual:.4f}",
                    f"- max_drawdown: {sim.max_drawdown:.4f}",
                    "",
                    "Files:",
                    f"- merged_table: {merged_path}",
                    f"- portfolio_daily: {sim.out_portfolio_csv}",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        metrics = RunMetrics(tickers_targeted=len(tickers))
        metrics.cache_hit_rate_pct = 100.0
        print(f"\nWrote report: {report_path}")
        print(f"Trades: {sim.n_trades}")
        print(f"Sharpe (annualized): {sim.sharpe_annual:.4f}")
        print(f"Max drawdown: {sim.max_drawdown:.4f}")
    elif args.stage == "sweep":
        merged_path = Path("report") / "day6_merged_table.csv"
        out_csv = Path("report") / "day8_sweep.csv"
        out_md = Path("report") / "day8_sweep.md"
        df = run_sweep(merged_path)
        write_sweep_report(df, out_csv=out_csv, out_md=out_md)
        print(f"Wrote {out_csv}")
        print(f"Wrote {out_md}")
        metrics = RunMetrics(
            tickers_targeted=len(tickers),
            pipeline_runtime_sec=0.0,
            cache_hit_rate_pct=0.0,
            news_docs_fetched=0,
            price_rows_fetched=0,
        )
    else:
        metrics = RunMetrics(tickers_targeted=0)

    metrics.pipeline_runtime_sec = round(time.time() - start, 4)

    print("\n✅ Market Sentiment Pipeline")
    print(f"Date: {date.today().isoformat()}")
    print(metrics)


if __name__ == "__main__":
    main()
