# Zipf, Heaps and the Price of a Language

An adversarial study of Zipf's Law on Hindi, a measured flattening point for
Heaps' Law, and a Heaps-derived cost model for adding a new language to Google
Search and to Sarvam AI.

**Deliverables** live in `dist/`:

| File | What it is |
|---|---|
| `Zipf_Heaps_Hindi_Report.pdf` | 30-page report — full method, all nine attacks, the cost model |
| `Zipf_Heaps_Hindi_Presentation.pptx` | 20-slide deck with speaker notes, for the class presentation |
| `report.html` | HTML source of the report |

---

## Headline results

| | |
|---|---|
| Corpus | 378,726 Hindi tokens, 22,199 word types |
| Zipf exponent | α = 1.092 (ranks 10–5,000), R² = 0.9902 |
| Zipf–Mandelbrot | α = 0.988, b = 1.15, R² = 0.9963 |
| Heaps' Law | V = 19.17 · N^0.5521, R² = 0.9939 |
| **Flattening point** | **N ≈ 95,750 tokens / V ≈ 11,261 types** |
| Google Search, one new language | $11.42M one-time + $6.23M/year |
| Sarvam AI, one new language | $16.17M one-time + $4.23M/year |
| Curated : crawled text cost ratio | 10,000 : 1 |

Nine attacks were run against Zipf's Law. Six failed outright, two landed
partial hits — both on the idealised claim that α is exactly 1 — and one
(characters rather than words) succeeded exactly where the theory predicts it
must. The law was not disproved.

---

## Running it

```bash
pip install numpy scipy matplotlib wordfreq --break-system-packages

cd src
python 01_build_corpus.py --source mirror   # or --source wiki, see below
python 02_tokenize.py
python 03_zipf_analysis.py                  # ~50 s (bootstrap resampling)
python 04_heaps_analysis.py
python 05_cost_model.py
python 06_figures.py
python 07_report.py                         # needs headless Chromium
node   08_deck.js                           # needs pptxgenjs
python 09_verify.py                         # 33 cross-checks, exits non-zero on failure
```

Everything is seeded (`20260823`), so a clean run reproduces every number,
figure and table in the report exactly.

### Running on the real Wikipedia dump

`01_build_corpus.py --source wiki` streams
`hiwiki-latest-pages-articles.xml.bz2` straight from `dumps.wikimedia.org`,
strips MediaWiki markup and writes one cleaned article per line. Scripts 02–09
then run unchanged and regenerate the whole report at roughly 60× the corpus
size.

That path was unavailable in the environment this analysis ran in
(`dumps.wikimedia.org` returns HTTP 403 there), so the results shipped here use
`--source mirror`, which assembles Hindi text from GitHub-hosted sources — UD
Hindi HDTB, UD Hindi PUD and XQuAD Hindi. §2.1 and §7 of the report state this
plainly. The Zipf exponent measured here agrees to within 0.015 with an
independent Hindi frequency table built from billions of tokens, which is the
main evidence that the conclusions are not scale-limited.

---

## Layout

```
src/     01…09  the pipeline, in order
data/           corpus sources + the assembled corpus_hi.txt
out/            JSON results, token stream, frequency table
figures/        the twelve figures
dist/           report PDF, presentation, report HTML
```

## The nine attacks on Zipf's Law

| # | Attack | Outcome |
|---|---|---|
| 1 | The head is too flat for pure Zipf | **Partly lands** — Mandelbrot cuts mean top-10 error 107% → 19%, but a real residual remains |
| 2 | The tail collapses into a flat shelf | Fails — the shelf recedes as N grows; a sampling artefact |
| 3 | Formal Clauset–Shalizi–Newman KS test | **Partly lands** — rejects at a 2.25% CDF residual, but the same data passes at n = 500 and fails at n = 5,000 |
| 4 | Change the genre | Fails — newswire α = 0.988 vs Wikipedia α = 0.931 |
| 5 | Delete the 50 commonest types (40% of tokens) | Fails — remainder re-ranks to α = 1.005 |
| 6 | Collapse Hindi morphology to lemmas | Fails — V drops 19%, α moves 0.065 |
| 7 | Miller's monkeys: random typing is Zipfian too | Fails — monkey text is the *worse* power law (R² 0.74 vs 0.99) |
| 8 | Count characters instead of words | **Succeeds — and is out of scope.** Zipf is a claim about open vocabularies |
| 9 | Vary corpus size fiftyfold | Fails — α = 1.074 ± 0.019 |

## Notes on method

- **Tokenisation.** A token is a maximal run of Devanagari letters, matras,
  virama, nukta and ZWJ/ZWNJ. The danda (U+0964) sits inside the Devanagari
  block but is punctuation, not a letter, and is excluded.
- **Sentence shuffling.** The corpus file is written source-by-source, so
  reading it in file order makes vocabulary arrive in genre-shaped bursts and
  puts a spurious kink in V(N). Every token-order-dependent measurement runs on
  a seeded sentence-level shuffle. Frequency counts — and so all Zipf results —
  are unaffected. Figure 8b shows the difference.
- **Cost model.** The brief's $1,000-per-100,000-words anchor is applied only to
  curated text. The corpus *size* it multiplies is read off the fitted Heaps
  curve by inverting dV/dN = K·β·N^(β−1) for a target marginal yield, so part 3
  is computed from part 2 rather than estimated separately. All inputs are
  declared in `05_cost_model.py` and echoed into `out/cost_model.json`.
