"""
run_all.py - ORKESTRATOR. Hanya memanggil modul lain berurutan; tidak ada rumus di sini.
Urutan mengikuti butir tugas:
  [1] HW-1 (PR1 dilengkapi: GR, Vsh 3 metode, litologi, plot warna) -> sumur 13 & A-16
  [2] plot SP                        [3] Vsh per formasi/layer (Sand Wedge, Utsira L8..L1)
  [4] Vsh zona vs PR1 vs SP          [5] Rw (salinitas, SP klasik, Archie) + cross-check
Pakai: python run_all.py
"""
import json
import numpy as np
import pandas as pd
import config as C
import io_logs, zonation, vshale as V, rw, correlation, plots as P

C.FIG_DIR.mkdir(parents=True, exist_ok=True); C.TAB_DIR.mkdir(parents=True, exist_ok=True)
R = {}                                                  # semua angka kunci utk laporan -> results.json
fig = lambda n: C.FIG_DIR / n
tab = lambda n: C.TAB_DIR / n

# ---------- muat ----------
w13, a16 = io_logs.load_13(), io_logs.load_a16()

# ---------- [1] PR1 dilengkapi ----------
V.add_vsh_gr(w13, *C.GR_PR1["13"], "PR1", methods=("LIN", "CLA", "STB"))
V.add_vsh_gr(a16, *C.GR_PR1["A16"], "PR1", methods=("LIN", "CLA", "STB"))
for name, d, key in [("13", w13, "13"), ("A16", a16, "A16")]:
    g = d.dropna(subset=["GR"])
    R[f"pr1_{name}"] = dict(gr_min=C.GR_PR1[key][0], gr_max=C.GR_PR1[key][1],
        vsh_mean={m: float(g[f"VSH_{m}_PR1"].mean()) for m in ("LIN", "CLA", "STB")},
        lito_pct={m: g[f"LITO_{m}_PR1"].value_counts(normalize=True).mul(100).round(1).to_dict() for m in ("LIN", "CLA", "STB")})
    P.gr_vs_depth(d, *C.GR_PR1[key], "DEPTH", "Depth MD (m)", fig(f"gr_vs_depth_{name}.png"), f"GR vs Depth - 15/9-{'13' if name=='13' else 'A-16'}")
    P.ish_vs_vsh(d, "PR1", fig(f"ish_vs_vsh_{name}.png"), f"Vsh vs Ish - {name}")
g13 = w13.dropna(subset=["GR"])
P.tracks(w13, "PR1", (g13.DEPTH.min(), g13.DEPTH.max()), fig("tracks_PR1_13.png"), "15/9-13: GR, SP, Vsh (PR1)", sp=True,
         gmin=C.GR_PR1["13"][0], gmax=C.GR_PR1["13"][1])
ga = a16.dropna(subset=["GR"])
P.tracks(a16, "PR1", (ga.DEPTH.min(), ga.DEPTH.max()), fig("tracks_PR1_A16.png"), "15/9-A-16: GR & Vsh (PR1)",
         gmin=C.GR_PR1["A16"][0], gmax=C.GR_PR1["A16"][1])

# ---------- zonasi (satu sumber) ----------
ztab, picks = zonation.detect_zones(w13)
zonation.assign_zone(w13, ztab)
ztab.round(2).to_csv(tab("zonasi_13.csv"), index=False)
R["picks"] = {k: v for k, v in picks.items() if k != "thin"}

# ---------- [3] Vsh per zona ----------
gmin_z, gmax_z = V.zone_gr_limits(w13)
V.add_vsh_gr(w13, gmin_z, gmax_z, "ZN")
sp_sh, sp_sd = V.sp_baselines(w13, picks)
V.add_vsh_sp(w13, sp_sh, sp_sd, picks["sp_break"])
R["zona"] = dict(gr_min=gmin_z, gr_max=gmax_z, sp_shale=sp_sh, sp_sand=sp_sd, ssp=sp_sd - sp_sh,
                 sp_noise_std=w13.loc[w13.ZONA == "Utsira L3", "SP"].std())
