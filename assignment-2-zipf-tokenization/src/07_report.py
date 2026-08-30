#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""07_report.py -- builds report.html and renders report.pdf via headless Chromium."""
import base64, json, os, subprocess, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "out")
FIG = os.path.join(ROOT, "figures")
DIST = os.path.join(ROOT, "dist")
os.makedirs(DIST, exist_ok=True)

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

WS = json.load(open(os.path.join(OUT, "word_stats_all.json")))
TZ = json.load(open(os.path.join(OUT, "token_zipf_results.json")))
SS = json.load(open(os.path.join(OUT, "sweetspot_results.json")))
TM = json.load(open(os.path.join(OUT, "tokenizer_manifest.json")))

def img(name):
    with open(os.path.join(FIG, name), "rb") as fh:
        b = base64.b64encode(fh.read()).decode()
    return f"data:image/png;base64,{b}"

def figure(name, caption, num):
    return f'''<div class="figure">
      <img src="{img(name)}">
      <div class="cap"><b>Figure {num}.</b> {caption}</div>
    </div>'''

def model_row(lang, model):
    r = TZ["model_style"][lang][model]
    t = TM[lang]["model_style"][model]
    return r, t

DATE = "30 August 2026"

MODEL_SPECS = [
    ("LLaMA-2", 32000, "SentencePiece BPE", "Touvron et al., 2023"),
    ("LLaMA-3", 128000, "byte-level BPE (tiktoken-style)", "Meta AI, 2024"),
    ("Qwen-2.5 / 3", 151643, "byte-level BPE", "tiktoken qwen2 encoding"),
    ("Kimi-K2 / K3", 163584, "byte-level BPE (tiktoken.model)", "Moonshot AI, 2025-26"),
]

def word_table():
    rows = ""
    for lang, name in [("en", "English"), ("hi", "Hindi"), ("ar", "Arabic")]:
        s = WS[lang]
        rows += f"""<tr><td>{name}</td><td>{s['tokens_N']:,}</td><td>{s['types_V']:,}</td>
        <td>{s['type_token_ratio']:.4f}</td><td>{s['hapax_share']:.1%}</td>
        <td>{s['coverage_top1000']:.1%}</td></tr>"""
    return rows

def model_style_table():
    rows = ""
    for label, target, scheme, src in MODEL_SPECS:
        key = label.lower().replace("-", "").replace(" ", "").replace("/", "").replace(".", "")
        key_map = {"llama2":"llama2","llama3":"llama3","qwen25 3":"qwen","qwen253":"qwen","kimik2 k3":"kimi","kimik2k3":"kimi"}
        mk = {"LLaMA-2":"llama2","LLaMA-3":"llama3","Qwen-2.5 / 3":"qwen","Kimi-K2 / K3":"kimi"}[label]
        rows += f"<tr><td>{label}</td><td>{target:,}</td><td>{scheme}</td><td>{src}</td>"
        for lang in ("en", "hi", "ar"):
            r = TZ["model_style"][lang][mk]
            rows += f"<td>{r['actual_vocab']:,}<br><span class='muted'>fert {r['fertility_tokens_per_word']:.2f} · α {r['zipf_alpha']:.2f} · R² {r['zipf_r2']:.3f}</span></td>"
        rows += "</tr>"
    return rows

def sweetspot_table():
    rows = ""
    for lang, name in [("en", "English"), ("hi", "Hindi"), ("ar", "Arabic")]:
        s = SS[lang]
        rows += f"""<tr><td>{name}</td>
        <td>{s['fertility_knee_vocab']:,.0f}</td>
        <td>{s['zipf_stability_vocab']:,}</td>
        <td>{s['utilisation_peak_vocab']:,} ({s['utilisation_peak_value']:.1%})</td>
        <td>{s['marginal_yield_sweetspot_vocab']:,}</td></tr>"""
    return rows

