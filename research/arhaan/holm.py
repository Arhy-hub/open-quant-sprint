import numpy as np
from scipy.stats import norm


def p_values(z) -> np.ndarray:
    """Two-sided p-values from z statistics: p = 2 * P(Z > |z|)."""
    return 2 * norm.sf(np.abs(np.asarray(z, dtype=float)))


def holm(pvals, alpha: float = 0.05) -> tuple[np.ndarray, np.ndarray]:
    """Holm (1979) step-down correction across one family of tests.

    pvals: p-values in any order (e.g. all 126 VR tests). NaN is not allowed.
    Returns (reject, p_adj), both in the original order:
      reject[i] -- True if test i is rejected at family-wise level alpha
      p_adj[i]  -- Holm-adjusted p-value; reject[i] == (p_adj[i] <= alpha)
    """
    p = np.asarray(pvals, dtype=float)
    if np.isnan(p).any():
        raise ValueError("p-values contain NaN")
    m = p.size

    order = np.argsort(p)                         # smallest p first
    k = np.arange(1, m + 1)                       # rank 1..m
    stepped = (m - k + 1) * p[order]              # compare p_(k) with alpha / (m - k + 1)
    adj_sorted = np.minimum(np.maximum.accumulate(stepped), 1.0)  # step-down: never decreases

    p_adj = np.empty(m)
    p_adj[order] = adj_sorted
    return p_adj <= alpha, p_adj
