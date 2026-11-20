"""Variance-ratio results as GitHub Markdown, in the format Issue #17 asks for:
VR table (symbol x q) with z* and the Holm verdict, the VR curve for the index,
smallest p-values, and the split-half signs.

    python -m research.arhaan.report        # print the results Markdown from the CSVs in out/
                                            # (and redraw out/vr_index.png); all results live in RESULTS.md
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from research.arhaan.load import INDEX_NAME

OUT = Path("research/arhaan/out")


def _order(names) -> list[str]:
    return sorted(n for n in names if n != INDEX_NAME) + [INDEX_NAME]


def _md_grid(t: pd.DataFrame, cell) -> str:
    """series x q Markdown table; cell(row) -> str."""
    grid = t.assign(cell=t.apply(cell, axis=1)).pivot(index="series", columns="q", values="cell")
    grid = grid.loc[_order(grid.index)]
    head = "| series | " + " | ".join(f"q = {q}" for q in grid.columns) + " |"
    sep = "|---|" + ":---:|" * len(grid.columns)
    rows = [f"| {'**' + s + '**' if s == INDEX_NAME else s} | " + " | ".join(grid.loc[s]) + " |"
            for s in grid.index]
    return "\n".join([head, sep, *rows])


def vr_cell(r) -> str:
    """VR, z* underneath; bold + 'R' if rejected after Holm."""
    text = f"{r.VR:.3f}<br><sub>z* {r.z:+.2f}</sub>"
    return f"**{r.VR:.3f} R**<br><sub>z* {r.z:+.2f}</sub>" if r.reject else text


def plot_index_curve(t: pd.DataFrame, path: Path) -> None:
    d = t[t["series"] == INDEX_NAME].sort_values("q")
    fig, ax = plt.subplots(figsize=(6, 3.6))
    ax.fill_between(d["q"], d["band_lo"], d["band_hi"], color="0.88", label="|z*| < 1.96 (per test)")
    ax.axhline(1.0, color="0.4", lw=0.8, ls="--", label="random walk (VR = 1)")
    ax.plot(d["q"], d["VR"], color="C0", lw=1.6, marker="o", label="VR(q), equal-weight index")
    rej = d["reject"].astype(bool)
    if rej.any():
        ax.scatter(d["q"][rej], d["VR"][rej], color="C3", s=40, zorder=3, label="rejected (Holm)")
    ax.set_xscale("log")
    ax.minorticks_off()
    ax.set_xticks(d["q"])
    ax.set_xticklabels(d["q"])
    ax.set_xlabel("q (hours)")
    ax.set_ylabel("VR(q)")
    ax.set_title("Variance ratio, equal-weight index of 20 symbols", fontsize=10)
    ax.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def write_report(full, half1, half2, split, spans: dict[str, str], out: Path = OUT) -> str:
    out.mkdir(parents=True, exist_ok=True)
    plot_index_curve(full, out / "vr_index.png")
    n = len(full)
    outside = int(((full.VR < full.band_lo) | (full.VR > full.band_hi)).sum())

    top = full.nsmallest(10, "p")
    top_md = "\n".join(
        ["| series | q | VR | z* | p | p (Holm) | verdict |", "|---|---:|---:|---:|---:|---:|---|"]
        + [f"| {r.series} | {r.q} | {r.VR:.3f} | {r.z:+.2f} | {r.p:.4f} | {r.p_holm:.4f} | "
           f"{'reject' if r.reject else 'not rejected'} |" for r in top.itertuples()])

    below = full.groupby("q").agg(n_below=("VR", lambda v: int((v < 1).sum())),
                                  lo=("band_lo", "median"), hi=("band_hi", "median"))
    below_md = "\n".join(["| q | series with VR < 1 | typical band (\\|z*\\| < 1.96) |", "|---:|:---:|:---:|"]
                         + [f"| {q} | {int(r.n_below)} of {n // below.shape[0]} | {r.lo:.2f} – {r.hi:.2f} |"
                            for q, r in below.iterrows()])

    sym = {1: "+", -1: "−", 0: "0"}
    split_md = _md_grid(split, lambda r: f"{sym[r.sign_h1]} / {sym[r.sign_h2]}" + (" ⟂" if r.flips else ""))
    judged = full[full["reject"]].merge(split[["series", "q", "flips"]], on=["series", "q"])
    if judged.empty:
        split_verdict = ("No test is rejected on the full panel, so under the declared rule no effect is judged. "
                         f"{int(split.flips.sum())} of {len(split)} signs flip between halves, as expected for noise around VR = 1.")
    else:
        kept = judged[~judged["flips"]]
        split_verdict = (f"{len(judged)} full-panel rejection(s) judged; {len(kept)} keep their sign in both halves"
                         + (": " + ", ".join(f"{r.series} q = {r.q}" for r in kept.itertuples()) if len(kept) else "."))

    md = f"""## Variance-ratio results

**Holm rejections (5 % family-wise, {n} tests):** full panel **{int(full.reject.sum())}**, first half **{int(half1.reject.sum())}**, second half **{int(half2.reject.sum())}**. Outside the per-test band on the full panel: {outside} of {n}.

| period | span |
|---|---|
| full panel | {spans['full']} |
| first half | {spans['half1']} |
| second half | {spans['half2']} |

20 symbols + equal-weight index (mean of the 20 hourly log returns). Hourly close-to-close log returns. Lo–MacKinlay (1988) bias-corrected VR from overlapping sums; heteroskedasticity-robust z*; Holm over all {n} tests. q = 168 has only 88 non-overlapping weeks, so it is weak evidence either way.

### VR table, full panel (VR, with z* below; **R** = rejected after Holm)
VR > 1: moves continue (momentum). VR < 1: moves reverse.

{_md_grid(full, vr_cell)}

### VR curve, equal-weight index

![VR curve, equal-weight index](vr_index.png)

Grey band: VR values with |z*| < 1.96 for that test alone. Holm over {n} tests is stricter, so a point outside the band need not be rejected.

### Direction by horizon, full panel

{below_md}

### Smallest p-values, full panel

{top_md}

### Split-half: sign of VR − 1 (first half / second half)
⟂ = sign flips. Declared rule: only full-panel Holm rejections are judged, and a judged effect must keep its sign.

{split_md}

{split_verdict}

### All series
Per-series curves: [full panel](vr_full.png) · [first half](vr_half1.png) · [second half](vr_half2.png). Full numbers: `vr_full.csv`, `vr_half1.csv`, `vr_half2.csv`, `split_half.csv`.
"""
    decomp = out / "decomposition.csv"
    if decomp.exists():
        from research.arhaan.decomposition import to_markdown
        md += "\n### Contrarian profit decomposition (Lo–MacKinlay 1990)\n\n" + to_markdown(pd.read_csv(decomp)) + "\n"
    return md   # Markdown text; pasted into research/arhaan/RESULTS.md (no separate file is written)


def _span(idx) -> str:
    return f"{idx[0]:%Y-%m-%d %H:%M} to {idx[-1]:%Y-%m-%d %H:%M} UTC, {len(idx):,} h"


if __name__ == "__main__":
    from research.arhaan.load import load_returns
    from research.arhaan.vr_testing import split_halves

    returns = load_returns()
    h1, h2 = split_halves(returns)
    spans = {"full": _span(returns.index), "half1": _span(h1.index), "half2": _span(h2.index)}
    t = {k: pd.read_csv(OUT / f"{k}.csv") for k in ["vr_full", "vr_half1", "vr_half2", "split_half"]}
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print(write_report(t["vr_full"], t["vr_half1"], t["vr_half2"], t["split_half"], spans))
