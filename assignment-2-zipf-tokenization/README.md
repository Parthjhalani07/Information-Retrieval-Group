# Tokens, Not Words: Zipf's Law Under the Tokenizer

Assignment 2 (NLP) — companion study to *Zipf, Heaps and the Price of a Language*.

Investigates whether **tokens** (not words) obey Zipf's law across English, Hindi and Arabic;
compares the vocabulary size and tokenisation strategy of the LLaMA, Qwen and Kimi model
families; and asks whether a "sweet spot" vocabulary size exists for training a subword
tokenizer, and whether it can be found algorithmically.

**Report:** [`dist/Zipf_Tokenization_Report.pdf`](dist/Zipf_Tokenization_Report.pdf)
**Slides:** [`dist/Zipf_Tokenization_Presentation.pptx`](dist/Zipf_Tokenization_Presentation.pptx)

## Headline results

| Question | Answer |
|---|---|
| Do tokens obey Zipf's law? | Yes, and better than words in the mid-vocabulary band (R² up to 0.999) — but the fit degrades sharply at near-character vocab sizes and drifts mildly at very large ones. |
| LLaMA vs Qwen vs Kimi? | Published vocab sizes span 32k (LLaMA-2) to 164k (Kimi-K2/K3); on this study's corpus scale the three large-vocab families all saturate at the same data-bound ceiling regardless of target. |
| Is there a vocab-size sweet spot? | Yes, in a qualified sense: 3 of 4 independent criteria converge to a 3–16k band per language at this corpus scale; a 4th confirms returns diminish smoothly rather than stopping outright. |
| Does Zipf-stabilisation predict it? | Yes — within ~2× of the compression-based knee for 2 of 3 languages, and it's far cheaper to compute online. |
| Can vocab size be chosen algorithmically? | §7 of the report proposes a 3-signal stopping rule (Zipf-stability + utilisation decline + marginal fertility gain), validated post-hoc against the sweep. |

## Repository layout

```
src/
  01_build_corpora.py     Build English & Arabic corpora (UD treebanks + XQuAD); reuse Hindi from A1
  02_word_tokenize.py     Language-aware word tokenisation + baseline word-level Zipf stats
  03_train_bpe.py         Train 54 byte-level BPE tokenizers (18-point vocab sweep x 3 languages
                           + 4 model-style replicas x 3 languages: LLaMA-2/3, Qwen-2.5/3, Kimi-K2/K3)
  04_tokenize_and_zipf.py Tokenize + fit Zipf's law + fertility/compression/utilisation per tokenizer
  05_sweetspot.py         Four sweet-spot criteria (fertility-knee, Zipf-stability, utilisation-peak,
                           marginal byte-yield) via Kneedle + custom analysis
  06_figures.py           All 7 figures
  07_report.py            Renders the PDF report (HTML -> headless Chromium)
  08_deck.py               Renders the PPTX presentation

data/          corpus_en.txt, corpus_hi.txt, corpus_ar.txt  (+ raw UD/XQuAD source files)
out/           JSON/TSV results (word stats, tokenizer manifest, Zipf fits, sweet-spot results)
figures/       PNG figures used in the report and deck
tokenizers/    trained tokenizer.json files (regenerate with 03_train_bpe.py; not checked in — 118MB)
dist/          report.html, Zipf_Tokenization_Report.pdf, Zipf_Tokenization_Presentation.pptx
```

## Reproducing

```bash
pip install tokenizers sentencepiece scipy numpy matplotlib kneed
cd src
python3 01_build_corpora.py      # ~1 min, needs GitHub access
python3 02_word_tokenize.py
python3 03_train_bpe.py          # ~2 min, 54 tokenizers
python3 04_tokenize_and_zipf.py
python3 05_sweetspot.py
python3 06_figures.py
python3 07_report.py             # needs headless Chromium
python3 08_deck.py               # needs python-pptx
```

## Method notes & honest limitations

- **Network**: this environment cannot reach `huggingface.co`, so the actual released merge
  tables for LLaMA/Qwen/Kimi could not be downloaded. Each family's **published vocabulary size**
  and **published tokenisation scheme** (byte-level BPE, GPT-2-style byte alphabet) is reproduced
  exactly; the merges themselves are trained from scratch on our own corpus. See §1.1 of the
  report for the full justification — this is a hard *requirement* here, not a shortcut, because
  answering the sweet-spot question needs many vocab sizes per language, which no single
  downloaded tokenizer could provide anyway.
- **Corpus scale**: 250k–440k words per language (UD treebanks + XQuAD, mirrored on GitHub since
  `dumps.wikimedia.org` is also unreachable — same constraint Assignment 1 hit). All sweet-spot
  numbers are explicitly scale-relative, not universal constants; §7.1 and §8 of the report make
  this the central caveat.
- Hindi's corpus is reused verbatim from Assignment 1 for direct comparability.

## Corpus sources

- English: [UD_English-EWT](https://github.com/UniversalDependencies/UD_English-EWT), [UD_English-GUM](https://github.com/UniversalDependencies/UD_English-GUM), [XQuAD-en](https://github.com/google-deepmind/xquad)
- Hindi: reused from Assignment 1 (UD_Hindi-HDTB, UD_Hindi-PUD, XQuAD-hi)
- Arabic: [UD_Arabic-PADT](https://github.com/UniversalDependencies/UD_Arabic-PADT), [UD_Arabic-PUD](https://github.com/UniversalDependencies/UD_Arabic-PUD), [XQuAD-ar](https://github.com/google-deepmind/xquad)

## References

See report bibliography (§ References) for full citations: Zipf (1949), Sennrich et al. (2016),
Radford et al. (2019), Touvron et al. (2023), Meta AI (2024), Qwen Team (2024–25), Moonshot AI
(2025–26), Satopää et al. (2011), Heaps (1978).
