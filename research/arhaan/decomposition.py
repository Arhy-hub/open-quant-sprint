"""Lo-MacKinlay (1990) contrarian profit decomposition, as specified in Issue #17.

For q in {24, 72, 168}: non-overlapping q-hour log returns R_t of the 20 symbols.
    G[i, j] = cov(R[t-1, i], R[t, j])            lag-one cross-autocovariance matrix
    w[t, i] = -(R[t-1, i] - mean_j R[t-1, j]) / N contrarian weights (sum to zero)
    profit_t = sum_i w[t, i] * R[t, i]
Average profit = own + cross + mean, where
    own   = -(N - 1) / N**2 * trace(G)           from each symbol's own autocorrelation
    cross = (G.sum() - trace(G)) / N**2           from cross-autocorrelations between symbols
    mean  = -cross-sectional variance of the N mean returns
Covariances use 1/T (ddof=0) over the T window pairs, so the identity holds exactly up to
the gap between the means of R[t-1] and R[t] (the "small terms" the Issue mentions).

    python -m research.arhaan.decomposition     # writes out/decomposition.csv, prints the table
"""
from pathlib import Path

import numpy as np
import pandas as pd

Q_DECOMP = [24, 72, 168]
OUT = Path("research/arhaan/out")


def window_returns(returns: pd.DataFrame, q: int) -> np.ndarray:
    """Non-overlapping q-hour log returns (sums of q hourly log returns), from the first hour.
    Leftover hours at the end that don't fill a window are dropped. Shape (T+1, N)."""
    r = returns.to_numpy(dtype=float)
    n_win = len(r) // q
    return r[: n_win * q].reshape(n_win, q, r.shape[1]).sum(axis=1)


def parts_from_pairs(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    """x = R[t-1], y = R[t], one row per window pair. Returns the three parts and the profit."""
    T, N = x.shape
    xd, yd = x - x.mean(axis=0), y - y.mean(axis=0)
    G = xd.T @ yd / T                                  # G[i, j] = cov(x_i, y_j), ddof=0
    tr = np.trace(G)
    own = -(N - 1) / N**2 * tr
    cross = (G.sum() - tr) / N**2
    mean = -np.var(y.mean(axis=0))                     # cross-sectional variance of mean returns
    w = -(x - x.mean(axis=1, keepdims=True)) / N       # contrarian weights
    profit = float(np.mean(np.sum(w * y, axis=1)))
    return dict(own=own, cross=cross, mean=mean, total=own + cross + mean, profit=profit)


def block_bootstrap(x, y, block: int, reps: int, seed: int) -> pd.DataFrame:
    """Moving-block bootstrap over window pairs (x_t, y_t): blocks of consecutive pairs,
    drawn with replacement until T pairs. Returns one row of parts per replication."""
    T = len(x)
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(T / block))
    rows = []
    for _ in range(reps):
        starts = rng.integers(0, T - block + 1, size=n_blocks)
        idx = (starts[:, None] + np.arange(block)).ravel()[:T]
        rows.append(parts_from_pairs(x[idx], y[idx]))
    return pd.DataFrame(rows)


def decompose(returns: pd.DataFrame, q_list=Q_DECOMP, block_rule=lambda T: int(np.ceil(T ** (1 / 3))),
              reps: int = 2000, seed: int = 0, level: float = 0.95) -> pd.DataFrame:
    """One row per q: point estimates, bootstrap intervals, and the identity check."""
    lo_p, hi_p = 100 * (1 - level) / 2, 100 * (1 + level) / 2
    rows = []
    for q in q_list:
        R = window_returns(returns, q)
        x, y = R[:-1], R[1:]
        T = len(x)
        point = parts_from_pairs(x, y)
        block = block_rule(T)
        boot = block_bootstrap(x, y, block, reps, seed + q)
        row = dict(q=q, windows=len(R), pairs=T, block=block, reps=reps, **point,
                   gap=point["profit"] - point["total"])
        for k in ["own", "cross", "mean", "profit"]:
            row[f"{k}_lo"], row[f"{k}_hi"] = np.percentile(boot[k], [lo_p, hi_p])
        rows.append(row)
    return pd.DataFrame(rows)


def to_markdown(d: pd.DataFrame, unit: float = 1e4) -> str:
    """Parts in basis points of log return per window, with bootstrap intervals."""
    def ci(r, k):
        return f"{unit * r[k]:+.2f} <sub>[{unit * r[k + '_lo']:+.2f}, {unit * r[k + '_hi']:+.2f}]</sub>"

    lines = ["| q | windows | own | cross | mean | own + cross + mean | average profit | gap |",
             "|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for _, r in d.iterrows():
        lines.append(f"| {int(r.q)} | {int(r.windows)} | {ci(r, 'own')} | {ci(r, 'cross')} | {ci(r, 'mean')} | "
                     f"{unit * r.total:+.2f} | {ci(r, 'profit')} | {unit * r.gap:+.3f} |")
    b = d.iloc[0]
    note = (f"Basis points of log return per q-hour window. Brackets: {int(100 * 0.95)} % moving-block bootstrap "
            f"intervals over window pairs ({int(b.reps)} replications; block length ceil(T^(1/3)) = "
            + ", ".join(f"{int(r.block)} at q = {int(r.q)}" for _, r in d.iterrows())
            + "). Gap = average profit − (own + cross + mean), from estimating the means on R[t−1] vs R[t].")
    return "\n".join(lines) + "\n\n" + note


if __name__ == "__main__":
    import sys

    from research.arhaan.load import INDEX_NAME, load_returns

    sys.stdout.reconfigure(encoding="utf-8")

    returns = load_returns().drop(columns=[INDEX_NAME])
    d = decompose(returns)
    OUT.mkdir(parents=True, exist_ok=True)
    d.to_csv(OUT / "decomposition.csv", index=False)
    print(to_markdown(d))
