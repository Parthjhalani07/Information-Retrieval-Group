#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04_heaps_analysis.py
====================
Heaps' Law (Herdan's Law) for Hindi:      V(N) = K * N^beta

Three questions are answered:

  Q1  What are K and beta for Hindi, and how well does the model hold?
  Q2  WHERE DOES THE CURVE FLATTEN?  Two independent definitions are used
      so the answer does not depend on one arbitrary rule:
        (a) Kneedle (Satopaa et al., 2011) - the point of maximum distance
            from the chord joining the ends of the min-max normalised curve.
            This is "where the eye sees the elbow".
        (b) Marginal-yield thresholds - the token count at which the corpus
            stops returning more than X new word types per 1,000 tokens.
            This is the operationally useful definition: it tells a
            lexicographer or a tokeniser-builder when to stop reading.
  Q3  How does Hindi compare with English, and is beta ~ 1/alpha as the
      Zipf-Heaps duality predicts?

Outputs: out/heaps_results.json, out/heaps_curve.json
"""

import json
import os
from collections import Counter

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.abspath(os.path.join(HERE, "..", "data"))
OUT = os.path.abspath(os.path.join(HERE, "..", "out"))

from importlib.machinery import SourceFileLoader             # noqa: E402
tok_mod = SourceFileLoader("tok", os.path.join(HERE, "02_tokenize.py")).load_module()

RNG = np.random.default_rng(20260823)


# --------------------------------------------------------------------------
def vocab_growth(tokens, step=250):
    """Return (N grid, V(N)) sampled every `step` tokens."""
    seen, Ns, Vs = set(), [], []
    for i, t in enumerate(tokens, 1):
        seen.add(t)
        if i % step == 0:
            Ns.append(i)
            Vs.append(len(seen))
    if Ns[-1] != len(tokens):
        Ns.append(len(tokens))
        Vs.append(len(seen))
    return np.array(Ns, float), np.array(Vs, float)


def heaps_fit(N, V, nmin=1000):
    """OLS on log V = log K + beta log N."""
    m = N >= nmin
    slope, intercept, r, _, se = stats.linregress(np.log(N[m]), np.log(V[m]))
    return dict(K=float(np.exp(intercept)), beta=float(slope),
                r2=float(r ** 2), stderr=float(se), n_points=int(m.sum()))


def kneedle(N, V):
    """
    Point of maximum vertical distance from the straight chord joining the
    first and last points of the min-max normalised curve. Reported both on
    linear axes (the visual elbow) and on log axes.
    """
    def knee(x, y):
        xs = (x - x.min()) / (x.max() - x.min())
        ys = (y - y.min()) / (y.max() - y.min())
        d = ys - xs                       # chord is the identity line
        i = int(np.argmax(d))
        return i, float(d[i])

    i_lin, d_lin = knee(N, V)
    i_log, d_log = knee(np.log(N), np.log(V))
    return dict(linear=dict(index=i_lin, N=float(N[i_lin]), V=float(V[i_lin]),
                            distance=d_lin),
                log=dict(index=i_log, N=float(N[i_log]), V=float(V[i_log]),
                         distance=d_log))


def marginal_yield(N, V, window=10000):
    """
    New word types discovered per 1,000 tokens, measured over a sliding
    window so the estimate is local rather than cumulative.
    """
    rate_N, rate = [], []
    for i in range(len(N)):
        j = np.searchsorted(N, N[i] - window)
        if i - j < 2:
            continue
        dV = V[i] - V[j]
        dN = N[i] - N[j]
        rate_N.append(N[i])
        rate.append(1000.0 * dV / dN)
    return np.array(rate_N), np.array(rate)


def threshold_crossings(rate_N, rate, thresholds, K, beta):
    """
    First N at which the observed rate drops below each threshold, plus the
    N predicted analytically from the fitted Heaps model:
        dV/dN = K*beta*N^(beta-1)  ->  N = (1000*K*beta / rate)^(1/(1-beta))
    """
    out = []
    for th in thresholds:
        idx = np.where(rate < th)[0]
        obs = float(rate_N[idx[0]]) if len(idx) else None
        pred = float((1000.0 * K * beta / th) ** (1.0 / (1.0 - beta)))
        out.append(dict(threshold_per_1k=th, observed_N=obs, model_N=pred))
    return out


def conllu_forms(paths, col=1):
    for p in paths:
        for line in open(p, encoding="utf-8"):
            if line.strip() and not line.startswith("#"):
                parts = line.rstrip("\n").split("\t")
                if len(parts) > col and "-" not in parts[0] and "." not in parts[0]:
                    yield parts[col]


# --------------------------------------------------------------------------
def main():
    res, curves = {}, {}

    # ---------------- Hindi -------------------------------------------
    toks = open(os.path.join(OUT, "tokens.txt"), encoding="utf-8").read().split("\n")
    N, V = vocab_growth(toks)
    fit = heaps_fit(N, V)
    knees = kneedle(N, V)
    rN, rate = marginal_yield(N, V)
    thr = threshold_crossings(rN, rate, [100, 50, 25, 20, 15, 10, 5, 2, 1],
                              fit["K"], fit["beta"])

    res["hindi"] = dict(N_total=len(toks), V_total=int(V[-1]),
                        fit=fit, knee=knees, thresholds=thr,
                        rate_at_end=float(rate[-1]))
    curves["hindi"] = dict(N=N.tolist(), V=V.tolist(),
                           rate_N=rN.tolist(), rate=rate.tolist())

    # stability: refit on the first and second halves separately
    h = len(N) // 2
    res["hindi"]["fit_first_half"] = heaps_fit(N[:h], V[:h])
    res["hindi"]["fit_second_half"] = heaps_fit(N[h:], V[h:])

    # control 1 - full token-level shuffle (destroys all local burstiness)
    sh = list(toks)
    RNG.shuffle(sh)
    Ns, Vs = vocab_growth(sh)
    res["hindi_shuffled"] = dict(fit=heaps_fit(Ns, Vs))
    curves["hindi_shuffled"] = dict(N=Ns.tolist(), V=Vs.tolist())

    # control 2 - raw file order: sources are concatenated, so the genre
    # boundary injects a burst of new vocabulary and kinks the curve. Kept to
    # show why the analysis is run on a sentence-shuffled stream.
    fo = list(tok_mod.stream_tokens(
        os.path.join(DATA, "corpus_hi.txt"), shuffle_lines=False,
        devanagari_only=True))
    Nf, Vf = vocab_growth(fo)
    res["hindi_file_order"] = dict(fit=heaps_fit(Nf, Vf), knee=kneedle(Nf, Vf))
    curves["hindi_file_order"] = dict(N=Nf.tolist(), V=Vf.tolist())

    # ---------------- Hindi lemmas (morphology stripped) ---------------
    hi_conllu = [os.path.join(DATA, f) for f in
                 ("hi_hdtb-ud-train.conllu", "hi_hdtb-ud-dev.conllu",
                  "hi_hdtb-ud-test.conllu")]
    forms = [w for w in conllu_forms(hi_conllu, 1) if tok_mod.DEV_ONLY_RE.match(w)]
    lemmas = [w for w in conllu_forms(hi_conllu, 2) if tok_mod.DEV_ONLY_RE.match(w)]
    for name, seq in (("hindi_surface", forms), ("hindi_lemma", lemmas)):
        n, v = vocab_growth(seq)
        res[name] = dict(N_total=len(seq), V_total=int(v[-1]), fit=heaps_fit(n, v))
        curves[name] = dict(N=n.tolist(), V=v.tolist())

    # ---------------- English control ----------------------------------
    en_files = [os.path.join(DATA, f) for f in os.listdir(DATA)
                if f.startswith("en_") and f.endswith(".conllu")]
    en = [w.lower() for w in conllu_forms(sorted(en_files), 1) if w.isalpha()]
    en = en[:len(toks)]                       # match Hindi corpus size exactly
    ne, ve = vocab_growth(en)
    res["english"] = dict(N_total=len(en), V_total=int(ve[-1]),
                          fit=heaps_fit(ne, ve),
                          knee=kneedle(ne, ve))
    rNe, rate_e = marginal_yield(ne, ve)
    res["english"]["thresholds"] = threshold_crossings(
        rNe, rate_e, [100, 50, 25, 20, 15, 10, 5, 2, 1],
        res["english"]["fit"]["K"], res["english"]["fit"]["beta"])
    curves["english"] = dict(N=ne.tolist(), V=ve.tolist(),
                             rate_N=rNe.tolist(), rate=rate_e.tolist())

    # ---------------- Zipf-Heaps duality -------------------------------
    zipf = json.load(open(os.path.join(OUT, "zipf_results.json")))
    a = zipf["baseline"]["ols_core"]["alpha"]
    gamma = zipf["A3_gof"]["gamma"]
    res["duality"] = dict(
        zipf_alpha_core=a,
        zipf_alpha_all_ranks=zipf["baseline"]["ols_all"]["alpha"],
        observed_beta=res["hindi"]["fit"]["beta"],
        # naive rank-frequency duality
        beta_pred_from_alpha=1.0 / a,
        err_from_alpha=abs(1.0 / a - res["hindi"]["fit"]["beta"]),
        # correct duality via the frequency-of-frequencies exponent gamma:
        # for p(f) ~ f^-gamma with 1 < gamma < 2, Heaps' beta = gamma - 1
        freq_of_freq_gamma=gamma,
        beta_pred_from_gamma=gamma - 1.0,
        err_from_gamma=abs((gamma - 1.0) - res["hindi"]["fit"]["beta"]),
        note="beta = 1/alpha only holds asymptotically; on finite corpora the "
             "measured beta is biased low. beta = gamma - 1 is the tighter "
             "prediction and is the one that survives.")

    # ---------------- extrapolation to full Hindi Wikipedia ------------
    K, b = res["hindi"]["fit"]["K"], res["hindi"]["fit"]["beta"]
    res["extrapolation"] = [
        dict(N=n, V_pred=float(K * n ** b),
             new_types_per_1k=float(1000 * K * b * n ** (b - 1)))
        for n in (1e6, 1e7, 2.5e7, 1e8, 1e9)]

    json.dump(res, open(os.path.join(OUT, "heaps_results.json"), "w"),
              ensure_ascii=False, indent=2, default=float)
    json.dump(curves, open(os.path.join(OUT, "heaps_curve.json"), "w"))

    f = res["hindi"]["fit"]
    print(f"Hindi   V = {f['K']:.3f} * N^{f['beta']:.4f}   R2={f['r2']:.5f}")
    fe = res["english"]["fit"]
    print(f"English V = {fe['K']:.3f} * N^{fe['beta']:.4f}  R2={fe['r2']:.5f}")
    print("knee (linear axes) at N =", f"{knees['linear']['N']:,.0f}",
          "V =", f"{knees['linear']['V']:,.0f}")
    d = res["duality"]
    print(f"duality: beta_obs={f['beta']:.4f} | 1/alpha={d['beta_pred_from_alpha']:.4f}"
          f" | gamma-1={d['beta_pred_from_gamma']:.4f}")
    for t in thr:
        print(f"  rate < {t['threshold_per_1k']:>3}/1k tokens : observed N = "
              f"{t['observed_N']}, model N = {t['model_N']:,.0f}")


if __name__ == "__main__":
    main()
