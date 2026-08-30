const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const FIG = path.join(ROOT, "figures");
const DIST = path.join(ROOT, "dist");
if (!fs.existsSync(DIST)) fs.mkdirSync(DIST, { recursive: true });

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5

const INK = "1A1A1A", MUTE = "666666", BG = "FFFFFF", ACCENT = "1D4ED8", CARD = "F2F2F2";
const FONT = "Georgia";

function titleSlide() {
  const s = pres.addSlide();
  s.background = { color: BG };
  s.addText("NATURAL LANGUAGE PROCESSING · ASSIGNMENT 2", {
    x: 0.7, y: 0.55, w: 11.9, h: 0.4, fontFace: "Arial", fontSize: 12,
    color: MUTE, charSpacing: 2, isTextBox: true,
  });
  s.addText("Tokens, Not Words", {
    x: 0.7, y: 1.1, w: 11.9, h: 1.1, fontFace: FONT, fontSize: 44, bold: true,
    color: INK, isTextBox: true,
  });
  s.addText("Zipf's Law Under the Tokenizer", {
    x: 0.7, y: 2.05, w: 11.9, h: 0.7, fontFace: FONT, fontSize: 26,
    color: ACCENT, isTextBox: true,
  });
  s.addText(
    "Whether tokens obey Zipf's law across English, Hindi and Arabic; how LLaMA, Qwen and " +
    "Kimi's tokenizers differ; and whether a vocabulary-size sweet spot can be found algorithmically.",
    { x: 0.7, y: 2.85, w: 10.5, h: 0.9, fontFace: FONT, italic: true, fontSize: 15, color: "333333", isTextBox: true }
  );
  const stats = [
    ["54", "BPE tokenizers trained"],
    ["3", "languages · 3 scripts"],
    ["18", "vocab sizes per language"],
    ["4", "criteria for the sweet spot"],
  ];
  let x = 0.7;
  stats.forEach(([n, l]) => {
    s.addShape("rect", { x, y: 4.1, w: 2.75, h: 1.35, fill: { color: CARD }, line: { type: "none" } });
    s.addText(n, { x, y: 4.25, w: 2.75, h: 0.6, align: "center", fontFace: "Arial", fontSize: 30, bold: true, color: INK, isTextBox: true });
    s.addText(l, { x, y: 4.85, w: 2.75, h: 0.5, align: "center", fontFace: "Arial", fontSize: 11, color: MUTE, isTextBox: true });
    x += 2.95;
  });
  s.addText("30 August 2026", { x: 0.7, y: 6.9, w: 6, h: 0.4, fontFace: "Arial", fontSize: 11, color: MUTE, isTextBox: true });
}

function sectionSlide(kicker, title) {
  const s = pres.addSlide();
  s.background = { color: INK };
  s.addText(kicker, { x: 0.9, y: 3.0, w: 11.5, h: 0.5, fontFace: "Arial", fontSize: 13, color: "AAAAAA", charSpacing: 2, isTextBox: true });
  s.addText(title, { x: 0.9, y: 3.4, w: 11.5, h: 1.4, fontFace: FONT, fontSize: 36, bold: true, color: "FFFFFF", isTextBox: true });
  return s;
}

function bulletSlide(title, bullets, opts = {}) {
  const s = pres.addSlide();
  s.background = { color: BG };
  s.addText(title, { x: 0.7, y: 0.5, w: 11.9, h: 0.8, fontFace: FONT, fontSize: 26, bold: true, color: INK, isTextBox: true });
  const items = bullets.map((b, i) => ({
    text: b, options: { bullet: { code: "2022" }, breakLine: i < bullets.length - 1, paraSpaceAfter: 14 },
  }));
  s.addText(items, { x: 0.7, y: 1.5, w: opts.w || 11.9, h: 5.3, fontFace: FONT, fontSize: opts.fontSize || 17, color: "222222", valign: "top", isTextBox: true });
  return s;
}

function figureSlide(title, imgName, caption, opts = {}) {
  const s = pres.addSlide();
  s.background = { color: BG };
  s.addText(title, { x: 0.6, y: 0.35, w: 12.1, h: 0.7, fontFace: FONT, fontSize: 24, bold: true, color: INK, isTextBox: true });
  const imgPath = path.join(FIG, imgName);
  s.addImage({ path: imgPath, x: opts.x || 0.9, y: opts.y || 1.1, w: opts.w || 11.5, h: opts.h || 5.6, sizing: { type: "contain", w: opts.w || 11.5, h: opts.h || 5.6 } });
  if (caption) {
    s.addText(caption, { x: 0.9, y: 6.85, w: 11.5, h: 0.5, fontFace: "Arial", fontSize: 11, italic: true, color: MUTE, isTextBox: true });
  }
  return s;
}

