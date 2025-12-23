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


