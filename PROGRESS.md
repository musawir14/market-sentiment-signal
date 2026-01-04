## Day 1 — Setup + Skeleton
**What I shipped (GitHub link):**
- https://github.com/musawir14/market-sentiment-signal/commit/ae8cf3cffef45d2be1dd01c18c512f7ddfc59ad6

**Blockers / notes:**
- Fixed .gitignore to allow METRICS.csv (removed *.csv ignore)

**Metrics**
- tickers_targeted: 0
- pipeline_runtime_sec: 0.0
- cache_hit_rate_pct: 0.0
- news_docs_fetched: 0
- price_rows_fetched: 0

## Day 2 — Added Stooq Price Ingestions with Cache
**What I shipped (GitHub link):**
- https://github.com/musawir14/market-sentiment-signal/commit/cac584cc448b12e57b49ba3c02dc3f7023ad1514

**Metrics**
- tickers_targeted: 4
- pipeline_runtime_sec: 0.0415
- cache_hit_rate_pct: 100.0
- news_docs_fetched: 0
- price_rows_fetched: 32427

## Day 3 — Added GDELT News Ingestion with Cache

**What I shipped (GitHub link):**
- https://github.com/musawir14/market-sentiment-signal/commit/8cd9f0942be75e891937383ed1a91d67a1327c99

**Blockers / notes:**
- GDELT query for SPY initially failed due to special characters; changed query to "SPY".
- Added error handling to prevent one ticker from crashing the whole stage (try/except + continue).

**Metrics**
- tickers_targeted: 4
- pipeline_runtime_sec: 0.0032
- cache_hit_rate_pct: 100.0
- news_docs_fetched: 1000
- price_rows_fetched: 0

## Day 4 — Baseline sentiment + daily feature aggregation

**What I shipped (GitHub link):**
- https://github.com/musawir14/market-sentiment-signal/commit/6ffc4a4041e3125272202ea8987ea7e58d42e51c

**Blockers / notes:**
- Fixed GDELT `seendate` parsing so daily aggregation produces rows.

**Metrics**
- tickers_targeted: 4
- pipeline_runtime_sec: 0.1555
- cache_hit_rate_pct: 100.0
- news_docs_fetched: 1000
- daily_feature_rows: 32
- unique_days: 8

## Day 5 — Signal evaluation (merge features + forward returns)

**What I shipped (GitHub link):**
- https://github.com/musawir14/market-sentiment-signal/commit/ddc8e47fd45098d19a2ad521718ed2444a7db911

**Outputs**
- Wrote: `report/day5_results.md`

**Results**
- IC (Spearman, 1D): 0.1958
- Event study (burst days): n=9
  - mean_1d: 0.004464
  - mean_3d: -0.001841

**Run metrics**
- tickers_targeted: 4
- pipeline_runtime_sec: 1.6369
- cache_hit_rate_pct: 100.0
- merged_rows: 32

## Day 6 — Simple trading simulation (1-day delay + slippage)

**What I shipped (GitHub link):**
- https://github.com/musawir14/market-sentiment-signal/commit/10056605af9f96dcd33d208dc48deb634b296f2f

**Outputs**
- `report/day6_backtest.md`
- `report/portfolio_daily.csv`
- `report/day6_merged_table.csv`

**Strategy**
- Signal: long if avg_compound ≥ 0.05 on burst days (volume_z ≥ 1.0, docs ≥ 10); short if avg_compound ≤ -0.05 on burst days.
- Execution: 1-day delay.
- Portfolio: equal-weight across tickers with positions that day.
- Costs: 2 bps slippage per executed trade.
- Data quality: skip trades on days with missing forward returns (prevents NaNs in portfolio series).

**Results**
- trades (executed): 3
- sharpe_annual: -14.7371
- max_drawdown: 0.0000

**Run metrics**
- tickers_targeted: 4
- pipeline_runtime_sec: 0.0759
- cache_hit_rate_pct: 100.0

## Day 7 — Robustness checks (permutation p-value + bootstrap CIs)

**What I shipped (GitHub link):**
- https://github.com/musawir14/market-sentiment-signal/commit/a406715bcc8b9711b72ccb71b4476011a5458186

**Feature build**
- daily_features rows: 32
- unique_days: 8

**Evaluation (signal quality)**
- IC (Spearman, 1D): 0.1958
- Permutation p-value (IC): 0.5460
- Event study (burst days): n=9
  - mean_1d: 0.004464  (95% CI [-0.001589, 0.010647])
  - mean_3d: -0.001841 (95% CI [-0.001841, -0.001841])
- Interpretation: with this small sample, IC isn’t distinguishable from noise; next step is extending lookback window.”

**Simulation**
- trades (executed): 3
- sharpe_annual: -14.7371
- max_drawdown: 0.0000

**Run metrics**
- features runtime_sec: 0.1514
- eval runtime_sec: 0.4175
- simulate runtime_sec: 0.0793
- cache_hit_rate_pct: 100.0

## Day 8 — Parameter sweep (sensitivity analysis)

**What I added**
- Ran a grid search over simulation parameters to test sensitivity:
  - sent_thresh ∈ {0.02, 0.05, 0.08, 0.10}
  - vol_thresh ∈ {0.5, 1.0, 1.5, 2.0}
  - min_docs ∈ {5, 10, 20}
  - slippage_bps ∈ {0, 2, 5}
- Generated sweep artifacts:
  - `report/day8_sweep.csv` (all configs)
  - `report/day8_sweep.md` (top configs + summary)

**Key results**
- rows_tested: 144
- trades_range: 0 → 6
- Best-by-trades configs clustered around:
  - sent_thresh=0.02, vol_thresh=0.5, min_docs ∈ {5,10,20}, slippage_bps ∈ {0,2,5}
- In this short window, most configs have negative total_return and unstable Sharpe due to low trade count (small sample).

**Next**
- Extend lookback window (e.g., 60–180 days) so the sweep reflects more realistic performance and produces smoother equity curves.

## Day 9 — CI + Lint + Tests

**What I did**
- Set up automated checks to keep the repo clean and reproducible.
- Fixed Ruff issues (sorted imports, removed unused variables/imports).
- Made pytest run reliably on both local machine and GitHub Actions by ensuring `src/` imports work during test collection.

**Checks**
- ruff check . (passes)
- pytest -q (passes)

**Notes**
- VADER dependency emits DeprecationWarnings (third-party), but tests pass successfully.

## Day 10 — Simulation Run (Chosen Sweep Config)

**Command**
python -m src.pipeline --stage simulate --sent-thresh 0.02 --vol-thresh 0.5 --min-docs 5 --slippage-bps 0

**Strategy params**
- sent_thresh: 0.02
- vol_thresh: 0.5
- min_docs: 5
- slippage_bps: 0

**Results**
- trades: 6
- sharpe (annualized): -4.1952
- max_drawdown: 0.0000

**RunMetrics**
- tickers_targeted: 4
- pipeline_runtime_sec: 0.0907
- cache_hit_rate_pct: 100.0
- news_docs_fetched: 0
- price_rows_fetched: 0

**Outputs**
- report/day6_backtest.md
- report/day6_merged_table.csv
- report/portfolio_daily.csv
