#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_word_tokenize.py
====================
Language-aware WORD tokenisation (the baseline unit, before any subword
tokeniser touches the text) for English, Hindi and Arabic, plus basic
corpus statistics. Mirrors Assignment 1's method so the word-level Zipf
numbers here are directly comparable to the Hindi report.
"""
import json
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "out")
os.makedirs(OUT, exist_ok=True)

# Devanagari letters/matras/virama/nukta/ZWJ (same definition as Assignment 1)
RE_HI = re.compile(r"[\u0900-\u0903\u0905-\u0939\u093c-\u094d\u0951-\u0957\u0962\u0963]+")
# Arabic letters + diacritics + tatweel, excludes punctuation (U+060C etc.)
RE_AR = re.compile(r"[\u0621-\u063A\u0641-\u064A\u0660-\u0669\u064B-\u065F\u0670\u0674-\u06D3\u06D5\u0640]+")
# English: letter runs incl. internal apostrophes (don't -> one token)
RE_EN = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")

TOKENIZERS = {"en": RE_EN, "hi": RE_HI, "ar": RE_AR}


def word_tokenize(lang, text):
    return [w.lower() if lang == "en" else w for w in TOKENIZERS[lang].findall(text)]


def analyse(lang):
    path = os.path.join(DATA, f"corpus_{lang}.txt")
    text = open(path, encoding="utf-8").read()
    tokens = word_tokenize(lang, text)
    freq = Counter(tokens)
    N = len(tokens)
    V = len(freq)
    hapax = sum(1 for c in freq.values() if c == 1)
    ranked = freq.most_common()
    stats = {
        "lang": lang,
        "tokens_N": N,
        "types_V": V,
        "type_token_ratio": V / N,
        "hapax_legomena": hapax,
        "hapax_share": hapax / V,
        "top10": [{"word": w, "count": c} for w, c in ranked[:10]],
        "coverage_top100": sum(c for _, c in ranked[:100]) / N,
        "coverage_top1000": sum(c for _, c in ranked[:1000]) / N,
    }
    with open(os.path.join(OUT, f"word_stats_{lang}.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    # persist frequency table + token stream for downstream scripts
    with open(os.path.join(OUT, f"word_freq_{lang}.tsv"), "w", encoding="utf-8") as f:
        for w, c in ranked:
            f.write(f"{w}\t{c}\n")
    print(f"[{lang}] N={N:,} V={V:,} TTR={V/N:.4f} hapax%={hapax/V:.1%}")
    return stats


if __name__ == "__main__":
    all_stats = {lang: analyse(lang) for lang in ("en", "hi", "ar")}
    with open(os.path.join(OUT, "word_stats_all.json"), "w", encoding="utf-8") as f:
        json.dump(all_stats, f, ensure_ascii=False, indent=2)
