# Day 8 — Parameter Sweep (Sensitivity)

This report sweeps simulator parameters to show sensitivity of results to thresholds.

- rows_tested: 144
- trades_range: 0 → 16

## Top configs (by trades, then total return)

| sent_thresh | vol_thresh | min_docs | slippage_bps | trades | total_return | sharpe_ann | max_drawdown |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.02 | 0.5 | 5 | 0 | 16 | 0.0221 | 4.8131 | -0.0056 |
| 0.02 | 0.5 | 10 | 0 | 16 | 0.0221 | 4.8131 | -0.0056 |
| 0.02 | 0.5 | 5 | 2 | 16 | 0.0212 | 4.6425 | -0.0058 |
| 0.02 | 0.5 | 10 | 2 | 16 | 0.0212 | 4.6425 | -0.0058 |
| 0.02 | 0.5 | 5 | 5 | 16 | 0.0200 | 4.3866 | -0.0061 |
| 0.02 | 0.5 | 10 | 5 | 16 | 0.0200 | 4.3866 | -0.0061 |
| 0.02 | 0.5 | 20 | 0 | 15 | 0.0240 | 5.2974 | -0.0037 |
| 0.02 | 0.5 | 20 | 2 | 15 | 0.0232 | 5.1242 | -0.0039 |
| 0.02 | 0.5 | 20 | 5 | 15 | 0.0220 | 4.8645 | -0.0042 |
| 0.02 | 1.0 | 5 | 0 | 15 | 0.0144 | 3.1964 | -0.0056 |

## Notes
- Very low trade counts can make Sharpe unstable (one bad day dominates).
- This sweep is a sanity check and helps pick reasonable defaults for a longer lookback window.
