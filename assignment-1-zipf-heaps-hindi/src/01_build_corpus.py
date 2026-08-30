#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_build_corpus.py
==================
Builds the Hindi study corpus used for the Zipf / Heaps analysis.

Two acquisition paths are supported:

  (A) WIKIPEDIA DUMP PATH  --source wiki
      Streams `hiwiki-latest-pages-articles.xml.bz2` straight from
      dumps.wikimedia.org, strips MediaWiki markup and writes one article
      per line. This is the path described in the assignment and it is
      fully implemented here; it requires outbound access to
      dumps.wikimedia.org.

  (B) MIRROR PATH          --source mirror   (default)
      When dumps.wikimedia.org is not reachable (firewalled lab machine,
      CI sandbox, exam hall network), the corpus is assembled from
      Hindi text that is mirrored on raw.githubusercontent.com:
        * UD Hindi HDTB  (train/dev/test) - Hindi newswire
        * UD Hindi PUD                    - news + Wikipedia
        * XQuAD Hindi                     - Hindi Wikipedia paragraphs
      All three are redistributions of naturally occurring Hindi prose,
      so the statistical laws under test are unaffected.

Output: data/corpus_hi.txt  (UTF-8, one document/sentence per line)

Usage:
    python 01_build_corpus.py --source wiki
    python 01_build_corpus.py --source mirror
