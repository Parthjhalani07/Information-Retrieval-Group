#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04_tokenize_and_zipf.py
=========================
For every (language x tokenizer) pair in the manifest:
  1. Tokenize the language's corpus.
  2. Build the token rank-frequency table.
  3. Fit Zipf's law (least squares on log-log, core range) and report alpha, R^2.
  4. Record fertility (tokens/word), compression (chars/token, bytes/token),
     vocabulary utilisation (% of the trained vocab that actually appears),
     and hapax share among *used* tokens.

Output: out/token_zipf_results.json  (one record per language x tokenizer)
"""
import json
import os
import numpy as np
from collections import Counter
from tokenizers import Tokenizer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "out")

manifest = json.load(open(os.path.join(OUT, "tokenizer_manifest.json")))
word_stats = json.load(open(os.path.join(OUT, "word_stats_all.json")))

_corpus_cache = {}
def get_corpus(lang):
    if lang not in _corpus_cache:
        _corpus_cache[lang] = open(os.path.join(DATA, f"corpus_{lang}.txt"), encoding="utf-8").read()
    return _corpus_cache[lang]


def fit_zipf(freqs_sorted):
    """Least-squares fit of log(freq) ~ -alpha*log(rank) over the core range
    (rank 5 .. min(5000, V*0.9)), same window convention as Assignment 1."""
    V = len(freqs_sorted)
    lo = 5
    hi = min(5000, max(lo + 10, int(V * 0.9)))
    if V < lo + 10:
        lo, hi = 1, V
    ranks = np.arange(1, V + 1)[lo - 1:hi]
    freqs = np.array(freqs_sorted)[lo - 1:hi]
    x = np.log(ranks)
    y = np.log(freqs)
    A = np.vstack([x, np.ones_like(x)]).T
    slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]
    yhat = A @ [slope, intercept]
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {"alpha": float(-slope), "r2": float(r2), "range": [lo, hi]}


def analyse(lang, tag, path, target_vocab, actual_vocab):
    tok = Tokenizer.from_file(path)
    text = get_corpus(lang)
    encoding = tok.encode(text)
    ids = encoding.ids
    n_tokens = len(ids)
    freq = Counter(ids)
    freqs_sorted = sorted(freq.values(), reverse=True)
    zipf = fit_zipf(freqs_sorted)

    used_vocab = len(freq)
    hapax = sum(1 for c in freq.values() if c == 1)
    n_words = word_stats[lang]["tokens_N"]
    n_bytes = len(text.encode("utf-8"))
    n_chars = len(text)

    return {
        "lang": lang, "tag": tag, "target_vocab": target_vocab, "actual_vocab": actual_vocab,
        "n_tokens": n_tokens,
        "used_vocab": used_vocab,
        "vocab_utilisation": used_vocab / actual_vocab,
        "hapax_share_tokens": hapax / used_vocab if used_vocab else float("nan"),
        "fertility_tokens_per_word": n_tokens / n_words,
        "chars_per_token": n_chars / n_tokens,
        "bytes_per_token": n_bytes / n_tokens,
        "zipf_alpha": zipf["alpha"],
        "zipf_r2": zipf["r2"],
        "zipf_range": zipf["range"],
    }


def main():
    results = {"sweep": {"en": [], "hi": [], "ar": []},
               "model_style": {"en": {}, "hi": {}, "ar": {}}}

    for lang in ("en", "hi", "ar"):
        print(f"=== {lang.upper()} ===")
        for item in manifest[lang]["sweep"]:
            rec = analyse(lang, f"sweep_{item['target_vocab']}", item["path"],
                          item["target_vocab"], item["actual_vocab"])
            results["sweep"][lang].append(rec)
            print(f"  vocab={rec['actual_vocab']:>7,} fertility={rec['fertility_tokens_per_word']:.3f} "
                  f"alpha={rec['zipf_alpha']:.3f} R2={rec['zipf_r2']:.4f} "
                  f"vocab_util={rec['vocab_utilisation']:.1%}")
        for name, item in manifest[lang]["model_style"].items():
            rec = analyse(lang, name, item["path"], item["target_vocab"], item["actual_vocab"])
            results["model_style"][lang][name] = rec
            print(f"  [{name:<8}] vocab={rec['actual_vocab']:>7,} fertility={rec['fertility_tokens_per_word']:.3f} "
                  f"alpha={rec['zipf_alpha']:.3f} R2={rec['zipf_r2']:.4f}")

    with open(os.path.join(OUT, "token_zipf_results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("\nWrote out/token_zipf_results.json")


if __name__ == "__main__":
    main()
