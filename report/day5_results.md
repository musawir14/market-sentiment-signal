# Day 5 Results — Signal Evaluation

What this measures:
- **IC (Spearman, 1D):** rank correlation between daily sentiment and next-day return.
- **Event study:** average forward returns on **news-burst** days (volume_z ≥ 1.0, docs ≥ 10).

## Summary
- merged_rows: 117
- ic_spearman_1d: 0.1099
- events_n: 37
- event_mean_1d: 0.006483
- event_mean_3d: 0.008121
- ic_perm_pvalue: 0.4970
- event_mean_1d: 0.006483  (95% CI [0.000703, 0.012039])
- event_mean_3d: 0.008121  (95% CI [-0.001670, 0.017807])
