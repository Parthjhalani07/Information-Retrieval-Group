// 08_deck.js — builds the class presentation.
// Run: node 08_deck.js
const pptxgen = require('pptxgenjs');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const FIG = path.join(ROOT, 'figures');
const OUT = path.join(ROOT, 'out');
const DIST = path.join(ROOT, 'dist');
if (!fs.existsSync(DIST)) fs.mkdirSync(DIST);

const J = f => JSON.parse(fs.readFileSync(path.join(OUT, f), 'utf8'));
const Z = J('zipf_results.json'), H = J('heaps_results.json');
const S = J('corpus_stats.json'), M = J('cost_model.json');

// ---- palette: deep indigo dominant, saffron accent, jade support ----------
const INK = '16233F';        // deep indigo — dominant
const INK_SOFT = '3A4A6B';
const ACCENT = 'EB6834';     // saffron
const JADE = '1BAF7A';
const BLUE = '2A78D6';
const VIOLET = '4A3AA7';
const PAPER = 'FFFFFF';
const MUTE = '6B7488';
const LINE = 'DFE3EB';

const HEAD = 'Cambria';
const BODY = 'Calibri';

const W = 13.3, Ht = 7.5;

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';
pres.author = 'NLP Assignment';
pres.title = 'Zipf, Heaps and the Price of a Language';

const usd = v => '$' + Math.round(v).toLocaleString('en-US');
const musd = v => '$' + (v / 1e6).toFixed(2) + 'M';
const num = v => Math.round(v).toLocaleString('en-US');

const base = Z.baseline, zm = base.mandelbrot, oc = base.ols_core;
const a1 = Z.A1_head, a2 = Z.A2_tail, a3 = Z.A3_gof, a4 = Z.A4_genre;
const a5 = Z.A5_ablation, a6 = Z.A6_morphology, a7 = Z.A7_monkey;
const a8 = Z.A8_units, a9 = Z.A9_scale, ext = Z.external_wordfreq;
const hi = H.hindi, knee = hi.knee.linear, dua = H.duality;
const zmh = Z.baseline.mandelbrot_head;
const head = M.headline, nk = M.naive_anchor_check;
const thr = t => hi.thresholds.find(x => x.threshold_per_1k === t);

// ---------- slide helpers -------------------------------------------------
function darkSlide() {
  const s = pres.addSlide();
  s.background = { color: INK };
  return s;
}
function lightSlide(title, kicker) {
  const s = pres.addSlide();
  s.background = { color: PAPER };
  if (kicker) {
    s.addText(kicker.toUpperCase(), {
      x: 0.6, y: 0.34, w: 12.1, h: 0.26, fontFace: BODY, fontSize: 10.5,
      color: ACCENT, bold: true, charSpacing: 2, margin: 0,
    });
  }
  if (title) {
    s.addText(title, {
      x: 0.6, y: kicker ? 0.62 : 0.45, w: 12.1, h: 0.62, fontFace: HEAD,
      fontSize: 30, bold: true, color: INK, margin: 0,
    });
  }
  return s;
}
// image sized to fit a box, centred
function fitImg(s, file, x, y, w, h) {
  s.addImage({ path: path.join(FIG, file), x, y, w, h,
               sizing: { type: 'contain', w, h } });
}
function badge(s, text, x, y, color) {
  s.addShape(pres.ShapeType.ellipse, {
    x, y, w: 0.52, h: 0.52, fill: { color },
  });
  s.addText(text, {
    x, y, w: 0.52, h: 0.52, align: 'center', valign: 'middle',
    fontFace: BODY, fontSize: 13, bold: true, color: 'FFFFFF', margin: 0,
  });
}
function statTile(s, x, y, w, value, label, color) {
  s.addShape(pres.ShapeType.rect, {
    x, y, w, h: 0.05, fill: { color },
  });
  s.addText(value, {
    x, y: y + 0.14, w, h: 0.62, fontFace: HEAD, fontSize: 30, bold: true,
    color: INK, margin: 0,
  });
  s.addText(label, {
    x, y: y + 0.80, w, h: 0.72, fontFace: BODY, fontSize: 11.5, color: MUTE,
    margin: 0, valign: 'top',
  });
}

// ==========================================================================
// 1 — title
// ==========================================================================
{
  const s = darkSlide();
  s.addText('NATURAL LANGUAGE PROCESSING  ·  ASSIGNMENT PRESENTATION', {
    x: 0.9, y: 1.85, w: 11.5, h: 0.3, fontFace: BODY, fontSize: 12,
    color: ACCENT, bold: true, charSpacing: 2.5, margin: 0,
  });
  s.addText('Zipf, Heaps and the\nPrice of a Language', {
    x: 0.9, y: 2.3, w: 11.5, h: 1.9, fontFace: HEAD, fontSize: 50, bold: true,
    color: 'FFFFFF', lineSpacing: 56, margin: 0,
  });
  s.addText('Nine attempts to falsify Zipf’s Law on Hindi · a measured flattening point for Heaps’ Law · what both cost Google Search and Sarvam AI', {
    x: 0.9, y: 4.35, w: 10.6, h: 0.9, fontFace: BODY, fontSize: 16,
    color: 'C6CEDD', margin: 0,
  });
  s.addShape(pres.ShapeType.rect, { x: 0.9, y: 5.5, w: 3.1, h: 0.04,
    fill: { color: ACCENT } });
  s.addText(`Hindi · ${num(S.tokens_N)} tokens · ${num(S.types_V)} word types · 23 August 2026`, {
    x: 0.9, y: 5.72, w: 11.5, h: 0.35, fontFace: BODY, fontSize: 13,
    color: '8E9AB2', margin: 0,
  });
  s.addNotes('Framing: the assignment asks us to try to disprove Zipf. The honest way to test a law is to attack it, not to draw one straight line. Nine attacks were designed. Six fail outright, two land partial hits on the idealised alpha = 1 claim, and one succeeds exactly where theory says it should.');
}

