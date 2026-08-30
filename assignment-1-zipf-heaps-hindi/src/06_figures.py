#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
06_figures.py
=============
All figures for the report and the slide deck.

Palette and mark conventions follow a validated categorical set:
  slot1 blue #2a78d6 | slot2 orange #eb6834 | slot3 aqua #1baf7a
  slot4 yellow #eda100 | slot5 magenta #e87ba4 | slot7 violet #4a3aa7
Charts stay at three data series or fewer wherever the form allows, every
multi-series chart carries a legend, and grid/axes are kept recessive so the
data is the darkest thing on the page.
"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "out"))
FIG = os.path.abspath(os.path.join(HERE, "..", "figures"))
os.makedirs(FIG, exist_ok=True)

C = dict(blue="#2a78d6", orange="#eb6834", aqua="#1baf7a", yellow="#eda100",
         magenta="#e87ba4", green="#008300", violet="#4a3aa7", red="#e34948")
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#dedcd6"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "font.size": 9.5,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlepad": 10,
    "axes.labelsize": 9.5, "axes.grid": True, "axes.axisbelow": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "grid.alpha": 0.9,
    "xtick.color": INK2, "ytick.color": INK2,
    "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
    "legend.frameon": False, "legend.fontsize": 8.5,
    "lines.linewidth": 2.0, "lines.markersize": 3.5,
    "figure.dpi": 150, "savefig.dpi": 150, "savefig.bbox": "tight",
})


def despine(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def save(fig, name):
    p = os.path.join(FIG, name)
    fig.savefig(p)
    plt.close(fig)
    print("wrote", name)


Z = json.load(open(os.path.join(OUT, "zipf_results.json")))
T = json.load(open(os.path.join(OUT, "zipf_tables.json")))
H = json.load(open(os.path.join(OUT, "heaps_results.json")))
HC = json.load(open(os.path.join(OUT, "heaps_curve.json")))
M = json.load(open(os.path.join(OUT, "cost_model.json")))


def rf(key):
    a = np.array(T[key], dtype=float)
    return a[:, 0], a[:, 1]


# ==========================================================================
# FIG 1 - the master Zipf plot
# ==========================================================================
def fig_zipf_main():
    r, f = rf("rank_freq")
    fig, ax = plt.subplots(figsize=(7.4, 5.0))

    ax.loglog(r, f, ".", color=C["blue"], ms=2.2, alpha=.55,
              label="Hindi corpus (378,726 tokens)")

    pure = f[0] / r
    ax.loglog(r, pure, "--", color="#8a8880", lw=1.6,
              label=r"Pure Zipf, $\alpha=1$")

    o = Z["baseline"]["ols_core"]
    ax.loglog(r, o["C"] * r ** (-o["alpha"]), "-", color=C["orange"], lw=2.0,
              label=fr"Least-squares fit, $\alpha={o['alpha']:.3f}$ ($R^2$={o['r2']:.3f})")

    zm = Z["baseline"]["mandelbrot"]
    ax.loglog(r, zm["C"] / (r + zm["b"]) ** zm["alpha"], "-", color=C["aqua"],
              lw=2.0,
              label=(fr"Zipf–Mandelbrot, $\alpha$={zm['alpha']:.3f}, "
                     fr"$b$={zm['b']:.2f} ($R^2$={zm['r2']:.4f})"))

    p0 = Z["A2_tail"]["plateau_start_rank"]
    ax.axvspan(p0, r[-1], color=C["yellow"], alpha=.10)
    ax.annotate("hapax shelf — 44.7% of the\nvocabulary occurs exactly once",
                xy=(p0 * .92, 3.2), fontsize=8, color=INK2, ha="right")

    ax.set_xlabel("Rank  $r$  (log)")
    ax.set_ylabel("Frequency  $f(r)$  (log)")
    ax.set_title("Zipf's Law on Hindi — and the two places it visibly bends")
    ax.legend(loc="lower left", handlelength=1.8)
    ax.set_ylim(0.7, f[0] * 2.2)
    despine(ax)
    save(fig, "fig01_zipf_main.png")


# ==========================================================================
# FIG 2 - head anomaly and tail plateau
# ==========================================================================
def fig_head_tail():
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.2))

    a = axes[0]
    r, f = rf("rank_freq")
    n = 30
    zm = Z["baseline"]["mandelbrot"]
    a.plot(r[:n], f[:n], "o-", color=C["blue"], ms=4.5, label="observed")
    a.plot(r[:n], f[0] / r[:n], "--", color="#8a8880", lw=1.6,
           label=r"pure Zipf ($\alpha=1$)")
    a.plot(r[:n], zm["C"] / (r[:n] + zm["b"]) ** zm["alpha"], "-",
           color=C["aqua"], lw=2.0, label="Zipf–Mandelbrot")
    a.set_xlabel("Rank"); a.set_ylabel("Frequency")
    a.set_title("Attack 1 — the head is too flat for pure Zipf")
    a.annotate(f"$f(1)/f(2)$ = {Z['A1_head']['ratio_f1_f2']:.2f}\n"
               "pure Zipf demands 2.00", xy=(9, 15500), fontsize=8.5,
               color=INK2)
    a.legend(); despine(a)

    b = axes[1]
    sc = Z["A2_tail"]["plateau_scaling"]
    Ns = [s["N"] for s in sc]
    ps = [s["plateau_start_rank"] for s in sc]
    b.plot(Ns, ps, "o-", color=C["orange"], ms=6)
    for s in sc:
        b.annotate(f"{s['plateau_start_rank']:,}",
                   xy=(s["N"], s["plateau_start_rank"]),
                   xytext=(0, 8), textcoords="offset points",
                   ha="center", fontsize=8, color=INK2)
    b.set_xlabel("Corpus size $N$ (tokens)")
    b.set_ylabel("Rank at which the shelf begins")
    b.set_title("Attack 2 — the shelf moves right as $N$ grows")
    b.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v/1000:.0f}k"))
    b.text(.03, .93, "A real break in the law would sit still.\n"
                     "This one recedes — it is a sampling artefact.",
           transform=b.transAxes, fontsize=8.5, color=INK2, va="top")
    despine(b)
    fig.tight_layout()
    save(fig, "fig02_head_tail.png")


