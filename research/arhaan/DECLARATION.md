# Track 11 — pre-registration (Issue #17)

Declared before the first full-panel run. Posted to the PR on: **<date, time UTC>**

## Data
- Panel: `data/train_1h.parquet`, 20 symbols, hourly bars.
- Series: hourly close-to-close log returns, `ln(close_t / close_{t-1})`, per symbol, on a full hourly timestamp grid (missing hours → NaN; NaN dropped inside `variance_ratio`, as the Issue specifies).
- Equal-weighted index: cross-sectional mean of the 20 symbols' hourly log returns each hour, over the symbols present that hour (as in #17).

## Tests
- Horizons q: 2, 4, 8, 24, 72, 168 hours.
- Statistic: Lo–MacKinlay (1988) VR from overlapping q-hour sums with bias corrections; heteroskedasticity-robust z*.
- p-values: two-sided, from the standard normal.
- Multiple testing: Holm across all 126 tests (21 series × 6 horizons) at 5% family-wise error.
- Primary test: z* with Holm. VR curve against q shown with the band where |z*| < 1.96.

## Stability
- Split-half: first and second half of the panel by timestamp midpoint; same tests on each half. An effect whose sign of VR − 1 flips between halves is not built on.

## Part 2 decomposition and intervals
- Lo–MacKinlay (1990) contrarian profit decomposition (own / cross / mean parts), formulas as given in #17.
- Block bootstrap intervals: block length **<TBD>**, replications **<TBD>**.

## Strategy
- Contrarian, horizon Q = **<TBD, ≥ 72h>** hours.
- Signal via `cross_sectional_zscore`; `rebalance_deadband` = **<TBD>**.
- Audit: `python -m src.audit strategies/arhaan_contrarian.py`, output pasted in the PR whatever the verdict.

## Runs before this declaration
- <none / "ran once on <date> before declaring: <what was seen>">
