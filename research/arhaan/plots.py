import math

import matplotlib.pyplot as plt
import pandas as pd


def plot_vr_curves(table: pd.DataFrame, path: str | None = None, ncols: int = 4):
    """One panel per series: VR against q (log x-axis), shaded band where |z*| < 1.96,
    dashed line at VR = 1. If `table` has a boolean `reject` column (Holm), rejected
    points are filled; others are hollow.
    """
    series = list(dict.fromkeys(table["series"]))
    nrows = math.ceil(len(series) / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(3.2 * ncols, 2.4 * nrows),
                             sharex=True, squeeze=False)

    for ax, name in zip(axes.flat, series):
        t = table[table["series"] == name].sort_values("q")
        ax.fill_between(t["q"], t["band_lo"], t["band_hi"], color="0.85", label="|z*| < 1.96")
        ax.axhline(1.0, color="0.4", lw=0.8, ls="--")
        ax.plot(t["q"], t["VR"], color="C0", lw=1.2)
        if "reject" in t:
            rej = t["reject"].astype(bool)
            ax.scatter(t["q"][rej], t["VR"][rej], color="C3", s=18, zorder=3, label="Holm reject")
            ax.scatter(t["q"][~rej], t["VR"][~rej], facecolors="white", edgecolors="C0", s=18, zorder=3)
        else:
            ax.scatter(t["q"], t["VR"], color="C0", s=12, zorder=3)
        ax.set_xscale("log")
        ax.minorticks_off()
        ax.set_xticks(sorted(t["q"]))
        ax.set_xticklabels(sorted(t["q"]), fontsize=7)
        ax.set_title(name, fontsize=9)
        ax.tick_params(labelsize=7, labelbottom=True)

    for ax in list(axes.flat)[len(series):]:
        ax.set_visible(False)

    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower right", fontsize=8, frameon=False)
    fig.supxlabel("q (hours)", fontsize=9)
    fig.supylabel("VR(q)", fontsize=9)
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=150)
    return fig
