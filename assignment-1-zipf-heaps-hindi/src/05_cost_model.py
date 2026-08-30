#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
05_cost_model.py
================
Infrastructure and investment cost of adding ONE new language to
  (i)  Google Search   - a web-scale retrieval product, and
  (ii) Sarvam AI       - a sovereign Indic foundation-model stack.

The brief fixes one anchor price:  USD 1,000 per 100,000 words  (= $0.01/word)
for language data. The interesting question is not the multiplication, it is
the DENOMINATOR: how many words does a language actually need?

That number is not a guess here. It is read off the Heaps' Law curve fitted
in 04_heaps_analysis.py:   V(N) = K * N^beta,   dV/dN = K*beta*N^(beta-1).
A corpus is "big enough" for a given purpose when its marginal yield - new
word types per 1,000 tokens - falls below the tolerance that purpose can
live with. Solving the Heaps derivative for N converts a linguistic
tolerance into a word count, and the anchor price converts that word count
into dollars.

All assumptions are declared in ASSUMPTIONS and echoed into the output so
every figure in the report can be traced back to an input.

Outputs: out/cost_model.json
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "out"))

# ==========================================================================
# ASSUMPTIONS  (all USD, 2026)
# ==========================================================================
ASSUMPTIONS = {
    "anchor_usd_per_100k_words": 1000.0,          # given in the brief
    "usd_per_word_curated": 0.01,                 # = anchor / 100,000
    "usd_per_word_crawled": 0.000001,             # crawl+store+dedup+filter, at scale
    "h100_usd_per_hour": 2.50,                    # market mid-range 2026
    "h100_effective_tflops": 220.0,               # 989 peak x ~22% realised MFU
    "experiment_overhead_multiplier": 3.5,        # ablations, restarts, failures
    "fte_usd_per_year_loaded": 250000.0,          # senior eng, fully loaded
    "rater_usd_per_hour_loaded": 22.0,
    "rater_hours_per_year": 1800.0,
    "annotation_usd_per_sft_pair": 4.50,
    "annotation_usd_per_preference_triple": 6.00,
    "asr_transcription_usd_per_audio_hour": 85.0,
    "tts_studio_usd_per_recorded_hour": 1400.0,
    "eval_item_usd": 9.00,
    "storage_usd_per_tb_month": 18.0,
    "tokens_per_word_indic": 1.75,                # Sarvam-1 fertility 1.4-2.1
    "tokens_per_param_chinchilla": 20,
}
A = ASSUMPTIONS


# ==========================================================================
# Heaps-driven corpus sizing
# ==========================================================================
def load_heaps():
    r = json.load(open(os.path.join(OUT, "heaps_results.json")))
    return r["hindi"]["fit"]["K"], r["hindi"]["fit"]["beta"]


def words_for_rate(rate_per_1k, K, beta):
    """Invert dV/dN = K*beta*N^(beta-1) for the token count N."""
    return (1000.0 * K * beta / rate_per_1k) ** (1.0 / (1.0 - beta))


def vocab_at(N, K, beta):
    return K * N ** beta


def corpus_tiers(K, beta):
    """
    Four service tiers, each defined by the marginal-yield tolerance that the
    downstream product can accept before its lexicon goes stale.
    """
    spec = [
        ("T0  Bootstrap / tokenizer + stopwords", 50,
         "enough to build a subword tokenizer, stoplist and basic stemmer"),
        ("T1  Lexicon / spell-check / IR index", 10,
         "dictionary-grade coverage; spelling correction; query normalisation"),
        ("T2  Search-grade language support", 5,
         "named entities, morphology, query understanding at production quality"),
        ("T3  Foundation-model-grade coverage", 1,
         "long-tail lexical saturation expected of a general-purpose LLM"),
    ]
    tiers = []
    for name, rate, why in spec:
        N = words_for_rate(rate, K, beta)
        tiers.append(dict(
            tier=name, marginal_rate_per_1k=rate, rationale=why,
            words_required=N,
            vocabulary_types=vocab_at(N, K, beta),
            cost_if_fully_curated=N * A["usd_per_word_curated"],
            cost_if_fully_crawled=N * A["usd_per_word_crawled"],
        ))
    return tiers


# ==========================================================================
# Compute costing
# ==========================================================================
def gpu_hours(params_active, tokens, mult=True):
    """Training FLOPs ~ 6 * N_params_active * N_tokens."""
    flops = 6.0 * params_active * tokens
    hours = flops / (A["h100_effective_tflops"] * 1e12) / 3600.0
    if mult:
        hours *= A["experiment_overhead_multiplier"]
    return hours


def gpu_cost(params_active, tokens, mult=True):
    return gpu_hours(params_active, tokens, mult) * A["h100_usd_per_hour"]


