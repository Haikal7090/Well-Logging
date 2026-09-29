"""plots.py - HANYA menggambar. Tidak menghitung apa pun selain penataan tampilan."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import ConnectionPatch, Patch
import config as C
import vshale as V


def _style(axs):
    for a in np.atleast_1d(axs):
        a.xaxis.set_label_position("top"); a.xaxis.tick_top(); a.grid(ls=":", alpha=0.5)


def _lito_fill(ax, x, y, lito):
    for k, col in C.LITO_COLORS.items():
        ax.fill_betweenx(y, ax.get_xlim()[0], x, where=(lito == k).values, color=col, lw=0, alpha=0.9)


def gr_vs_depth(df, gmin, gmax, ycol, ylab, path, title):
    g = df.dropna(subset=["GR"])
    fig, a = plt.subplots(figsize=(4.5, 12))
    a.plot(g.GR, g[ycol], "g", lw=0.6)
    a.axvline(gmin, c="orange", ls="--", lw=0.9); a.axvline(gmax, c="brown", ls="--", lw=0.9)
    a.set_xlim(0, 150); a.set_ylim(g[ycol].max(), g[ycol].min())
    a.set_xlabel("GR (API)"); a.set_ylabel(ylab); a.set_title(title, fontweight="bold", y=1.03)
    _style(a); fig.tight_layout(); fig.savefig(path, dpi=170); plt.close(fig)


def tracks(df, tag, ylim, path, title, sp=False, methods=("LIN", "CLA", "STB"), ztab=None, picks=None,
           extra_vsh=(), gmin=None, gmax=None):
    """GR (isi warna litologi) | [SP] | Vsh | strip litologi. tag='PR1' atau 'ZN'."""
    w = df[df.DEPTH.between(*ylim)]
    n = 3 + int(sp)
    fig, ax = plt.subplots(1, n, figsize=(2.6 * n + 1, 12), sharey=True,
                           gridspec_kw={"width_ratios": [1] * (n - 1) + [0.25]})
    k = 0
    ax[k].set_xlim(0, 150); ax[k].plot(w.GR, w.DEPTH, "k", lw=0.6)
    _lito_fill(ax[k], w.GR, w.DEPTH, w[f"LITO_CLA_{tag}"])
    if gmin is not None:
        ax[k].axvline(gmin, c="g", ls="--", lw=0.8); ax[k].axvline(gmax, c="brown", ls="--", lw=0.8)
    ax[k].set_xlabel("GR (API)"); k += 1
    if sp:
        ax[k].plot(w.SP, w.DEPTH, "b", lw=0.7)
        ax[k].set_xlim(w.SP.quantile(.005) - 3, w.SP.quantile(.995) + 3); ax[k].set_xlabel("SP (mV)"); k += 1
    cols = {"LIN": "k", "CLA": "r", "STB": "b", "LAR": "tab:green"}
    for m in list(methods) + list(extra_vsh):
        ax[k].plot(w[f"VSH_{m}_{tag}"], w.DEPTH, c=cols[m], lw=0.7, label=V.NAMES[m])
    if sp and "VSH_SP" in w:
        ax[k].plot(w.VSH_SP, w.DEPTH, c="tab:purple", lw=0.8, label="SP")
    for c in C.VSH_CUT:
        ax[k].axvline(c, c="grey", ls=":", lw=0.8)
    ax[k].set_xlim(0, 1); ax[k].set_xlabel("Vsh (v/v)"); ax[k].legend(loc="lower right", fontsize=7); k += 1
    lito = w[f"LITO_CLA_{tag}"]
    for name, col in C.LITO_COLORS.items():
        ax[k].fill_betweenx(w.DEPTH, 0, 1, where=(lito == name).values, color=col, lw=0)
    ax[k].set_xticks([]); ax[k].set_xlabel("Litologi\n(Clavier)")
    if picks and ztab is not None:
        for a in ax[:-1]:
            for t in ztab.top_m: 
                if ylim[0] <= t <= ylim[1]: a.axhline(t, c="m", lw=0.4, alpha=0.6)
    ax[0].set_ylabel("Depth MD (m)"); ax[0].set_ylim(ylim[1], ylim[0])
    _style(ax)
    fig.legend(handles=[Patch(color=c, label=n) for n, c in C.LITO_COLORS.items()], loc="lower center", ncol=3, fontsize=8)
    fig.suptitle(title, fontweight="bold", y=0.995); fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(path, dpi=170); plt.close(fig)


def ish_vs_vsh(df, tag, path, title, methods=("LIN", "CLA", "STB")):
    d = df.dropna(subset=[f"IGR_{tag}"])
    fig, a = plt.subplots(figsize=(5.5, 5.5))
    cols = {"LIN": "k", "CLA": "r", "STB": "b", "LAR": "tab:green"}
    for m in methods:
        o = d.sort_values(f"IGR_{tag}")
        a.plot(o[f"IGR_{tag}"], o[f"VSH_{m}_{tag}"], c=cols[m], lw=1.4, label=V.NAMES[m])
    a.set_xlabel("Ish (IGR)"); a.set_ylabel("Vsh"); a.set_title(title, fontweight="bold")
    a.legend(); a.grid(ls=":", alpha=0.5); fig.tight_layout(); fig.savefig(path, dpi=170); plt.close(fig)


def gr_vs_sp_crossplot(df, ztab, stats, path):
    m = df.dropna(subset=["VSH_LAR_ZN", "VSH_SP"]).merge(ztab[["zona", "tipe"]], left_on="ZONA", right_on="zona", how="left")
    fig, a = plt.subplots(figsize=(5.5, 5.5))
    for t, c in [("sand", "tab:green"), ("shale", "tab:brown")]:
        s = m[m.tipe == t]; a.scatter(s.VSH_LAR_ZN, s.VSH_SP, s=4, alpha=0.4, c=c, label=t)
    a.plot([0, 1], [0, 1], "k--", lw=0.8, label="1:1")
    a.set_xlabel("Vsh GR (Larionov, zona)"); a.set_ylabel("Vsh SP")
    a.set_title(f"Vsh GR vs SP (r = {stats['pearson']:.2f})"); a.legend(); a.grid(ls=":", alpha=0.5)
    fig.tight_layout(); fig.savefig(path, dpi=170); plt.close(fig)


def rw_methods(summary, path):
    fig, a = plt.subplots(figsize=(7.5, 4.5))
    for i, r in enumerate(summary.itertuples()):
        a.plot([i, i], [r.Rw_min, r.Rw_maks], lw=7, alpha=0.6, solid_capstyle="round")
        a.plot(i, (r.Rw_min * r.Rw_maks) ** 0.5, "o", c="k", ms=3)
    a.set_xticks(range(len(summary))); a.set_xticklabels([m.replace(", ", "\n") for m in summary.metode], fontsize=7.5)
    a.set_yscale("log"); a.set_ylabel("Rw (ohm.m)"); a.grid(ls=":", alpha=0.5, axis="y")
    a.set_title("Rw: perbandingan metode (rentang)", fontweight="bold")
    fig.tight_layout(); fig.savefig(path, dpi=170); plt.close(fig)


def rw_cross_check(sal_prof, clean, archie_tab, shift, top13, base13, path):
    fig, a = plt.subplots(figsize=(7.5, 8))
    a.fill_betweenx(sal_prof.depth_m, sal_prof.Rw_lo, sal_prof.Rw_hi, color="tab:blue", alpha=0.25,
                    label=f"15/9-13 salinitas {C.SALINITY_PPM[0]}-{C.SALINITY_PPM[1]} ppm")
    pal = {"1.3": "#f2a154", "1.5": "#e8712c", "1.8": "#b3491a", "2.0": "#7a2e0e"}
    for k, col in pal.items():
        aa, m = C.M_GRID[k]
        rw75 = clean.RT * clean.PHIF ** m / aa * (clean.T_C + 21.5) / (23.9 + 21.5)
        med = rw75.groupby((clean.z13_equiv // 15) * 15).median()
        a.plot(med.values, med.index, c=col, lw=1.6, label=f"A-16 Archie m={m}")
    a.set_xlim(0, 0.5); a.set_ylim(base13 + 10, top13 - 10); a.grid(ls=":", alpha=0.5); a.legend(fontsize=8)
    a.set_xlabel("Rw @75F (ohm.m)"); a.set_ylabel(f"Kedalaman setara 15/9-13 (m) [A-16 digeser -{shift:.1f} m]")
    a.set_title("Cross-check Rw pada basis suhu yang sama", fontweight="bold")
    fig.tight_layout(); fig.savefig(path, dpi=170); plt.close(fig)


def shift_test(cr, path):
    fig, (b1, b2) = plt.subplots(2, 1, figsize=(9, 8), sharex=True)
    b1.plot(cr["shifts"], cr["r_full"], "k", label=f"jendela {C.WIN_FULL} (memuat step Top)")
    b1.plot(cr["shifts"], cr["r_intra"], c="tab:blue", label=f"jendela {C.WIN_INTRA} (intra-Utsira)")
    b1.axvline(cr["shift0"], c="crimson", ls="--", lw=0.8); b1.set_ylabel("Pearson r"); b1.legend(fontsize=8); b1.grid(ls=":")
    b2.step(cr["shifts"], cr["n_match"], c="tab:orange", where="mid")
    b2.axhline(cr["n_match_mean"], c="0.4", ls=":", label=f"rata-rata = {cr['n_match_mean']:.1f}")
    b2.axvline(cr["shift0"], c="crimson", ls="--", lw=0.8, label=f"shift {cr['shift0']:.1f} m -> {cr['n_match_at_shift0']} cocok")
    b2.set_xlabel("Shift TVD A-16 - DEPTH 13 (m)"); b2.set_ylabel("# puncak cocok"); b2.legend(fontsize=8); b2.grid(ls=":")
    fig.tight_layout(); fig.savefig(path, dpi=170); plt.close(fig)


def correlation_panel(cr, path, ylim13=(830, 1100)):
    s13, s16, sh = cr["s13"], cr["s16"], cr["shift0"]
    md = cr["md_at_tvd"]; tab, unm = cr["ties"], cr["unmatched16"]
    XL, GRC = (0, 140), 55
    ylim16 = (ylim13[0] + sh, ylim13[1] + sh)
    fig = plt.figure(figsize=(12.5, 13))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 0.55, 1], wspace=0, left=0.07, right=0.78, top=0.87, bottom=0.10)
    ax1, axm, ax2 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1]), fig.add_subplot(gs[2]); axm.axis("off")

    def draw(ax, s, yl, col, title):
        x = s.loc[yl[0]:yl[1]]
        ax.plot(x.values, x.index, color=col, lw=0.8)
        ax.fill_betweenx(x.index, XL[0], x.values, where=x.values < GRC, color="#f3e08a", alpha=0.7, lw=0)
        ax.fill_betweenx(x.index, XL[0], x.values, where=x.values >= GRC, color="#8c6d4f", alpha=0.75, lw=0)
        ax.set_xlim(*XL); ax.set_ylim(yl[1], yl[0]); ax.grid(ls=":", alpha=0.5)
        ax.xaxis.set_label_position("top"); ax.xaxis.tick_top(); ax.set_xlabel("GR (API)")
        ax.set_title(title, fontsize=11, fontweight="bold", pad=30)
    draw(ax1, s13, ylim13, "k", "15/9-13\n(vertikal, y = DEPTH)")
    draw(ax2, s16, ylim16, "darkgreen", f"15/9-A-16\n(y = TVD, skala +{sh:.1f} m)")
    ax1.set_ylabel("Depth (m)"); ax2.yaxis.tick_right()

    L13, L16 = [], []
    def tie(z13, z16, st, col, lw=1.2):
        fig.add_artist(ConnectionPatch(xyA=(XL[1], z13), xyB=(XL[0], z16), coordsA="data", coordsB="data",
                                       axesA=ax1, axesB=ax2, color=col, ls=st, lw=lw, zorder=5))
    def flush(labs, ax, x, ha):
        prev = -1e9
        for z, txt, col in sorted(labs, key=lambda t: t[0]):
            y = max(z, prev + 3.2); prev = y
            ax.text(x, y, txt, transform=ax.get_yaxis_transform(), ha=ha, va="center", fontsize=7, color=col)

    tie(cr["top13"], cr["top16"], "-", "crimson", 2)
    L13.append((cr["top13"], f"Top Utsira {cr['top13']:.0f}", "crimson"))
    L16.append((cr["top16"], f"Top Utsira {cr['top16']:.0f} TVD | MD {md(cr['top16']):.0f}", "crimson"))
    for r in tab.itertuples():
        if r.grade == "tanpa pasangan":
            L13.append((r.z13_m, f"{r.z13_m:.0f} (tak ada pasangan)", "0.45")); continue
        col = "navy" if r.grade == "A" else "darkorange"
        tie(r.z13_m, r.a16_tvd_m, "-" if r.grade == "A" else "--", col, 1.1)
        L13.append((r.z13_m, f"{r.z13_m:.0f}", col)); L16.append((r.a16_tvd_m, f"{r.a16_tvd_m:.0f} | MD {r.a16_md_m:.0f}", col))
    for r in unm.itertuples():
        L16.append((r.z, f"{r.z:.0f} | MD {md(r.z):.0f} (tak ada pasangan)", "0.45"))
    lo, hi = cr["base16_lo"], cr["base16_hi"]
    tie(cr["base13"], lo, "--", "purple", 1.6); tie(cr["base13"], hi, ":", "purple", 1.0)
    ax1.axhline(cr["base13"], c="purple", lw=0.8); L13.append((cr["base13"], f"Base Utsira {cr['base13']:.0f}", "purple"))
    ax2.axhspan(lo, hi, color="purple", alpha=0.15, lw=0)
    L16.append((lo, f"Base? >={lo:.0f} TVD | MD {md(lo):.0f}", "purple")); L16.append((hi, f"Base? <={hi:.0f} TVD | MD {md(hi):.0f}", "purple"))
    ax1.axhline(cr["top13"], c="crimson", lw=0.8); ax2.axhline(cr["top16"], c="crimson", lw=0.8)
    flush(L13, ax1, 0.985, "right"); flush(L16, ax2, 1.11, "left")
    for lab, st, col in [("Top Utsira", "-", "crimson"), ("Grade A", "-", "navy"), ("Grade B", "--", "darkorange"), ("Base Utsira (13 tegas, A-16 tidak)", "--", "purple")]:
        axm.plot([], [], st, c=col, label=lab)
    h, l = axm.get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, fontsize=8, bbox_to_anchor=(0.45, 0.03))
    fig.suptitle("Korelasi GR 15/9-13 vs 15/9-A-16 (TVD) - Utsira", fontweight="bold", fontsize=13, y=0.995)
    fig.text(0.07, 0.008, f"Skala A-16 digeser +{sh:.1f} m. Tie miring = deviasi dari ketebalan konstan. Tie shale tipis bersifat interpretatif.", fontsize=7, color="0.3")
    fig.savefig(path, dpi=170); plt.close(fig)