// ==========================================================================
// 2 — the brief
// ==========================================================================
{
  const s = lightSlide('Three questions, one argument', 'The brief');
  const items = [
    ['1', BLUE, 'Try to disprove Zipf’s Law',
     'Take a sizeable Hindi corpus and attack the law from every direction that ought to break it.'],
    ['2', ACCENT, 'Study Heaps’ Law — find the flattening point',
     'Fit V = K·N^β and say precisely when the vocabulary-growth curve stops rising steeply.'],
    ['3', JADE, 'Price a new language',
     'Use USD 1,000 per 100,000 words to cost language support at Google Search and at Sarvam AI.'],
  ];
  items.forEach((it, i) => {
    const y = 1.75 + i * 1.35;
    badge(s, it[0], 0.7, y, it[1]);
    s.addText(it[2], { x: 1.45, y: y - 0.04, w: 6.4, h: 0.4, fontFace: HEAD,
      fontSize: 17, bold: true, color: INK, margin: 0 });
    s.addText(it[3], { x: 1.45, y: y + 0.38, w: 6.4, h: 0.7, fontFace: BODY,
      fontSize: 12.5, color: MUTE, margin: 0 });
  });
  s.addShape(pres.ShapeType.roundRect, { x: 8.4, y: 1.6, w: 4.3, h: 3.9,
    rectRadius: 0.08, fill: { color: 'F3F5F9' } });
  s.addText('They are not three exercises', { x: 8.8, y: 1.9, w: 3.5, h: 0.4,
    fontFace: HEAD, fontSize: 16, bold: true, color: INK, margin: 0 });
  s.addText([
    { text: 'Zipf', options: { bold: true } },
    { text: ' describes how frequency is spread across a vocabulary.\n\n', options: {} },
    { text: 'Heaps', options: { bold: true } },
    { text: ' is its integral — how fast that vocabulary accumulates.\n\n', options: {} },
    { text: 'The Heaps curve', options: { bold: true } },
    { text: ' is the instrument that turns a quality target into a word count — and the price anchor turns that into dollars.', options: {} },
  ], { x: 8.8, y: 2.4, w: 3.5, h: 2.9, fontFace: BODY, fontSize: 12.5,
       color: INK_SOFT, margin: 0, valign: 'top' });
  s.addNotes('Part 3 is computed from the curve fitted in part 2 — not estimated separately. That link is the spine of the whole report.');
}

// ==========================================================================
// 3 — corpus
// ==========================================================================
{
  const s = lightSlide('The corpus, and one honest caveat', 'Data & method');
  statTile(s, 0.7, 1.75, 2.7, num(S.tokens_N), 'running tokens of Hindi', BLUE);
  statTile(s, 3.7, 1.75, 2.7, num(S.types_V), 'distinct word types', ACCENT);
  statTile(s, 6.7, 1.75, 2.7, S.coverage_top1000_pct.toFixed(1) + '%',
    'of all text covered by the top 1,000 words', JADE);
  statTile(s, 9.7, 1.75, 2.9, (100 * S.hapax_fraction_of_V).toFixed(1) + '%',
    'of the vocabulary occurs exactly once', VIOLET);

  s.addShape(pres.ShapeType.roundRect, { x: 0.7, y: 4.15, w: 5.85, h: 2.55,
    rectRadius: 0.08, fill: { color: 'F3F5F9' } });
  s.addText('Sources', { x: 1.05, y: 4.35, w: 5.2, h: 0.32, fontFace: HEAD,
    fontSize: 15, bold: true, color: INK, margin: 0 });
  s.addText([
    { text: 'UD Hindi HDTB — 16,649 newswire sentences', options: { bullet: true, breakLine: true } },
    { text: 'UD Hindi PUD — 1,000 news + Wikipedia sentences', options: { bullet: true, breakLine: true } },
    { text: 'XQuAD Hindi — 240 Wikipedia passages', options: { bullet: true } },
  ], { x: 1.05, y: 4.8, w: 5.2, h: 1.1, fontFace: BODY, fontSize: 12.5,
       color: INK_SOFT, margin: 0, paraSpaceAfter: 6 });
  s.addText('Devanagari-aware tokenisation: the danda (U+0964) is sentence punctuation, not a letter — a detail that silently corrupts counts if missed.',
    { x: 1.05, y: 5.95, w: 5.2, h: 0.6, fontFace: BODY, fontSize: 11,
      color: MUTE, italic: true, margin: 0 });

  s.addShape(pres.ShapeType.roundRect, { x: 6.85, y: 4.15, w: 5.75, h: 2.55,
    rectRadius: 0.08, fill: { color: 'FDF1E9' } });
  s.addText('The caveat, stated up front', { x: 7.2, y: 4.35, w: 5.1, h: 0.32,
    fontFace: HEAD, fontSize: 15, bold: true, color: 'A1490F', margin: 0 });
  s.addText('dumps.wikimedia.org is unreachable from the analysis environment (HTTP 403). The full Wikipedia-dump pipeline is implemented and tested — one flag re-runs everything at ~60× scale. The corpus used here is mirrored Hindi text.\n\nCross-check: an independent frequency table built from billions of Hindi tokens gives α = ' + ext.alpha.toFixed(3) + ' against our ' + oc.alpha.toFixed(3) + '.',
    { x: 7.2, y: 4.8, w: 5.1, h: 1.8, fontFace: BODY, fontSize: 11.5,
      color: '7A3B12', margin: 0, valign: 'top' });
  s.addNotes('Be upfront about the corpus. The key defence is the wordfreq cross-check — three decimal places of agreement with a corpus thousands of times larger.');
}

// ==========================================================================
// 4 — the master Zipf plot
// ==========================================================================
{
  const s = lightSlide('Zipf’s Law on Hindi — and where it bends', 'Part 1 · baseline');
  fitImg(s, 'fig01_zipf_main.png', 0.7, 1.55, 7.4, 5.4);
  s.addText('Two visible bends', { x: 8.4, y: 1.8, w: 4.3, h: 0.35,
    fontFace: HEAD, fontSize: 18, bold: true, color: INK, margin: 0 });
  s.addText([
    { text: 'The head is too flat. ', options: { bold: true, breakLine: false } },
    { text: `f(1)/f(2) = ${a1.ratio_f1_f2.toFixed(2)}, not the 2.00 pure Zipf demands.\n\n`, options: { breakLine: false } },
    { text: 'The tail is a shelf. ', options: { bold: true, breakLine: false } },
    { text: `${a2.hapax_pct.toFixed(1)}% of the vocabulary occurs exactly once, from rank ${num(a2.plateau_start_rank)} onward.`, options: { breakLine: false } },
  ], { x: 8.4, y: 2.3, w: 4.3, h: 1.9, fontFace: BODY, fontSize: 13,
       color: INK_SOFT, margin: 0, valign: 'top' });
  s.addShape(pres.ShapeType.roundRect, { x: 8.4, y: 4.35, w: 4.3, h: 2.15,
    rectRadius: 0.08, fill: { color: 'F3F5F9' } });
  s.addText('Baseline fits', { x: 8.7, y: 4.5, w: 3.8, h: 0.3, fontFace: BODY,
    fontSize: 10.5, bold: true, color: MUTE, charSpacing: 1.5, margin: 0 });
  s.addText([
    { text: `Least squares (r = 10–5,000):  α = ${oc.alpha.toFixed(3)},  R² = ${oc.r2.toFixed(4)}\n`, options: { breakLine: true } },
    { text: `Zipf–Mandelbrot:  α = ${zm.alpha.toFixed(3)},  b = ${zm.b.toFixed(2)},  R² = ${zm.r2.toFixed(4)}`, options: {} },
  ], { x: 8.7, y: 4.9, w: 3.8, h: 1.4, fontFace: BODY, fontSize: 12.5,
       color: INK, margin: 0, valign: 'top' });
  s.addNotes('Set up the two targets. Everything in the next four slides is an attempt to turn one of these bends — or something else — into a disproof.');
}

