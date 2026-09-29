"""io_logs.py - HANYA baca + bersihkan data. Tidak ada perhitungan petrofisika."""
import numpy as np
import pandas as pd
import config as C


def _read(path):
    d = pd.read_excel(path)
    d.columns = d.columns.str.strip().str.upper()
    return d.apply(pd.to_numeric, errors="coerce").replace(C.NULL, np.nan)


def load_13(path=C.FILE_13):
    d = _read(path).dropna(subset=["DEPTH"]).drop_duplicates("DEPTH")
    d = d.sort_values("DEPTH").reset_index(drop=True)
    d = d.drop(columns=d.columns[d.isna().all()])            # RT/PHIF/dst. kosong 100% di sumur 13
    d.loc[d["SP"] == 0, "SP"] = np.nan                       # spike SP = 0
    lo, hi = C.DT_VALID
    d.loc[(d["DT"] < lo) | (d["DT"] > hi), "DT"] = np.nan    # outlier DT ~ +/-2000
    d["GR_S"] = d["GR"].rolling(C.GR_SMOOTH_WIN, center=True, min_periods=1).median()
    return d


def load_a16(path=C.FILE_A16):
    d = _read(path).dropna(subset=["DEPTH", "TVD"])
    d = d.sort_values("DEPTH").reset_index(drop=True)        # DEPTH = MD, TVD terpisah
    return d