# ==========================================================================
# FIG 3 - the formal goodness-of-fit test and its power
# ==========================================================================
def fig_gof():
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.2))
    g = Z["A3_gof"]

    a = axes[0]
    sc = g["xmin_scan"]
    a.plot([s["xmin"] for s in sc], [s["ks"] for s in sc], "o-",
           color=C["blue"], ms=5)
    a.set_xscale("log")
    a.set_xlabel("$x_{min}$ (minimum count included in the fit)")
    a.set_ylabel("KS distance")
    a.set_title("Attack 3a — how far off is the power law, really?")
    a.axhline(g["ks_distance"], color=C["orange"], ls="--", lw=1.4)
    a.annotate(f"best KS = {g['ks_distance']:.4f}\n"
               f"(max CDF error {g['max_cdf_deviation_pct']:.2f}%)",
               xy=(2.2, g["ks_distance"] * 1.06), fontsize=8.5, color=INK2)
    despine(a)

    b = axes[1]
    pw = g["power_analysis"]
    ns = [p["n"] for p in pw]
    ps = [p["p"] for p in pw]
    b.plot(ns, ps, "o-", color=C["violet"], ms=6, label="bootstrap $p$-value")
    b.axhline(.10, color=C["red"], ls="--", lw=1.4)
    b.annotate("rejection threshold $p=0.10$", xy=(235, .105), fontsize=8.5,
               color=C["red"], va="bottom")
    b.set_xscale("log")
    b.set_xlabel("Number of word types fed to the test")
    b.set_ylabel("$p$-value")
    b.set_title("Attack 3b — the rejection is bought with sample size")
    b.text(.44, .97, "Same distribution, same $\\gamma\\approx1.66$.\n"
                     "Only $n$ changes. Below $n\\approx1{,}000$ the very\n"
                     "same data 'passes'; above $n\\approx5{,}000$ it 'fails'.",
           transform=b.transAxes, fontsize=8.5, color=INK2, va="top")
    b.legend(loc="center right"); despine(b)
    fig.tight_layout()
    save(fig, "fig03_goodness_of_fit.png")


