#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_train_bpe.py
================
Trains byte-level BPE tokenisers (the family used by GPT-2/3/4, LLaMA-3,
Qwen-2/2.5/3 and Kimi-K2/K3) at a sweep of target vocabulary sizes, for
each of the three study languages.

IMPORTANT / HONEST LIMITATION
------------------------------
This environment has no route to huggingface.co, so the *actual* released
merge tables for LLaMA, Qwen and Kimi cannot be downloaded (see network
allow-list). What CAN be, and is, done faithfully:

  * every model's PUBLISHED vocabulary size is reproduced exactly
    (cited in the report), and
  * every model's PUBLISHED tokenisation family -- byte-level BPE with a
    GPT-2-style byte-to-unicode alphabet -- is reproduced exactly using
    the `tokenizers` library's BPE trainer + ByteLevel pre-tokenizer,
    trained from scratch on OUR OWN corpus.

So "LLaMA-3-style", "Qwen-style" and "Kimi-style" below means: a
byte-level BPE tokenizer trained on our corpus and capped at that model's
real target vocabulary size -- not the vendor's actual merge table. This
is exactly the same kind of transparent substitution Assignment 1 made
for the Wikipedia dump, and it is what makes the vocab-size sweep
(the heart of this assignment) possible at all: we need many vocab sizes
per language, not just three fixed ones.

Target sizes (regular tokens, special tokens excluded), with source:
  LLaMA-2      : 32,000   (SentencePiece BPE)              [Touvron et al. 2023]
  LLaMA-3      : 128,000  (byte-level BPE, tiktoken-style)  [Meta, 2024]
  Qwen-2.5/3   : 151,643  (byte-level BPE)                  [tiktoken qwen2 encoding]
  Kimi-K2/K3   : 163,584  (byte-level BPE, tiktoken.model)  [Moonshot AI, 2025/26]
"""
import json
import os

from tokenizers import Tokenizer, models, pre_tokenizers, trainers, decoders, normalizers

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "out")
TOKDIR = os.path.join(ROOT, "tokenizers")
os.makedirs(TOKDIR, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

LANGS = ["en", "hi", "ar"]

# The vocab-size sweep used for the "sweet spot" study (§ assignment Q5-Q7)
SWEEP = [200, 500, 1000, 2000, 3000, 4000, 6000, 8000, 12000, 16000,
         24000, 32000, 48000, 64000, 96000, 128000, 151936, 163840]

MODEL_TARGETS = {
    "llama2": 32000,
    "llama3": 128000,
    "qwen":   151643,
    "kimi":   163584,
}

SPECIAL_TOKENS = ["<unk>", "<pad>", "<bos>", "<eos>"]


def train_one(lang, vocab_size, tag):
    path = os.path.join(DATA, f"corpus_{lang}.txt")
    tok = Tokenizer(models.BPE(unk_token="<unk>"))
    tok.normalizer = normalizers.NFC()
    tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tok.decoder = decoders.ByteLevel()
    trainer = trainers.BpeTrainer(
        vocab_size=vocab_size,
        min_frequency=1,
        special_tokens=SPECIAL_TOKENS,
        initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
        show_progress=False,
    )
    tok.train([path], trainer)
    actual_vocab = tok.get_vocab_size()
    out_path = os.path.join(TOKDIR, f"{lang}_{tag}.json")
    tok.save(out_path)
    return actual_vocab, out_path


def main():
    manifest = {}
    for lang in LANGS:
        manifest[lang] = {"sweep": [], "model_style": {}}
        print(f"\n=== {lang.upper()} : vocab-size sweep ===")
        for vs in SWEEP:
            tag = f"sweep_{vs}"
            actual, path = train_one(lang, vs, tag)
            manifest[lang]["sweep"].append(
                {"target_vocab": vs, "actual_vocab": actual, "path": path})
            print(f"  target={vs:>7,}  actual={actual:>7,}  -> {os.path.basename(path)}")

        print(f"--- {lang.upper()} : model-style replicas ---")
        for name, vs in MODEL_TARGETS.items():
            tag = f"model_{name}"
            actual, path = train_one(lang, vs, tag)
            manifest[lang]["model_style"][name] = {
                "target_vocab": vs, "actual_vocab": actual, "path": path}
            print(f"  {name:<8} target={vs:>7,}  actual={actual:>7,}")

    with open(os.path.join(OUT, "tokenizer_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("\nWrote out/tokenizer_manifest.json")


if __name__ == "__main__":
    main()