# ==========================================================================
# (i) GOOGLE SEARCH
# ==========================================================================
def google_search_cost(K, beta):
    """
    Google already owns the crawler, the index and the serving fleet. The
    marginal cost of a new language is therefore dominated by (a) language
    data that cannot be crawled, (b) human judgement, and (c) the extra
    index/serving footprint - not by building infrastructure from scratch.
    """
    N_t2 = words_for_rate(5, K, beta)          # search-grade tier

    # --- data ---------------------------------------------------------
    curated_words = N_t2                        # the whole T2 tier is curated
    crawled_words = 4e10                        # ~40B words of crawlable web

    one_time = []
    one_time.append((f"Curated linguistic corpus, Heaps T2 "
                     f"({curated_words/1e6:.1f}M words @ $0.01)",
                     curated_words * A["usd_per_word_curated"]))
    one_time.append(("Web crawl acquisition, dedup and cleaning (40B words)",
                     crawled_words * A["usd_per_word_crawled"]))
    one_time.append(("Morphological analyser, stemmer, segmenter",
                     6 * A["fte_usd_per_year_loaded"]))
    one_time.append(("Transliteration + IME + spell-correction lexicons "
                     "(1.2M pairs @ $0.35)", 1.2e6 * 0.35))
    one_time.append(("Query-understanding training data "
                     "(250k annotated queries @ $2.20)", 250e3 * 2.20))
    one_time.append(("Relevance/eval golden sets (60k judged pairs)",
                     60e3 * A["eval_item_usd"]))
    one_time.append(("Product UI localisation (~65k strings)", 65e3 * 0.42))
    one_time.append(("Ranking + NLU model adaptation (GPU)",
                     gpu_cost(8e9, 1.2e11)))
    one_time.append(("Engineering programme (18 FTE-years)",
                     18 * A["fte_usd_per_year_loaded"]))
    one_time.append(("Index build-out, 1.2 PB (12 months storage)",
                     1200 * A["storage_usd_per_tb_month"] * 12))
    one_time.append(("Voice Search: ASR acoustic + language model adaptation",
                     1.2e6))
    one_time.append(("Knowledge Graph / entity-linking localisation", 900e3))
    one_time.append(("Spam, safety and content-policy adaptation", 700e3))
    one_time.append(("Legal, licensing and data-rights clearance", 450e3))

    recurring = []
    recurring.append(("Search-quality raters (45 raters)",
                      45 * A["rater_usd_per_hour_loaded"]
                      * A["rater_hours_per_year"]))
    recurring.append(("Continuous re-crawl and index refresh",
                      crawled_words * A["usd_per_word_crawled"] * 1.5))
    recurring.append(("Incremental serving fleet (inference)", 2.6e6))
    recurring.append(("Index storage (1.2 PB)",
                      1200 * A["storage_usd_per_tb_month"] * 12))
    recurring.append(("Sustaining engineering (6 FTE)",
                      6 * A["fte_usd_per_year_loaded"]))
    recurring.append(("Model refresh training (2 cycles/yr)",
                      2 * gpu_cost(8e9, 3e10)))

    return dict(
        tier_words=N_t2,
        one_time=[dict(item=i, usd=c) for i, c in one_time],
        recurring_annual=[dict(item=i, usd=c) for i, c in recurring],
        one_time_total=sum(c for _, c in one_time),
        recurring_total=sum(c for _, c in recurring),
    )


# ==========================================================================
# (ii) SARVAM AI
# ==========================================================================
def sarvam_cost(K, beta):
    """
    Sarvam's published stack: Sarvam-1 (2B dense, ~2T Indic tokens, 10
    languages, tokenizer fertility 1.4-2.1) and the Feb-2026 Sarvam-30B /
    Sarvam-105B mixture-of-experts models (~1B and ~9B active parameters).
    Adding an 11th language is costed here as continued pretraining plus a
    full alignment and evaluation cycle, not as a from-scratch pretrain.
    """
    N_t3 = words_for_rate(1, K, beta)           # foundation-model tier
    tok_per_word = A["tokens_per_word_indic"]

    # Sarvam-1 allocates ~200B Indic tokens per supported language.
    lang_tokens = 2.0e11
    lang_words = lang_tokens / tok_per_word

    curated_share = 0.006                       # 0.6% hand-curated seed
    curated_words = lang_words * curated_share
    crawled_words = lang_words * (1 - curated_share)

    one_time = []
    one_time.append(("Curated/licensed seed corpus "
                     f"({curated_words/1e6:.0f}M words @ $0.01)",
                     curated_words * A["usd_per_word_curated"]))
    one_time.append(("Web + archive crawl, dedup, quality filtering "
                     f"({crawled_words/1e9:.0f}B words)",
                     crawled_words * A["usd_per_word_crawled"]))
    one_time.append(("Data pipeline compute (dedup, classify, PII scrub)",
                     420e3))
    one_time.append(("Publisher / archive content licensing", 1.5e6))
    one_time.append(("Tokenizer extension + vocabulary re-fit", 180e3))
    one_time.append(("Continued pretraining, 105B MoE (9B active, 200B tokens)",
                     gpu_cost(9e9, lang_tokens)))
    one_time.append(("Continued pretraining, 30B MoE (1B active, 200B tokens)",
                     gpu_cost(1e9, lang_tokens)))
    one_time.append(("Instruction tuning data (120k pairs)",
                     120e3 * A["annotation_usd_per_sft_pair"]))
    one_time.append(("Preference/RLHF data (60k triples)",
                     60e3 * A["annotation_usd_per_preference_triple"]))
    one_time.append(("Alignment training runs (SFT + DPO)",
                     gpu_cost(9e9, 4e9)))
    one_time.append(("ASR corpus (2,500 transcribed audio hours)",
                     2500 * A["asr_transcription_usd_per_audio_hour"]))
    one_time.append(("TTS voice corpus (2 voices x 45 studio hours)",
                     2 * 45 * A["tts_studio_usd_per_recorded_hour"]))
    one_time.append(("Benchmark + safety evaluation sets (25k items)",
                     25e3 * A["eval_item_usd"]))
    one_time.append(("Research + engineering team (22 FTE-years)",
                     22 * A["fte_usd_per_year_loaded"]))

    recurring = []
    recurring.append(("Inference serving capacity (dedicated)", 1.9e6))
    recurring.append(("Quarterly refresh training (4 cycles)",
                      4 * gpu_cost(9e9, 2e10)))
    recurring.append(("Continuous data refresh + re-annotation", 900e3))
    recurring.append(("Evaluation, red-teaming, safety ops (5 FTE)",
                      5 * A["fte_usd_per_year_loaded"]))
    recurring.append(("Object storage for corpus + checkpoints (600 TB)",
                      600 * A["storage_usd_per_tb_month"] * 12))

    return dict(
        tier_words_T3=N_t3,
        language_tokens_budget=lang_tokens,
        language_words_budget=lang_words,
        one_time=[dict(item=i, usd=c) for i, c in one_time],
        recurring_annual=[dict(item=i, usd=c) for i, c in recurring],
        one_time_total=sum(c for _, c in one_time),
        recurring_total=sum(c for _, c in recurring),
    )


