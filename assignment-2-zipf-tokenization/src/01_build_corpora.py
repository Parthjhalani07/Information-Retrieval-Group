#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_build_corpora.py
====================
Builds parallel-scale study corpora for English, Hindi and Arabic.

Same acquisition strategy as Assignment 1 (dumps.wikimedia.org is not
reachable from this environment -> mirrored UD treebanks + XQuAD Wikipedia
paragraphs, all naturally-occurring prose, redistributed on GitHub).

  English  : UD_English-EWT (news/blogs/reviews/email) + UD_English-GUM
             (mixed genre) + XQuAD-en (Wikipedia paragraphs)
  Hindi    : re-used verbatim from Assignment 1 (data/corpus_hi.txt copied in)
  Arabic   : UD_Arabic-PADT (news) + UD_Arabic-PUD (news+wiki) + XQuAD-ar
             (Wikipedia paragraphs)

Output: data/corpus_<lang>.txt  (UTF-8, one sentence/paragraph per line)
"""
import json
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.abspath(os.path.join(HERE, "..", "data"))
os.makedirs(DATA, exist_ok=True)

SOURCES = {
    "en": [
        ("en_ewt-train.conllu", "conllu",
         "https://raw.githubusercontent.com/UniversalDependencies/UD_English-EWT/master/en_ewt-ud-train.conllu"),
        ("en_ewt-dev.conllu", "conllu",
         "https://raw.githubusercontent.com/UniversalDependencies/UD_English-EWT/master/en_ewt-ud-dev.conllu"),
        ("en_ewt-test.conllu", "conllu",
         "https://raw.githubusercontent.com/UniversalDependencies/UD_English-EWT/master/en_ewt-ud-test.conllu"),
        ("en_gum-train.conllu", "conllu",
         "https://raw.githubusercontent.com/UniversalDependencies/UD_English-GUM/master/en_gum-ud-train.conllu"),
        ("en_gum-dev.conllu", "conllu",
         "https://raw.githubusercontent.com/UniversalDependencies/UD_English-GUM/master/en_gum-ud-dev.conllu"),
        ("xquad.en.json", "xquad",
         "https://raw.githubusercontent.com/google-deepmind/xquad/master/xquad.en.json"),
    ],
    "ar": [
        ("ar_padt-train.conllu", "conllu",
         "https://raw.githubusercontent.com/UniversalDependencies/UD_Arabic-PADT/master/ar_padt-ud-train.conllu"),
        ("ar_padt-dev.conllu", "conllu",
         "https://raw.githubusercontent.com/UniversalDependencies/UD_Arabic-PADT/master/ar_padt-ud-dev.conllu"),
        ("ar_padt-test.conllu", "conllu",
         "https://raw.githubusercontent.com/UniversalDependencies/UD_Arabic-PADT/master/ar_padt-ud-test.conllu"),
        ("ar_pud-test.conllu", "conllu",
         "https://raw.githubusercontent.com/UniversalDependencies/UD_Arabic-PUD/master/ar_pud-ud-test.conllu"),
        ("xquad.ar.json", "xquad",
         "https://raw.githubusercontent.com/google-deepmind/xquad/master/xquad.ar.json"),
    ],
}


def _download(name, url):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        print(f"[fetch] {name}")
        urllib.request.urlretrieve(url, path)
    return path


def _conllu_sentences(path):
    for line in open(path, encoding="utf-8"):
        if line.startswith("# text = "):
            yield line[len("# text = "):].strip()


def _xquad_paragraphs(path):
    data = json.load(open(path, encoding="utf-8"))
    seen = set()
    for art in data["data"]:
        for para in art["paragraphs"]:
            ctx = para["context"].strip()
            if ctx not in seen:
                seen.add(ctx)
                yield ctx


def build(lang):
    out_path = os.path.join(DATA, f"corpus_{lang}.txt")
    n = 0
    with open(out_path, "w", encoding="utf-8") as out:
        for name, kind, url in SOURCES[lang]:
            path = _download(name, url)
            gen = _xquad_paragraphs(path) if kind == "xquad" else _conllu_sentences(path)
            c = 0
            for s in gen:
                if s:
                    out.write(s + "\n")
                    c += 1
            print(f"[{lang}] {name}: {c:,} segments")
            n += c
    print(f"[{lang}] TOTAL segments: {n:,} -> {out_path}")
    return n


if __name__ == "__main__":
    for lang in ("en", "ar"):
        build(lang)

    # Hindi: reuse Assignment 1's corpus verbatim (same sources, same method)
    hi_src = "/home/claude/a1/zipf/data/corpus_hi.txt"
    hi_dst = os.path.join(DATA, "corpus_hi.txt")
    if os.path.exists(hi_src) and not os.path.exists(hi_dst):
        with open(hi_src, encoding="utf-8") as f, open(hi_dst, "w", encoding="utf-8") as g:
            g.write(f.read())
        print(f"[hi] reused Assignment 1 corpus -> {hi_dst}")
