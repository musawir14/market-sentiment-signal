# Day 5 Results — Signal Evaluation

What this measures:
- **IC (Spearman, 1D):** rank correlation between daily sentiment and next-day return.
- **Event study:** average forward returns on **news-burst** days (volume_z ≥ 1.0, docs ≥ 10).

## Dataset
- merged_rows: 223
- tickers: 15 (aapl.us, amzn.us, avgo.us, cost.us, googl.us, jpm.us, ma.us, meta.us, msft.us, nvda.us, spy.us, tsla.us, unh.us, v.us, xom.us)
- date_span: 2025-12-27 → 2026-01-10

## Summary
- ic_spearman_1d: 0.1003
- ic_perm_pvalue: 0.4180
- events_n: 57
- event_mean_1d: -0.001749 (95% CI [-0.007845, 0.004329])
- event_mean_3d: 0.003809 (95% CI [-0.008633, 0.015956])

## Interpretation
The sentiment feature shows a 0.1003 Spearman IC with next-day returns and is not statistically significant (perm p-value = 0.4180).
On burst days (high volume_z), the event study suggests average forward returns of -0.001749 (1D) and 0.003809 (3D). Use this as a directional signal quality check, not a guarantee of predictability.