P.tracks(w13, "ZN", (780, 1100), fig("tracks_zona_13.png"), "15/9-13: Vsh per zona (GR & SP)", sp=True,
         methods=("LIN", "STB"), extra_vsh=("LAR",), ztab=ztab, picks=picks, gmin=gmin_z, gmax=gmax_z)

# ---------- [4] bandingkan: zona vs PR1 vs SP ----------
cols = ["VSH_LIN_PR1", "VSH_CLA_PR1", "VSH_STB_PR1", "VSH_LIN_ZN", "VSH_CLA_ZN", "VSH_STB_ZN", "VSH_LAR_ZN", "VSH_SP"]
summ = V.zone_summary(w13, ztab, cols)
summ.round(3).to_csv(tab("vsh_per_zona.csv"))
win = w13.DEPTH.between(picks["top_sw"] - 40, picks["sp_break"])
R["cmp"] = {
    "GRzona_vs_SP":  V.agreement(w13.loc[win, "VSH_LAR_ZN"], w13.loc[win, "VSH_SP"]),
    "PR1cla_vs_zona": V.agreement(w13.loc[win, "VSH_CLA_PR1"], w13.loc[win, "VSH_CLA_ZN"]),
    "PR1lin_vs_zona": V.agreement(w13.loc[win, "VSH_LIN_PR1"], w13.loc[win, "VSH_LIN_ZN"]),
    "PR1cla_vs_SP":  V.agreement(w13.loc[win, "VSH_CLA_PR1"], w13.loc[win, "VSH_SP"]),
}
P.gr_vs_sp_crossplot(w13[win], ztab, R["cmp"]["GRzona_vs_SP"], fig("crossplot_vsh_gr_vs_sp.png"))

# ---------- korelasi 13 vs A-16 (dibutuhkan Archie A-16) ----------
cr = correlation.run(w13, a16, picks)
cr["ties"].round(2).to_csv(tab("tie_korelasi.csv"), index=False)
P.correlation_panel(cr, fig("korelasi_13_vs_A16.png")); P.shift_test(cr, fig("uji_shift.png"))
R["korelasi"] = {k: cr[k] for k in ("shift0", "r_at_shift0", "r_far_mean", "r_intra_at_shift0", "n_match_at_shift0",
                                    "n_match_mean", "n_peaks13", "top13", "base13", "top16", "base16_lo", "base16_hi")}

# ---------- [5] Rw ----------
R["validasi_slide"] = rw.validate_slide_example()
sal = rw.rw_salinity_profile(picks["top_sw"], picks["base_utsira"])
sal.to_csv(tab("rw_salinitas_profil.csv"), index=False)
R["temp_gradient_C_per_km"] = rw.temp_gradient_c_per_km()

es = rw.essp_from_log(w13, picks)
R["essp"] = es
sp_tab = rw.rw_sp_table(es["essp_max"]); sp_tab.round(3).to_csv(tab("rw_sp.csv"), index=False)

a16["VSH_ARCHIE"] = V.METHODS["LAR"](V.igr(a16["GR"], *C.GR_PR1["A16"]))
clean, n_zone = rw.archie_clean_sand(a16, cr["top16"], cr["base16_lo"], "VSH_ARCHIE")
R["archie"] = dict(n_zone=n_zone, n_clean=len(clean), pickett=rw.pickett_fit(clean))
arch = rw.archie_rw(clean, cr["shift0"]); arch.round(3).to_csv(tab("rw_archie_a16.csv"), index=False)
P.rw_cross_check(sal, clean, arch, cr["shift0"], picks["top_sw"], picks["base_utsira"], fig("rw_cross_check.png"))

rws = rw.rw_summary(sal, sp_tab, arch); rws.round(3).to_csv(tab("rw_ringkasan.csv"), index=False)
P.rw_methods(rws, fig("rw_perbandingan_metode.png"))

# ---------- simpan ----------
json.dump(R, open(C.OUT / "results.json", "w"), indent=1, default=lambda o: float(o) if isinstance(o, (np.floating, np.integer)) else str(o))
print("Selesai. Angka kunci -> output/results.json | tabel -> output/tables | gambar -> output/figures")
print(rws.round(3).to_string(index=False))
