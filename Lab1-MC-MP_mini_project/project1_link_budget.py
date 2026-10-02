import numpy as np
import matplotlib.pyplot as plt

def fspl_db(d_km, f_mhz):
    return 20 * np.log10(d_km) + 20 * np.log10(f_mhz) + 32.44

def link_budget_dbm(p_tx_dbm, g_tx_db, l_path_db, g_rx_db, l_other_db):
    return p_tx_dbm + g_tx_db - l_path_db + g_rx_db - l_other_db

def max_range_km(f_mhz, p_tx, g_tx, g_rx, l_other, sens):
    """Closed-form range where P_RX == sensitivity (FSPL is invertible)."""
    budget = p_tx + g_tx + g_rx - l_other - sens          # allowed path loss, dB
    return 10 ** ((budget - 20*np.log10(f_mhz) - 32.44) / 20)

# Step 4 of the manual: 500 log-spaced points from 0.01 km to 100 km
distances = np.logspace(-2, 2, 500)
# Supplement: free space gives huge ranges, so 700 MHz never drops below sensitivity within
# 100 km. This wider grid (to 10,000 km) is used only for the extra "extended" figure.
distances_ext = np.logspace(-2, 4, 600)
SENS = -100.0
REF_KM = 1.0
BASE = dict(p_tx=40, g_tx=15, g_rx=0, l_other=3)
bands = {"700 MHz (low-band)": 700, "28 GHz (mmWave)": 28000}

def prx_curve(f, p_tx, g_tx, g_rx, l_other, d=None):
    d = distances if d is None else d
    return link_budget_dbm(p_tx, g_tx, fspl_db(d, f), g_rx, l_other)

# ---------- Main comparison ----------
print("=== MAIN COMPARISON (40 dBm, 15 dBi Tx, 0 dBi Rx, 3 dB other, sens -100 dBm) ===")
plt.figure(figsize=(8, 5))
for name, f in bands.items():
    prx = prx_curve(f, **BASE)
    plt.plot(distances, prx, label=name)
    pl_ref = fspl_db(REF_KM, f)
    prx_ref = link_budget_dbm(BASE["p_tx"], BASE["g_tx"], pl_ref, BASE["g_rx"], BASE["l_other"])
    above = distances[prx > SENS]                       # boolean indexing (step 10)
    dmax_grid = above.max()
    capped = " (capped at grid edge)" if dmax_grid >= distances.max() * 0.999 else ""
    dmax = max_range_km(f, **BASE, sens=SENS)           # closed-form, not limited by the grid
    print(f"{name:20s} PL@1km={pl_ref:6.2f} dB  PRX@1km={prx_ref:7.2f} dBm  "
          f"margin={prx_ref-SENS:6.2f} dB  max range on 100 km grid={dmax_grid:7.2f} km{capped}; "
          f"closed-form={dmax:8.1f} km")
plt.axhline(SENS, ls="--", color="k", label="Sensitivity -100 dBm")
plt.xscale("log"); plt.xlabel("Distance (km)"); plt.ylabel("Received power (dBm)")
plt.title("P_RX vs distance: 700 MHz vs 28 GHz (free space)")
plt.grid(True, which="both", alpha=.3); plt.legend(); plt.tight_layout()
plt.savefig("link_budget_comparison.png", dpi=150); plt.close()

# Supplementary figure on the extended grid so both curves cross the sensitivity line
plt.figure(figsize=(8, 5))
for name, f in bands.items():
    plt.plot(distances_ext, prx_curve(f, **BASE, d=distances_ext), label=name)
plt.axhline(SENS, ls="--", color="k", label="Sensitivity -100 dBm")
plt.xscale("log"); plt.xlabel("Distance (km)"); plt.ylabel("Received power (dBm)")
plt.title("Extended range (to 10,000 km): both curves cross sensitivity")
plt.grid(True, which="both", alpha=.3); plt.legend(); plt.tight_layout()
plt.savefig("link_budget_extended_range.png", dpi=150); plt.close()

r_lo = max_range_km(700, **BASE, sens=SENS); r_hi = max_range_km(28000, **BASE, sens=SENS)
print(f"Range ratio 700 MHz / 28 GHz = {r_lo/r_hi:.1f}x  (= 28000/700 = 40x, as expected)\n")

# ---------- Task 1: 24 dBi phased array at 28 GHz ----------
b1 = dict(BASE, g_tx=24)
r_hi24 = max_range_km(28000, **b1, sens=SENS)
print("=== TASK 1: 28 GHz with 24 dBi Tx gain ===")
print(f"28 GHz range: {r_hi:.1f} km -> {r_hi24:.1f} km  (x{r_hi24/r_hi:.2f} for +9 dB)\n")

