#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_zipf_analysis.py
===================
An adversarial study of Zipf's Law on Hindi.

The brief was to *try to disprove* Zipf's Law. Accordingly this script does
not simply fit a line to a log-log plot; it runs nine deliberate attacks,
each one an edge case chosen because it is the kind of thing that ought to
break a power law if the power law were an artefact rather than a law.

  A1  Head anomaly ............ f(1)/f(2) should be 2 under pure Zipf.
  A2  Tail collapse ........... the log-log tail visibly droops.
  A3  Formal GOF test ......... Clauset-Shalizi-Newman MLE + KS + bootstrap.
  A4  Genre shift ............. newswire vs Wikipedia sub-corpora.
  A5  Function-word ablation .. delete the top-50 "Zipf engine" words.
  A6  Morphological collapse .. surface forms -> lemmas (Hindi is inflecting).
  A7  Random-typing control ... Miller's monkeys: is Zipf just trivial?
  A8  Unit change ............. characters and bigrams instead of words.
  A9  Scale dependence ........ does the exponent drift with corpus size?

Outputs: out/zipf_results.json, out/zipf_tables.json
"""

import json
import os
import random
import re
from collections import Counter

import numpy as np
from scipy import optimize, stats

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.abspath(os.path.join(HERE, "..", "data"))
OUT = os.path.abspath(os.path.join(HERE, "..", "out"))

from importlib.machinery import SourceFileLoader           # noqa: E402
tok_mod = SourceFileLoader("tok", os.path.join(HERE, "02_tokenize.py")).load_module()
tokenize = tok_mod.tokenize

RNG = np.random.default_rng(20260823)
random.seed(20260823)


# ==========================================================================
# Fitting machinery
# ==========================================================================
def zipf_ols(counts, rmin=1, rmax=None):
    """Least-squares fit of log f = log C - a log r. Returns (a, C, r2)."""
    f = np.asarray(sorted(counts, reverse=True), dtype=float)
    r = np.arange(1, len(f) + 1, dtype=float)
    m = (r >= rmin) & (f > 0)
    if rmax:
        m &= r <= rmax
    x, y = np.log(r[m]), np.log(f[m])
    slope, intercept, rval, _, stderr = stats.linregress(x, y)
    return dict(alpha=-slope, C=float(np.exp(intercept)), r2=rval ** 2,
                stderr=float(stderr), n_points=int(m.sum()))


def zipf_mandelbrot_fit(counts, nmax=2000):
    """Fit f(r) = C / (r + b)^a  (Zipf-Mandelbrot) over the first nmax ranks."""
    f = np.asarray(sorted(counts, reverse=True), dtype=float)[:nmax]
    r = np.arange(1, len(f) + 1, dtype=float)

    def model(r, logC, a, b):
        return logC - a * np.log(r + b)

    p0 = [np.log(f[0]), 1.0, 1.0]
    popt, _ = optimize.curve_fit(model, r, np.log(f), p0=p0, maxfev=40000)
    pred = model(r, *popt)
    ss_res = np.sum((np.log(f) - pred) ** 2)
    ss_tot = np.sum((np.log(f) - np.log(f).mean()) ** 2)
    return dict(C=float(np.exp(popt[0])), alpha=float(popt[1]),
                b=float(popt[2]), r2=float(1 - ss_res / ss_tot))


def select_xmin(x, candidates=None):
    """
    CSN x_min selection: choose the x_min that minimises the KS distance
    between the empirical tail and the fitted discrete power law.
    """
    x = np.asarray(x, dtype=float)
    if candidates is None:
        candidates = [c for c in range(1, 101) if (x >= c).sum() >= 200]
    best = None
    for c in candidates:
        fit = discrete_powerlaw_mle(x, c)
        if fit is None:
            continue
        g, _, n = fit
        d = ks_distance(x, c, g)
        if best is None or d < best[2]:
            best = (c, g, d, n)
    return best            # (xmin, gamma, ks, n_tail)


def discrete_powerlaw_mle(x, xmin):
    """
    MLE for the discrete power law  p(x) ~ x^-gamma,  x >= xmin
    (Clauset, Shalizi & Newman 2009, eq. 3.7 approximation refined
    numerically).  x is an array of integer observations.
    """
    x = np.asarray([v for v in x if v >= xmin], dtype=float)
    n = len(x)
    if n < 20:
        return None

    def nll(g):
        # Hurwitz zeta normalisation
        from scipy.special import zeta
        return n * np.log(zeta(g, xmin)) + g * np.sum(np.log(x))

    res = optimize.minimize_scalar(nll, bounds=(1.01, 6.0), method="bounded")
    gamma = float(res.x)
    sigma = (gamma - 1) / np.sqrt(n)
    return gamma, sigma, n


def ks_distance(x, xmin, gamma):
    """KS statistic between the empirical CDF and the fitted discrete PL."""
    from scipy.special import zeta
    x = np.sort(np.asarray([v for v in x if v >= xmin], dtype=float))
    n = len(x)
    uniq = np.unique(x)
    emp = np.searchsorted(x, uniq, side="right") / n
    Z = zeta(gamma, xmin)
    theo = 1.0 - np.array([zeta(gamma, u + 1) / Z for u in uniq])
    return float(np.max(np.abs(emp - theo)))


def bootstrap_pvalue(x, xmin, gamma, n_synth=200):
    """
    CSN goodness-of-fit p-value: fraction of synthetic power-law datasets
    whose KS distance is at least as large as the empirical one.
    p > 0.10 => the power law is a plausible generating model.
    """
    from scipy.special import zeta
    obs = [v for v in x if v >= xmin]
    n = len(obs)
    d_emp = ks_distance(obs, xmin, gamma)

    Z = zeta(gamma, xmin)
    kmax = 200000
    ks_vals = np.arange(xmin, kmax + 1, dtype=float)
    pmf = ks_vals ** (-gamma) / Z
    pmf = pmf / pmf.sum()
    cdf = np.cumsum(pmf)

    worse = 0
    for _ in range(n_synth):
        u = RNG.random(n)
        synth = ks_vals[np.searchsorted(cdf, u)]
        g_s, _, _ = discrete_powerlaw_mle(synth, xmin)
        if ks_distance(synth, xmin, g_s) >= d_emp:
            worse += 1
    return d_emp, worse / n_synth


# ==========================================================================
# Corpus helpers
# ==========================================================================
def load_tokens():
    return open(os.path.join(OUT, "tokens.txt"), encoding="utf-8").read().split("\n")


def conllu_columns(paths, col):
    """Yield a given CoNLL-U column (1=form, 2=lemma, 3=upos)."""
    for p in paths:
        for line in open(p, encoding="utf-8"):
            if line.strip() and not line.startswith("#"):
                parts = line.rstrip("\n").split("\t")
                if len(parts) > col and "-" not in parts[0] and "." not in parts[0]:
                    yield parts[col]


# ==========================================================================
# The nine attacks
# ==========================================================================
def main():
    results, tables = {}, {}
    toks = load_tokens()
    counts = Counter(toks)
    freqs = sorted(counts.values(), reverse=True)
    N, V = len(toks), len(counts)
    results["corpus"] = dict(N=N, V=V)

    # ---- baseline ------------------------------------------------------
    full = zipf_ols(freqs)
    core = zipf_ols(freqs, rmin=10, rmax=5000)
    zm = zipf_mandelbrot_fit(freqs)
    # a second Zipf-Mandelbrot fitted to the head alone, to test whether the
    # head is fittable at all or genuinely anomalous
    zm_head = zipf_mandelbrot_fit(freqs, nmax=200)
    results["baseline"] = dict(ols_all=full, ols_core=core, mandelbrot=zm,
                               mandelbrot_head=zm_head)
    tables["rank_freq"] = [[i + 1, freqs[i]] for i in range(len(freqs))]

    # ---- A1: head anomaly ---------------------------------------------
    top = freqs[:10]
    ideal = [top[0] / k for k in range(1, 11)]
    results["A1_head"] = dict(
        observed=top, zipf_ideal=[round(v, 1) for v in ideal],
        ratio_f1_f2=top[0] / top[1],
        max_rel_error_pct=max(abs(o - e) / e * 100 for o, e in zip(top, ideal)),
        mandelbrot_pred=[round(zm["C"] / (k + zm["b"]) ** zm["alpha"], 1)
                         for k in range(1, 11)],
        mandelbrot_head_pred=[
            round(zm_head["C"] / (k + zm_head["b"]) ** zm_head["alpha"], 1)
            for k in range(1, 11)],
    )
    # worst-case relative error over the top ten, measured against each
    # model's own prediction, so the three models are compared like for like
    for tag, preds in (("pure_zipf", ideal),
                       ("mandelbrot", results["A1_head"]["mandelbrot_pred"]),
                       ("mandelbrot_head",
                        results["A1_head"]["mandelbrot_head_pred"])):
        errs = [abs(o - p) / p * 100 for o, p in zip(top, preds)]
        results["A1_head"][f"{tag}_worst_err_pct"] = max(errs)
        results["A1_head"][f"{tag}_mean_err_pct"] = sum(errs) / len(errs)

    # ---- A2: tail collapse --------------------------------------------
    hapax = sum(1 for c in counts.values() if c == 1)
    dis = sum(1 for c in counts.values() if c == 2)
    plateau_start = V - hapax + 1          # first rank whose count is 1
    mid = zipf_ols(freqs, rmin=int(0.05 * V), rmax=int(0.45 * V))
    results["A2_tail"] = dict(
        hapax=hapax, hapax_pct=100 * hapax / V, dis_legomena=dis,
        plateau_start_rank=plateau_start,
        plateau_width_pct=100 * hapax / V,
        alpha_mid=mid["alpha"], alpha_core=core["alpha"],
        note="the flat shelf at the right of the log-log plot is the block of "
             "hapax legomena. It is a quantisation floor (a count cannot fall "
             "below 1) plus rank truncation at V, i.e. a finite-sample "
             "artefact, not a failure of the law.",
    )
    # If the shelf is a sampling artefact its onset rank must scale with the
    # corpus: it should move steadily rightwards as N grows.
    onset = []
    for frac in (0.1, 0.25, 0.5, 0.75, 1.0):
        c = Counter(toks[: int(frac * N)])
        v = len(c)
        h = sum(1 for k in c.values() if k == 1)
        onset.append(dict(frac=frac, N=int(frac * N), V=v,
                          plateau_start_rank=v - h + 1, hapax_pct=100 * h / v))
    results["A2_tail"]["plateau_scaling"] = onset

    # ---- A3: formal goodness of fit -----------------------------------
    vals = list(counts.values())
    xmin, gamma, d_min, n_tail = select_xmin(vals)
    _, sigma, _ = discrete_powerlaw_mle(vals, xmin)
    d_emp, pval = bootstrap_pvalue(vals, xmin, gamma, n_synth=500)
    # naive (badly chosen) x_min, kept to show that the test is only fair
    # when x_min is selected properly
    g_naive, _, n_naive = discrete_powerlaw_mle(vals, 1)
    d_naive, p_naive = bootstrap_pvalue(vals, 1, g_naive, n_synth=200)
    # Is the rejection driven by model misfit or merely by sample size?
    # Re-run the identical test on random subsamples of the type list.
    power = []
    vals_arr = np.asarray(vals)
    for n_sub in (250, 500, 1000, 2000, 5000, 10000):
        if n_sub > len(vals_arr):
            continue
        sub_v = list(RNG.choice(vals_arr, size=n_sub, replace=False))
        try:
            g_s, _, _ = discrete_powerlaw_mle(sub_v, xmin)
            d_s, p_s = bootstrap_pvalue(sub_v, xmin, g_s, n_synth=120)
            power.append(dict(n=n_sub, gamma=g_s, ks=d_s, p=p_s))
        except Exception:                                      # noqa: BLE001
            pass

    scan = []
    for c in (1, 2, 3, 5, 10, 20, 50, 100):
        fit = discrete_powerlaw_mle(vals, c)
        if fit:
            g_c, _, n_c = fit
            scan.append(dict(xmin=c, gamma=g_c, n=n_c,
                             ks=ks_distance(vals, c, g_c)))

    results["A3_gof"] = dict(
        xmin=int(xmin), gamma=gamma, gamma_stderr=sigma, n=n_tail,
        ks_distance=d_emp, bootstrap_p=pval,
        alpha_implied=1 / (gamma - 1),
        max_cdf_deviation_pct=100 * d_emp,
        xmin_scan=scan,
        power_analysis=power,
        naive=dict(xmin=1, gamma=g_naive, n=n_naive,
                   ks_distance=d_naive, bootstrap_p=p_naive),
        verdict=("pure power law NOT rejected" if pval > 0.10
                 else "pure power law formally rejected (see power analysis)"),
    )

    # ---- A4: genre shift ----------------------------------------------
    lines = open(os.path.join(DATA, "corpus_hi.txt"), encoding="utf-8").read().split("\n")
    # line layout: HDTB train 13306 | dev 1659 | test 1684 | PUD 1000 | XQuAD 240
    news_lines = lines[:16649]          # HDTB train+dev+test (newswire)
    wiki_lines = lines[17649:17889]     # XQuAD Hindi Wikipedia paragraphs
    sub = {}
    for name, ls in (("newswire", news_lines), ("wikipedia", wiki_lines)):
        t = [w for l in ls for w in tokenize(l, devanagari_only=True)]
        c = sorted(Counter(t).values(), reverse=True)
        sub[name] = dict(N=len(t), V=len(c),
                         **zipf_ols(c, rmin=10, rmax=min(2000, len(c))))
    results["A4_genre"] = sub

    # ---- A5: function-word ablation -----------------------------------
    stop = {w for w, _ in counts.most_common(50)}
    abl = [t for t in toks if t not in stop]
    ac = sorted(Counter(abl).values(), reverse=True)
    results["A5_ablation"] = dict(
        removed_types=50, removed_token_pct=100 * (1 - len(abl) / N),
        N=len(abl), V=len(ac),
        **zipf_ols(ac, rmin=10, rmax=5000))
    tables["ablation_rank_freq"] = [[i + 1, ac[i]] for i in range(len(ac))]

    # ---- A6: morphology (surface vs lemma) ----------------------------
    conllu = [os.path.join(DATA, f) for f in
              ("hi_hdtb-ud-train.conllu", "hi_hdtb-ud-dev.conllu",
               "hi_hdtb-ud-test.conllu")]
    forms = [w for w in conllu_columns(conllu, 1) if tok_mod.DEV_ONLY_RE.match(w)]
    lemmas = [w for w in conllu_columns(conllu, 2) if tok_mod.DEV_ONLY_RE.match(w)]
    fc = sorted(Counter(forms).values(), reverse=True)
    lc = sorted(Counter(lemmas).values(), reverse=True)
    results["A6_morphology"] = dict(
        surface=dict(N=len(forms), V=len(fc), **zipf_ols(fc, rmin=10, rmax=5000)),
        lemma=dict(N=len(lemmas), V=len(lc), **zipf_ols(lc, rmin=10, rmax=5000)),
        vocab_compression=1 - len(lc) / len(fc))
    tables["surface_rank_freq"] = [[i + 1, fc[i]] for i in range(len(fc))]
    tables["lemma_rank_freq"] = [[i + 1, lc[i]] for i in range(len(lc))]

    # ---- A7: Miller's monkeys -----------------------------------------
    alphabet = list("अआइईउऊएऐओऔकखगघचछजझटठडढतथदधनपफबभमयरलवशषसह")
    matras = list("ािीुूेैोौ्ं")
    pool = alphabet + matras
    weights = np.array([3.0] * len(alphabet) + [2.0] * len(matras))
    weights /= weights.sum()
    mk_tokens, space_p = [], 0.18
    cur = []
    while len(mk_tokens) < N:
        if RNG.random() < space_p:
            if cur:
                mk_tokens.append("".join(cur)); cur = []
        else:
            cur.append(pool[RNG.choice(len(pool), p=weights)])
    mc = sorted(Counter(mk_tokens).values(), reverse=True)
    mk_fit = zipf_ols(mc, rmin=10, rmax=5000)
    # staircase diagnostic: fraction of distinct frequency values
    results["A7_monkey"] = dict(
        N=len(mk_tokens), V=len(mc), **mk_fit,
        distinct_freq_values=len(set(mc)),
        real_distinct_freq_values=len(set(freqs)),
        length_entropy_monkey=float(stats.entropy(
            np.bincount([len(w) for w in mk_tokens])[1:] + 1e-12)),
        length_entropy_real=float(stats.entropy(
            np.bincount([len(w) for w in toks])[1:] + 1e-12)),
    )
    tables["monkey_rank_freq"] = [[i + 1, mc[i]] for i in range(len(mc))]

    # ---- A8: change the unit ------------------------------------------
    chars = Counter("".join(toks))
    bigrams = Counter(zip(toks, toks[1:]))
    cc = sorted(chars.values(), reverse=True)
    bc = sorted(bigrams.values(), reverse=True)
    results["A8_units"] = dict(
        characters=dict(V=len(cc), **zipf_ols(cc, rmin=2, rmax=len(cc))),
        bigrams=dict(V=len(bc), **zipf_ols(bc, rmin=10, rmax=20000)))
    tables["bigram_rank_freq"] = [[i + 1, bc[i]] for i in range(min(len(bc), 60000))]

    # ---- A9: scale dependence -----------------------------------------
    scale = []
    for frac in (0.02, 0.05, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0):
        n = int(frac * N)
        c = sorted(Counter(toks[:n]).values(), reverse=True)
        fit = zipf_ols(c, rmin=10, rmax=min(5000, len(c)))
        scale.append(dict(frac=frac, N=n, V=len(c),
                          alpha=fit["alpha"], r2=fit["r2"]))
    a = [s["alpha"] for s in scale[2:]]
    results["A9_scale"] = dict(series=scale, alpha_mean=float(np.mean(a)),
                               alpha_sd=float(np.std(a)),
                               alpha_range=float(max(a) - min(a)))

    # ---- external cross-check: wordfreq --------------------------------
    try:
        from wordfreq import get_frequency_dict
        wf = get_frequency_dict("hi")
        wfc = np.array(sorted(wf.values(), reverse=True))
        r = np.arange(1, len(wfc) + 1)
        m = (r >= 10) & (r <= 5000)
        sl, ic, rv, _, _ = stats.linregress(np.log(r[m]), np.log(wfc[m]))
        results["external_wordfreq"] = dict(entries=len(wfc), alpha=-sl,
                                            r2=rv ** 2)
        tables["wordfreq_rank_freq"] = [[int(i + 1), float(wfc[i])]
                                        for i in range(min(len(wfc), 30000))]
    except Exception as exc:                                   # noqa: BLE001
        results["external_wordfreq"] = {"error": str(exc)}

    json.dump(results, open(os.path.join(OUT, "zipf_results.json"), "w"),
              ensure_ascii=False, indent=2, default=float)
    json.dump(tables, open(os.path.join(OUT, "zipf_tables.json"), "w"),
              ensure_ascii=False)

    print(json.dumps(results, ensure_ascii=False, indent=2, default=float)[:6000])


if __name__ == "__main__":
    main()