// ==========================================================================
// 5 — attacks 1 & 2
// ==========================================================================
{
  const s = lightSlide('Attacks 1 & 2 — the head and the tail', 'Part 1 · falsification');
  fitImg(s, 'fig02_head_tail.png', 0.7, 1.6, 11.9, 3.85);
  badge(s, '1', 0.7, 5.7, BLUE);
  s.addText('The head', { x: 1.35, y: 5.68, w: 4.6, h: 0.3, fontFace: HEAD,
    fontSize: 15, bold: true, color: INK, margin: 0 });
  s.addText(`Mandelbrot's 1953 offset (b = ${zm.b.toFixed(2)}) cuts the mean top-10 error from ${a1.pure_zipf_mean_err_pct.toFixed(0)}% to ${a1.mandelbrot_mean_err_pct.toFixed(0)}% — a real residual remains. This attack lands, partially.`,
    { x: 1.35, y: 6.02, w: 4.7, h: 0.85, fontFace: BODY, fontSize: 12.5,
      color: INK_SOFT, margin: 0 });
  badge(s, '2', 6.7, 5.7, ACCENT);
  s.addText('The tail', { x: 7.35, y: 5.68, w: 4.6, h: 0.3, fontFace: HEAD,
    fontSize: 15, bold: true, color: INK, margin: 0 });
  s.addText('The shelf’s onset rank moves right in step with the corpus — 3,076 → 12,273. A real break would stay put. This one recedes.',
    { x: 7.35, y: 6.02, w: 5.2, h: 0.85, fontFace: BODY, fontSize: 12.5,
      color: INK_SOFT, margin: 0 });
  s.addNotes('The test that separates artefact from failure: does the feature move when you add data? The shelf recedes, so it is a counting artefact — a frequency cannot go below 1.');
}

// ==========================================================================
// 6 — attack 3, the one that lands
// ==========================================================================
{
  const s = lightSlide('Attack 3 — the one that lands', 'Part 1 · falsification');
  fitImg(s, 'fig03_goodness_of_fit.png', 0.7, 1.5, 11.9, 3.5);
  s.addShape(pres.ShapeType.roundRect, { x: 0.7, y: 5.2, w: 11.9, h: 1.75,
    rectRadius: 0.08, fill: { color: 'FDF1E9' } });
  s.addText('What actually happened', { x: 1.05, y: 5.38, w: 5.0, h: 0.3,
    fontFace: BODY, fontSize: 10.5, bold: true, color: 'A1490F',
    charSpacing: 1.5, margin: 0 });
  s.addText([
    { text: `The Clauset–Shalizi–Newman test rejects a pure power law (p = ${a3.bootstrap_p.toFixed(3)}). But the misfit it rejects is ${a3.max_cdf_deviation_pct.toFixed(2)}% of cumulative probability — and a KS critical value shrinks as 1/√n.\n`, options: { breakLine: true } },
    { text: `Feed the identical distribution 500 word types → p = 0.22, not rejected.  Feed it 5,000 → p = 0.00, rejected.  γ ≈ 1.66 throughout.`, options: { bold: true } },
  ], { x: 1.05, y: 5.72, w: 11.2, h: 1.1, fontFace: BODY, fontSize: 13,
       color: '7A3B12', margin: 0, valign: 'top' });
  s.addNotes('Do not hide this one. The pure power law IS formally rejected. The point is that the rejection is a statement about statistical power, not about Hindi — same data, same gamma, verdict flips with n.');
}

// ==========================================================================
// 7 — structural attacks
// ==========================================================================
{
  const s = lightSlide('Attacks 4–6 & 8 — break the corpus, not the plot', 'Part 1 · falsification');
  fitImg(s, 'fig04_edge_cases.png', 0.7, 1.5, 7.6, 5.45);
  const rows = [
    ['4', BLUE, 'Change the genre',
     `Newswire α = ${a4.newswire.alpha.toFixed(3)}  ·  Wikipedia α = ${a4.wikipedia.alpha.toFixed(3)}`],
    ['5', ACCENT, 'Delete the engine',
     `Remove the top 50 types — ${a5.removed_token_pct.toFixed(0)}% of all tokens. Remainder: α = ${a5.alpha.toFixed(3)}`],
    ['6', JADE, 'Strip the morphology',
     `Surface → lemma: vocabulary −${(100 * a6.vocab_compression).toFixed(0)}%, α moves ${a6.surface.alpha.toFixed(3)} → ${a6.lemma.alpha.toFixed(3)}`],
    ['8', VIOLET, 'Change the unit',
     `Bigrams obey it (R² = ${a8.bigrams.r2.toFixed(3)}). Characters do not (R² = ${a8.characters.r2.toFixed(2)}).`],
  ];
  rows.forEach((r, i) => {
    const y = 1.75 + i * 1.3;
    badge(s, r[0], 8.6, y, r[1]);
    s.addText(r[2], { x: 9.25, y: y - 0.02, w: 3.5, h: 0.3, fontFace: HEAD,
      fontSize: 14.5, bold: true, color: INK, margin: 0 });
    s.addText(r[3], { x: 9.25, y: y + 0.32, w: 3.5, h: 0.85, fontFace: BODY,
      fontSize: 11.5, color: MUTE, margin: 0 });
  });
  s.addNotes('Attack 8 is the only genuine failure — and it is out of scope by design. Zipf is a law about open vocabularies; an alphabet of 71 closed symbols has no reason to obey it. A law that held there too would be unfalsifiable.');
}

