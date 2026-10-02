"""
main.py  --  Mini Project 1.2: Measurement-Based WCET Estimation Tool
Run:  python main.py [--samples 500] [--margin 50] [--seed 2026]
"""

import argparse
import csv
import os

import numpy as np

from measurement import measure, timer_overhead
from statistics_analysis import summarise, margin_to_utilisation, recommended_wcet
from target_functions import TARGETS
from visualization import plot_histogram

HERE = os.path.dirname(os.path.abspath(__file__))


def run_experiments(samples, margin_pct, seed):
    """Run both strategies for every target. Returns a list of records."""
    records = []
    for idx, (name, func, rand_gen, adv_gen, desc) in enumerate(TARGETS):
        # Separate, reproducible RNG per target/strategy (inputs are reproducible;
        # the TIMINGS are of course not, they depend on the machine).
        rng_r = np.random.default_rng([seed, idx, 0])
        rng_a = np.random.default_rng([seed, idx, 1])
        m_r = measure(func, lambda n: rand_gen(n, rng_r), repeats=samples,
                      name=name, strategy="random")
        m_a = measure(func, lambda n: adv_gen(n, rng_a), repeats=samples,
                      name=name, strategy="adversarial")
        records.append({"name": name, "desc": desc, "random": m_r, "adversarial": m_a,
                        "stats_r": summarise(m_r.durations, margin_pct),
                        "stats_a": summarise(m_a.durations, margin_pct)})
    return records


def write_csvs(records, margin_pct, results_dir):
    stat_cols = ["Function", "Strategy", "Samples", "Min_us", "Mean_us", "Max_us", "StdDev_us",
                 "P90_us", "P95_us", "P99_us", "Max_over_P99", "Outlier_flag",
                 "Extreme_outliers", "Margin_pct", "Recommended_WCET_us"]
    with open(os.path.join(results_dir, "statistics.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(stat_cols)
        for r in records:
            for strat in ("random", "adversarial"):
                s = r["stats_" + strat[0]]
                w.writerow([r["name"], strat, s["n"], f"{s['min']:.3f}", f"{s['mean']:.3f}",
                            f"{s['max']:.3f}", f"{s['std']:.3f}", f"{s['p90']:.3f}",
                            f"{s['p95']:.3f}", f"{s['p99']:.3f}", f"{s['max_over_p99']:.2f}",
                            s["outlier_flag"], s["n_extreme_outliers"], f"{margin_pct:g}",
                            f"{s['recommended_wcet']:.3f}"])

    with open(os.path.join(results_dir, "comparison.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Function", "Random_Max_us", "Adversarial_Max_us", "Adv_over_Random",
                    "Largest_observed_from", "Overall_Max_us", "Margin_pct",
                    "Recommended_WCET_us"])
        for r in records:
            mr, ma = r["stats_r"]["max"], r["stats_a"]["max"]
            overall = max(mr, ma)
            w.writerow([r["name"], f"{mr:.3f}", f"{ma:.3f}", f"{ma / mr:.2f}",
                        "adversarial" if ma >= mr else "random", f"{overall:.3f}",
                        f"{margin_pct:g}", f"{recommended_wcet(overall, margin_pct):.3f}"])

    # Raw samples (every single execution time), for reproducibility / re-analysis.
    with open(os.path.join(results_dir, "raw_samples.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Function", "Strategy", "Index", "Input", "Duration_us"])
        for r in records:
            for strat in ("random", "adversarial"):
                m = r[strat]
                for i, (x, d) in enumerate(zip(m.inputs, m.durations)):
                    w.writerow([r["name"], strat, i, str(x)[:40], f"{d * 1e6:.3f}"])


def markdown_tables(records, margin_pct):
    """Build the two required tables as Markdown (saved + printed)."""
    t1 = ["| Function | Strategy | Min | Mean | Max | Std Dev | P90 | P95 | P99 | Recommended WCET |",
          "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in records:
        for strat in ("random", "adversarial"):
            s = r["stats_" + strat[0]]
            t1.append(f"| {r['name']} | {strat} | {s['min']:.2f} | {s['mean']:.2f} | {s['max']:.2f} | "
                      f"{s['std']:.2f} | {s['p90']:.2f} | {s['p95']:.2f} | {s['p99']:.2f} | "
                      f"{s['recommended_wcet']:.2f} |")
    t2 = ["| Function | Random Maximum | Adversarial Maximum | Adv/Random | Margined recommendation |",
          "|---|---:|---:|---:|---:|"]
    for r in records:
        mr, ma = r["stats_r"]["max"], r["stats_a"]["max"]
        t2.append(f"| {r['name']} | {mr:.2f} | {ma:.2f} | {ma / mr:.2f} | "
                  f"{recommended_wcet(max(mr, ma), margin_pct):.2f} |")
    t3 = ["| Function | Strategy | Max / P99 | Outlier flag (>1.5) | Extreme outliers (Tukey 3xIQR) |",
          "|---|---|---:|:---:|---:|"]
    for r in records:
        for strat in ("random", "adversarial"):
            s = r["stats_" + strat[0]]
            t3.append(f"| {r['name']} | {strat} | {s['max_over_p99']:.2f} | "
                      f"{'YES' if s['outlier_flag'] else 'no'} | {s['n_extreme_outliers']} |")
    return "\n".join(t1), "\n".join(t2), "\n".join(t3)


def main():
    ap = argparse.ArgumentParser(description="Measurement-based WCET estimation tool")
    ap.add_argument("--samples", type=int, default=500, help="timed calls per experiment")
    ap.add_argument("--margin", type=float, default=50.0,
                    help="safety margin in percent added to the measured maximum")
    ap.add_argument("--seed", type=int, default=2026, help="seed for input generation")
    args = ap.parse_args()

    results_dir = os.path.join(HERE, "results")
    figures_dir = os.path.join(HERE, "figures")
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(figures_dir, exist_ok=True)

    ovh = timer_overhead()
    print(f"Samples/experiment: {args.samples} | margin: {args.margin:g}% "
          f"(= {margin_to_utilisation(args.margin):.1f}% utilisation budget) | seed: {args.seed}")
    print(f"perf_counter start/stop overhead (median): {ovh * 1e9:.0f} ns\n")

    records = run_experiments(args.samples, args.margin, args.seed)
    write_csvs(records, args.margin, results_dir)

    for i, r in enumerate(records, 1):
        plot_histogram(r["name"], r["random"], r["adversarial"], args.margin,
                       os.path.join(figures_dir, f"function{i}_{r['name']}_histogram.png"))

    t1, t2, t3 = markdown_tables(records, args.margin)
    text = (f"Times in microseconds (us). {args.samples} samples per row, margin {args.margin:g}%.\n"
            f"Timer overhead (median): {ovh * 1e9:.0f} ns.\n\n"
            f"### Statistics\n\n{t1}\n\n### Random vs adversarial\n\n{t2}\n\n"
            f"### Outlier checks\n\n{t3}\n")
    with open(os.path.join(results_dir, "tables.md"), "w") as f:
        f.write(text)
    print(text)
    print("NOTE: a measured maximum is NOT a guaranteed WCET. See README.md / report.")
    print(f"Files written to: {results_dir} and {figures_dir}")


if __name__ == "__main__":
    main()
