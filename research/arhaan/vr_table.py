import numpy as np
import pandas as pd

from src.contrib.arhaan import variance_ratio
from research.arhaan.holm import holm, p_values

Q_LIST = [2, 4, 8, 24, 72, 168]
Z_CRIT = 1.96


def vr_table(returns: pd.DataFrame, q_list=Q_LIST, alpha: float = 0.05) -> pd.DataFrame:
    """VR, z*, p, Holm and the |z*| < 1.96 band for every column of `returns` and every q.

    returns: hours x series (from load.returns_from_bars).
    Output: one row per (series, q), columns
      series, q, nq, VR, z, p, p_holm, reject, band_lo, band_hi
    Holm runs once over all rows of this table (one family, level alpha).
    band_lo / band_hi: the VR values at which |z*| = 1.96, i.e. 1 -/+ 1.96 * sqrt(theta / nq).
    """
    rows = []
    for series in returns.columns:
        r = returns[series].to_numpy(dtype=float)
        nq = int(np.sum(~np.isnan(r)))
        for q in q_list:
            vr, z = variance_ratio(r, q)
            # sqrt(theta) recovered from z* = sqrt(nq) * (VR - 1) / sqrt(theta)
            half = Z_CRIT * (vr - 1) / z if z != 0 else np.nan   # = 1.96 * sqrt(theta / nq)
            rows.append(dict(series=series, q=q, nq=nq, VR=vr, z=z,
                             band_lo=1 - abs(half), band_hi=1 + abs(half)))
    table = pd.DataFrame(rows)
    table["p"] = p_values(table["z"])
    table["reject"], table["p_holm"] = holm(table["p"], alpha)
    return table[["series", "q", "nq", "VR", "z", "p", "p_holm", "reject", "band_lo", "band_hi"]]