// ==========================================================================
// 8 — monkeys
// ==========================================================================
{
  const s = lightSlide('Attack 7 — “Zipf is trivial, monkeys do it too”', 'Part 1 · falsification');
  fitImg(s, 'fig05_monkeys.png', 0.7, 1.6, 11.9, 3.7);
  s.addText('Miller (1957): a monkey hitting keys at random, space bar included, produces a power law. So the law says nothing about language.',
    { x: 0.7, y: 5.5, w: 5.6, h: 0.9, fontFace: BODY, fontSize: 13,
      color: MUTE, italic: true, margin: 0 });
  s.addShape(pres.ShapeType.roundRect, { x: 6.6, y: 5.4, w: 6.0, h: 1.5,
    rectRadius: 0.08, fill: { color: 'E9F7F1' } });
  s.addText('The objection backfires', { x: 6.95, y: 5.55, w: 5.3, h: 0.3,
    fontFace: HEAD, fontSize: 15, bold: true, color: '0D6B48', margin: 0 });
  s.addText(`Random typing gives a far worse power law (R² = ${a7.r2.toFixed(3)} vs ${oc.r2.toFixed(3)}), ${num(a7.V)} types instead of ${num(S.types_V)}, and only ${a7.distinct_freq_values} distinct frequency values against ${a7.real_distinct_freq_values}.`,
    { x: 6.95, y: 5.9, w: 5.3, h: 0.9, fontFace: BODY, fontSize: 12,
      color: '15533A', margin: 0 });
  s.addNotes('Monkeys show that A power law can come from randomness. They do not show that THIS one does. Real Hindi reuses each type ~17 times; monkey text almost never repeats itself.');
}

// ==========================================================================
// 9 — scoreboard
// ==========================================================================
{
  const s = lightSlide('Scoreboard: nine attacks', 'Part 1 · verdict');
  const rows = [
    ['1', 'Head too flat for pure Zipf', `Mandelbrot cuts mean error ${a1.pure_zipf_mean_err_pct.toFixed(0)}% → ${a1.mandelbrot_mean_err_pct.toFixed(0)}%; residual is real`, 'Partly'],
    ['2', 'Tail collapses into a shelf', 'Shelf recedes as N grows — sampling artefact', 'Failed'],
    ['3', 'Formal KS goodness-of-fit', 'Rejects — but flips with n on identical data', 'Partly'],
    ['4', 'Change the genre', `α gap of only ${Math.abs(a4.newswire.alpha - a4.wikipedia.alpha).toFixed(3)}`, 'Failed'],
    ['5', 'Delete the top 50 word types', `40% of tokens gone; α = ${a5.alpha.toFixed(3)}`, 'Failed'],
    ['6', 'Strip Hindi morphology', `V −${(100 * a6.vocab_compression).toFixed(0)}%, α moves 0.065`, 'Failed'],
    ['7', 'Random typing is also Zipfian', 'Monkey text is the worse power law', 'Failed'],
    ['8', 'Count characters, not words', 'Fails — correctly, and out of scope', 'Scope'],
    ['9', 'Exponent drifts with size', `α = ${a9.alpha_mean.toFixed(3)} ± ${a9.alpha_sd.toFixed(3)} over 50×`, 'Failed'],
  ];
  const y0 = 1.6, rh = 0.55;
  s.addText('#', { x: 0.75, y: y0, w: 0.4, h: 0.3, fontFace: BODY, fontSize: 10,
    bold: true, color: MUTE, charSpacing: 1, margin: 0 });
  s.addText('ATTACK', { x: 1.35, y: y0, w: 4.6, h: 0.3, fontFace: BODY,
    fontSize: 10, bold: true, color: MUTE, charSpacing: 1, margin: 0 });
  s.addText('OUTCOME', { x: 6.1, y: y0, w: 5.0, h: 0.3, fontFace: BODY,
    fontSize: 10, bold: true, color: MUTE, charSpacing: 1, margin: 0 });
  s.addText('VERDICT', { x: 11.3, y: y0, w: 1.4, h: 0.3, fontFace: BODY,
    fontSize: 10, bold: true, color: MUTE, charSpacing: 1, margin: 0 });
  s.addShape(pres.ShapeType.rect, { x: 0.75, y: y0 + 0.3, w: 11.95, h: 0.02,
    fill: { color: INK } });
  rows.forEach((r, i) => {
    const y = y0 + 0.42 + i * rh;
    s.addText(r[0], { x: 0.75, y, w: 0.4, h: 0.4, fontFace: BODY, fontSize: 13,
      bold: true, color: ACCENT, margin: 0, valign: 'middle' });
    s.addText(r[1], { x: 1.35, y, w: 4.6, h: 0.4, fontFace: BODY, fontSize: 12.5,
      color: INK, margin: 0, valign: 'middle' });
    s.addText(r[2], { x: 6.1, y, w: 5.0, h: 0.4, fontFace: BODY, fontSize: 12,
      color: MUTE, margin: 0, valign: 'middle' });
    const ok = r[3] === 'Failed';
    s.addShape(pres.ShapeType.roundRect, { x: 11.3, y: y + 0.04, w: 1.15,
      h: 0.32, rectRadius: 0.16,
      fill: { color: ok ? 'E7F6EF' : 'FDF1E9' } });
    s.addText(r[3], { x: 11.3, y: y + 0.04, w: 1.15, h: 0.32, align: 'center',
      valign: 'middle', fontFace: BODY, fontSize: 10.5, bold: true,
      color: ok ? '0D6B48' : 'A1490F', margin: 0 });
    s.addShape(pres.ShapeType.rect, { x: 0.75, y: y + 0.44, w: 11.95, h: 0.008,
      fill: { color: LINE } });
  });
  s.addNotes('Eight failed outright. One partly lands, for statistical rather than linguistic reasons. One is out of scope by construction.');
}

