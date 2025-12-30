# Day 8 — Parameter Sweep (Sensitivity)

This report sweeps simulator parameters to show sensitivity of results to thresholds.

- rows_tested: 144
- trades_range: 0 → 6

## Top configs (by trades, then total return)

| sent_thresh | vol_thresh | min_docs | slippage_bps | trades | total_return | sharpe_ann | max_drawdown |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.02 | 0.5 | 5 | 0 | 6 | -0.0064 | -4.1952 | 0.0000 |
| 0.02 | 0.5 | 10 | 0 | 6 | -0.0064 | -4.1952 | 0.0000 |
| 0.02 | 0.5 | 20 | 0 | 6 | -0.0064 | -4.1952 | 0.0000 |
| 0.02 | 0.5 | 5 | 2 | 6 | -0.0068 | -4.4637 | 0.0000 |
| 0.02 | 0.5 | 10 | 2 | 6 | -0.0068 | -4.4637 | 0.0000 |
| 0.02 | 0.5 | 20 | 2 | 6 | -0.0068 | -4.4637 | 0.0000 |
| 0.02 | 0.5 | 5 | 5 | 6 | -0.0074 | -4.8664 | 0.0000 |
| 0.02 | 0.5 | 10 | 5 | 6 | -0.0074 | -4.8664 | 0.0000 |
| 0.02 | 0.5 | 20 | 5 | 6 | -0.0074 | -4.8664 | 0.0000 |
| 0.02 | 1.0 | 5 | 0 | 5 | -0.0139 | -13.6922 | 0.0000 |

## Notes
- Very low trade counts can make Sharpe unstable (one bad day dominates).
- This sweep is a sanity check and helps pick reasonable defaults for a longer lookback window.
