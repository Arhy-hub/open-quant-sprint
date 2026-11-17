"""Track 11, Part 2: variance-ratio study on the full panel and on each half.

Run from the repo root (only after the declaration is posted on the PR):
    python -m research.arhaan.VR_testing

Writes to research/arhaan/out/:
    vr_full.csv, vr_half1.csv, vr_half2.csv   -- one row per (series, q), Holm within each
    split_half.csv                            -- sign of VR - 1 in each half, and whether it flips
    vr_full.png, vr_half1.png, vr_half2.png   -- VR curves with the |z*| < 1.96 band
"""
from pathlib import Path

import numpy as np
import pandas as pd

from research.arhaan.load import load_returns
from research.arhaan.plots import plot_vr_curves
from research.arhaan.vr_table import vr_table

OUT = Path("research/arhaan/out")


def split_halves(returns: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """First and second half by timestamp midpoint (the grid is complete, so equal row counts)."""
    mid = len(returns) // 2
    return returns.iloc[:mid], returns.iloc[mid:]


def split_half_check(t1: pd.DataFrame, t2: pd.DataFrame) -> pd.DataFrame:
    """Sign of VR - 1 in each half, per (series, q). flips = the sign changes between halves."""
    keep = ["series", "q", "VR", "z", "reject"]
    m = t1[keep].merge(t2[keep], on=["series", "q"], suffixes=("_h1", "_h2"))
    m["sign_h1"] = np.sign(m["VR_h1"] - 1).astype(int)
    m["sign_h2"] = np.sign(m["VR_h2"] - 1).astype(int)
    m["flips"] = m["sign_h1"] != m["sign_h2"]
    return m


def run(returns: pd.DataFrame, out: Path = OUT) -> dict[str, pd.DataFrame]:
    out.mkdir(parents=True, exist_ok=True)
    h1, h2 = split_halves(returns)

    tables = {"full": vr_table(returns), "half1": vr_table(h1), "half2": vr_table(h2)}
    periods = {"full": returns, "half1": h1, "half2": h2}
    for name, t in tables.items():
        t.to_csv(out / f"vr_{name}.csv", index=False)
        idx = periods[name].index
        fig = plot_vr_curves(t, out / f"vr_{name}.png")
        fig.suptitle(f"VR(q), {name}: {idx[0]} to {idx[-1]} ({len(idx)} h)", fontsize=10)
        fig.savefig(out / f"vr_{name}.png", dpi=150)

    split = split_half_check(tables["half1"], tables["half2"])
    split.to_csv(out / "split_half.csv", index=False)
    tables["split"] = split
    return tables


if __name__ == "__main__":
    tables = run(load_returns())
    full, split = tables["full"], tables["split"]
    print(f"full panel: {int(full['reject'].sum())} of {len(full)} tests rejected after Holm")
    print(f"split-half: {int(split['flips'].sum())} of {len(split)} (series, q) flip sign")
    print(f"written to {OUT}/")