# ==========================================================================
# FIG 4 - four structural attacks
# ==========================================================================
def fig_edge_cases():
    fig, axes = plt.subplots(2, 2, figsize=(10.6, 7.6))

    # (a) genre
    a = axes[0, 0]
    r, f = rf("rank_freq")
    gen = Z["A4_genre"]
    for (name, col, lab) in (("newswire", C["blue"], "Newswire (HDTB)"),
                             ("wikipedia", C["orange"], "Wikipedia (XQuAD)")):
        d = gen[name]
        rr = np.arange(1, 2001)
        a.loglog(rr, d["C"] / d["N"] * rr ** (-d["alpha"]), color=col, lw=2.0,
                 label=f"{lab}: "r"$\alpha$="f"{d['alpha']:.3f}"
                       f" (N={d['N']:,})")
    a.set_title("Attack 4 — change the genre")
    a.set_xlabel("Rank"); a.set_ylabel("Relative frequency  $f/N$")
    a.text(.04, .10, "Two unrelated genres, a 10× size gap —\n"
                     "and the curves lie on top of each other.",
           transform=a.transAxes, fontsize=8.5, color=INK2)
    a.legend(); despine(a)

    # (b) ablation
    b = axes[0, 1]
    r2, f2 = rf("ablation_rank_freq")
    b.loglog(r, f, ".", color=C["blue"], ms=1.8, alpha=.45, label="full corpus")
    b.loglog(r2, f2, ".", color=C["orange"], ms=1.8, alpha=.45,
             label="top-50 word types deleted")
    ab = Z["A5_ablation"]
    b.set_title("Attack 5 — remove the 'Zipf engine'")
    b.set_xlabel("Rank"); b.set_ylabel("Frequency")
    b.text(.04, .12, f"40.0% of all tokens removed\n"
                     r"$\alpha$: "f"{Z['baseline']['ols_core']['alpha']:.3f}"
                     r" $\rightarrow$ "f"{ab['alpha']:.3f}",
           transform=b.transAxes, fontsize=8.5, color=INK2)
    b.legend(loc="upper right"); despine(b)

    # (c) morphology
    c = axes[1, 0]
    rs, fs = rf("surface_rank_freq")
    rl, fl = rf("lemma_rank_freq")
    c.loglog(rs, fs, ".", color=C["blue"], ms=1.8, alpha=.45,
             label=f"surface forms (V={Z['A6_morphology']['surface']['V']:,})")
    c.loglog(rl, fl, ".", color=C["aqua"], ms=1.8, alpha=.45,
             label=f"lemmas (V={Z['A6_morphology']['lemma']['V']:,})")
    mo = Z["A6_morphology"]
    c.set_title("Attack 6 — strip Hindi morphology")
    c.set_xlabel("Rank"); c.set_ylabel("Frequency")
    c.text(.04, .12, f"vocabulary −{100*mo['vocab_compression']:.1f}%\n"
                     r"$\alpha$: "f"{mo['surface']['alpha']:.3f}"
                     r" $\rightarrow$ "f"{mo['lemma']['alpha']:.3f}",
           transform=c.transAxes, fontsize=8.5, color=INK2)
    c.legend(loc="upper right"); despine(c)

    # (d) unit change
    d = axes[1, 1]
    rb, fb = rf("bigram_rank_freq")
    d.loglog(r, f, ".", color=C["blue"], ms=1.8, alpha=.45, label="unigrams")
    d.loglog(rb, fb, ".", color=C["violet"], ms=1.8, alpha=.45, label="bigrams")
    u = Z["A8_units"]
    d.set_title("Attack 8 — change the unit of counting")
    d.set_xlabel("Rank"); d.set_ylabel("Frequency")
    d.text(.04, .12, r"bigram $\alpha$="f"{u['bigrams']['alpha']:.3f}"
                     f"  ($R^2$={u['bigrams']['r2']:.3f})\n"
                     r"characters $R^2$="f"{u['characters']['r2']:.2f}"
                     "  ← the one true failure",
           transform=d.transAxes, fontsize=8.5, color=INK2)
    d.legend(loc="upper right"); despine(d)

    fig.tight_layout()
    save(fig, "fig04_edge_cases.png")