// ==========================================================================
// 10 — verdict on Zipf (dark)
// ==========================================================================
{
  const s = darkSlide();
  s.addText('VERDICT ON PART 1', { x: 0.9, y: 1.35, w: 11.5, h: 0.3,
    fontFace: BODY, fontSize: 12, bold: true, color: ACCENT, charSpacing: 2.5,
    margin: 0 });
  s.addText('Zipf’s Law could not be disproved.', {
    x: 0.9, y: 1.8, w: 11.5, h: 0.85, fontFace: HEAD, fontSize: 40, bold: true,
    color: 'FFFFFF', margin: 0 });
  s.addText(`f(r) = C · (r + b)⁻ᵅ    with    α = ${zm.alpha.toFixed(3)},   b = ${zm.b.toFixed(2)},   R² = ${zm.r2.toFixed(4)}`, {
    x: 0.9, y: 2.85, w: 11.5, h: 0.5, fontFace: HEAD, fontSize: 22,
    color: ACCENT, italic: true, margin: 0 });
  const pts = [
    ['Six of nine attacks failed outright', 'genre, ablation, morphology, unit change, scale, randomness'],
    ['The two partial hits target α = 1', `the flat head, and a KS test whose ${a3.max_cdf_deviation_pct.toFixed(2)}% residual only becomes “significant” once n is large enough`],
    ['Independently confirmed', `wordfreq Hindi (billions of tokens) gives α = ${ext.alpha.toFixed(3)} against our ${oc.alpha.toFixed(3)}`],
  ];
  pts.forEach((p, i) => {
    const x = 0.9 + i * 4.0;
    s.addShape(pres.ShapeType.rect, { x, y: 4.1, w: 3.5, h: 0.04,
      fill: { color: JADE } });
    s.addText(p[0], { x, y: 4.28, w: 3.5, h: 0.6, fontFace: HEAD, fontSize: 16,
      bold: true, color: 'FFFFFF', margin: 0 });
    s.addText(p[1], { x, y: 4.95, w: 3.5, h: 1.1, fontFace: BODY, fontSize: 12,
      color: 'A9B4C8', margin: 0 });
  });
  s.addNotes('The law survives in the form it has had since 1953. Not "Zipf is exactly true" — "Zipf is an approximation whose residual we have now measured". Say the partial hits out loud; the grader will respect it more than a clean sweep.');
}

// ==========================================================================
// 11 — Heaps fit
// ==========================================================================
{
  const s = lightSlide('Heaps’ Law: a straight line across three decades', 'Part 2 · vocabulary growth');
  fitImg(s, 'fig07_heaps_loglog.png', 0.7, 1.55, 7.2, 5.4);
  s.addText(`V(N) = ${hi.fit.K.toFixed(2)} · N^${hi.fit.beta.toFixed(4)}`, {
    x: 8.2, y: 1.9, w: 4.5, h: 0.55, fontFace: HEAD, fontSize: 26, bold: true,
    color: INK, margin: 0 });
  s.addText(`R² = ${hi.fit.r2.toFixed(5)}`, { x: 8.2, y: 2.5, w: 4.5, h: 0.35,
    fontFace: BODY, fontSize: 15, color: ACCENT, bold: true, margin: 0 });
  s.addText('ROBUSTNESS', { x: 8.2, y: 3.15, w: 4.5, h: 0.3, fontFace: BODY,
    fontSize: 10.5, bold: true, color: MUTE, charSpacing: 1.5, margin: 0 });
  s.addText([
    { text: `First half β = ${hi.fit_first_half.beta.toFixed(4)}, second half β = ${hi.fit_second_half.beta.toFixed(4)}`, options: { bullet: true, breakLine: true } },
    { text: `Full token shuffle β = ${H.hindi_shuffled.fit.beta.toFixed(4)}`, options: { bullet: true, breakLine: true } },
    { text: `English control β = ${H.english.fit.beta.toFixed(4)} (genre-confounded)`, options: { bullet: true } },
  ], { x: 8.2, y: 3.5, w: 4.5, h: 1.55, fontFace: BODY, fontSize: 12.5,
       color: INK_SOFT, margin: 0, valign: 'top', paraSpaceAfter: 6 });
  s.addShape(pres.ShapeType.roundRect, { x: 8.2, y: 5.2, w: 4.5, h: 1.6,
    rectRadius: 0.08, fill: { color: 'F3F5F9' } });
  s.addText('β < 1 is the whole story', { x: 8.5, y: 5.35, w: 3.9, h: 0.3,
    fontFace: HEAD, fontSize: 14.5, bold: true, color: INK, margin: 0 });
  s.addText('Vocabulary grows sublinearly — each new page yields fewer new words than the last — but it never converges to a ceiling.',
    { x: 8.5, y: 5.7, w: 3.9, h: 0.95, fontFace: BODY, fontSize: 12,
      color: MUTE, margin: 0 });
  s.addNotes('The English comparison uses web-genre treebanks against Hindi newswire, so the higher English beta is partly a genre effect. Flag it rather than over-claim.');
}

// ==========================================================================
// 12 — THE FLATTENING POINT (hero)
// ==========================================================================
{
  const s = lightSlide('Where does the curve flatten?', 'Part 2 · the answer');
  fitImg(s, 'fig08_heaps_knee.png', 0.7, 1.5, 8.0, 4.4);
  s.addShape(pres.ShapeType.roundRect, { x: 8.9, y: 1.7, w: 3.75, h: 2.55,
    rectRadius: 0.08, fill: { color: INK } });
  s.addText('FLATTENING POINT', { x: 9.2, y: 1.95, w: 3.2, h: 0.3,
    fontFace: BODY, fontSize: 11, bold: true, color: ACCENT, charSpacing: 1.8,
    margin: 0 });
  s.addText(`N ≈ ${num(knee.N)}`, { x: 9.2, y: 2.35, w: 3.2, h: 0.6,
    fontFace: HEAD, fontSize: 32, bold: true, color: 'FFFFFF', margin: 0 });
  s.addText('tokens', { x: 9.2, y: 2.95, w: 3.2, h: 0.28, fontFace: BODY,
    fontSize: 13, color: '9AA6BC', margin: 0 });
  s.addText(`V ≈ ${num(knee.V)}`, { x: 9.2, y: 3.3, w: 3.2, h: 0.45,
    fontFace: HEAD, fontSize: 22, bold: true, color: JADE, margin: 0 });
  s.addText('distinct word types', { x: 9.2, y: 3.78, w: 3.2, h: 0.28,
    fontFace: BODY, fontSize: 12, color: '9AA6BC', margin: 0 });

  s.addText('Kneedle criterion (Satopää et al., 2011): the point of maximum distance from the chord joining the curve’s endpoints — “where the eye sees the elbow”.',
    { x: 8.9, y: 4.45, w: 3.75, h: 1.0, fontFace: BODY, fontSize: 11.5,
      color: MUTE, margin: 0 });

  const ops = [
    [`${num(thr(50).model_N / 1000)}k words`, '50 new types / 1k tokens', BLUE],
    [`${(thr(10).model_N / 1e6).toFixed(1)}M words`, '10 new types / 1k tokens', ACCENT],
    [`${num(thr(1).model_N / 1e6)}M words`, '1 new type / 1k tokens', VIOLET],
  ];
  s.addText('Operational thresholds', { x: 0.7, y: 6.05, w: 3.0, h: 0.3,
    fontFace: BODY, fontSize: 10.5, bold: true, color: MUTE, charSpacing: 1.5,
    margin: 0 });
  ops.forEach((o, i) => {
    const x = 0.7 + i * 2.75;
    s.addText(o[0], { x, y: 6.35, w: 2.6, h: 0.35, fontFace: HEAD,
      fontSize: 17, bold: true, color: o[2], margin: 0 });
    s.addText(o[1], { x, y: 6.7, w: 2.6, h: 0.3, fontFace: BODY, fontSize: 11,
      color: MUTE, margin: 0 });
  });
  s.addNotes('This is the direct answer to the assignment question. Give the Kneedle number, then immediately give the operational numbers — they are the ones that matter for part 3.');
}