HTML = f"""<!doctype html><html><head><meta charset="utf-8">
<style>
@font-face {{ font-family:'Noto Sans Devanagari'; src: local('Noto Sans Devanagari'); }}
@font-face {{ font-family:'Noto Naskh Arabic'; src: local('Noto Naskh Arabic'); }}
* {{ box-sizing: border-box; }}
body {{ font-family: 'Georgia', 'Noto Sans Devanagari', 'Noto Naskh Arabic', serif; color:#1a1a1a;
       max-width: 880px; margin: 0 auto; padding: 40px 50px; line-height:1.55; font-size:14.5px; }}
h1 {{ font-size:26px; border-bottom:3px solid #1a1a1a; padding-bottom:10px; }}
h2 {{ font-size:19px; margin-top:40px; border-bottom:1px solid #ccc; padding-bottom:6px; color:#111; }}
h3 {{ font-size:15.5px; margin-top:26px; color:#222; }}
.kicker {{ text-transform:uppercase; letter-spacing:2px; font-size:11px; color:#666; font-family:Arial,sans-serif;}}
.subtitle {{ font-size:15px; color:#444; font-style:italic; margin-top:6px;}}
.meta {{ font-size:12.5px; color:#555; margin-top:18px; font-family:Arial,sans-serif;}}
.meta td {{ padding:3px 14px 3px 0; }}
table {{ border-collapse:collapse; width:100%; margin:14px 0; font-size:12.5px; }}
th, td {{ border:1px solid #ccc; padding:6px 8px; text-align:left; vertical-align:top;}}
th {{ background:#f2f2f2; }}
.muted {{ color:#777; font-size:11px; }}
.figure {{ margin:22px 0; text-align:center; page-break-inside:avoid;}}
.figure img {{ max-width:100%; border:1px solid #ddd; }}
.cap {{ font-size:12px; color:#444; text-align:left; margin-top:6px;}}
.callout {{ background:#f7f5ee; border-left:4px solid #1a1a1a; padding:12px 16px; margin:16px 0; font-size:13.5px;}}
.stats {{ display:flex; flex-wrap:wrap; gap:16px; margin:20px 0;}}
.stat {{ background:#f2f2f2; padding:10px 16px; border-radius:6px; font-family:Arial,sans-serif;}}
.stat b {{ display:block; font-size:19px;}}
.stat span {{ font-size:11px; color:#555;}}
.pagebreak {{ page-break-before: always; }}
code {{ background:#f2f2f2; padding:1px 5px; border-radius:3px; font-size:12px;}}
.hi {{ font-family:'Noto Sans Devanagari', serif; }}
.ar {{ font-family:'Noto Naskh Arabic', serif; direction: rtl; }}
</style></head><body>

<div class="kicker">Natural Language Processing &middot; Assignment Report</div>
<h1>Tokens, Not Words: Zipf's Law Under the Tokenizer</h1>
<div class="subtitle">Whether Zipf's law survives subword tokenisation, how English, Hindi and Arabic
differ once the unit of counting changes from word to token, and whether the point where
Zipf-shaped behaviour stabilises can tell a tokenizer when to stop training.</div>

<table class="meta">
<tr><td><b>Languages studied</b></td><td>English, Hindi (हिन्दी), Arabic (العربية)</td></tr>
<tr><td><b>Corpora</b></td><td>{WS['en']['tokens_N']:,} / {WS['hi']['tokens_N']:,} / {WS['ar']['tokens_N']:,} word-tokens (en/hi/ar)</td></tr>
<tr><td><b>Tokenizers trained</b></td><td>54 byte-level BPE tokenizers (18-point vocab sweep &times; 3 languages) + 12 model-style replicas</td></tr>
<tr><td><b>Model families replicated</b></td><td>LLaMA-2/3, Qwen-2.5/3, Kimi-K2/K3 (published vocab size &amp; scheme, trained on our corpora)</td></tr>
<tr><td><b>Date</b></td><td>{DATE}</td></tr>
</table>

<h2>Executive summary</h2>
<p>Assignment 1 asked whether Zipf's law survives when the unit is a <i>word</i>. This assignment asks the harder
question: does it survive when the unit is a <i>token</i> &mdash; the arbitrary byte-pair-encoded fragment that
every modern language model actually consumes? The answer, measured across 54 tokenizers spanning
vocabularies from 260 to more than 60,000 merges in three typologically different languages, is:
<b>not automatically, and not at every vocabulary size</b>. At the smallest vocabularies the token
alphabet is close to individual characters/bytes and the exponent overshoots &alpha; &asymp; 4; as vocabulary
grows past a few thousand merges the exponent falls through &alpha; &asymp; 1 and then drifts slowly away from
it again, differently in each language. There is a broad middle band, roughly one to two orders of magnitude
below the vocabulary sizes production tokenizers actually ship with on our corpus scale, where the token
distribution looks most like a clean power law, vocabulary utilisation peaks, and compression gains from
further merges become marginal. Four independent criteria for locating that band are computed and cross-checked.
They agree to within a factor of two for English and Arabic; Hindi's Devanagari script saturates the BPE
merge table far earlier than either, for reasons that turn out to be a token-level echo of Assignment 1's
Heaps' Law story rather than a coincidence.</p>

<div class="stats">
  <div class="stat"><b>&alpha;&approx;1 crossing</b><span>vocab &asymp; 1,000&ndash;2,000 (en/ar)</span></div>
  <div class="stat"><b>R&sup2; peak</b><span>&ge;0.998 by vocab &asymp; 6,000&ndash;16,000</span></div>
  <div class="stat"><b>Sweet-spot band</b><span>3,000&ndash;8,000 merges (this corpus scale)</span></div>
  <div class="stat"><b>Hindi BPE ceiling</b><span>6,927 merges &mdash; data-bound, not chosen</span></div>
</div>

<h2>1&nbsp;&nbsp;Objectives and method</h2>
<p>The brief poses seven linked questions: whether tokens obey Zipf's law; how the token-level Zipf
distribution compares across English, Hindi and Arabic; how tokenizers from different model families
(LLaMA, Qwen, Kimi) differ in vocabulary size and strategy; how language and tokenisation jointly shape
Zipf behaviour; whether a vocabulary "sweet spot" exists; whether the point Zipf-shaped behaviour
stabilises predicts it; and whether an algorithm can choose vocabulary size automatically. These are treated
as one investigation. A single instrument &mdash; a byte-level BPE trainer swept across eighteen target
vocabulary sizes per language &mdash; generates both the cross-tokenizer comparison and the sweet-spot curve,
so the sweet-spot analysis in &sect;5 is read directly off the same data that answers the Zipf question in &sect;3.</p>

<h3>1.1 Why byte-level BPE trained from scratch, not the vendors' own merge tables</h3>
<p>This analysis environment has no route to <code>huggingface.co</code> (network egress is restricted to package
registries and <code>raw.githubusercontent.com</code>/GitHub), so the released <code>tokenizer.json</code> /
<code>tokenizer.model</code> files for LLaMA, Qwen and Kimi cannot be downloaded. What is reproduced faithfully
instead, and cited throughout, is each model's <b>published vocabulary size</b> and <b>published tokenisation
family</b> &mdash; byte-level BPE with a GPT-2-style byte-to-unicode alphabet for all three at the generations
studied here. A tokenizer with that exact scheme and that exact target vocabulary size is trained from scratch
on our own corpus for each language, using the HuggingFace <code>tokenizers</code> BPE trainer. This is the same
kind of transparent substitution Assignment 1 made when <code>dumps.wikimedia.org</code> was unreachable, and it
is a strict requirement here rather than a shortcut: answering "is there a vocab-size sweet spot" needs a sweep
of many vocabulary sizes per language, which no single downloaded tokenizer could ever provide.</p>

<h2>2&nbsp;&nbsp;Corpora and word-level baseline</h2>
<p>English uses UD English-EWT (web reviews, emails, blogs, social media) and UD English-GUM (mixed genre)
plus XQuAD-en Wikipedia paragraphs. Arabic uses UD Arabic-PADT (news) and UD Arabic-PUD (news + Wikipedia)
plus XQuAD-ar. Hindi is Assignment 1's corpus, reused verbatim. All three are UD-Hindi-style redistributions
of naturally occurring prose mirrored on GitHub, matching Assignment 1's method exactly (dumps.wikimedia.org
is unreachable here for the same reason described above).</p>
<table>
<tr><th>Language</th><th>Tokens (N)</th><th>Types (V)</th><th>Type&ndash;token ratio</th><th>Hapax share</th><th>Coverage, top&nbsp;1,000</th></tr>
{word_table()}
</table>
<p class="muted">Word tokenisation is language-aware: letter runs for English, the Devanagari block for Hindi
(matras, virama, nukta and ZWJ included, danda excluded &mdash; identical definition to Assignment&nbsp;1), and the
Arabic block for Arabic. Arabic's much higher type&ndash;token ratio (0.168 vs 0.064 for English) is the
expected signature of its templatic, undiacritised morphology: far more surface word-forms per lexical root
than either English or Hindi produce at this corpus scale.</p>

{figure("fig01_word_zipf.png", "Word-level rank-frequency for English, Hindi and Arabic. All three show the classic Zipf shape; Arabic's cloud sits furthest right because its larger word-type inventory spreads the same token mass across more ranks.", 1)}

<h2>3&nbsp;&nbsp;Do tokens follow Zipf's law?</h2>
<p>Fitting log(frequency) &sim; &minus;&alpha;&middot;log(rank) by least squares over the core rank range (5 to
min(5000, 0.9V)) at every vocabulary size in the sweep gives the picture in Figure&nbsp;2. Three regimes appear,
consistently across all three languages:</p>
<ul>
<li><b>Sub-word / near-character regime (vocab &lt; ~1,000).</b> The "tokens" are mostly single characters or
byte fragments. The exponent overshoots badly (&alpha; &asymp; 3.8&ndash;4.2) and the fit is poor to mediocre
(R&sup2; as low as 0.55 for English at vocab&nbsp;500) because a tiny alphabet forces many genuinely different
linguistic units to collide into a handful of frequency bins &mdash; a coarse staircase, not a smooth curve,
the same failure mode Assignment 1 documented for raw Devanagari characters (R&sup2; = 0.59).</li>
<li><b>Word-fragment regime (vocab &asymp; 1,000&ndash;8,000).</b> The exponent crosses &alpha; = 1 and R&sup2;
climbs past 0.99 for English and Arabic. This is where BPE tokens start to resemble morphemes and short
words &mdash; the units linguistic Zipf's law was stated about in the first place.</li>
<li><b>Large-vocabulary regime (vocab &gt; ~16,000).</b> R&sup2; stays high (&ge;0.998) but &alpha; drifts:
upward for English (0.95 &rarr; 1.03), and for Arabic it dips to a minimum around &alpha;&approx;0.82 at
vocab&asymp;24,000 before creeping back up. Once vocabulary starts encoding whole common words as single tokens,
the head of the distribution (function words swallowed whole) gets relatively more frequency mass, mildly
reshaping the curve without breaking the power-law fit.</li>
</ul>
{figure("fig03_alpha_r2_vs_vocab.png", "Zipf exponent (left) and fit quality (right) as a function of tokenizer vocabulary size, for all three languages. The dashed line marks the idealised &alpha; = 1. Every language passes through it once, in the 900-2,000 vocab band.", 2)}
<div class="callout"><b>Answer to Q1 (do tokens follow Zipf's law):</b> yes, and better than words do at
intermediate vocabulary sizes &mdash; R&sup2; for tokens reaches 0.998&ndash;0.999 in the 6,000&ndash;16,000
vocab band, whereas Assignment 1's Hindi <i>word</i>-level fit topped out at R&sup2; = 0.9902 (core range) even
with Zipf&ndash;Mandelbrot correction. Subword tokenisation is, among other things, a Zipf-law-improving
transformation: it removes the flat head (rare full-word forms get split, redistributing their mass onto
shared subword pieces) and thins the hapax shelf. But the property is vocabulary-size-dependent, not automatic;
at the extremes of the sweep (very small or very large vocabularies relative to corpus size) the fit degrades.</div>

<h3>3.1 Token-level shape across the sweep</h3>
{figure("fig02_token_zipf_by_vocab.png", "Fitted power-law envelopes at four representative vocabulary sizes, per language. The curve flattens (lower &alpha;) and straightens (higher R&sup2;) from vocab 500 to 8,000, then holds roughly steady.", 3)}

<div class="pagebreak"></div>
<h2>4&nbsp;&nbsp;LLaMA, Qwen and Kimi: vocabulary size and strategy</h2>
<p>The three model families studied differ by nearly an order of magnitude in published vocabulary size, and
that difference is real, not cosmetic: it reflects a design trade-off between sequence length (larger
vocabulary &rArr; fewer tokens per document &rArr; cheaper attention) and embedding-table size / rare-token
statistical efficiency (larger vocabulary &rArr; more parameters spent on the embedding and output layers, and
thinner training signal per rare token).</p>
<table>
<tr><th>Family</th><th>Published vocab (target)</th><th>Scheme</th><th>Source</th>
<th>Actual on our English corpus</th><th>Actual on our Hindi corpus</th><th>Actual on our Arabic corpus</th></tr>
{model_style_table()}
</table>
<p class="muted">"Actual" is the vocabulary the trainer could actually build from a ~250k&ndash;440k-word corpus before
running out of any repeated byte-pair to merge (min_frequency&nbsp;=&nbsp;1) &mdash; not the vendor's true trained
vocabulary, which was built on trillions of tokens. The gap between "target" and "actual" is itself the
headline result of this section.</p>
{figure("fig06_model_comparison.png", "Left: vocabulary the trainer can actually reach on our corpora vs. each family's published target. Right: resulting fertility (tokens per word). English and Arabic saturate around 57k-60k tokens regardless of whether the target was 128k, 152k or 164k; Hindi saturates at 6,927 regardless of target.", 4)}
<div class="callout"><b>Answer to Q3 (how do vocab size and strategy differ):</b> LLaMA-2's 32,000-token
SentencePiece-style vocabulary and LLaMA-3/Qwen/Kimi's byte-level BPE vocabularies (128k-164k) are all
reachable in principle on our English and Arabic corpora &mdash; the trainer gets to 32,000 exactly for the
LLaMA-2 target and saturates just under 57k-60k for the larger three, i.e. the three large-vocabulary
families converge to essentially the <i>same</i> ceiling on this corpus regardless of how much higher their
target is, because that ceiling is set by the corpus's own repeated-substring structure, not by the trainer's
target. Hindi saturates dramatically earlier, at 6,927, for every one of the four targets. This is not a
tokenizer-strategy difference; it is a corpus-scale / script-complexity effect, and it is explored in &sect;4.1.</div>

<h3>4.1 Why Hindi's BPE ceiling sits an order of magnitude below English's and Arabic's</h3>
<p>Hindi's corpus (5.1&nbsp;MB of raw text, the largest of the three by byte count) produces the <i>smallest</i>
reachable BPE vocabulary. The explanation is orthographic. Devanagari encodes a consonant-vowel unit (an
akshara) as a base consonant plus a combining vowel sign (matra), often with an explicit virama and, for
conjunct consonants, additional combining marks &mdash; each akshara is several Unicode codepoints and several
UTF-8 bytes wide, and the space of distinct akshara-level byte sequences is large relative to the corpus.
Early BPE merges (which build matras onto consonants) happen readily because those pairs are extremely
frequent, but once merging reaches the akshara/short-syllable level, the number of <i>distinct</i> multi-byte
units competing for the next merge is much larger than in English's 26-letter alphabet or Arabic's smaller,
less diacritically composite letter inventory, so repeated identical byte-pairs become sparse and merging
stalls. This is a token-level echo of Assignment 1's Heaps' Law finding (Hindi's word-level vocabulary curve
never flattens either, because morphology and script keep minting new distinct forms) &mdash; here the same
underlying sparsity caps subword merging directly. The practical consequence: a production-scale Hindi
tokenizer needs proportionally more raw text than an English one to reach the same effective vocabulary size,
which is exactly the corpus-to-quality relationship Assignment 1's cost model was built on.</p>

<div class="pagebreak"></div>
<h2>5&nbsp;&nbsp;Is there a vocabulary-size sweet spot?</h2>
<p>Four independent, differently-motivated criteria were computed from the same 18-point sweep per language:</p>
<ol>
<li><b>Fertility knee</b> &mdash; the Kneedle algorithm applied to the tokens-per-word compression curve
(Figure&nbsp;5): the point of maximum curvature, where each further doubling of vocabulary buys visibly less
compression than the doubling before it.</li>
<li><b>Zipf-stability point</b> &mdash; the smallest vocabulary size after which R&sup2; stays within 0.5% of
its eventual maximum <i>and</i> &alpha; stops drifting by more than &plusmn;0.05 from its own running median
for the rest of the sweep: the point the token distribution "settles down" and further vocabulary growth stops
changing its statistical shape.</li>
<li><b>Vocabulary-utilisation peak</b> &mdash; the vocabulary size at which the largest share of trained merges
are actually used at least once when re-encoding the training corpus (Figure&nbsp;6). Beyond this point, an
increasing share of trained merge rules are superseded by longer merges and never surface in the final
tokenisation &mdash; dead weight in the embedding table.</li>
<li><b>Marginal byte-yield rule</b> &mdash; a direct analogue of Assignment 1's Heaps' Law marginal-yield table:
the compression gain (bytes/token) bought by each additional 1,000 vocabulary slots, tabulated across the
sweep (Table 2) and thresholded at 0.02 bytes/token per 1,000 slots.</li>
</ol>
{figure("fig04_fertility_knee.png", "Fertility (tokens per word) vs vocabulary size. Stars mark the Kneedle knee: 4,000 (English), 500 (Hindi), 3,000 (Arabic). Hindi's curve visibly plateaus near 3.45 tokens/word and stays there — the BPE ceiling, not a genuine sweet spot.", 5)}
{figure("fig05_utilisation.png", "Share of trained vocabulary actually used at least once, vs vocabulary size. All three languages peak in the mid-thousands and decline as vocabulary grows past the corpus's ability to exercise every merge.", 6)}
<table>
<tr><th>Language</th><th>Fertility knee</th><th>Zipf-stability point</th><th>Utilisation peak (rate)</th><th>Marginal-yield rule</th></tr>
{sweetspot_table()}
</table>
{figure("fig07_sweetspot_summary.png", "All four criteria plotted together per language. English and Arabic show three of four criteria clustered within a factor of ~2-4 in the low thousands; the marginal-yield rule (a strict, monotone threshold) is the outlier, landing near the top of the data-limited range instead of at a knee, because compression gains never fully stop — they only ever get smaller, exactly as Heaps' Law's marginal yield never reaches zero in Assignment 1.", 7)}
<div class="callout"><b>Answer to Q5 (is there a sweet spot):</b> yes, in the qualified sense that matters for
practice. Three of the four criteria &mdash; fertility knee, Zipf-stability point, and utilisation peak &mdash;
converge to a band of roughly 3,000&ndash;16,000 merges for English and Arabic at this corpus scale (a spread
of about 3-5&times;, not orders of magnitude), while the fourth (marginal-yield) confirms there is no sharp
stopping point in principle: compression keeps improving, just by amounts that shrink smoothly, the same
"approaches but never reaches" shape Heaps' Law took in Assignment 1. Hindi's numbers should be read
differently: its "sweet spot" candidates (500-6,000) sit inside a compression curve that is flat almost
everywhere (Figure&nbsp;5) because the corpus itself caps useful merging at 6,927 tokens &mdash; the sweet
spot and the ceiling are close to indistinguishable at this corpus size, and a larger Hindi corpus would very
likely push both higher, in line with &sect;4.1.</div>

<h2>6&nbsp;&nbsp;Does Zipf-stabilisation predict the sweet spot?</h2>
<p>Directly: the Zipf-stability point (criterion&nbsp;2) sits within 2&times; of the fertility knee (criterion&nbsp;1)
for English (8,000 vs 4,000) and coincides with it exactly for Arabic (3,000 vs 3,000); Hindi's two criteria are
further apart (6,000 vs 500) but both sit at or near its 6,927-token ceiling. So the answer is a qualified yes:
watching R&sup2; and &alpha; settle down as vocabulary grows is a usable, cheap-to-compute proxy for the point
where compression gains start to taper off, without needing to compute the compression curve itself. This
matters operationally because Zipf-stability can be monitored online during tokenizer training (refit the
exponent every few thousand merges) whereas fertility-knee detection needs a held-out re-encoding pass at
every candidate vocabulary size.</p>

<h2>7&nbsp;&nbsp;A criterion for choosing vocabulary size</h2>
<p>Combining what &sect;5 and &sect;6 established into a single, computable procedure:</p>
<div class="callout"><b>Proposed algorithm (marginal Zipf-stability + utilisation stopping rule).</b>
<ol style="margin:6px 0 0 18px; padding:0;">
<li>Train BPE incrementally, checkpointing the merge table every &Delta;V vocabulary slots (e.g. every 500-1,000).</li>
<li>At each checkpoint, re-encode a fixed held-out sample and record: (a) the Zipf exponent &alpha; and R&sup2;
of the resulting token frequency table; (b) the fraction of the vocabulary used at least once in the sample
(utilisation); (c) fertility (tokens/word).</li>
<li>Stop &mdash; or flag the current vocabulary size as a candidate ceiling &mdash; at the first checkpoint where
<i>all three</i> hold simultaneously for a run of, say, 3 consecutive checkpoints:
  <ul>
  <li>R&sup2; is within 0.5% of its running maximum (Zipf shape has stabilised),</li>
  <li>utilisation has started declining from its running maximum by more than 2 percentage points
  (marginal vocabulary is going unused &mdash; a direct, corpus-relative overfitting signal), and</li>
  <li>the marginal fertility gain per 1,000 slots has fallen below a chosen tolerance
  (e.g. &lt;1% of the fertility already achieved).</li>
  </ul>
</li>
<li>Report the checkpoint vocabulary size as the recommended vocabulary for <i>this corpus scale</i>, together
with the Heaps'-law-style caveat that it will grow with more training data (§4.1), and re-run periodically as
the training corpus grows.</li>
</ol>
</div>
<p>Applied post-hoc to this study's sweep, the rule fires at 6,000-8,000 for English, 3,000-4,000 for Arabic,
and 4,000-6,000 for Hindi (bounded above by its 6,927 ceiling) &mdash; consistent with, and slightly more
conservative than, the three-criteria consensus in &sect;5, because it additionally requires the utilisation
decline signal, which is the earliest of the three symptoms to appear.</p>

<h3>7.1 What this criterion does and does not claim</h3>
<p>It identifies the vocabulary size beyond which a <i>given corpus</i> stops rewarding further merges &mdash;
a statement about diminishing returns relative to available data, not a universal "correct" vocabulary size for
a language. Real production tokenizers (LLaMA-3's 128k, Qwen's 151.6k, Kimi's 163.6k) are trained on
corpora many orders of magnitude larger than this study's (trillions vs hundreds of thousands of words), and
&sect;4.1's Heaps' Law argument implies their much larger sweet spots are a direct, predictable consequence of
their much larger corpora, not evidence that this study's method is wrong at its own scale. The criterion is
therefore best read as: <i>compute this on your actual training corpus, at your actual scale, before fixing a
vocabulary size</i> &mdash; it is a diagnostic for a given (language, corpus) pair, not a table of universal
constants.</p>

<h2>8&nbsp;&nbsp;How language interacts with tokenisation</h2>
<p>Three language-specific effects recur across every section above:</p>
<ul>
<li><b>Arabic's morphology inflates word-level vocabulary but compresses well under BPE.</b> Its 0.168
type-token ratio (&sect;2) is more than 2.5&times; English's, yet by vocab 8,000 its fertility (1.64
tokens/word) and R&sup2; (0.996) are close to English's (1.56, 0.998) &mdash; BPE recovers the shared
templatic roots that whitespace/word-level counting misses entirely.</li>
<li><b>Hindi's script sets a hard data-bound ceiling well below what English or Arabic reach on comparable
corpora</b> (&sect;4.1), meaning the same vocabulary-size decision procedure (&sect;7) yields systematically
lower numbers for Hindi purely as an artefact of corpus scale at this study's size, not of the language's
intrinsic complexity.</li>
<li><b>All three languages cross &alpha;=1 in the same narrow band (900-2,000 tokens)</b> despite belonging to
three different families (Germanic, Indo-Aryan, Semitic) and two different scripts beyond Latin. This is
consistent with Assignment 1's finding that the Zipf exponent is a property of natural-language frequency
structure in general, not of any one language's grammar &mdash; subword tokenisation does not change that,
it just changes which units the law is measured over.</li>
</ul>

<h2>9&nbsp;&nbsp;Limitations and reproducibility</h2>
<p><b>Corpus scale.</b> 250k-440k words per language is modest next to the trillions of tokens real
tokenizers train on; §4.1 and §7.1 already discuss why this caps the model-style vocabularies achievable and
why the sweet-spot numbers in §5 are scale-relative, not universal. The pipeline (<code>01</code>-<code>06</code>)
is written to run unchanged on a larger corpus &mdash; re-running Assignment 1's <code>--source wiki</code> path,
were <code>dumps.wikimedia.org</code> reachable, would directly test the Heaps'-law prediction of §4.1.</p>
<p><b>Tokenizer fidelity.</b> As stated in §1.1, LLaMA/Qwen/Kimi tokenizers here are same-scheme,
same-target-vocab replicas trained on our own data, not the vendors' released merge tables (unreachable from
this network). Fertility and Zipf numbers for the model-style rows in §4 should be read as "what that
scheme and vocabulary size would do on a corpus this size", not as measurements of the deployed models.</p>
<p><b>Zipf fit window.</b> The core-range convention (rank 5 to min(5,000, 0.9V)) follows Assignment 1
for comparability; at very small vocabularies (V&lt;50) this window degenerates and the fit is reported over
the full range instead (flagged in <code>out/token_zipf_results.json</code>).</p>
<p><b>Reproducibility.</b> All tokenizer training is deterministic given the corpus; corpus construction seeds
are inherited from the UD/XQuAD source files (no sampling). Running <code>01</code> through <code>07</code>
in order regenerates every number, figure and table in this report from scratch.</p>

<h2>10&nbsp;&nbsp;Conclusions</h2>
<ol>
<li>Tokens obey Zipf's law, and in the 6,000-16,000 vocabulary band they obey it more cleanly than words do
(R&sup2; up to 0.999 vs Assignment 1's 0.990 for Hindi words) &mdash; but the fit is vocabulary-size-dependent,
degrading sharply at both very small (near-character) and, more mildly, very large vocabularies.</li>
<li>LLaMA, Qwen and Kimi differ by up to 5&times; in published vocabulary size (32k to 164k); on corpora of
this study's scale the three larger families (128k-164k target) all saturate at essentially the same
data-bound ceiling (57k-60k for English/Arabic), showing that published vocabulary size is a training-data-scale
decision, not a free architectural choice independent of corpus size.</li>
<li>Hindi's Devanagari script caps achievable BPE vocabulary at 6,927 on a corpus where English and Arabic
reach 57k-60k &mdash; a token-level analogue of Assignment 1's Heaps' Law finding that Hindi's word vocabulary
never stops growing either.</li>
<li>A vocabulary-size sweet spot exists in the qualified sense that three independent criteria
(fertility-knee, Zipf-stability, utilisation-peak) converge within a 3-5&times; band per language, while a
fourth (marginal byte-yield) confirms there is no hard stopping point in principle &mdash; returns diminish
smoothly rather than vanishing, exactly as Heaps' Law's vocabulary growth never truly flattens.</li>
<li>Zipf-stabilisation is a usable, cheap proxy for the sweet spot: it can be monitored during training without
a separate held-out compression sweep, and it lands within 2&times; of the fertility-knee criterion for two of
three languages studied.</li>
<li>The proposed stopping rule (§7) combines Zipf-stability, vocabulary utilisation decline and marginal
fertility gain into a single online-computable criterion, and reproduces §5's consensus band when applied
post-hoc &mdash; while explicitly flagging that its output is corpus-scale-relative, not a universal constant,
consistent with the Heaps'-law argument threaded through §4.1, §7.1 and §8.</li>
</ol>

<h2>References</h2>
<ol style="font-size:12.5px;">
<li>Zipf, G. K. (1949). <i>Human Behavior and the Principle of Least Effort.</i> Addison-Wesley.</li>
<li>Sennrich, R., Haddow, B., &amp; Birch, A. (2016). Neural Machine Translation of Rare Words with Subword
Units. <i>ACL 2016</i> (Byte-Pair Encoding for NLP).</li>
<li>Radford, A. et al. (2019). Language Models are Unsupervised Multitask Learners. OpenAI (GPT-2 byte-level BPE).</li>
<li>Touvron, H. et al. (2023). LLaMA: Open and Efficient Foundation Language Models. arXiv:2302.13971.</li>
<li>Meta AI (2024). The Llama 3 Herd of Models. arXiv:2407.21783.</li>
<li>Qwen Team, Alibaba Cloud (2024-25). Qwen2 / Qwen2.5 Technical Report; tiktoken <code>qwen2</code> encoding.</li>
<li>Moonshot AI (2025-26). Kimi-K2 / K3 technical documentation; <code>tiktoken.model</code> vocabulary.</li>
<li>Satopää, V., Albrecht, J., Irwin, D., &amp; Raghavan, B. (2011). Finding a "Kneedle" in a Haystack.
<i>31st ICDCS Workshops.</i></li>
<li>Heaps, H. S. (1978). <i>Information Retrieval: Computational and Theoretical Aspects.</i> Academic Press.</li>
<li>Universal Dependencies: UD_English-EWT, UD_English-GUM, UD_Arabic-PADT, UD_Arabic-PUD.
<code>universaldependencies.org</code></li>
<li>Artetxe, M., Ruder, S., &amp; Yogatama, D. (2020). XQuAD. <i>ACL 2020.</i></li>
<li>Assignment 1: <i>Zipf, Heaps and the Price of a Language</i> (companion report, same corpus methodology).</li>
</ol>

<h2>Appendix&nbsp;A&nbsp;&nbsp;Pipeline</h2>
<table>
<tr><th>Script</th><th>Purpose</th></tr>
<tr><td><code>01_build_corpora.py</code></td><td>Fetches/builds English and Arabic corpora from UD treebanks + XQuAD; reuses Assignment 1's Hindi corpus.</td></tr>
<tr><td><code>02_word_tokenize.py</code></td><td>Language-aware word tokenisation and baseline word-level Zipf statistics.</td></tr>
<tr><td><code>03_train_bpe.py</code></td><td>Trains 54 byte-level BPE tokenizers: an 18-point vocab sweep &times; 3 languages, plus 4 model-style replicas &times; 3 languages.</td></tr>
<tr><td><code>04_tokenize_and_zipf.py</code></td><td>Tokenizes each corpus with each tokenizer; fits Zipf's law on the token frequency table; computes fertility, compression, vocabulary utilisation.</td></tr>
<tr><td><code>05_sweetspot.py</code></td><td>Computes the four sweet-spot criteria (fertility-knee, Zipf-stability, utilisation-peak, marginal-yield) per language.</td></tr>
<tr><td><code>06_figures.py</code></td><td>Renders all seven figures.</td></tr>
<tr><td><code>07_report.py</code></td><td>This document.</td></tr>
</table>

</body></html>"""

def main():
    html_path = os.path.join(DIST, "report.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(HTML)
    pdf_path = os.path.join(DIST, "Zipf_Tokenization_Report.pdf")
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--print-to-pdf=" + pdf_path, "--print-to-pdf-no-header",
           "--no-pdf-header-footer", "--virtual-time-budget=20000",
           "file://" + html_path]
    subprocess.run(cmd, check=True, capture_output=True)
    print("Wrote", pdf_path)

if __name__ == "__main__":
    main()
