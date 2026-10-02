"""
statistics_analysis.py
======================
Summary statistics, outlier flagging and the margined WCET recommendation.
All durations are handled in seconds and reported in microseconds (us).
"""

import numpy as np

DEFAULT_MARGIN_PCT = 50.0   # 50 % margin  <=>  ~67 % utilisation budget (1/1.5)


def margin_to_utilisation(margin_pct):
    """A margin m% is the same as budgeting only 1/(1+m/100) of the time:
    50 % -> 66.7 %, 43 % -> 70 %, 67 % -> 60 %  (Section 1.7: 60-70 % rule)."""
    return 100.0 / (1.0 + margin_pct / 100.0)


def recommended_wcet(measured_max, margin_pct=DEFAULT_MARGIN_PCT):
    """Recommended WCET = measured maximum + safety margin (percentage)."""
    return measured_max * (1.0 + margin_pct / 100.0)


def summarise(durations, margin_pct=DEFAULT_MARGIN_PCT, outlier_ratio=1.5):
    """Return a dict of statistics (in microseconds) for one experiment.

    Outlier checks (a rare, extreme sample is a sign the tail is poorly
    sampled, so the maximum may be an unreliable guide):
      * max_over_p99      : measured max / 99th percentile
      * outlier_flag      : True if max_over_p99 > outlier_ratio
      * n_extreme_outliers: samples above Q3 + 3*IQR (Tukey 'far out' fence)
    """
    us = np.asarray(durations) * 1e6
    p90, p95, p99 = np.percentile(us, [90, 95, 99])
    q1, q3 = np.percentile(us, [25, 75])
    fence = q3 + 3.0 * (q3 - q1)
    mx = float(us.max())
    return {
        "n": int(us.size),
        "min": float(us.min()),
        "mean": float(us.mean()),
        "max": mx,
        "std": float(us.std(ddof=1)),
        "p90": float(p90), "p95": float(p95), "p99": float(p99),
        "max_over_p99": mx / float(p99),
        "outlier_flag": bool(mx / float(p99) > outlier_ratio),
        "n_extreme_outliers": int((us > fence).sum()),
        "margin_pct": margin_pct,
        "recommended_wcet": recommended_wcet(mx, margin_pct),
    }