function tableSlide(title, header, rows, opts = {}) {
  const s = pres.addSlide();
  s.background = { color: BG };
  s.addText(title, { x: 0.7, y: 0.5, w: 11.9, h: 0.8, fontFace: FONT, fontSize: 24, bold: true, color: INK, isTextBox: true });
  const tableRows = [header.map(h => ({ text: h, options: { bold: true, fill: { color: CARD }, color: INK } }))]
    .concat(rows.map(r => r.map(c => ({ text: String(c), options: {} }))));
  s.addTable(tableRows, {
    x: 0.7, y: 1.5, w: 11.9, h: opts.h || 4.8, fontFace: "Arial", fontSize: opts.fontSize || 13,
    color: "222222", border: { type: "solid", color: "DDDDDD", pt: 0.75 }, autoPage: false,
    colW: opts.colW,
  });
  return s;
}

// ---------------------------------------------------------------- Deck
titleSlide();

bulletSlide("Executive summary", [
  "Assignment 1 asked whether Zipf's law survives at the word level. This asks: does it survive at the token level, the unit language models actually consume?",
  "54 byte-level BPE tokenizers trained across an 18-point vocab sweep x English, Hindi, Arabic + 4 model-style replicas (LLaMA-2/3, Qwen-2.5/3, Kimi-K2/K3).",
  "Answer: tokens obey Zipf's law, and better than words do in the mid-vocabulary band (R\u00B2 up to 0.999) \u2014 but not automatically at every vocab size.",
  "A qualified vocabulary-size sweet spot exists: 3 of 4 independent criteria converge to a 3\u201316k-token band per language at this corpus scale.",
  "Hindi's Devanagari script caps achievable BPE vocabulary an order of magnitude below English/Arabic \u2014 a token-level echo of Assignment 1's Heaps' Law finding.",
]);

sectionSlide("PART 1", "Do Tokens Follow Zipf's Law?");

figureSlide("Word-level baseline: English, Hindi, Arabic", "fig01_word_zipf.png",
  "All three show the classic Zipf shape at the word level \u2014 the starting point before any tokenizer touches the text.");

figureSlide("Zipf exponent & fit quality vs vocabulary size", "fig03_alpha_r2_vs_vocab.png",
  "Three regimes: near-character (\u03B1\u22484), word-fragment (\u03B1 crosses 1, R\u00B2>0.99), large-vocabulary (R\u00B2 stays high, \u03B1 drifts).");

figureSlide("Token rank\u2013frequency shape across the sweep", "fig02_token_zipf_by_vocab.png",
  "The curve flattens and straightens from vocab 500 to 8,000 per language, then holds roughly steady.");

bulletSlide("Answer: Q1", [
  "Yes \u2014 tokens obey Zipf's law, and in the 6,000\u201316,000 vocab band they obey it more cleanly than words (R\u00B2 up to 0.999 vs Assignment 1's 0.990 for Hindi words).",
  "But the fit is vocabulary-size dependent: near-character vocabularies overshoot badly (\u03B1\u22484, R\u00B2 as low as 0.55), and very large vocabularies drift mildly away from \u03B1=1.",
  "Subword tokenisation is a Zipf-law-improving transformation: it removes the flat head (rare word-forms split into shared subwords) and thins the hapax shelf.",
]);

sectionSlide("PART 2", "LLaMA vs Qwen vs Kimi");

tableSlide("Published vocabulary size & scheme", ["Family", "Vocab (target)", "Scheme", "Source"], [
  ["LLaMA-2", "32,000", "SentencePiece BPE", "Touvron et al., 2023"],
  ["LLaMA-3", "128,000", "byte-level BPE (tiktoken-style)", "Meta AI, 2024"],
  ["Qwen-2.5 / 3", "151,643", "byte-level BPE", "tiktoken qwen2 encoding"],
  ["Kimi-K2 / K3", "163,584", "byte-level BPE (tiktoken.model)", "Moonshot AI, 2025-26"],
], { h: 3.2, fontSize: 15 });

figureSlide("Target vocab vs what our corpus can actually reach", "fig06_model_comparison.png",
  "English/Arabic saturate ~57k-60k regardless of a 128k/152k/164k target. Hindi saturates at 6,927 for every target.");

bulletSlide("Answer: Q3 \u2014 how do they differ?", [
  "Published vocab sizes span 5x: 32k (LLaMA-2) to 164k (Kimi-K2/K3) \u2014 a real design trade-off between sequence length and embedding-table cost.",
  "On this study's corpus, the three large-vocab families (128k-164k target) all converge to the SAME data-bound ceiling (~57k-60k for English/Arabic).",
  "That ceiling is set by the corpus's own repeated-substring structure, not the trainer's target \u2014 vocab size is a training-data-scale decision.",
  "Hindi's ceiling (6,927) sits an order of magnitude below \u2014 explained by Devanagari's multi-codepoint akshara structure sparsifying byte-pair repeats.",
], { fontSize: 16 });

sectionSlide("PART 3", "The Vocabulary-Size Sweet Spot");

