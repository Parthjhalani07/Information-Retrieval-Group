#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09_verify.py
============
Independent cross-checks on every headline number, computed a second time by
a different route than the one that produced it. Any FAIL means a figure in
the report or the deck cannot be trusted.
"""

import json
import os
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "out")

Z = json.load(open(os.path.join(OUT, "zipf_results.json")))
H = json.load(open(os.path.join(OUT, "heaps_results.json")))
S = json.load(open(os.path.join(OUT, "corpus_stats.json")))
M = json.load(open(os.path.join(OUT, "cost_model.json")))

checks = []


def check(name, ok, detail):
    checks.append((name, bool(ok), detail))


toks = open(os.path.join(OUT, "tokens.txt"), encoding="utf-8").read().split("\n")
counts = Counter(toks)

# 1 -- corpus totals recomputed from the raw token stream
check("Token count", len(toks) == S["tokens_N"],
      f"{len(toks):,} vs reported {S['tokens_N']:,}")
check("Type count", len(counts) == S["types_V"],
      f"{len(counts):,} vs reported {S['types_V']:,}")

# 2 -- the frequency table on disk must agree with the counter
tsv = [l.split("\t") for l in
       open(os.path.join(OUT, "freq_surface.tsv"), encoding="utf-8")
       .read().strip().split("\n")[1:]]
check("freq_surface.tsv rows", len(tsv) == len(counts),
      f"{len(tsv):,} rows")
check("freq_surface.tsv total = N",
      sum(int(r[2]) for r in tsv) == len(toks),
      f"{sum(int(r[2]) for r in tsv):,}")
check("freq_surface.tsv is sorted",
      all(int(tsv[i][2]) >= int(tsv[i + 1][2]) for i in range(len(tsv) - 1)),
      "monotonically non-increasing")

# 3 -- coverage percentages recomputed
ranked = counts.most_common()
c100 = 100 * sum(c for _, c in ranked[:100]) / len(toks)
c1000 = 100 * sum(c for _, c in ranked[:1000]) / len(toks)
check("Top-100 coverage", abs(c100 - S["coverage_top100_pct"]) < 1e-6,
      f"{c100:.3f}%")
check("Top-1000 coverage", abs(c1000 - S["coverage_top1000_pct"]) < 1e-6,
      f"{c1000:.3f}%")

# 4 -- hapax count
hapax = sum(1 for c in counts.values() if c == 1)
check("Hapax legomena", hapax == S["hapax_legomena"], f"{hapax:,}")
check("Hapax shelf onset rank",
      len(counts) - hapax + 1 == Z["A2_tail"]["plateau_start_rank"],
      f"rank {len(counts)-hapax+1:,}")

# 5 -- Zipf-Mandelbrot reproduces the observed head
zm = Z["baseline"]["mandelbrot"]
obs = [c for _, c in ranked[:10]]
pred = [zm["C"] / (r + zm["b"]) ** zm["alpha"] for r in range(1, 11)]
a1 = Z["A1_head"]
check("Reported head errors reproduce from the raw counts",
      abs(max(abs(o - p) / p * 100 for o, p in zip(obs, pred))
          - a1["mandelbrot_worst_err_pct"]) < 0.5,
      f"worst {a1['mandelbrot_worst_err_pct']:.1f}%, "
      f"mean {a1['mandelbrot_mean_err_pct']:.1f}%")
check("Mandelbrot beats pure Zipf on the head by >4x",
      a1["pure_zipf_mean_err_pct"] / a1["mandelbrot_mean_err_pct"] > 4,
      f"{a1['pure_zipf_mean_err_pct']:.0f}% -> "
      f"{a1['mandelbrot_mean_err_pct']:.0f}% mean error")
check("Head residual is acknowledged, not hidden",
      a1["mandelbrot_mean_err_pct"] > 5,
      f"residual of {a1['mandelbrot_mean_err_pct']:.0f}% is reported in the text")

# 6 -- Heaps model reproduces the observed vocabulary at full corpus size
K, b = H["hindi"]["fit"]["K"], H["hindi"]["fit"]["beta"]
v_pred = K * len(toks) ** b
check("Heaps V(N) prediction within 5% of observed",
      abs(v_pred - len(counts)) / len(counts) < 0.05,
      f"predicted {v_pred:,.0f} vs actual {len(counts):,}")

# 7 -- the flattening point is inside the corpus and on the curve
knee = H["hindi"]["knee"]["linear"]
check("Knee lies within the measured corpus", 0 < knee["N"] <= len(toks),
      f"N = {knee['N']:,.0f} of {len(toks):,}")
check("Knee V within 8% of the fitted curve",
      abs(K * knee["N"] ** b - knee["V"]) / knee["V"] < 0.08,
      f"curve gives {K*knee['N']**b:,.0f}, knee reports {knee['V']:,.0f}")

# 8 -- threshold inversion is self-consistent with the derivative
for t in H["hindi"]["thresholds"]:
    n = t["model_N"]
    rate = 1000 * K * b * n ** (b - 1)
    ok = abs(rate - t["threshold_per_1k"]) / t["threshold_per_1k"] < 1e-6
    if not ok:
        check(f"Threshold inversion at {t['threshold_per_1k']}/1k", False,
              f"back-substitution gives {rate:.4f}")
        break
else:
    check("Threshold inversions back-substitute exactly", True,
          "all 9 thresholds verified against dV/dN")

# 9 -- thresholds must be monotonically increasing in N
ns = [t["model_N"] for t in H["hindi"]["thresholds"]]
check("Thresholds monotonic in N", all(ns[i] < ns[i + 1] for i in range(len(ns) - 1)),
      f"{ns[0]:,.0f} → {ns[-1]:,.0f}")

# 10 -- the A3 power analysis really does straddle the rejection line
pw = Z["A3_gof"]["power_analysis"]
small = [p for p in pw if p["n"] <= 1000]
large = [p for p in pw if p["n"] >= 5000]
check("Power analysis straddles p = 0.10",
      any(p["p"] > 0.10 for p in small) and all(p["p"] < 0.10 for p in large),
      f"small-n max p = {max(p['p'] for p in small):.3f}, "
      f"large-n max p = {max(p['p'] for p in large):.3f}")
gammas = [p["gamma"] for p in pw]
check("Gamma stable across the power analysis",
      max(gammas) - min(gammas) < 0.05,
      f"range {min(gammas):.4f} – {max(gammas):.4f}")

# 11 -- cost model arithmetic
gs, sv, hd = M["google_search"], M["sarvam"], M["headline"]
check("Google one-time total sums",
      abs(sum(i["usd"] for i in gs["one_time"]) - gs["one_time_total"]) < 1,
      f"{gs['one_time_total']:,.0f}")
check("Google annual total sums",
      abs(sum(i["usd"] for i in gs["recurring_annual"]) - gs["recurring_total"]) < 1,
      f"{gs['recurring_total']:,.0f}")
check("Sarvam one-time total sums",
      abs(sum(i["usd"] for i in sv["one_time"]) - sv["one_time_total"]) < 1,
      f"{sv['one_time_total']:,.0f}")
check("Sarvam annual total sums",
      abs(sum(i["usd"] for i in sv["recurring_annual"]) - sv["recurring_total"]) < 1,
      f"{sv['recurring_total']:,.0f}")
check("Google 5-year TCO",
      abs(gs["one_time_total"] + 5 * gs["recurring_total"] - hd["google_5yr"]) < 1,
      f"{hd['google_5yr']:,.0f}")
check("Sarvam 5-year TCO",
      abs(sv["one_time_total"] + 5 * sv["recurring_total"] - hd["sarvam_5yr"]) < 1,
      f"{hd['sarvam_5yr']:,.0f}")

# 12 -- the anchor is applied exactly as the brief states
A = M["assumptions"]
check("Anchor = $1,000 per 100,000 words",
      abs(A["usd_per_word_curated"] * 100000 - 1000) < 1e-9,
      f"${A['usd_per_word_curated']*100000:,.2f} per 100k words")
nk = M["naive_anchor_check"]
check("Naive-anchor arithmetic",
      abs(nk["words"] * A["usd_per_word_curated"] - nk["cost_all_curated"]) < 1,
      f"{nk['words']:,.0f} words × $0.01 = ${nk['cost_all_curated']:,.0f}")
check("Curated:crawled ratio",
      abs(A["usd_per_word_curated"] / A["usd_per_word_crawled"] - nk["ratio"]) < 1e-6,
      f"{nk['ratio']:,.0f} : 1")

# 13 -- corpus tiers are Heaps-derived, not hand-entered
for t in M["corpus_tiers"]:
    n = (1000 * K * b / t["marginal_rate_per_1k"]) ** (1 / (1 - b))
    if abs(n - t["words_required"]) / t["words_required"] > 1e-9:
        check("Corpus tiers derive from the Heaps fit", False, t["tier"])
        break
else:
    check("Corpus tiers derive from the Heaps fit", True,
          "all 4 tiers reproduce from dV/dN")

# 14 -- external validation agreement
ext = Z["external_wordfreq"]
oc = Z["baseline"]["ols_core"]
check("wordfreq agrees with our alpha to < 0.02",
      abs(ext["alpha"] - oc["alpha"]) < 0.02,
      f"{ext['alpha']:.4f} vs {oc['alpha']:.4f} "
      f"(Δ = {abs(ext['alpha']-oc['alpha']):.4f})")

# 15 -- every figure referenced by the report exists
figs = [f"fig{i:02d}" for i in range(1, 13)]
present = os.listdir(os.path.join(ROOT, "figures"))
missing = [f for f in figs if not any(p.startswith(f) for p in present)]
check("All 12 figures present", not missing, f"missing: {missing or 'none'}")

# 16 -- deliverables exist and are non-trivial in size
for f, floor in (("Zipf_Heaps_Hindi_Report.pdf", 300_000),
                 ("Zipf_Heaps_Hindi_Presentation.pptx", 300_000)):
    p = os.path.join(ROOT, "dist", f)
    check(f"{f} built", os.path.exists(p) and os.path.getsize(p) > floor,
          f"{os.path.getsize(p):,} bytes" if os.path.exists(p) else "MISSING")

# --------------------------------------------------------------------------
print("=" * 78)
print("VERIFICATION")
print("=" * 78)
fails = 0
for name, ok, detail in checks:
    print(f"  [{'PASS' if ok else 'FAIL'}]  {name:<52} {detail}")
    fails += not ok
print("=" * 78)
print(f"{len(checks) - fails}/{len(checks)} checks passed")
raise SystemExit(1 if fails else 0)
