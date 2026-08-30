#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""06_figures.py -- renders every figure used in the report."""
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "out")
FIG = os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 140, "savefig.dpi": 140, "font.size": 10.5,
    "axes.grid": True, "grid.alpha": 0.25, "axes.spines.top": False,
    "axes.spines.right": False,
})

COLORS = {"en": "#2563eb", "hi": "#ea580c", "ar": "#16a34a"}
LANG_NAMES = {"en": "English", "hi": "Hindi", "ar": "Arabic"}

results = json.load(open(os.path.join(OUT, "token_zipf_results.json")))
sweetspot = json.load(open(os.path.join(OUT, "sweetspot_results.json")))
word_stats = json.load(open(os.path.join(OUT, "word_stats_all.json")))


def dedupe(recs):
    seen, out = set(), []
    for r in recs:
        if r["actual_vocab"] not in seen:
            seen.add(r["actual_vocab"]); out.append(r)
    return sorted(out, key=lambda r: r["actual_vocab"])


# ---------------------------------------------------------------- Fig 1
# Word-level Zipf, all three languages
def fig1_word_zipf():
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    for lang in ("en", "hi", "ar"):
        freq = [int(l.split("\t")[1]) for l in
                open(os.path.join(OUT, f"word_freq_{lang}.tsv"), encoding="utf-8")]
        ranks = np.arange(1, len(freq) + 1)
        ax.loglog(ranks, freq, ".", ms=2, alpha=0.55, color=COLORS[lang],
                   label=f"{LANG_NAMES[lang]} (V={len(freq):,})")
    ax.set_xlabel("Rank $r$ (log)"); ax.set_ylabel("Frequency $f(r)$ (log)")
    ax.set_title("Word-level Zipf: English, Hindi, Arabic")
    ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig01_word_zipf.png")); plt.close(fig)


# ---------------------------------------------------------------- Fig 2
# Token-level Zipf at several vocab sizes, one panel per language
def fig2_token_zipf_by_vocab():
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=False)
    show_sizes = [500, 2000, 8000, 32000]
    for ax, lang in zip(axes, ("en", "hi", "ar")):
        recs = dedupe(results["sweep"][lang])
        by_target = {r["target_vocab"]: r for r in results["sweep"][lang]}
        for vs in show_sizes:
            r = by_target.get(vs)
            if r is None:
                continue
        # plot from freq if available: recompute is expensive, so approximate via zipf fit params
        for vs in show_sizes:
            rec = next((r for r in results["sweep"][lang] if r["target_vocab"] == vs), None)
            if rec is None:
                continue
            V = rec["used_vocab"]
            ranks = np.geomspace(1, V, 200)
            # synthetic Zipf-Mandelbrot-free curve from fitted alpha (illustrative envelope)
            C = np.exp(np.log(ranks[0]) * 0)  # placeholder, normalized below
            f = ranks ** (-rec["zipf_alpha"])
            f = f / f[0]
            ax.loglog(ranks, f, label=f"vocab={rec['actual_vocab']:,} (α={rec['zipf_alpha']:.2f}, R²={rec['zipf_r2']:.3f})")
        ax.set_title(LANG_NAMES[lang])
        ax.set_xlabel("Rank (log)")
        if lang == "en":
            ax.set_ylabel("Normalised frequency (log)")
        ax.legend(fontsize=7.5)
    fig.suptitle("Token rank–frequency shape vs vocabulary size (fitted power-law envelopes)")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig02_token_zipf_by_vocab.png")); plt.close(fig)


# ---------------------------------------------------------------- Fig 3
# alpha and R^2 vs vocab size, all languages
def fig3_alpha_r2_vs_vocab():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for lang in ("en", "hi", "ar"):
        recs = dedupe(results["sweep"][lang])
        v = [r["actual_vocab"] for r in recs]
        a = [r["zipf_alpha"] for r in recs]
        r2 = [r["zipf_r2"] for r in recs]
        axes[0].semilogx(v, a, "o-", color=COLORS[lang], label=LANG_NAMES[lang], ms=4)
        axes[1].semilogx(v, r2, "o-", color=COLORS[lang], label=LANG_NAMES[lang], ms=4)
    axes[0].axhline(1.0, ls="--", color="grey", lw=1, label="α = 1 (pure Zipf)")
    axes[0].set_xlabel("Vocabulary size (log)"); axes[0].set_ylabel("Zipf exponent α")
    axes[0].set_title("Zipf exponent vs tokenizer vocab size"); axes[0].legend(fontsize=8)
    axes[1].set_xlabel("Vocabulary size (log)"); axes[1].set_ylabel("Goodness of fit R²")
    axes[1].set_title("Zipf fit quality vs tokenizer vocab size"); axes[1].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig03_alpha_r2_vs_vocab.png")); plt.close(fig)


