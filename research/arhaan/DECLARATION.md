# Track 11 — pre-registration (Issue #17)

Declared before the first full-panel run. Posted to the PR on: **<date, time UTC>**

## Data
- Panel: `data/train_1h.parquet`, 20 symbols, hourly bars.
- Series: hourly close-to-close log returns, `ln(close_t / close_{t-1})`, per symbol, rows sorted by timestamp; the first return of each symbol (NaN) is dropped. Confirmed by the organiser on #17; the same returns the backtest (`src/backtest.py`) and quality check (`src/quality.py`) use.
- Grid: complete hourly grid, verified in code (every symbol has a close every hour; consecutive timestamps exactly 1 h apart). The loader raises instead of filling gaps.
- Equal-weighted index: cross-sectional mean of the 20 symbols' hourly log returns each hour (as in #17). This is the mean of log returns, a close approximation to the log of the mean gross return; not a mean of prices.

## Tests
- Horizons q: 2, 4, 8, 24, 72, 168 hours.
- Statistic: Lo–MacKinlay (1988) VR from overlapping q-hour sums with bias corrections; heteroskedasticity-robust z*.
- p-values: two-sided, from the standard normal.
- Multiple testing: Holm across all 126 tests (21 series × 6 horizons) as one family, at 5% family-wise error. Adjusted p-values reported.
- Primary test: z* with Holm. VR curve against q shown with the band where |z*| < 1.96, i.e. `1 ± 1.96·sqrt(theta/nq)`, with `sqrt(theta)` recovered from the Part 1 output as `sqrt(nq)·(VR − 1)/z*` (Part 1 signature unchanged).
- Size check (organiser, on this function): 2,000 random walks of 14,871 h rejected in 5.2% of runs at q = 168 and 5.0% at q = 72, so z* is not conservative at long horizons; the Issue's earlier note is not repeated.

## Stability
- Split-half: first and second half of the returns by timestamp midpoint (equal hours; the grid is complete). Same 126 tests on each half, with Holm applied separately within each half.
- Comparison: sign of VR − 1 in each half, per (series, q).
- Rule: **<choose: (a) only tests rejected on the full panel are judged — their sign must match in both halves; or (b) every (series, q) is judged>**. An effect whose sign flips between halves is not built on. (Sign flips of non-significant tests are expected noise around VR = 1.)

## Part 2 decomposition and intervals
- Lo–MacKinlay (1990) contrarian profit decomposition (own / cross / mean parts), formulas as given in #17.
- Block bootstrap intervals: block length **<TBD>**, replications **<TBD>**.

## Strategy
- Contrarian, horizon Q = **<TBD, ≥ 72h>** hours.
- Signal via `cross_sectional_zscore`; `rebalance_deadband` = **<TBD>**.
- Audit: `python -m src.audit strategies/arhaan_contrarian.py`, output pasted in the PR whatever the verdict.

## Code layout (research/arhaan)
- `load.py` — panel → returns table (hours × 20 symbols + `EW_index`).
- `holm.py` — two-sided p-values from z*; Holm step-down.
- `vr_table.py` — VR, z*, p, Holm (`p_holm`, `reject`) and band for every series × q, using `variance_ratio` imported from `src/contrib/arhaan.py`.
- `plots.py` — one panel per series: VR vs q (log x), band, line at 1; Holm rejections filled. Caption note: the band is the per-test 1.96 cut-off; Holm is stricter, so a point outside the band need not be rejected.
- `VR_testing.py` — main: full panel + each half → `out/vr_{full,half1,half2}.csv|png`, `out/split_half.csv`. Run from repo root: `python -m research.arhaan.VR_testing`.
- Only numpy / pandas / scipy outside plotting; matplotlib for figures only.

## Runs before this declaration
- <none / "ran once on <date> before declaring: <what was seen>">