# ---------- Task 2: add 3.5 GHz ----------
bands3 = {"700 MHz": 700, "3.5 GHz (mid-band)": 3500, "28 GHz": 28000}
plt.figure(figsize=(8, 5))
print("=== TASK 2: three bands ===")
for name, f in bands3.items():
    plt.plot(distances_ext, prx_curve(f, **BASE, d=distances_ext), label=name)
    print(f"{name:20s} max range = {max_range_km(f, **BASE, sens=SENS):8.1f} km")
plt.axhline(SENS, ls="--", color="k", label="Sensitivity")
plt.xscale("log"); plt.xlabel("Distance (km)"); plt.ylabel("Received power (dBm)")
plt.title("Three bands: 700 MHz, 3.5 GHz, 28 GHz"); plt.grid(True, which="both", alpha=.3)
plt.legend(); plt.tight_layout(); plt.savefig("link_budget_three_bands.png", dpi=150); plt.close()
print()

# ---------- Task 3: 8 dB shadowing margin ----------
print("=== TASK 3: +8 dB shadowing/fading margin (l_other 3 -> 11 dB) ===")
b3 = dict(BASE, l_other=11)
for name, f in bands3.items():
    r0, r1 = max_range_km(f, **BASE, sens=SENS), max_range_km(f, **b3, sens=SENS)
    print(f"{name:20s} {r0:8.1f} km -> {r1:8.1f} km  (shrinks to {100*r1/r0:.1f}%, lost {r0-r1:.1f} km)")
print()

# ---------- Task 4: SNR and Shannon capacity ----------
NOISE, BW = -104.0, 10e6
def capacity_mbps(prx_dbm, bw_hz=BW, noise_dbm=NOISE):
    snr = 10 ** ((prx_dbm - noise_dbm) / 10)
    return bw_hz * np.log2(1 + snr) / 1e6
print("=== TASK 4: SNR and capacity (noise -104 dBm, 10 MHz) ===")
fig, ax = plt.subplots(1, 2, figsize=(11, 4.5))
for name, f in bands.items():
    prx = prx_curve(f, **BASE)
    ax[0].plot(distances, prx - NOISE, label=name)
    ax[1].plot(distances, capacity_mbps(prx), label=name)
ax[0].axhline(0, ls="--", color="k"); ax[0].set_xscale("log"); ax[0].set_ylabel("SNR (dB)")
ax[1].set_xscale("log"); ax[1].set_ylabel("Capacity (Mbps)")
for a in ax: a.set_xlabel("Distance (km)"); a.grid(True, which="both", alpha=.3); a.legend()
ax[0].set_title("SNR vs distance"); ax[1].set_title("Shannon capacity vs distance (10 MHz)")
plt.tight_layout(); plt.savefig("snr_capacity.png", dpi=150); plt.close()
for d in (0.1, 1, 10, 30):
    row = f"d={d:5.1f} km | "
    for name, f in bands.items():
        prx = link_budget_dbm(BASE["p_tx"], BASE["g_tx"], fspl_db(d, f), BASE["g_rx"], BASE["l_other"])
        row += f"{name.split()[0]+' '+name.split()[1]:>8s}: PRX {prx:7.1f} dBm, SNR {prx-NOISE:6.1f} dB, C {capacity_mbps(prx):7.1f} Mbps | "
    print(row)
print()

# ---------- Task 5: double power vs double bandwidth ----------
print("=== TASK 5: double Tx power vs double bandwidth (at d = 20 km) ===")
for name, f in bands.items():
    prx = link_budget_dbm(BASE["p_tx"], BASE["g_tx"], fspl_db(20, f), BASE["g_rx"], BASE["l_other"])
    c0 = capacity_mbps(prx)
    c_pwr = capacity_mbps(prx + 3.01)                                   # 2x power = +3 dB
    c_bw = capacity_mbps(prx, bw_hz=2*BW, noise_dbm=NOISE + 3.01)       # noise power scales with B
    print(f"{name:20s} SNR={prx-NOISE:5.1f} dB  baseline={c0:6.1f} Mbps | 2x power={c_pwr:6.1f} (+{100*(c_pwr/c0-1):4.1f}%) "
          f"| 2x bandwidth={c_bw:6.1f} (+{100*(c_bw/c0-1):5.1f}%)")