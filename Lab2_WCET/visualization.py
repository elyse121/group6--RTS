"""
visualization.py
================
One histogram per target function: both input strategies are overlaid, and the
measured maximum and the margined (recommended) WCET are marked.
"""

import matplotlib
matplotlib.use("Agg")                    # no display needed; just save files
import matplotlib.pyplot as plt
import numpy as np

from statistics_analysis import recommended_wcet


def plot_histogram(name, random_m, adversarial_m, margin_pct, path):
    """Save a histogram PNG for one target function (times in microseconds)."""
    r = random_m.durations * 1e6
    a = adversarial_m.durations * 1e6
    overall_max = max(r.max(), a.max())               # measured maximum (both strategies)
    wcet = recommended_wcet(overall_max, margin_pct)  # margined recommendation

    # Shared bin edges so the two histograms are directly comparable.
    lo, hi = min(r.min(), a.min()), overall_max
    bins = np.linspace(lo, hi, 60)

    fig, ax = plt.subplots(figsize=(9, 5.8))
    ax.hist(r, bins=bins, alpha=0.65, color="tab:blue", label="Random inputs")
    ax.hist(a, bins=bins, alpha=0.65, color="tab:orange", label="Adversarial inputs")
    ax.axvline(overall_max, color="red", linestyle="--", linewidth=2,
               label=f"Measured max = {overall_max:.1f} us")
    ax.axvline(wcet, color="green", linestyle="-", linewidth=2,
               label=f"Recommended WCET (+{margin_pct:g}%) = {wcet:.1f} us")
    ax.set_xlim(lo - 0.02 * (wcet - lo), wcet * 1.03)
    ax.set_xlabel("Execution time (microseconds)")
    ax.set_yscale("log")             # log counts keep rare tail samples visible
    ax.set_ylabel("Number of executions (log scale)")
    ax.set_title(f"Execution-time distribution: {name}")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2, fontsize=9)
    ax.grid(alpha=0.3)
    fig.text(0.5, 0.008, "Measured maximum is an observation, NOT a guaranteed WCET.",
             ha="center", fontsize=8, style="italic")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, dpi=150)
    plt.close(fig)
