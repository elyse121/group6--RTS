Times in microseconds (us). 500 samples per row, margin 50%.
Timer overhead (median): 0 ns.

### Statistics

| Function | Strategy | Min | Mean | Max | Std Dev | P90 | P95 | P99 | Recommended WCET |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| early_exit_search | random | 0.40 | 51.52 | 755.10 | 60.30 | 92.02 | 119.45 | 260.46 | 1132.65 |
| early_exit_search | adversarial | 68.40 | 88.98 | 502.20 | 35.73 | 130.13 | 143.47 | 202.25 | 753.30 |
| collatz_loop | random | 1.90 | 11.90 | 266.90 | 16.59 | 17.90 | 20.11 | 25.52 | 400.35 |
| collatz_loop | adversarial | 32.40 | 43.46 | 1086.70 | 54.85 | 55.14 | 66.32 | 136.40 | 1630.05 |
| nested_packet | random | 0.90 | 4.94 | 31.70 | 5.05 | 11.11 | 15.30 | 23.71 | 47.55 |
| nested_packet | adversarial | 21.60 | 28.35 | 599.60 | 28.38 | 38.61 | 44.61 | 73.79 | 899.40 |

### Random vs adversarial

| Function | Random Maximum | Adversarial Maximum | Adv/Random | Margined recommendation |
|---|---:|---:|---:|---:|
| early_exit_search | 755.10 | 502.20 | 0.67 | 1132.65 |
| collatz_loop | 266.90 | 1086.70 | 4.07 | 1630.05 |
| nested_packet | 31.70 | 599.60 | 18.91 | 899.40 |

### Outlier checks

| Function | Strategy | Max / P99 | Outlier flag (>1.5) | Extreme outliers (Tukey 3xIQR) |
|---|---|---:|:---:|---:|
| early_exit_search | random | 2.90 | YES | 9 |
| early_exit_search | adversarial | 2.48 | YES | 63 |
| collatz_loop | random | 10.46 | YES | 3 |
| collatz_loop | adversarial | 7.97 | YES | 49 |
| nested_packet | random | 1.34 | no | 12 |
| nested_packet | adversarial | 8.13 | YES | 98 |
