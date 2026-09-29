"""vshale.py - HANYA rumus Vsh (GR & SP), klasifikasi, ringkasan per zona, dan uji kesesuaian."""
import numpy as np
import pandas as pd
import config as C

METHODS = {
    "LIN": lambda i: i,                                        # linear (batas atas)
    "CLA": lambda i: 1.7 - np.sqrt(3.38 - (i + 0.7) ** 2),     # Clavier
    "STB": lambda i: i / (3 - 2 * i),                          # Steiber
    "LAR": lambda i: (0.083 * (2 ** (3.7 * i) - 1)).clip(0, 1) # Larionov - Tersier
}
NAMES = {"LIN": "Linear", "CLA": "Clavier", "STB": "Steiber", "LAR": "Larionov (Tersier)"}


def igr(gr, gmin, gmax):
    return ((gr - gmin) / (gmax - gmin)).clip(0, 1)


def classify(v):
    out = pd.Series(np.where(v < C.VSH_CUT[0], "Clean Sand",
                    np.where(v <= C.VSH_CUT[1], "Shaly Sand", "Shale")), index=v.index)
    return out.where(v.notna())


def add_vsh_gr(df, gmin, gmax, tag, methods=("LIN", "CLA", "STB", "LAR")):
    """tambah IGR_<tag>, VSH_<m>_<tag>, LITO_<m>_<tag>. tag = 'PR1' atau 'ZN'."""
    df[f"IGR_{tag}"] = igr(df["GR"], gmin, gmax)
    for m in methods:
        df[f"VSH_{m}_{tag}"] = METHODS[m](df[f"IGR_{tag}"])
        df[f"LITO_{m}_{tag}"] = classify(df[f"VSH_{m}_{tag}"])
    return df


def zone_gr_limits(df):
    """GRmin dari pasir (Sand Wedge + Utsira L*), GRmax dari shale Nordland."""
    sand = df.ZONA.fillna("").str.contains("Utsira L|Sand Wedge")
    return (df.loc[sand, "GR"].quantile(0.02),
            df.loc[df.ZONA == "Nordland (caprock)", "GR"].quantile(0.98))


def sp_baselines(df, picks, vsh_col="VSH_LAR_ZN"):
    sh = df.loc[df.DEPTH.between(picks["top_sw"] - 45, picks["top_sw"] - 1), "SP"].median()
    sd = df.loc[df.ZONA.fillna("").str.startswith("Utsira L") & (df[vsh_col] < 0.1), "SP"].median()
    return sh, sd


def add_vsh_sp(df, sp_shale, sp_sand, sp_break):
    df["VSH_SP"] = ((df["SP"] - sp_sand) / (sp_shale - sp_sand)).clip(0, 1)
    df.loc[df.DEPTH >= sp_break, "VSH_SP"] = np.nan       # SP setelah lompatan tak sebanding
    return df


def zone_summary(df, ztab, cols):
    s = df.dropna(subset=["ZONA"]).groupby("ZONA")[cols].mean().reindex(ztab.zona)
    s.insert(0, "tebal_m", ztab.set_index("zona").tebal_m)
    return s


def agreement(a, b):
    """statistik kesesuaian dua seri Vsh (b - a)."""
    m = pd.concat([a, b], axis=1).dropna()
    x, y = m.iloc[:, 0], m.iloc[:, 1]
    return dict(n=len(m), pearson=x.corr(y), spearman=x.corr(y, method="spearman"),
                bias=(y - x).mean(), rmse=float(np.sqrt(((y - x) ** 2).mean())))