# ---------------------------------------------------------------- Fig 4
# fertility vs vocab size (compression curve) with knee marked
def fig4_fertility_knee():
    fig, ax = plt.subplots(figsize=(8, 5.5))
    for lang in ("en", "hi", "ar"):
        recs = dedupe(results["sweep"][lang])
        v = [r["actual_vocab"] for r in recs]
        fert = [r["fertility_tokens_per_word"] for r in recs]
        ax.semilogx(v, fert, "o-", color=COLORS[lang], label=LANG_NAMES[lang], ms=4)
        knee = sweetspot[lang]["fertility_knee_vocab"]
        if knee:
            idx = min(range(len(v)), key=lambda i: abs(v[i] - knee))
            ax.plot(v[idx], fert[idx], "*", color=COLORS[lang], ms=18, mec="black", mew=0.6)
    ax.set_xlabel("Vocabulary size (log)"); ax.set_ylabel("Fertility (tokens / word)")
    ax.set_title("Compression curve: fertility vs vocabulary size\n(stars = Kneedle knee)")
    ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig04_fertility_knee.png")); plt.close(fig)


# ---------------------------------------------------------------- Fig 5
# vocab utilisation vs vocab size
def fig5_utilisation():
    fig, ax = plt.subplots(figsize=(8, 5.5))
    for lang in ("en", "hi", "ar"):
        recs = dedupe(results["sweep"][lang])
        v = [r["actual_vocab"] for r in recs]
        u = [r["vocab_utilisation"] * 100 for r in recs]
        ax.semilogx(v, u, "o-", color=COLORS[lang], label=LANG_NAMES[lang], ms=4)
        peak = sweetspot[lang]["utilisation_peak_vocab"]
        if peak:
            idx = min(range(len(v)), key=lambda i: abs(v[i] - peak))
            ax.plot(v[idx], u[idx], "*", color=COLORS[lang], ms=18, mec="black", mew=0.6)
    ax.set_xlabel("Vocabulary size (log)"); ax.set_ylabel("Vocabulary utilisation (%)")
    ax.set_title("Share of trained merges actually used at least once\n(stars = utilisation peak)")
    ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig05_utilisation.png")); plt.close(fig)


# ---------------------------------------------------------------- Fig 6
# model-style comparison: vocab + fertility across LLaMA2/3, Qwen, Kimi
def fig6_model_comparison():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
    models = ["llama2", "llama3", "qwen", "kimi"]
    mlabels = ["LLaMA-2\n(32k target)", "LLaMA-3\n(128k target)", "Qwen-2.5/3\n(151.6k target)", "Kimi-K2/K3\n(163.6k target)"]
    x = np.arange(len(models))
    width = 0.25
    for i, lang in enumerate(("en", "hi", "ar")):
        actual = [results["model_style"][lang][m]["actual_vocab"] for m in models]
        axes[0].bar(x + (i - 1) * width, actual, width, color=COLORS[lang], label=LANG_NAMES[lang])
        fert = [results["model_style"][lang][m]["fertility_tokens_per_word"] for m in models]
        axes[1].bar(x + (i - 1) * width, fert, width, color=COLORS[lang], label=LANG_NAMES[lang])
    axes[0].set_xticks(x); axes[0].set_xticklabels(mlabels, fontsize=8)
    axes[0].set_ylabel("Actual (data-capped) vocab reached")
    axes[0].set_title("Model-style tokenizers: vocab actually reachable\non our corpora vs published target")
    axes[0].legend(fontsize=8)
    axes[1].set_xticks(x); axes[1].set_xticklabels(mlabels, fontsize=8)
    axes[1].set_ylabel("Fertility (tokens / word)")
    axes[1].set_title("Fertility of model-style tokenizers")
    axes[1].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig06_model_comparison.png")); plt.close(fig)


# ---------------------------------------------------------------- Fig 7
# sweet-spot criteria summary (dumbbell-ish)
def fig7_sweetspot_summary():
    fig, ax = plt.subplots(figsize=(9, 5))
    labels = ["Fertility knee", "Zipf stability", "Utilisation peak", "Marginal-yield rule"]
    keys = ["fertility_knee_vocab", "zipf_stability_vocab", "utilisation_peak_vocab", "marginal_yield_sweetspot_vocab"]
    langs = ("en", "hi", "ar")
    y = np.arange(len(labels))
    for i, lang in enumerate(langs):
        vals = [sweetspot[lang][k] or np.nan for k in keys]
        ax.scatter(vals, y + (i - 1) * 0.18, color=COLORS[lang], s=70, label=LANG_NAMES[lang], zorder=3)
    ax.set_yticks(y); ax.set_yticklabels(labels)
    ax.set_xscale("log")
    ax.set_xlabel("Candidate vocabulary sweet spot (log)")
    ax.set_title("Four independent criteria for the vocab-size sweet spot")
    ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig07_sweetspot_summary.png")); plt.close(fig)


if __name__ == "__main__":
    fig1_word_zipf()
    fig2_token_zipf_by_vocab()
    fig3_alpha_r2_vs_vocab()
    fig4_fertility_knee()
    fig5_utilisation()
    fig6_model_comparison()
    fig7_sweetspot_summary()
    print("Wrote 7 figures to", FIG)