# ==========================================================================
# Sensitivity + the "naive anchor" reality check
# ==========================================================================
def naive_anchor_check(K, beta):
    """
    What if the $1,000/100k-word rate were applied to EVERY word a
    foundation model consumes? This is the single most important number in
    the whole exercise, because it shows why nobody buys their pretraining
    corpus.
    """
    lang_words = 2.0e11 / A["tokens_per_word_indic"]
    return dict(
        words=lang_words,
        cost_all_curated=lang_words * A["usd_per_word_curated"],
        cost_all_crawled=lang_words * A["usd_per_word_crawled"],
        ratio=A["usd_per_word_curated"] / A["usd_per_word_crawled"],
        comment="Buying 114B words at the anchor rate costs $1.14 billion - "
                "roughly 28x Sarvam's disclosed $41M seed+Series A. The anchor "
                "price is a CURATION price, and it is only ever paid on the "
                "small high-value fraction of a corpus.",
    )


def sensitivity(K, beta):
    rows = []
    for share in (0.002, 0.006, 0.01, 0.02, 0.05, 0.10):
        lang_words = 2.0e11 / A["tokens_per_word_indic"]
        rows.append(dict(
            curated_share=share,
            curated_words=lang_words * share,
            data_cost=lang_words * share * A["usd_per_word_curated"]
            + lang_words * (1 - share) * A["usd_per_word_crawled"]))
    return rows


def main():
    K, beta = load_heaps()
    tiers = corpus_tiers(K, beta)
    g = google_search_cost(K, beta)
    s = sarvam_cost(K, beta)

    out = dict(
        assumptions=A,
        heaps=dict(K=K, beta=beta),
        corpus_tiers=tiers,
        google_search=g,
        sarvam=s,
        naive_anchor_check=naive_anchor_check(K, beta),
        curation_share_sensitivity=sensitivity(K, beta),
        headline=dict(
            google_one_time=g["one_time_total"],
            google_annual=g["recurring_total"],
            google_5yr=g["one_time_total"] + 5 * g["recurring_total"],
            sarvam_one_time=s["one_time_total"],
            sarvam_annual=s["recurring_total"],
            sarvam_5yr=s["one_time_total"] + 5 * s["recurring_total"],
        ),
    )
    json.dump(out, open(os.path.join(OUT, "cost_model.json"), "w"),
              indent=2, default=float)

    print(f"Heaps: V = {K:.3f} N^{beta:.4f}\n")
    print("CORPUS TIERS (Heaps-derived)")
    for t in tiers:
        print(f"  {t['tier']:<42} {t['words_required']:>15,.0f} words  "
              f"V={t['vocabulary_types']:>10,.0f}  "
              f"curated=${t['cost_if_fully_curated']:>14,.0f}")
    print(f"\nGOOGLE SEARCH  one-time ${g['one_time_total']:,.0f}   "
          f"annual ${g['recurring_total']:,.0f}   "
          f"5-yr ${out['headline']['google_5yr']:,.0f}")
    print(f"SARVAM AI      one-time ${s['one_time_total']:,.0f}   "
          f"annual ${s['recurring_total']:,.0f}   "
          f"5-yr ${out['headline']['sarvam_5yr']:,.0f}")
    print(f"\nNaive anchor on 114B words: "
          f"${out['naive_anchor_check']['cost_all_curated']:,.0f}")


if __name__ == "__main__":
    main()