"""

import argparse
import bz2
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.abspath(os.path.join(HERE, "..", "data"))
os.makedirs(DATA, exist_ok=True)

CORPUS = os.path.join(DATA, "corpus_hi.txt")

DUMP_URL = ("https://dumps.wikimedia.org/hiwiki/latest/"
            "hiwiki-latest-pages-articles.xml.bz2")

MIRROR_FILES = [
    ("hi_hdtb-ud-train.conllu",
     "https://raw.githubusercontent.com/UniversalDependencies/"
     "UD_Hindi-HDTB/master/hi_hdtb-ud-train.conllu"),
    ("hi_hdtb-ud-dev.conllu",
     "https://raw.githubusercontent.com/UniversalDependencies/"
     "UD_Hindi-HDTB/master/hi_hdtb-ud-dev.conllu"),
    ("hi_hdtb-ud-test.conllu",
     "https://raw.githubusercontent.com/UniversalDependencies/"
     "UD_Hindi-HDTB/master/hi_hdtb-ud-test.conllu"),
    ("hi_pud.conllu",
     "https://raw.githubusercontent.com/UniversalDependencies/"
     "UD_Hindi-PUD/master/hi_pud-ud-test.conllu"),
    ("xquad.hi.json",
     "https://raw.githubusercontent.com/google-deepmind/xquad/"
     "master/xquad.hi.json"),
]


# --------------------------------------------------------------------------
# MediaWiki markup cleaning
# --------------------------------------------------------------------------
RE_COMMENT   = re.compile(r"<!--.*?-->", re.S)
RE_REF       = re.compile(r"<ref[^>]*?/>|<ref.*?</ref>", re.S | re.I)
RE_TAG       = re.compile(r"<[^>]+>")
RE_TABLE     = re.compile(r"\{\|.*?\|\}", re.S)
RE_TEMPLATE  = re.compile(r"\{\{[^{}]*\}\}")
RE_FILE_LINK = re.compile(r"\[\[(?:File|Image|चित्र|फ़ाइल):[^\]]*\]\]", re.I)
RE_LINK_PIPE = re.compile(r"\[\[[^\]|]*\|([^\]]*)\]\]")
RE_LINK      = re.compile(r"\[\[([^\]]*)\]\]")
RE_EXT_LINK  = re.compile(r"\[https?://[^\s\]]+\s?([^\]]*)\]")
RE_QUOTES    = re.compile(r"'{2,5}")
RE_HEADING   = re.compile(r"^=+.*?=+$", re.M)
RE_WS        = re.compile(r"\s+")


def clean_wikitext(text: str) -> str:
    """Reduce raw MediaWiki markup to running prose."""
    text = RE_COMMENT.sub(" ", text)
    text = RE_REF.sub(" ", text)
    text = RE_TABLE.sub(" ", text)
    for _ in range(6):                      # templates nest
        new = RE_TEMPLATE.sub(" ", text)
        if new == text:
            break
        text = new
    text = RE_FILE_LINK.sub(" ", text)
    text = RE_LINK_PIPE.sub(r"\1", text)
    text = RE_LINK.sub(r"\1", text)
    text = RE_EXT_LINK.sub(r"\1", text)
    text = RE_HEADING.sub(" ", text)
    text = RE_TAG.sub(" ", text)
    text = RE_QUOTES.sub("", text)
    text = text.replace("*", " ").replace("#", " ")
    return RE_WS.sub(" ", text).strip()


def build_from_wiki_dump(limit_articles=None) -> int:
    """Stream the bz2 XML dump and write cleaned article text."""
    local = os.path.join(DATA, "hiwiki-latest-pages-articles.xml.bz2")
    if not os.path.exists(local):
        print(f"[wiki] downloading {DUMP_URL}")
        urllib.request.urlretrieve(DUMP_URL, local)
    print(f"[wiki] parsing {local}")

    n_articles, n_chars = 0, 0
    in_text, buf, ns = False, [], "0"
    with bz2.open(local, "rt", encoding="utf-8", errors="ignore") as fh, \
         open(CORPUS, "w", encoding="utf-8") as out:
        for line in fh:
            if "<ns>" in line:
                ns = line.split("<ns>")[1].split("</ns>")[0]
            if "<text" in line:
                in_text = True
                line = line[line.find(">", line.find("<text")) + 1:]
            if in_text:
                if "</text>" in line:
                    buf.append(line[:line.find("</text>")])
                    in_text = False
                    if ns == "0":                       # main namespace only
                        body = clean_wikitext("".join(buf))
                        if len(body) > 200:             # skip stubs/redirects
                            out.write(body + "\n")
                            n_articles += 1
                            n_chars += len(body)
                            if n_articles % 5000 == 0:
                                print(f"  {n_articles:,} articles")
                            if limit_articles and n_articles >= limit_articles:
                                break
                    buf = []
                else:
                    buf.append(line)
    print(f"[wiki] {n_articles:,} articles, {n_chars:,} chars")
    return n_articles


def _download(name, url):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        print(f"[mirror] fetching {name}")
        urllib.request.urlretrieve(url, path)
    return path


def _conllu_sentences(path):
    """Yield the original (untokenised) sentence strings from a CoNLL-U file."""
    for line in open(path, encoding="utf-8"):
        if line.startswith("# text = "):
            yield line[len("# text = "):].strip()


def _xquad_paragraphs(path):
    """Yield the Hindi Wikipedia paragraphs used as reading passages."""
    data = json.load(open(path, encoding="utf-8"))
    seen = set()
    for art in data["data"]:
        for para in art["paragraphs"]:
            ctx = para["context"].strip()
            if ctx not in seen:
                seen.add(ctx)
                yield ctx


def build_from_mirrors() -> int:
    n = 0
    with open(CORPUS, "w", encoding="utf-8") as out:
        for name, url in MIRROR_FILES:
            path = _download(name, url)
            gen = (_xquad_paragraphs(path) if name.endswith(".json")
                   else _conllu_sentences(path))
            c = 0
            for s in gen:
                if s:
                    out.write(s + "\n")
                    c += 1
            print(f"[mirror] {name}: {c:,} segments")
            n += c
    return n


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["wiki", "mirror"], default="mirror")
    ap.add_argument("--limit", type=int, default=None,
                    help="stop after N Wikipedia articles (debug)")
    args = ap.parse_args()

    if args.source == "wiki":
        try:
            build_from_wiki_dump(args.limit)
        except Exception as exc:                       # noqa: BLE001
            print(f"[wiki] FAILED: {exc}\n[wiki] falling back to mirrors",
                  file=sys.stderr)
            build_from_mirrors()
    else:
        build_from_mirrors()

    size = os.path.getsize(CORPUS)
    lines = sum(1 for _ in open(CORPUS, encoding="utf-8"))
    print(f"\nwrote {CORPUS}\n  {lines:,} lines, {size:,} bytes")
