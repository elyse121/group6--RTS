"""Mini Project 1.2 - FDD vs TDD utilization under traffic asymmetry.

Capacity is normalised: the paired FDD spectrum (or the single TDD channel of equal
total bandwidth) carries 100 capacity units in total.
  FDD: two fixed channels, 50 units each, always on.
  TDD: one channel, frame of N slots; a fraction of slots is guard/switching overhead
       (carries no traffic); the remaining slots are split DL/UL (integer slots).
Offered load is expressed as a fraction of total capacity, split by the DL:UL ratio.
"""
import numpy as np
import matplotlib.pyplot as plt

TOTAL = 100.0          # total capacity units
SLOTS = 20             # slots per TDD frame

def fdd(dl_share, load=1.0):
    dl_d, ul_d = TOTAL * load * dl_share, TOTAL * load * (1 - dl_share)
    dl, ul = min(dl_d, TOTAL / 2), min(ul_d, TOTAL / 2)       # cannot be reallocated
    return dl, ul, (dl + ul) / TOTAL

def tdd(dl_share, guard_slots, load=1.0, slots=SLOTS):
    dl_d, ul_d = TOTAL * load * dl_share, TOTAL * load * (1 - dl_share)
    usable = slots - guard_slots
    per_slot = TOTAL / slots
    best = None
    for n_dl in range(usable + 1):                            # pick best integer DL/UL split
        dl = min(dl_d, n_dl * per_slot)
        ul = min(ul_d, (usable - n_dl) * per_slot)
        if best is None or dl + ul > best[0] + best[1] + 1e-9:
            best = (dl, ul, n_dl, usable - n_dl)
    return best[0], best[1], (best[0] + best[1]) / TOTAL, best[2], best[3] # type: ignore

scenarios = [(0.5, "50:50"), (0.7, "70:30"), (0.9, "90:10"), (0.95, "95:5")]
GUARDS = {"1/20 (5%)": 1, "2/20 (10%)": 2, "4/20 (20%)": 4}

print("Offered load = 100% of total capacity (network saturated)\n")
hdr = f"{'Scenario':8s} | {'FDD DL/UL':>11s} {'util':>6s} | " + " | ".join(f"TDD g={k}: DL/UL (slots) util" for k in GUARDS)
print(hdr); print("-" * len(hdr))
for p, lab in scenarios:
    dl, ul, u = fdd(p)
    row = f"{lab:8s} | {dl:5.1f}/{ul:4.1f} {u*100:5.1f}% | "
    cells = []
    for k, g in GUARDS.items():
        a, b, ut, nd, nu = tdd(p, g)
        cells.append(f"{a:5.1f}/{b:4.1f} ({nd}D/{nu}U) {ut*100:5.1f}%")
    print(row + " | ".join(cells))

print("\nLight load (50% of capacity):")
for p, lab in scenarios:
    f = fdd(p, 0.5); t = tdd(p, 1, 0.5)
    print(f"{lab:8s} FDD util {f[2]*100:5.1f}%  TDD(5% guard) util {t[2]*100:5.1f}%")

# Sweep asymmetry and find crossover points
shares = np.linspace(0.5, 0.95, 91)
plt.figure(figsize=(8, 5))
plt.plot(shares * 100, [fdd(s)[2] * 100 for s in shares], "k-", lw=2.5, label="FDD")
cross = {}
for k, g in GUARDS.items():
    u = np.array([tdd(s, g)[2] * 100 for s in shares])
    f = np.array([fdd(s)[2] * 100 for s in shares])
    plt.plot(shares * 100, u, label=f"TDD, guard {k}")
    idx = np.where(u > f + 1e-9)[0]
    cross[k] = shares[idx[0]] * 100 if len(idx) else None
plt.xlabel("Downlink share of traffic (%)"); plt.ylabel("Utilization (%)")
plt.title("Utilization vs traffic asymmetry (saturated load)")
plt.grid(alpha=.3); plt.legend(); plt.tight_layout()
plt.savefig("fdd_tdd_utilization.png", dpi=150); plt.close()
print("\nAsymmetry (DL %) beyond which TDD beats FDD:")
for k, v in cross.items():
    print(f"  guard {k}: {v:.1f}% DL" if v else f"  guard {k}: never")

# Bar chart for the 3 required scenarios
labels = [l for _, l in scenarios[:3]]
x = np.arange(3); w = 0.2
plt.figure(figsize=(8, 5))
plt.bar(x - 1.5*w, [fdd(p)[2]*100 for p, _ in scenarios[:3]], w, label="FDD", color="k")
for i, (k, g) in enumerate(GUARDS.items()):
    plt.bar(x + (i-0.5)*w, [tdd(p, g)[2]*100 for p, _ in scenarios[:3]], w, label=f"TDD {k}")
plt.xticks(x, labels); plt.ylabel("Utilization (%)"); plt.xlabel("DL:UL demand")
plt.title("FDD vs TDD utilization by scenario"); plt.legend(); plt.ylim(0, 105); plt.tight_layout()
plt.savefig("fdd_tdd_bars.png", dpi=150); plt.close()

# Optional: slot allocation across 3 frames at 90:10 with 1 guard slot
dl, ul, ut, nd, nu = tdd(0.9, 1)
frame = ["D"] * nd + ["G"] + ["U"] * nu
print("\nOne TDD frame at 90:10 (1 guard):", "".join(frame), " x3 frames")

# Optional extension: slot allocation over several frames, FDD (parallel channels) vs TDD
FRAMES = 4
fig, axes = plt.subplots(2, 1, figsize=(11, 3.8), sharex=True)
cols = {"D": "#1f77b4", "U": "#ff7f0e", "G": "#999999"}
for ax, (lab, p) in zip(axes, [("TDD 90:10 (1 guard slot)", 0.9), ("TDD 50:50 (1 guard slot)", 0.5)]):
    _, _, _, nd, nu = tdd(p, 1)
    frame = ["D"] * nd + ["G"] + ["U"] * nu
    for f in range(FRAMES):
        for i, c in enumerate(frame):
            ax.barh(0, 1, left=f * SLOTS + i, color=cols[c], edgecolor="white")
    ax.set_yticks([]); ax.set_ylabel(lab, rotation=0, ha="right", va="center", fontsize=8)
axes[1].set_xlabel("Time (slots); blue = downlink, orange = uplink, grey = guard")
axes[0].set_title(f"TDD slot allocation over {FRAMES} frames. FDD instead runs DL and UL channels continuously in parallel (50 units each).")
plt.tight_layout(); plt.savefig("fdd_tdd_multiframe.png", dpi=150); plt.close()
print("Saved fdd_tdd_multiframe.png")