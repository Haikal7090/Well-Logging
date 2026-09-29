"""
config.py - SATU-SATUNYA tempat konstanta, asumsi, dan jendela pencarian.
Modul lain TIDAK boleh menulis angka-angka ini ulang (hard-code).
"""
from pathlib import Path

# ---------- file ----------
DATA_DIR = Path(".")                       # folder tempat xlsx berada
FILE_13  = DATA_DIR / "Well_159_13.xlsx"
FILE_A16 = DATA_DIR / "Well_159-A-16.xlsx"
OUT      = Path("output")
FIG_DIR, TAB_DIR = OUT / "figures", OUT / "tables"
NULL = -999.25

# ---------- PR 1 (dipertahankan persis agar bisa dibandingkan) ----------
GR_PR1   = {"13": (23, 132), "A16": (25, 130)}    # (GRmin, GRmax) API, sheet Excel PR01
VSH_CUT  = (0.10, 0.33)                            # Clean Sand < 0.10 <= Shaly Sand <= 0.33 < Shale

# ---------- pembersihan ----------
DT_VALID = (40, 250)                               # us/ft; di luar ini = outlier
GR_SMOOTH_WIN = 5                                  # median filter (sampel) utk deteksi batas

# ---------- zonasi 15/9-13 (jendela pencarian, m MD) ----------
SHALE_REF_WINDOW = (700, 840)
SAND_REF_WINDOW  = (900, 1000)
SW_SEARCH        = (800, 900)                      # Top Sand Wedge
BASE_SEARCH      = (1030, 1100)                    # Base Utsira
SP_BREAK_SEARCH  = (1100, 1300)                    # lompatan baseline SP
N_THIN_MUD       = 7                               # mudstone tipis intra-Utsira (=> L8..L1)
MANUAL_PICKS     = {}                              # isi bila ada well picks resmi, mis. {"top_sw": 846.0}

# ---------- Rw: asumsi (TIDAK terverifikasi dari data sumur) ----------
SALINITY_PPM = (33500, 35000)                      # NaCl ppm, literatur
T_ANCHORS    = ((812.0, 32.0), (1012.0, 37.0))     # (m, C)
RMF_REF, T_RMF_REF = 5.6, 11.0                     # ohm.m @ C, DIBERIKAN di slide dosen
TF_CASES     = (33.0, 37.0)                        # C, kasus Tf slide & anchor dalam
RMFE_FACTORS = (1.0, 0.85)                         # Rmfe = f * Rmf (slide: 1.0 atau 0.85)
RW_OVER_RWE  = (1.0, 1 / 0.85)                     # langkah 6 di luar chart -> skenario ekstrapolasi
ESSP_QUANTILE = 0.05                               # "kick maksimum" robust thd noise
M_GRID = {"1.3": (1.0, 1.3), "1.5": (1.0, 1.5), "1.8": (1.0, 1.8),
          "2.0": (1.0, 2.0), "Humble": (0.62, 2.15)}   # (a, m)
ARCHIE_MIN_PHI, ARCHIE_VSH_MAX = 0.05, 0.10

# ---------- korelasi 13 vs A-16 ----------
STEP        = 0.5
SHIFT_SCAN  = (30, 100, 0.5)                       # start, stop, step
WIN_FULL    = (850, 1050)                          # memuat step Top Utsira
WIN_INTRA   = (870, 1040)                          # intra-Utsira saja
PROM_MIN, TOL_MATCH, TOL_A = 8, 4.0, 2.0
A16_TOP_SEARCH, A16_BASE_SEARCH = (890, 930), (1100, 1160)    # TVD, m
A16_BASE_LEVELS = (45, 55)                         # API; batas bawah/atas ketidakpastian Base Utsira A-16 (transisi tidak tegas)

# ---------- tampilan ----------
LITO_COLORS = {"Clean Sand": "#f6e27a", "Shaly Sand": "#d99a3d", "Shale": "#7b5b3f"}