# ==========================================================================
# FIG 5 - Miller's monkeys
# ==========================================================================
def fig_monkey():
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.2))
    r, f = rf("rank_freq")
    rm, fm = rf("monkey_rank_freq")
    mk = Z["A7_monkey"]

    a = axes[0]
    a.loglog(r, f, ".", color=C["blue"], ms=2.0, alpha=.5,
             label=f"real Hindi (V={Z['corpus']['V']:,})")
    a.loglog(rm, fm, ".", color=C["magenta"], ms=2.0, alpha=.5,
             label=f"random Devanagari typing (V={mk['V']:,})")
    a.set_xlabel("Rank"); a.set_ylabel("Frequency")
    a.set_title("Attack 7 — 'Zipf is trivial, monkeys do it too'")
    a.legend(loc="upper right"); despine(a)

    b = axes[1]
    labels = ["fit quality\n$R^2$", "vocabulary\n(×10⁴ types)",
              "distinct frequency\nvalues (×10)"]
    real = [Z["baseline"]["ols_core"]["r2"], Z["corpus"]["V"] / 1e4,
            mk["real_distinct_freq_values"] / 10]
    monk = [mk["r2"], mk["V"] / 1e4, mk["distinct_freq_values"] / 10]
    x = np.arange(3); w = .36
    b.bar(x - w / 2, real, w, color=C["blue"], label="real Hindi")
    b.bar(x + w / 2, monk, w, color=C["magenta"], label="monkey text")
    for xi, v in zip(x - w / 2, real):
        b.text(xi, v, f"{v:.2f}", ha="center", va="bottom", fontsize=8,
               color=INK2)
    for xi, v in zip(x + w / 2, monk):
        b.text(xi, v, f"{v:.2f}", ha="center", va="bottom", fontsize=8,
               color=INK2)
    b.set_xticks(x); b.set_xticklabels(labels)
    b.set_title("Monkey text is a *worse* power law, not a better one")
    b.grid(axis="x", visible=False)
    b.legend(); despine(b)
    fig.tight_layout()
    save(fig, "fig05_monkeys.png")


# ==========================================================================
# FIG 6 - exponent stability
# ==========================================================================
def fig_alpha_stability():
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    s = Z["A9_scale"]["series"]
    N = [x["N"] for x in s]
    al = [x["alpha"] for x in s]
    ax.plot(N, al, "o-", color=C["blue"], ms=6, label=r"measured $\alpha$")
    ax.set_xscale("log")
    ext = Z.get("external_wordfreq", {})
    if "alpha" in ext:
        ax.axhline(ext["alpha"], color=C["orange"], ls="--", lw=1.6)
        ax.annotate(f"independent check — wordfreq Hindi frequency table\n"
                    f"({ext['entries']:,} entries, billions of tokens): "
                    r"$\alpha$="f"{ext['alpha']:.3f}",
                    xy=(1.1e4, ext["alpha"] + .012), fontsize=8.5,
                    color=C["orange"])
    m = Z["A9_scale"]["alpha_mean"]; sd = Z["A9_scale"]["alpha_sd"]
    ax.axhspan(m - sd, m + sd, color=C["blue"], alpha=.08)
    ax.set_xlabel("Corpus size $N$ (tokens, log)")
    ax.set_ylabel(r"Zipf exponent $\alpha$")
    ax.set_title("Attack 9 — does the exponent drift with corpus size?")
    ax.text(.04, .90, f"α = {m:.3f} ± {sd:.3f} once N > 30k.\n"
                      f"Total drift across a 50× size range: "
                      f"{Z['A9_scale']['alpha_range']:.3f}",
            transform=ax.transAxes, fontsize=8.5, color=INK2, va="top")
    ax.legend(loc="lower right"); despine(ax)
    save(fig, "fig06_alpha_stability.png")


# ==========================================================================
# FIG 7 - Heaps log-log
# ==========================================================================
def fig_heaps_loglog():
    fig, ax = plt.subplots(figsize=(7.4, 5.0))
    for key, col, lab in (("hindi", C["blue"], "Hindi"),
                          ("english", C["orange"], "English (size-matched)")):
        N = np.array(HC[key]["N"]); V = np.array(HC[key]["V"])
        fitd = H[key]["fit"]
        ax.loglog(N, V, ".", color=col, ms=2.4, alpha=.55)
        ax.loglog(N, fitd["K"] * N ** fitd["beta"], "-", color=col, lw=2.0,
                  label=(f"{lab}: "r"$V=$"f"{fitd['K']:.1f}"r"$N^{"
                         f"{fitd['beta']:.4f}"r"}$"
                         f"  ($R^2$={fitd['r2']:.4f})"))
    ax.set_xlabel("Tokens $N$ (log)")
    ax.set_ylabel("Vocabulary $V$ (log)")
    ax.set_title("Heaps' Law — a straight line across three decades")
    ax.legend(loc="upper left"); despine(ax)
    save(fig, "fig07_heaps_loglog.png")


