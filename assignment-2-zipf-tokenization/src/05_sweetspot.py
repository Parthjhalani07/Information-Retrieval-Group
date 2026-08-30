#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
05_sweetspot.py
=================
Answers the assignment's core open questions:
  * Is there a "sweet spot" vocabulary size for a tokenizer, per language?
  * Does the point where Zipf-law behaviour stabilises predict it?
  * Can an algorithm/criterion choose vocab size automatically?

Three independent criteria are computed per language and cross-checked:

  (1) FERTILITY KNEE (Kneedle on vocab_size vs tokens/word)
      -- the classic "diminishing returns" compression curve.
  (2) ZIPF-STABILITY POINT
      -- the smallest vocab size after which R^2 stays within 0.5% of its
         running max AND alpha stays within +-0.05 of its own running
         median for the rest of the sweep (i.e. where the Zipf fit
         "settles down" and stops drifting with vocab size).
  (3) VOCAB-UTILISATION PEAK
      -- the vocab size at which the largest share of trained merges are
         actually used at least once (beyond this, added vocab slots are
         increasingly dead weight -- a direct, corpus-relative signal).

A fourth, ALGORITHMIC criterion (the "marginal byte-yield" rule, directly
analogous to Assignment 1's Heaps' Law marginal-yield table) is also
computed: the smallest vocab size at which adding 1,000 more merges buys
less than a chosen compression-improvement tolerance (bytes/token gain).
"""
import json
import os
import numpy as np
from kneed import KneeLocator

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "out")

results = json.load(open(os.path.join(OUT, "token_zipf_results.json")))


def dedupe_by_vocab(records):
    """Collapse the saturation plateau (many target sizes -> same actual vocab)."""
    seen, out = set(), []
    for r in records:
        if r["actual_vocab"] not in seen:
            seen.add(r["actual_vocab"])
            out.append(r)
    return sorted(out, key=lambda r: r["actual_vocab"])


def fertility_knee(recs):
    x = np.array([r["actual_vocab"] for r in recs], dtype=float)
    y = np.array([r["fertility_tokens_per_word"] for r in recs], dtype=float)
    try:
        kl = KneeLocator(x, y, curve="convex", direction="decreasing")
        return float(kl.knee) if kl.knee is not None else None
    except Exception:
        return None


def zipf_stability_point(recs):
    r2 = np.array([r["zipf_r2"] for r in recs])
    alpha = np.array([r["zipf_alpha"] for r in recs])
    vocabs = np.array([r["actual_vocab"] for r in recs])
    n = len(recs)
    for i in range(n):
        r2_tail = r2[i:]
        alpha_tail = alpha[i:]
        if len(r2_tail) < 2:
            break
        r2_ok = np.all(r2_tail >= r2_tail.max() - 0.005)
        alpha_med = np.median(alpha_tail)
        alpha_ok = np.all(np.abs(alpha_tail - alpha_med) <= 0.05)
        if r2_ok and alpha_ok:
            return int(vocabs[i])
    return None


def utilisation_peak(recs):
    util = [r["vocab_utilisation"] for r in recs]
    idx = int(np.argmax(util))
    return recs[idx]["actual_vocab"], util[idx]


def marginal_byte_yield(recs, tolerance=0.02):
    """Smallest vocab size beyond which each extra 1,000 vocab slots buys
    < `tolerance` bytes/token of further compression (a direct analogue of
    Assignment 1's 'new types per 1,000 tokens' Heaps table)."""
    vocabs = np.array([r["actual_vocab"] for r in recs], dtype=float)
    bpt = np.array([r["bytes_per_token"] for r in recs], dtype=float)
    # bytes/token increases with vocab (each token covers more bytes);
    # marginal gain = d(bytes_per_token)/d(vocab) per 1000 slots
    table = []
    for i in range(1, len(recs)):
        dv = vocabs[i] - vocabs[i - 1]
        if dv <= 0:
            continue
        dbpt = bpt[i] - bpt[i - 1]
        gain_per_1k = dbpt / dv * 1000
        table.append({"vocab": int(vocabs[i]), "gain_per_1k_slots": float(gain_per_1k)})
        if gain_per_1k < tolerance and vocabs[i] > 2000:
            return int(vocabs[i]), table
    return (int(vocabs[-1]) if len(vocabs) else None), table


def main():
    summary = {}
    for lang in ("en", "hi", "ar"):
        recs = dedupe_by_vocab(results["sweep"][lang])
        fk = fertility_knee(recs)
        zs = zipf_stability_point(recs)
        up, up_val = utilisation_peak(recs)
        mby, table = marginal_byte_yield(recs)

        summary[lang] = {
            "n_points": len(recs),
            "vocab_range": [recs[0]["actual_vocab"], recs[-1]["actual_vocab"]],
            "fertility_knee_vocab": fk,
            "zipf_stability_vocab": zs,
            "utilisation_peak_vocab": up,
            "utilisation_peak_value": up_val,
            "marginal_yield_sweetspot_vocab": mby,
            "marginal_yield_table": table,
            "candidates_agree_within_2x": None,
        }
        cands = [v for v in (fk, zs, up, mby) if v]
        if len(cands) >= 2:
            summary[lang]["candidates_agree_within_2x"] = bool(max(cands) <= 2 * min(cands))

        print(f"[{lang}] fertility-knee={fk}  zipf-stability={zs}  "
              f"utilisation-peak={up} ({up_val:.1%})  marginal-yield={mby}")

    with open(os.path.join(OUT, "sweetspot_results.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("\nWrote out/sweetspot_results.json")


if __name__ == "__main__":
    main()