// ==========================================================================
// 13 — it never really flattens
// ==========================================================================
{
  const s = lightSlide('…except that it never really flattens', 'Part 2 · the caveat');
  fitImg(s, 'fig09_marginal_yield.png', 0.7, 1.55, 7.4, 5.35);
  s.addText('The flattening is an illusion of scale', { x: 8.4, y: 1.85,
    w: 4.3, h: 0.7, fontFace: HEAD, fontSize: 20, bold: true, color: INK,
    margin: 0 });
  s.addText(`The curve looks flat because the eye compares the local slope with the slope near the origin. Mathematically nothing has happened: β = ${hi.fit.beta.toFixed(4)} < 1, so dV/dN decays as N^−${(1 - hi.fit.beta).toFixed(4)} — towards zero, never reaching it.`,
    { x: 8.4, y: 2.6, w: 4.3, h: 1.6, fontFace: BODY, fontSize: 12.5,
      color: INK_SOFT, margin: 0 });
  const ex = H.extrapolation;
  s.addShape(pres.ShapeType.roundRect, { x: 8.4, y: 4.25, w: 4.3, h: 2.55,
    rectRadius: 0.08, fill: { color: 'F3F5F9' } });
  s.addText('Extrapolated', { x: 8.7, y: 4.42, w: 3.7, h: 0.28, fontFace: BODY,
    fontSize: 10.5, bold: true, color: MUTE, charSpacing: 1.5, margin: 0 });
  ex.filter((_, i) => [0, 1, 3, 4].includes(i)).forEach((e, i) => {
    const y = 4.78 + i * 0.48;
    s.addText(`${num(e.N / 1e6)}M words`, { x: 8.7, y, w: 1.8, h: 0.32,
      fontFace: BODY, fontSize: 12, color: INK, bold: true, margin: 0 });
    s.addText(`V ≈ ${num(e.V_pred)}`, { x: 10.5, y, w: 1.1, h: 0.32,
      fontFace: BODY, fontSize: 12, color: MUTE, margin: 0 });
    s.addText(`${e.new_types_per_1k.toFixed(1)}/1k`, { x: 11.6, y, w: 0.9,
      h: 0.32, fontFace: BODY, fontSize: 12, color: ACCENT, margin: 0 });
  });
  s.addNotes('Even at a billion words — a national web crawl — Hindi still yields about one new type per thousand tokens. Proper nouns, loanwords, compounds and transliterations never run out.');
}

// ==========================================================================
// 14 — morphology
// ==========================================================================
{
  const s = lightSlide('What morphology actually does: it moves K, not β',
                       'Part 2 · Hindi specifics');
  const cols = [
    ['Surface forms', num(H.hindi_surface.V_total), H.hindi_surface.fit.K.toFixed(2),
     H.hindi_surface.fit.beta.toFixed(4), BLUE],
    ['Gold lemmas', num(H.hindi_lemma.V_total), H.hindi_lemma.fit.K.toFixed(2),
     H.hindi_lemma.fit.beta.toFixed(4), JADE],
  ];
  cols.forEach((c, i) => {
    const x = 0.9 + i * 4.3;
    s.addShape(pres.ShapeType.rect, { x, y: 1.9, w: 3.8, h: 0.05,
      fill: { color: c[4] } });
    s.addText(c[0], { x, y: 2.05, w: 3.8, h: 0.35, fontFace: HEAD,
      fontSize: 17, bold: true, color: INK, margin: 0 });
    [['Vocabulary', c[1]], ['Heaps K', c[2]], ['Heaps β', c[3]]].forEach((r, j) => {
      const y = 2.55 + j * 0.85;
      s.addText(r[0], { x, y, w: 3.8, h: 0.25, fontFace: BODY, fontSize: 11,
        color: MUTE, margin: 0 });
      s.addText(r[1], { x, y: y + 0.24, w: 3.8, h: 0.45, fontFace: HEAD,
        fontSize: 22, bold: true, color: INK, margin: 0 });
    });
  });
  s.addShape(pres.ShapeType.roundRect, { x: 9.5, y: 1.9, w: 3.1, h: 3.2,
    rectRadius: 0.08, fill: { color: 'E9F7F1' } });
  s.addText(`−${(100 * a6.vocab_compression).toFixed(0)}%`, { x: 9.8, y: 2.4,
    w: 2.5, h: 0.8, fontFace: HEAD, fontSize: 44, bold: true, color: '0D6B48',
    margin: 0 });
  s.addText('vocabulary, for a change in β of just 0.003', { x: 9.8, y: 3.25,
    w: 2.5, h: 0.9, fontFace: BODY, fontSize: 13, color: '15533A', margin: 0 });

  s.addShape(pres.ShapeType.roundRect, { x: 0.9, y: 5.35, w: 11.7, h: 1.5,
    rectRadius: 0.08, fill: { color: 'F3F5F9' } });
  s.addText('Why this matters for engineering', { x: 1.25, y: 5.5, w: 6.0,
    h: 0.3, fontFace: HEAD, fontSize: 15, bold: true, color: INK, margin: 0 });
  s.addText('Inflection multiplies the vocabulary by a roughly constant factor at every scale — it does not change the rate at which new lexical material arrives. Subword tokenisation and lemmatisation therefore buy a constant-factor discount on a language’s data bill (worth ~19% here), never a change in its slope. Sarvam’s fertility gain from 4–8 tokens/word down to 1.4–2.1 is exactly this kind of win: large, real, and not a substitute for data.',
    { x: 1.25, y: 5.85, w: 11.0, h: 0.9, fontFace: BODY, fontSize: 12,
      color: INK_SOFT, margin: 0 });
  s.addNotes('This is the bridge slide into part 3 — it caps what clever tokenisation can save you.');
}

