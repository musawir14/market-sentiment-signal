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

