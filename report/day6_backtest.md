# Day 6 — Simple Trading Simulation

Strategy:
- Build daily signal from news features.
- Long if sentiment >= threshold on burst days; short if <= -threshold on burst days.
- Execute with a 1-day delay (more realistic).
- Equal-weight portfolio across tickers with positions that day.

Parameters:
- sent_thresh: 0.02
- vol_thresh: 0.5
- min_docs: 5
- slippage_bps: 0.0

Results:
- signal_days (raw): 13
- trades (executed): 6
- sharpe_annual: -4.1952
- max_drawdown: 0.0000

Files:
- merged_table: report/day6_merged_table.csv
- portfolio_daily: report/portfolio_daily.csv
