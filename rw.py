"""rw.py - HANYA penentuan Rw (3 metode) + cross-check. Semua batas zona datang dari argumen."""
import numpy as np
import pandas as pd
import config as C

# ---------- utilitas ----------
def bateman_konen_75F(ppm):                 # Rw (ohm.m) @ 75F / 23.9C
    return 0.0123 + 3647.5 / ppm ** 0.955

def arps(r1, t1_c, t2_c):                   # koreksi suhu Arps (C)
    return r1 * (t1_c + 21.5) / (t2_c + 21.5)

def temp_at(z):
    (z1, t1), (z2, t2) = C.T_ANCHORS
    return t1 + (np.asarray(z, float) - z1) * (t2 - t1) / (z2 - z1)

def temp_gradient_c_per_km():
    (z1, t1), (z2, t2) = C.T_ANCHORS
    return (t2 - t1) / (z2 - z1) * 1000


# ---------- Metode 1: salinitas + suhu (15/9-13) ----------
def rw_salinity_profile(top, base):
    z = np.arange(top, base + 1, 1.0)
    T = temp_at(z)
    lo = arps(bateman_konen_75F(C.SALINITY_PPM[1]), 23.9, T)   # salinitas tinggi -> Rw rendah
    hi = arps(bateman_konen_75F(C.SALINITY_PPM[0]), 23.9, T)
    return pd.DataFrame({"depth_m": z, "T_C": T, "Rw_lo": lo, "Rw_hi": hi, "Rw_mid": (lo + hi) / 2})


# ---------- Metode 2: SP klasik (6 langkah slide) ----------
def rmf_at_T(rmf1, t1, t2):
    return arps(rmf1, t1, t2)

def rwe_from_essp(essp_mv, tf_c, rmfe):
    return rmfe / 10 ** (essp_mv / (-0.24 * (tf_c + 271)))

def validate_slide_example():
    """contoh dosen: Rmf=5.6@11C, Tf=33C, Essp=-50 mV -> Rmfe~3.3, Rwe~0.68."""
    rmfe = rmf_at_T(5.6, 11, 33)
    rwe = rwe_from_essp(-50, 33, rmfe)
    return dict(rmf_at_33C=rmfe, rwe=rwe, cocok=abs(rwe - 0.68) < 0.01)

def essp_from_log(df, picks, vsh_col="VSH_LAR_ZN"):
    """Essp aktual dari SP 15/9-13. return dict(shale, sand_med, sand_pXX, essp_med, essp_max, n)."""
    sh = df.loc[df.DEPTH.between(picks["top_sw"] - 45, picks["top_sw"] - 1), "SP"].median()
    m = df.DEPTH.between(picks["top_sw"], picks["base_utsira"]) & (df[vsh_col] < 0.1)
    clean = df.loc[m, "SP"].dropna()
    q = clean.quantile(C.ESSP_QUANTILE)
    return dict(sp_shale=sh, sp_sand_med=clean.median(), sp_sand_q=q,
                essp_med=clean.median() - sh, essp_max=q - sh, n=len(clean),
                essp_p1=clean.quantile(0.01) - sh)

def rw_sp_table(essp):
    """langkah 1-5 (+ skenario langkah 6 karena Rwe di luar chart) utk tiap Tf, faktor Rmfe, rasio Rw/Rwe."""
    rows = []
    for tf in C.TF_CASES:
        rmf = rmf_at_T(C.RMF_REF, C.T_RMF_REF, tf)
        for f in C.RMFE_FACTORS:
            rwe = rwe_from_essp(essp, tf, f * rmf)
            for k in C.RW_OVER_RWE:
                rows.append(dict(Tf_C=tf, Rmf_at_Tf=rmf, faktor_Rmfe=f, Essp_mV=essp,
                                 Rwe=rwe, rasio_Rw_Rwe=k, Rw=rwe * k))
    return pd.DataFrame(rows)


# ---------- Metode 3: Archie (15/9-A-16) ----------
def archie_clean_sand(a16, top_tvd, base_tvd, vsh_col):
    z = a16[a16.TVD.between(top_tvd, base_tvd)]
    m = (z[vsh_col] < C.ARCHIE_VSH_MAX) & z.RT.notna() & z.PHIF.notna() & (z.PHIF > C.ARCHIE_MIN_PHI)
    return z[m].copy(), len(z)

def pickett_fit(clean):
    x, y = np.log10(clean.PHIF.values), np.log10(clean.RT.values)
    s, i = np.polyfit(x, y, 1)
    r2 = 1 - np.var(y - (s * x + i)) / np.var(y)
    return dict(m=-s, aRw=10 ** i, r2=r2, phi_p25=clean.PHIF.quantile(.25), phi_p75=clean.PHIF.quantile(.75))

def archie_rw(clean, shift):
    """Rwa in-situ (median) dan Rw@75F, per skema (a,m). shift = TVD A-16 - DEPTH 13."""
    clean["z13_equiv"] = clean.TVD - shift
    clean["T_C"] = temp_at(clean.z13_equiv)
    rows = []
    for name, (a, m) in C.M_GRID.items():
        rwa = clean.RT * clean.PHIF ** m / a
        rw75 = rwa * (clean.T_C + 21.5) / (23.9 + 21.5)
        rows.append(dict(skema=name, a=a, m=m, Rwa_insitu_med=(clean.RT.median() * clean.PHIF.median() ** m / a),
                         Rw75_med=rw75.median()))
    return pd.DataFrame(rows)


# ---------- ringkasan lintas-metode (dihitung, bukan diketik) ----------
def rw_summary(sal_prof, sp_tab, archie_tab):
    s75 = (bateman_konen_75F(C.SALINITY_PPM[1]), bateman_konen_75F(C.SALINITY_PPM[0]))
    return pd.DataFrame([
        ["Salinitas+suhu (13), Rw in-situ", sal_prof.Rw_lo.mean(), sal_prof.Rw_hi.mean()],
        ["Salinitas (13), Rw @75F", *s75],
        ["SP klasik (13), semua skenario", sp_tab.Rw.min(), sp_tab.Rw.max()],
        ["Archie (A-16), Rw @75F, m=1.3-2.0", archie_tab.Rw75_med.iloc[:4].min(), archie_tab.Rw75_med.iloc[:4].max()],
    ], columns=["metode", "Rw_min", "Rw_maks"])
