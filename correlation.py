"""correlation.py - HANYA korelasi GR 15/9-13 (DEPTH) vs 15/9-A-16 (TVD). Batas sumur 13 datang dari zonation."""
import numpy as np
import pandas as pd
from scipy.signal import find_peaks
import config as C


def to_grid(z, g, step=C.STEP):
    t = (np.asarray(z) / step).round() * step
    s = pd.Series(np.asarray(g), index=t).groupby(level=0).mean()
    return s.reindex(np.arange(s.index.min(), s.index.max() + step, step)).interpolate()

def first_cross(s, lo, hi, lvl, above):
    x = s.loc[lo:hi].rolling(5, center=True, min_periods=1).median()
    m = (x > lvl) if above else (x < lvl)
    return float(x.index[m.values][0])

def _scan(s13, s16, win, shifts):
    x = s13.loc[win[0]:win[1]]
    out = []
    for sh in shifts:
        y = s16.reindex(x.index + sh)
        out.append(np.nan if y.isna().any() else np.corrcoef(x.values, y.values)[0, 1])
    return np.array(out)

def _peaks(s, lo, hi):
    x = s.loc[lo:hi].rolling(3, center=True, min_periods=1).mean()
    p, pr = find_peaks(x.values, prominence=C.PROM_MIN, distance=4)
    return pd.DataFrame({"z": x.index[p].values, "gr": x.values[p], "prom": pr["prominences"]})


def run(w13, a16, picks):
    """return dict hasil korelasi (tabel tie, shift, picks A-16, uji shift)."""
    a = a16.dropna(subset=["GR"])
    s13, s16 = to_grid(w13.DEPTH, w13.GR), to_grid(a.TVD, a.GR)
    md_at_tvd = lambda v: float(np.interp(v, a.TVD.values, a.DEPTH.values))

    top13, base13, cut = picks["top_sw"], picks["base_utsira"], picks["gr_cutoff"]
    shifts = np.arange(C.SHIFT_SCAN[0], C.SHIFT_SCAN[1] + 1e-9, C.SHIFT_SCAN[2])
    r_full, r_intra = _scan(s13, s16, C.WIN_FULL, shifts), _scan(s13, s16, C.WIN_INTRA, shifts)
    shift0 = float(shifts[np.nanargmax(r_full)])
    i0 = int(np.argmin(np.abs(shifts - shift0)))

    # picks A-16 (aturan level GR yang sama dgn zonasi sumur 13)
    top16 = first_cross(s16, *C.A16_TOP_SEARCH, cut, above=False)
    base_lo = first_cross(s16, *C.A16_BASE_SEARCH, C.A16_BASE_LEVELS[0], above=True)
    base_hi = first_cross(s16, *C.A16_BASE_SEARCH, C.A16_BASE_LEVELS[1], above=True)

    p13 = _peaks(s13, top13 + 8, base13 - 7)
    p16 = _peaks(s16, top16 + 9, base_lo - 3)
    used, ties = set(), []
    for i in p13.sort_values("prom", ascending=False).index:
        z13 = p13.z[i]
        d = (p16.z - (z13 + shift0)).abs()
        d = d[[j for j in d.index if j not in used]]
        if len(d) and d.min() <= C.TOL_MATCH:
            j = d.idxmin(); used.add(j)
            dsh, ratio = p16.z[j] - z13, p16.prom[j] / p13.prom[i]
            g = "A" if (abs(dsh - shift0) <= C.TOL_A and 0.4 <= ratio <= 2.5) else "B"
            ties.append((z13, p16.z[j], dsh, p13.prom[i], p16.prom[j], ratio, g))
        else:
            ties.append((z13, np.nan, np.nan, p13.prom[i], np.nan, np.nan, "tanpa pasangan"))
    tab = pd.DataFrame(ties, columns=["z13_m", "a16_tvd_m", "shift_m", "prom13", "prom16", "rasio_prom", "grade"])
    tab["a16_md_m"] = tab.a16_tvd_m.map(lambda v: md_at_tvd(v) if pd.notna(v) else np.nan)
    tab = tab.sort_values("z13_m").reset_index(drop=True)
    unm16 = p16.loc[[j for j in p16.index if j not in used]].copy()

    nm = np.array([sum(np.min(np.abs(p16.z.values - (z + sh))) <= C.TOL_A for z in p13.z.values) for sh in shifts])
    return dict(s13=s13, s16=s16, shifts=shifts, r_full=r_full, r_intra=r_intra, shift0=shift0,
                r_at_shift0=r_full[i0], r_far_mean=np.nanmean(r_full[np.abs(shifts - shift0) > 10]),
                r_intra_at_shift0=r_intra[i0], n_match=nm, n_match_at_shift0=int(nm[i0]),
                n_match_mean=float(nm.mean()), n_peaks13=len(p13),
                top13=top13, base13=base13, top16=top16, base16_lo=base_lo, base16_hi=base_hi,
                md_at_tvd=md_at_tvd, ties=tab, unmatched16=unm16)