# ==========================================================================
# FIG 8 - where the curve flattens
# ==========================================================================
def fig_heaps_knee():
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(12.0, 4.8),
                                 gridspec_kw={"width_ratios": [1.45, 1]})
    N = np.array(HC["hindi"]["N"]); V = np.array(HC["hindi"]["V"])
    ax.plot(N, V, "-", color=C["blue"], lw=2.2, label="Hindi vocabulary growth")

    k = H["hindi"]["knee"]["linear"]
    ax.plot([k["N"]], [k["V"]], "o", color=C["orange"], ms=10, zorder=5,
            markeredgecolor=SURFACE, markeredgewidth=2)
    ax.annotate(f"FLATTENING POINT\nN ≈ {k['N']:,.0f} tokens\nV ≈ {k['V']:,.0f} types",
                xy=(k["N"], k["V"]), xytext=(k["N"] * 1.25, k["V"] * .62),
                fontsize=9.5, color=INK, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=C["orange"], lw=1.6))

    ax.axvspan(0, k["N"], color=C["aqua"], alpha=.07)
    ax.text(k["N"] * .5, V.max() * .93, "steep phase\n(every page brings\nnew words)",
            ha="center", fontsize=8.5, color=INK2)
    ax.text((k["N"] + N.max()) / 2, V.max() * .45,
            "flattened phase\n(returns diminish,\nbut never reach zero)",
            ha="center", fontsize=8.5, color=INK2)

    ax.set_xlabel("Tokens $N$")
    ax.set_ylabel("Vocabulary $V$")
    ax.set_title("Where does the Hindi curve start to flatten?")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v/1000:.0f}k"))
    ax.legend(loc="lower right"); despine(ax)

    Nf = np.array(HC["hindi_file_order"]["N"])
    Vf = np.array(HC["hindi_file_order"]["V"])
    bx.plot(Nf, Vf, "-", color=C["magenta"], lw=2.0,
            label=f"raw file order (β={H['hindi_file_order']['fit']['beta']:.4f}, "
                  f"$R^2$={H['hindi_file_order']['fit']['r2']:.4f})")
    bx.plot(N, V, "-", color=C["blue"], lw=2.0,
            label=f"sentence-shuffled (β={H['hindi']['fit']['beta']:.4f}, "
                  f"$R^2$={H['hindi']['fit']['r2']:.4f})")
    bx.set_xlabel("Tokens $N$"); bx.set_ylabel("Vocabulary $V$")
    bx.set_title("Why the corpus is shuffled first", fontsize=10.5)
    bx.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v/1000:.0f}k"))
    bx.text(.04, .95, "Reading the sources back-to-back makes the\n"
                      "genre boundary look like a law of language.",
            transform=bx.transAxes, fontsize=8.5, color=INK2, va="top")
    bx.legend(loc="lower right"); despine(bx)
    fig.tight_layout()
    save(fig, "fig08_heaps_knee.png")


# ==========================================================================
# FIG 9 - marginal yield
# ==========================================================================
def fig_marginal_yield():
    fig, ax = plt.subplots(figsize=(7.8, 5.0))
    rN = np.array(HC["hindi"]["rate_N"]); rate = np.array(HC["hindi"]["rate"])
    ax.loglog(rN, rate, "-", color=C["blue"], lw=2.0,
              label="measured (10k-token sliding window)")

    K = H["hindi"]["fit"]["K"]; b = H["hindi"]["fit"]["beta"]
    Nx = np.logspace(4, 9.2, 200)
    ax.loglog(Nx, 1000 * K * b * Nx ** (b - 1), "--", color=C["orange"],
              lw=1.8, label="Heaps model, extrapolated")

    for th, col in ((50, C["aqua"]), (10, C["violet"]), (1, C["red"])):
        row = next(t for t in H["hindi"]["thresholds"]
                   if t["threshold_per_1k"] == th)
        ax.axhline(th, color=col, ls=":", lw=1.2)
        ax.plot([row["model_N"]], [th], "o", color=col, ms=7, zorder=5,
                markeredgecolor=SURFACE, markeredgewidth=1.5)
        noun = "type" if th == 1 else "types"
        ha = "right" if th == 1 else "left"
        xoff = 0.55 if th == 1 else 1.5
        ax.annotate(f"{th} new {noun} / 1k tokens\nat N ≈ {row['model_N']:,.0f} words",
                    xy=(row["model_N"] * xoff, th * 1.25), fontsize=8.5,
                    color=col, ha=ha)

    ax.axvspan(1e4, rN.max(), color=C["blue"], alpha=.06)
    ax.text(np.sqrt(1e4 * rN.max()), 480, "measured range", fontsize=8.5,
            color=INK2, ha="center")
    ax.set_xlim(1e4, 3e9)
    ax.set_ylim(.5, 700)
    ax.set_xlabel("Corpus size $N$ (words, log)")
    ax.set_ylabel("New word types per 1,000 tokens (log)")
    ax.set_title("The operational flattening point: when does reading more stop paying?")
    ax.legend(loc="upper right"); despine(ax)
    save(fig, "fig09_marginal_yield.png")


