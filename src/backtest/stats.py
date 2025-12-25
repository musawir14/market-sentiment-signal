from __future__ import annotations

import numpy as np
import pandas as pd


def spearman_ic(x: pd.Series, y: pd.Series) -> float:
    df = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(df) < 10:
        return 0.0
    # Spearman = Pearson corr of ranks (no SciPy needed)
    xr = df["x"].rank(method="average")
    yr = df["y"].rank(method="average")
    ic = xr.corr(yr)
    return float(ic) if ic == ic else 0.0


def permutation_pvalue_ic(
    x: pd.Series,
    y: pd.Series,
    n_perm: int = 1000,
    seed: int = 42,
) -> float:
    """
    Null: x has no relationship to y.
    We shuffle y and recompute IC, then see how often |IC_perm| >= |IC_obs|.
    """
    df = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(df) < 10:
        return 1.0

    rng = np.random.default_rng(seed)
    x_vals = df["x"].to_numpy()
    y_vals = df["y"].to_numpy()

    ic_obs = spearman_ic(pd.Series(x_vals), pd.Series(y_vals))
    ic_perm = []

    for _ in range(n_perm):
        y_shuf = rng.permutation(y_vals)
        ic_perm.append(spearman_ic(pd.Series(x_vals), pd.Series(y_shuf)))

    ic_perm = np.asarray(ic_perm)
    p = float((np.abs(ic_perm) >= abs(ic_obs)).mean())
    return p


def bootstrap_mean_ci(
    s: pd.Series,
    n_boot: int = 2000,
    seed: int = 42,
    alpha: float = 0.05,
) -> tuple[float, float, float]:
    """
    Returns (mean, lo, hi) for a bootstrap CI on the mean.
    """
    x = pd.to_numeric(s, errors="coerce").dropna().to_numpy()
    if len(x) < 5:
        m = float(np.nanmean(x)) if len(x) else 0.0
        return m, m, m

    rng = np.random.default_rng(seed)
    m = float(x.mean())
    boots = []
    for _ in range(n_boot):
        samp = rng.choice(x, size=len(x), replace=True)
        boots.append(samp.mean())

    boots = np.asarray(boots)
    lo = float(np.quantile(boots, alpha / 2))
    hi = float(np.quantile(boots, 1 - alpha / 2))
    return m, lo, hi
