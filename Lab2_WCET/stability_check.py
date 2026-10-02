"""
stability_check.py  --  How repeatable is a measured maximum?
Run:  python stability_check.py [--campaigns 10] [--samples 500]

Repeats the whole measurement campaign several times and records, per
function/strategy, the maximum and P99 of EACH campaign.  If the measured
maximum were a true WCET it would be (nearly) identical every time; the
spread shown here is direct evidence that it is only an observation.
Output: results/stability.csv and results/stability.md
"""
import argparse
import csv
import os

import numpy as np

from main import run_experiments, HERE

ap = argparse.ArgumentParser()
ap.add_argument("--campaigns", type=int, default=10)
ap.add_argument("--samples", type=int, default=500)
ap.add_argument("--seed", type=int, default=2026)
args = ap.parse_args()

per_run = {}      # (function, strategy) -> {"max": [...], "p99": [...]}
for c in range(args.campaigns):
    for r in run_experiments(args.samples, 50.0, args.seed):
        for strat in ("random", "adversarial"):
            s = r["stats_" + strat[0]]
            d = per_run.setdefault((r["name"], strat), {"max": [], "p99": []})
            d["max"].append(s["max"])
            d["p99"].append(s["p99"])
    print(f"campaign {c + 1}/{args.campaigns} done")

rows = [["Function", "Strategy", "Campaigns", "Max_min_us", "Max_median_us", "Max_max_us",
         "Max_spread_ratio", "P99_min_us", "P99_median_us", "P99_max_us", "P99_spread_ratio"]]
for (fn, st), d in per_run.items():
    m, p = np.array(d["max"]), np.array(d["p99"])
    rows.append([fn, st, args.campaigns, f"{m.min():.2f}", f"{np.median(m):.2f}", f"{m.max():.2f}",
                 f"{m.max() / m.min():.2f}", f"{p.min():.2f}", f"{np.median(p):.2f}",
                 f"{p.max():.2f}", f"{p.max() / p.min():.2f}"])

out = os.path.join(HERE, "results")
with open(os.path.join(out, "stability.csv"), "w", newline="") as f:
    csv.writer(f).writerows(rows)
md = ["| Function | Strategy | Max: min | Max: median | Max: largest | Max spread (largest/min) | P99 spread (largest/min) |",
      "|---|---|---:|---:|---:|---:|---:|"]
for r in rows[1:]:
    md.append(f"| {r[0]} | {r[1]} | {r[3]} | {r[4]} | {r[5]} | {r[6]} | {r[10]} |")
text = f"Maximum and P99 over {args.campaigns} repeated campaigns of {args.samples} samples (us)\n\n" + "\n".join(md) + "\n"
open(os.path.join(out, "stability.md"), "w").write(text)
print(text)