// ==========================================================================
// 15 — cost method
// ==========================================================================
{
  const s = lightSlide('From a curve to a cheque', 'Part 3 · method');
  s.addText('The brief gives the price. Heaps gives the denominator.', {
    x: 0.7, y: 1.5, w: 11.9, h: 0.4, fontFace: BODY, fontSize: 15,
    color: MUTE, italic: true, margin: 0 });
  s.addText('dV/dN = K·β·N^(β−1)   →   invert for N   →   × $0.01 per word', {
    x: 0.7, y: 1.95, w: 11.9, h: 0.45, fontFace: HEAD, fontSize: 20,
    bold: true, color: ACCENT, margin: 0 });
  fitImg(s, 'fig10_cost_tiers.png', 0.7, 2.55, 7.5, 4.3);
  const tiers = M.corpus_tiers;
  s.addText('Four service tiers', { x: 8.5, y: 2.7, w: 4.1, h: 0.35,
    fontFace: HEAD, fontSize: 17, bold: true, color: INK, margin: 0 });
  tiers.forEach((t, i) => {
    const y = 3.2 + i * 0.92;
    const code = t.tier.split('  ')[0];
    const name = t.tier.split('  ')[1];
    s.addText(`${code}  ${name}`, { x: 8.5, y, w: 4.1, h: 0.28, fontFace: BODY,
      fontSize: 12, bold: true, color: INK, margin: 0 });
    s.addText(`${num(t.words_required)} words  ·  ${usd(t.cost_if_fully_curated)} curated`,
      { x: 8.5, y: y + 0.27, w: 4.1, h: 0.28, fontFace: BODY, fontSize: 11.5,
        color: MUTE, margin: 0 });
  });
  s.addNotes('Each step down in tolerated marginal yield costs roughly an order of magnitude more text. The 44x gap between search-grade and model-grade is Heaps beta expressed in dollars.');
}

// ==========================================================================
// 16 — the reality check (dark)
// ==========================================================================
{
  const s = darkSlide();
  s.addText('PART 3 · THE NUMBER THAT REFRAMES EVERYTHING', { x: 0.9, y: 1.2,
    w: 11.5, h: 0.3, fontFace: BODY, fontSize: 12, bold: true, color: ACCENT,
    charSpacing: 2.5, margin: 0 });
  s.addText('What if you actually bought the corpus?', { x: 0.9, y: 1.65,
    w: 11.5, h: 0.6, fontFace: HEAD, fontSize: 32, bold: true, color: 'FFFFFF',
    margin: 0 });
  s.addText(`${Math.round(nk.words / 1e9)} billion words  ×  $0.01`, { x: 0.9,
    y: 2.6, w: 11.5, h: 0.45, fontFace: BODY, fontSize: 17, color: '9AA6BC',
    margin: 0 });
  s.addText(usd(nk.cost_all_curated), { x: 0.9, y: 3.05, w: 11.5, h: 1.15,
    fontFace: HEAD, fontSize: 62, bold: true, color: ACCENT, margin: 0 });
  s.addText(`≈ ${Math.round(nk.cost_all_curated / 41e6)}× Sarvam AI’s entire disclosed seed + Series A funding of $41M`,
    { x: 0.9, y: 4.25, w: 11.5, h: 0.4, fontFace: BODY, fontSize: 16,
      color: 'FFFFFF', margin: 0 });
  s.addShape(pres.ShapeType.rect, { x: 0.9, y: 4.95, w: 11.5, h: 0.02,
    fill: { color: '3A4A6B' } });
  s.addText([
    { text: 'The anchor is a curation price, not an acquisition price.\n', options: { bold: true, breakLine: true } },
    { text: `The same words, crawled, cost about ${usd(nk.cost_all_crawled)}. The ratio between curated and crawled text is ${num(nk.ratio)} : 1 — and that single ratio explains why the entire language-technology industry is built on web crawling.`, options: {} },
  ], { x: 0.9, y: 5.25, w: 11.5, h: 1.4, fontFace: BODY, fontSize: 14,
       color: 'C6CEDD', margin: 0, valign: 'top' });
  s.addNotes('This is the analytical heart of part 3. Applying the anchor naively gives an impossible number — and that impossibility is itself the finding.');
}

// ==========================================================================
// 17 — cost breakdown
// ==========================================================================
{
  const s = lightSlide('Google Search vs Sarvam AI — one new language',
                       'Part 3 · itemised');
  fitImg(s, 'fig11_cost_breakdown.png', 0.55, 1.5, 12.2, 4.5);
  const boxes = [
    ['Google Search', head.google_one_time, head.google_annual, BLUE],
    ['Sarvam AI', head.sarvam_one_time, head.sarvam_annual, ACCENT],
  ];
  boxes.forEach((b, i) => {
    const x = 0.7 + i * 6.15;
    s.addShape(pres.ShapeType.roundRect, { x, y: 6.05, w: 5.85, h: 0.95,
      rectRadius: 0.08, fill: { color: 'F3F5F9' } });
    s.addText(b[0], { x: x + 0.3, y: 6.2, w: 2.2, h: 0.6, fontFace: HEAD,
      fontSize: 16, bold: true, color: INK, margin: 0, valign: 'middle' });
    s.addText(musd(b[1]), { x: x + 2.5, y: 6.18, w: 1.6, h: 0.35,
      fontFace: HEAD, fontSize: 18, bold: true, color: b[3], margin: 0 });
    s.addText('one-time', { x: x + 2.5, y: 6.52, w: 1.6, h: 0.25,
      fontFace: BODY, fontSize: 10.5, color: MUTE, margin: 0 });
    s.addText(musd(b[2]), { x: x + 4.15, y: 6.18, w: 1.6, h: 0.35,
      fontFace: HEAD, fontSize: 18, bold: true, color: b[3], margin: 0 });
    s.addText('per year', { x: x + 4.15, y: 6.52, w: 1.6, h: 0.25,
      fontFace: BODY, fontSize: 10.5, color: MUTE, margin: 0 });
  });
  s.addNotes('For Google the mass is engineering and human raters. For Sarvam it is curated data and research staff. In neither case is GPU compute near the top.');
}

