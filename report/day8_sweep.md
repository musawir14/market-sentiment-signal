# Day 8 — Parameter Sweep (Sensitivity)

This report sweeps simulator parameters to show sensitivity of results to thresholds.

- rows_tested: 144
- trades_range: 0 → 28

## Top configs (by trades, then total return)

| sent_thresh | vol_thresh | min_docs | slippage_bps | trades | total_return | sharpe_ann | max_drawdown |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.02 | 0.5 | 5 | 0 | 28 | 0.0042 | 2.4344 | -0.0076 |
| 0.02 | 0.5 | 5 | 2 | 28 | 0.0032 | 1.8605 | -0.0078 |
| 0.02 | 0.5 | 5 | 5 | 28 | 0.0017 | 0.9996 | -0.0081 |
| 0.05 | 0.5 | 5 | 0 | 27 | 0.0047 | 2.7177 | -0.0076 |
| 0.05 | 0.5 | 5 | 2 | 27 | 0.0037 | 2.1491 | -0.0078 |
| 0.05 | 0.5 | 5 | 5 | 27 | 0.0022 | 1.2961 | -0.0081 |
| 0.08 | 0.5 | 5 | 0 | 22 | 0.0011 | 0.6338 | -0.0122 |
| 0.08 | 0.5 | 5 | 2 | 22 | 0.0001 | 0.0867 | -0.0126 |
| 0.08 | 0.5 | 5 | 5 | 22 | -0.0014 | -0.7341 | -0.0132 |
| 0.02 | 1.0 | 5 | 0 | 21 | 0.0245 | 6.2442 | -0.0060 |

## Notes
- Very low trade counts can make Sharpe unstable (one bad day dominates).
- This sweep is a sanity check and helps pick reasonable defaults for a longer lookback window.