figureSlide("Compression curve: fertility vs vocabulary size", "fig04_fertility_knee.png",
  "Stars = Kneedle knee. Hindi's curve plateaus near 3.45 tokens/word early \u2014 the BPE ceiling, not a genuine sweet spot.");

figureSlide("Vocabulary utilisation vs vocabulary size", "fig05_utilisation.png",
  "All three languages peak in the mid-thousands, then decline as vocabulary outgrows the corpus's ability to exercise every merge.");

tableSlide("Four independent sweet-spot criteria", ["Language", "Fertility knee", "Zipf-stability", "Utilisation peak", "Marginal-yield rule"], [
  ["English", "4,000", "8,000", "6,000 (98.2%)", "32,000"],
  ["Hindi", "500", "6,000", "4,000 (95.2%)", "3,000"],
  ["Arabic", "3,000", "3,000", "12,000 (98.1%)", "60,335"],
], { h: 2.6, fontSize: 15 });

figureSlide("All four criteria, side by side", "fig07_sweetspot_summary.png",
  "3 of 4 criteria cluster within ~3-5x for English/Arabic. Marginal-yield never hits a hard floor \u2014 gains just keep shrinking, like Heaps' Law.");

bulletSlide("Answer: Q5\u2013Q6 \u2014 sweet spot & Zipf-stabilisation", [
  "Yes, in a qualified sense: fertility-knee, Zipf-stability and utilisation-peak converge to a 3,000\u201316,000-merge band per language at this corpus scale.",
  "The 4th criterion (marginal byte-yield) confirms there's no hard stopping point in principle \u2014 compression keeps improving, just by shrinking amounts.",
  "Zipf-stabilisation is a USABLE, CHEAP proxy for the sweet spot: within 2x of the fertility-knee for 2 of 3 languages, and monitorable online during training \u2014 no held-out compression sweep required.",
], { fontSize: 17 });

sectionSlide("PART 4", "An Algorithm for Choosing Vocab Size");

bulletSlide("Proposed stopping rule", [
  "1. Train BPE incrementally; checkpoint the merge table every \u0394V vocab slots (e.g. every 500-1,000).",
  "2. At each checkpoint, re-encode a held-out sample and record: Zipf \u03B1 & R\u00B2, vocabulary utilisation, fertility.",
  "3. Stop when, for 3 consecutive checkpoints, ALL THREE hold: R\u00B2 within 0.5% of its running max; utilisation has declined >2pp from its running max; marginal fertility gain per 1,000 slots < 1% of fertility achieved.",
  "4. Report that vocab size as the recommendation for THIS corpus scale \u2014 with the explicit caveat that it will grow with more training data (Heaps' Law), and re-run as the corpus grows.",
], { fontSize: 16 });

bulletSlide("What it does \u2014 and doesn't \u2014 claim", [
  "Applied post-hoc: fires at 6,000-8,000 (English), 3,000-4,000 (Arabic), 4,000-6,000 (Hindi, capped by its ceiling) \u2014 consistent with, slightly more conservative than, the \u00A75 consensus.",
  "It identifies where a GIVEN corpus stops rewarding further merges \u2014 not a universal 'correct' vocab size for a language.",
  "Real production tokenizers train on trillions of tokens vs this study's hundreds of thousands \u2014 their much larger sweet spots are a predictable Heaps'-Law consequence, not a contradiction.",
  "Practical takeaway: compute this on YOUR actual training corpus, at YOUR actual scale, before fixing a vocabulary size.",
]);

bulletSlide("Conclusions", [
  "Tokens obey Zipf's law, and more cleanly than words in the 6k-16k vocab band \u2014 but the fit is vocabulary-size dependent, not automatic.",
  "LLaMA/Qwen/Kimi differ up to 5x in published vocab size; on this corpus scale the larger three all hit the same data-bound ceiling regardless of target.",
  "Hindi's script caps achievable BPE vocabulary an order of magnitude below English/Arabic \u2014 a token-level Heaps' Law echo.",
  "A vocab-size sweet spot exists in the qualified sense that 3 of 4 criteria converge within a 3-5x band; the 4th confirms returns diminish smoothly, never vanishing.",
  "Zipf-stabilisation is a cheap, usable proxy for the sweet spot, and feeds directly into a proposed 3-signal stopping rule for choosing vocabulary size.",
], { fontSize: 16 });

const s = pres.addSlide();
s.background = { color: INK };
s.addText("Thank you", { x: 0.9, y: 3.0, w: 11.5, h: 1.0, fontFace: FONT, fontSize: 40, bold: true, color: "FFFFFF", isTextBox: true });
s.addText("Code, data, figures and full report: github.com/<repo>/zipf-tokenization", {
  x: 0.9, y: 3.9, w: 11.5, h: 0.5, fontFace: "Arial", fontSize: 14, color: "AAAAAA", isTextBox: true,
});

pres.writeFile({ fileName: path.join(DIST, "Zipf_Tokenization_Presentation.pptx") }).then(() => {
  console.log("Wrote deck");
});
