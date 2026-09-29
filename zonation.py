"""zonation.py - SATU sumber batas formasi/layer 15/9-13 (dari GR). Dipakai semua modul lain."""
import numpy as np
import pandas as pd
from scipy.signal import find_peaks, peak_widths
import config as C


def _first_cross(df, lo, hi, cond):
    m = df["DEPTH"].between(lo, hi) & cond
    return float(df.loc[m, "DEPTH"].iloc[0])


def detect_zones(df):
    """return (ztab, picks). ztab: zona, top_m, base_m, tipe, tebal_m."""
    shale_ref = df.loc[df.DEPTH.between(*C.SHALE_REF_WINDOW), "GR_S"].median()
    sand_ref = df.loc[df.DEPTH.between(*C.SAND_REF_WINDOW), "GR_S"].median()
    half = (shale_ref + sand_ref) / 2
    gs, mp = df["GR_S"], C.MANUAL_PICKS

    top_sw = mp.get("top_sw") or _first_cross(df, *C.SW_SEARCH, gs < half)
    mud_top = mp.get("mud_top") or _first_cross(df, top_sw, top_sw + 60, gs > half)
    mud_base = mp.get("mud_base") or _first_cross(df, mud_top, mud_top + 60, gs < half)
    base = mp.get("base_utsira") or _first_cross(df, *C.BASE_SEARCH, gs > half)

    seg = df[(df.DEPTH > mud_base + 1) & (df.DEPTH < base - 1)].reset_index(drop=True)
    pk, _ = find_peaks(seg["GR_S"].values, prominence=8, distance=20)
    best = np.sort(pk[np.argsort(seg["GR_S"].values[pk])[::-1][:C.N_THIN_MUD]])
    _, _, l_ips, r_ips = peak_widths(seg["GR_S"].values, best, rel_height=0.5)
    idx = np.arange(len(seg))
    thin = [(float(np.interp(l, idx, seg.DEPTH)), float(np.interp(r, idx, seg.DEPTH)))
            for l, r in zip(l_ips, r_ips)]

    sp_s = df["SP"].rolling(25, center=True, min_periods=5).median()
    win = df.DEPTH.between(*C.SP_BREAK_SEARCH)
    sp_break = float(df.loc[win, "DEPTH"].iloc[np.argmax(np.abs(sp_s.diff(25).loc[win].values))])

    zones = [("Nordland (caprock)", float(df.loc[df.GR.notna(), "DEPTH"].min()), top_sw, "shale"),
             ("Sand Wedge (L9)", top_sw, mud_top, "sand"),
             ("Mudstone 5-m (L9/L8)", mud_top, mud_base, "shale")]
    edges = [mud_base] + [x for t in thin for x in t] + [base]
    for i in range(len(thin) + 1):
        zones.append((f"Utsira L{8 - i}", edges[2 * i], edges[2 * i + 1], "sand"))
        if i < len(thin):
            zones.append((f"Mudstone L{8 - i}/L{7 - i}", thin[i][0], thin[i][1], "shale"))
    zones.append(("Di bawah Utsira", base, sp_break, "shale"))

    ztab = pd.DataFrame(zones, columns=["zona", "top_m", "base_m", "tipe"])
    ztab["tebal_m"] = ztab.base_m - ztab.top_m
    picks = dict(top_sw=top_sw, mud_top=mud_top, mud_base=mud_base, base_utsira=base,
                 sp_break=sp_break, gr_shale_ref=shale_ref, gr_sand_ref=sand_ref,
                 gr_cutoff=half, thin=thin)
    return ztab, picks


def assign_zone(df, ztab):
    df["ZONA"] = None
    for r in ztab.itertuples():
        df.loc[(df.DEPTH >= r.top_m) & (df.DEPTH < r.base_m), "ZONA"] = r.zona
    return df