# ==========================================================================
# FIG 10 - Heaps-derived corpus tiers and their price
# ==========================================================================
def fig_cost_tiers():
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    tiers = M["corpus_tiers"]
    labels = [t["tier"].split("  ")[0] + "\n" + t["tier"].split("  ")[1]
              for t in tiers]
    words = [t["words_required"] for t in tiers]
    cost = [t["cost_if_fully_curated"] for t in tiers]
    x = np.arange(len(tiers))
    bars = ax.bar(x, words, .55, color=C["blue"])
    ax.set_yscale("log")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel("Words required (log)")
    ax.set_title("Heaps' Law converts a quality target into a corpus size — and a price")
    for xi, w, c in zip(x, words, cost):
        ax.text(xi, w * 1.35, f"{w:,.0f} words\n${c:,.0f}", ha="center",
                fontsize=8.5, color=INK2)
    ax.set_ylim(1e4, 1e11)
    ax.grid(axis="x", visible=False)
    despine(ax)
    save(fig, "fig10_cost_tiers.png")


# ==========================================================================
# FIG 11 - cost breakdown
# ==========================================================================
def fig_cost_breakdown():
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 6.0))
    for ax, key, title, col in (
            (axes[0], "google_search", "Google Search — one-time cost of a new language", C["blue"]),
            (axes[1], "sarvam", "Sarvam AI — one-time cost of a new language", C["orange"])):
        items = sorted(M[key]["one_time"], key=lambda d: d["usd"])
        names = [i["item"] for i in items]
        vals = [i["usd"] for i in items]
        y = np.arange(len(items))
        ax.barh(y, vals, .62, color=col)
        ax.set_yticks(y)
        ax.set_yticklabels([n if len(n) < 52 else n[:50] + "…" for n in names],
                           fontsize=8)
        ax.set_xscale("log")
        ax.set_xlabel("USD (log)")
        ax.set_title(title, fontsize=10.5)
        for yi, v in zip(y, vals):
            ax.text(v * 1.25, yi, f"${v:,.0f}", va="center", fontsize=7.8,
                    color=INK2)
        ax.set_xlim(1e3, 5e7)
        ax.grid(axis="y", visible=False)
        despine(ax)
        tot = M[key]["one_time_total"]
        ax.text(.98, .02, f"total  ${tot:,.0f}", transform=ax.transAxes,
                ha="right", fontsize=10, fontweight="bold", color=INK)
    fig.tight_layout()
    save(fig, "fig11_cost_breakdown.png")


# ==========================================================================
# FIG 12 - the curation-share cliff
# ==========================================================================
def fig_sensitivity():
    fig, ax = plt.subplots(figsize=(7.8, 4.6))
    rows = M["curation_share_sensitivity"]
    x = [r["curated_share"] * 100 for r in rows]
    y = [r["data_cost"] for r in rows]
    ax.plot(x, y, "o-", color=C["blue"], ms=6, label="data acquisition cost")
    ax.set_yscale("log")
    for xi, yi in zip(x, y):
        ax.annotate(f"${yi/1e6:,.1f}M", xy=(xi, yi), xytext=(0, 9),
                    textcoords="offset points", ha="center", fontsize=8,
                    color=INK2)
    nk = M["naive_anchor_check"]
    ax.axhline(nk["cost_all_curated"], color=C["red"], ls="--", lw=1.6)
    ax.annotate(f"100% curated = ${nk['cost_all_curated']/1e9:.2f}B\n"
                "— 28× Sarvam's entire disclosed funding",
                xy=(1.2, nk["cost_all_curated"] * .35), fontsize=8.5,
                color=C["red"])
    ax.set_xlabel("Share of the 114-billion-word corpus that is hand-curated (%)")
    ax.set_ylabel("Data cost, USD (log)")
    ax.set_title("Why nobody buys their pretraining corpus")
    ax.legend(loc="lower right"); despine(ax)
    save(fig, "fig12_sensitivity.png")


if __name__ == "__main__":
    fig_zipf_main()
    fig_head_tail()
    fig_gof()
    fig_edge_cases()
    fig_monkey()
    fig_alpha_stability()
    fig_heaps_loglog()
    fig_heaps_knee()
    fig_marginal_yield()
    fig_cost_tiers()
    fig_cost_breakdown()
    fig_sensitivity()