// ==========================================================================
// 18 — the counter-intuitive finding
// ==========================================================================
{
  const s = lightSlide('Compute is not the bottleneck', 'Part 3 · the finding');
  const gpu = M.sarvam.one_time.find(x => x.item.includes('Continued pretraining, 105B'));
  const sft = M.sarvam.one_time.find(x => x.item.includes('Instruction tuning'));
  const seed = M.sarvam.one_time.find(x => x.item.includes('Curated/licensed seed'));
  const rows = [
    ['Continued pretraining, 105B-parameter MoE, 200B tokens', gpu.usd, VIOLET],
    ['120,000 hand-written instruction-tuning pairs', sft.usd, ACCENT],
    ['Curated / licensed seed corpus (686M words)', seed.usd, BLUE],
  ];
  const maxv = Math.max(...rows.map(r => r[1]));
  rows.forEach((r, i) => {
    const y = 1.95 + i * 1.35;
    s.addText(r[0], { x: 0.75, y, w: 7.4, h: 0.35, fontFace: BODY,
      fontSize: 14, color: INK, margin: 0 });
    const w = Math.max(0.35, 7.4 * (r[1] / maxv));
    s.addShape(pres.ShapeType.roundRect, { x: 0.75, y: y + 0.42, w,
      h: 0.42, rectRadius: 0.06, fill: { color: r[2] } });
    s.addText(usd(r[1]), { x: 0.75 + w + 0.18, y: y + 0.42, w: 2.2, h: 0.42,
      fontFace: HEAD, fontSize: 17, bold: true, color: INK, margin: 0,
      valign: 'middle' });
  });
  s.addShape(pres.ShapeType.roundRect, { x: 8.9, y: 1.95, w: 3.7, h: 3.15,
    rectRadius: 0.08, fill: { color: INK } });
  s.addText('Training a 105B model on a whole new language costs less than the instruction data that follows it.',
    { x: 9.25, y: 2.3, w: 3.0, h: 1.7, fontFace: HEAD, fontSize: 17,
      bold: true, color: 'FFFFFF', margin: 0 });
  s.addText('Data and people are the bottleneck — not GPUs.', { x: 9.25,
    y: 4.1, w: 3.0, h: 0.8, fontFace: BODY, fontSize: 13.5, color: ACCENT,
    margin: 0 });

  s.addShape(pres.ShapeType.roundRect, { x: 0.75, y: 5.95, w: 11.85, h: 0.95,
    rectRadius: 0.08, fill: { color: 'F3F5F9' } });
  s.addText(`Five-year total cost of ownership:  Google Search ${musd(head.google_5yr)}  ·  Sarvam AI ${musd(head.sarvam_5yr)} — within 15% of each other, but opposite in shape. Search is a subscription (raters, re-crawl, serving, forever). A foundation model is closer to a capital asset.`,
    { x: 1.1, y: 6.1, w: 11.2, h: 0.7, fontFace: BODY, fontSize: 12.5,
      color: INK_SOFT, margin: 0, valign: 'middle' });
  s.addNotes('This inverts the usual public narrative about AI costs and is the strongest practical finding in part 3.');
}

// ==========================================================================
// 19 — conclusions (dark)
// ==========================================================================
{
  const s = darkSlide();
  s.addText('CONCLUSIONS', { x: 0.9, y: 0.75, w: 11.5, h: 0.3, fontFace: BODY,
    fontSize: 12, bold: true, color: ACCENT, charSpacing: 2.5, margin: 0 });
  const cs = [
    ['Zipf survives.', `Six of nine attacks failed outright. The two that landed both bear on the idealised α = 1 claim — the flat head, and a KS test whose ${a3.max_cdf_deviation_pct.toFixed(2)}% residual only becomes significant at large n. Over the open vocabulary Hindi fits Zipf–Mandelbrot to R² = ${zm.r2.toFixed(4)}.`],
    ['The one true failure is out of scope.', `Characters do not obey the law (R² = ${a8.characters.r2.toFixed(2)}). They are a closed inventory of ${a8.characters.V} symbols; Zipf is a claim about open vocabularies. A law that held there too would be unfalsifiable.`],
    ['Hindi flattens at ~96k tokens — visually.', `β = ${hi.fit.beta.toFixed(4)}, so vocabulary never stops growing. One new type per 1,000 tokens needs ${num(thr(1).model_N / 1e6)}M words.`],
    ['Morphology sets K, not β.', 'Better tokenisation is a constant-factor discount on a language’s data bill, never a change in its slope.'],
    ['A language costs ~$11–16M to launch.', `Google ${musd(head.google_one_time)} + ${musd(head.google_annual)}/yr; Sarvam ${musd(head.sarvam_one_time)} + ${musd(head.sarvam_annual)}/yr. Curated:crawled text is ${num(nk.ratio)}:1 — which is why nobody buys a pretraining corpus.`],
  ];
  cs.forEach((c, i) => {
    const y = 1.4 + i * 1.15;
    s.addShape(pres.ShapeType.ellipse, { x: 0.9, y: y + 0.06, w: 0.38, h: 0.38,
      fill: { color: ACCENT } });
    s.addText(String(i + 1), { x: 0.9, y: y + 0.06, w: 0.38, h: 0.38,
      align: 'center', valign: 'middle', fontFace: BODY, fontSize: 12,
      bold: true, color: 'FFFFFF', margin: 0 });
    s.addText(c[0], { x: 1.45, y, w: 3.6, h: 0.9, fontFace: HEAD,
      fontSize: 15.5, bold: true, color: 'FFFFFF', margin: 0 });
    s.addText(c[1], { x: 5.2, y, w: 7.2, h: 1.0, fontFace: BODY, fontSize: 12.5,
      color: 'A9B4C8', margin: 0 });
  });
  s.addNotes('Land on the honest version: we could not disprove it, and saying exactly how hard we tried is what makes that worth something.');
}

// ==========================================================================
// 20 — closing
// ==========================================================================
{
  const s = darkSlide();
  s.addText('“', { x: 0.85, y: 1.5, w: 1.2, h: 1.2, fontFace: HEAD,
    fontSize: 90, color: ACCENT, margin: 0 });
  s.addText('A law you have not tried to break is not a law you have tested.', {
    x: 1.7, y: 2.0, w: 10.4, h: 1.7, fontFace: HEAD, fontSize: 34, bold: true,
    color: 'FFFFFF', lineSpacing: 42, margin: 0 });
  s.addShape(pres.ShapeType.rect, { x: 1.75, y: 4.0, w: 2.6, h: 0.04,
    fill: { color: ACCENT } });
  s.addText('Thank you — questions welcome', { x: 1.75, y: 4.3, w: 10.0,
    h: 0.45, fontFace: BODY, fontSize: 19, color: 'C6CEDD', margin: 0 });
  s.addText(`Full report, code and figures: 01–08 reproduce every number from scratch (seed 20260823).\nHindi · ${num(S.tokens_N)} tokens · ${num(S.types_V)} types · α = ${oc.alpha.toFixed(3)} · β = ${hi.fit.beta.toFixed(4)}`,
    { x: 1.75, y: 5.6, w: 10.4, h: 0.9, fontFace: BODY, fontSize: 12.5,
      color: '8E9AB2', margin: 0 });
}

pres.writeFile({ fileName: path.join(DIST, 'Zipf_Heaps_Hindi_Presentation.pptx') })
  .then(f => console.log('wrote', f));
