# Lab 2 – Measurement-Based WCET Estimation and Confidence Tool
Real-Time Systems, Unit 1 – Mini Project 1.2

A small, reusable Python tool that **estimates** a function's worst-case execution
time (WCET) from measurements, and states honestly why the result is **not** a
guaranteed WCET (measurement-based = cheap but unsound, Section 1.7).

## Install and run
```bash
pip install -r requirements.txt
python main.py                       # full experiment (500 samples, 50 % margin)
python main.py --samples 1000 --margin 43   # optional: more samples / different margin
python stability_check.py            # optional: repeat the campaign 10x (about 1 min)
```
Tested with Python 3.12, NumPy 2.4, Matplotlib 3.10 (Python 3.9+ should work).

## Files
| File | Purpose |
|---|---|
| `main.py` | Runs every experiment, writes CSVs, tables and figures. CLI: `--samples`, `--margin`, `--seed`. |
| `measurement.py` | Generic harness: `measure(func, inputs, repeats)` times each call with `time.perf_counter()` and keeps **every** sample. Works for any one-argument function. |
| `target_functions.py` | Three targets (early-exit search, data-dependent Collatz loop, nested-conditional packet handler), each with a **random** and a **hand-derived adversarial** input generator. |
| `statistics_analysis.py` | Min/mean/max/std/P90/P95/P99, outlier flags, and `recommended WCET = max × (1 + margin%)`. |
| `visualization.py` | One histogram per function; marks measured max and margined WCET. |
| `stability_check.py` | Repeats the whole campaign to show how unstable a measured maximum is. |
| `results/statistics.csv` | Full statistics (6 rows: 3 functions × 2 strategies). |
| `results/comparison.csv` | Random max vs adversarial max vs margined recommendation. |
| `results/raw_samples.csv` | Every individual execution time (3,000 rows). |
| `results/tables.md`, `results/stability.*` | Markdown tables and repeat-campaign results. |
| `figures/function{1,2,3}_*_histogram.png` | Execution-time histograms. |
| `report/Lab2_Report.md` | The written lab report. |

## Safety margin
`Recommended WCET = measured maximum × (1 + margin/100)`. The default 50 % margin is
equivalent to budgeting about 66.7 % of the time (1/1.5), inside the 60–70 %
utilisation convention of Section 1.7. Change it with `--margin`.

## Important
**Measured maximum ≠ guaranteed WCET.** Only the executions that were tested are
seen; the margin is a heuristic, not a proof. Timings differ on every run and
machine (inputs are seeded and reproducible, timings are not). The numbers in
`report/Lab2_Report.md` come from one specific run (see its Section 10).
