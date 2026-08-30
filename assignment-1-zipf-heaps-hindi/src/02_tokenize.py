#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_tokenize.py
==============
Devanagari-aware tokenisation + frequency counting for the Hindi corpus.

Design notes
------------
* Hindi is written in Devanagari (U+0900..U+097F). A "word" is taken to be a
  maximal run of Devanagari letters, dependent vowel signs (matras), virama,
  nukta and the internal ZWJ/ZWNJ that Devanagari uses for conjunct control.
* The danda (।) and double danda (॥) are sentence punctuation, NOT letters,
  so they are excluded even though they sit inside the Devanagari block.
* Devanagari digits (०-९) and Latin digits are mapped to a single NUM token
  when --fold-numbers is given; by default they are kept, because how you
  treat numerals is itself one of the Zipf edge cases we test later.
* Latin-script runs (English words that appear in Hindi Wikipedia/news) are
  kept as separate tokens and can be filtered out downstream.

Outputs (in out/):
  tokens.txt          one token per line, corpus order  (used by Heaps' law)
  freq_surface.tsv    rank <TAB> token <TAB> count      (used by Zipf's law)
  corpus_stats.json   headline counts
"""

import argparse
import json
import os
import random
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.abspath(os.path.join(HERE, "..", "data"))
OUT = os.path.abspath(os.path.join(HERE, "..", "out"))
os.makedirs(OUT, exist_ok=True)

CORPUS = os.path.join(DATA, "corpus_hi.txt")

# Devanagari letters + matras + virama + nukta + avagraha, plus ZWJ/ZWNJ.
# Explicitly EXCLUDES danda U+0964, double danda U+0965 and the Devanagari
# digits U+0966..U+096F (handled separately).
DEV_WORD = r"[ँ-ःअ-हऺ-ॏ॑-ॗक़-ॣ॰-ॿ‌‍]+"
LATIN_WORD = r"[A-Za-z]+(?:['’][A-Za-z]+)*"
NUMBER = r"[0-9०-९]+(?:[.,][0-9०-९]+)*"

TOKEN_RE = re.compile(f"{DEV_WORD}|{LATIN_WORD}|{NUMBER}")
DEV_ONLY_RE = re.compile(f"^{DEV_WORD}$")
NUM_RE = re.compile(f"^{NUMBER}$")


def tokenize(text, fold_numbers=False, devanagari_only=False):
    """Return the list of word tokens in `text`."""
    toks = TOKEN_RE.findall(text)
    out = []
    for t in toks:
        if NUM_RE.match(t):
            if devanagari_only:
                continue
            out.append("<NUM>" if fold_numbers else t)
        elif DEV_ONLY_RE.match(t):
            out.append(t)
        else:                                   # Latin-script token
            if devanagari_only:
                continue
            out.append(t.lower())
    return out


def stream_tokens(path, shuffle_lines=True, seed=20260823, **kw):
    """
    Yield the corpus token stream.

    `shuffle_lines` matters for Heaps' Law, not for Zipf's. The corpus file is
    written source-by-source (newswire, then Wikipedia), so reading it in file
    order makes vocabulary arrive in genre-shaped bursts and puts a spurious
    kink in V(N). Shuffling whole sentences with a fixed seed restores the
    i.i.d. sampling that Heaps' Law assumes, and leaves every frequency count
    - and therefore every Zipf result - bit-for-bit identical.
    """
    lines = open(path, encoding="utf-8").read().split("\n")
    if shuffle_lines:
        random.Random(seed).shuffle(lines)
    for line in lines:
        for t in tokenize(line, **kw):
            yield t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=CORPUS)
    ap.add_argument("--fold-numbers", action="store_true")
    ap.add_argument("--devanagari-only", action="store_true", default=True)
    ap.add_argument("--no-shuffle", action="store_true",
                    help="read the corpus in file order (shows the genre kink)")
    args = ap.parse_args()

    toks = list(stream_tokens(args.corpus,
                              shuffle_lines=not args.no_shuffle,
                              fold_numbers=args.fold_numbers,
                              devanagari_only=args.devanagari_only))
    counts = Counter(toks)

    with open(os.path.join(OUT, "tokens.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(toks))

    ranked = counts.most_common()
    with open(os.path.join(OUT, "freq_surface.tsv"), "w", encoding="utf-8") as fh:
        fh.write("rank\ttoken\tcount\n")
        for i, (w, c) in enumerate(ranked, 1):
            fh.write(f"{i}\t{w}\t{c}\n")

    N, V = len(toks), len(counts)
    hapax = sum(1 for c in counts.values() if c == 1)
    stats = {
        "tokens_N": N,
        "types_V": V,
        "type_token_ratio": V / N,
        "hapax_legomena": hapax,
        "hapax_fraction_of_V": hapax / V,
        "top10": ranked[:10],
        "coverage_top100_pct": 100 * sum(c for _, c in ranked[:100]) / N,
        "coverage_top1000_pct": 100 * sum(c for _, c in ranked[:1000]) / N,
    }
    json.dump(stats, open(os.path.join(OUT, "corpus_stats.json"), "w"),
              ensure_ascii=False, indent=2)

    print(f"tokens N = {N:,}")
    print(f"types  V = {V:,}")
    print(f"TTR      = {V/N:.4f}")
    print(f"hapax    = {hapax:,} ({100*hapax/V:.1f}% of vocabulary)")
    print(f"top-100 words cover {stats['coverage_top100_pct']:.1f}% of tokens")
    print("top 10:", ranked[:10])


if __name__ == "__main__":
    main()
