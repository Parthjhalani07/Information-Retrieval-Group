This directory ships only the 12 model-style tokenizers (LLaMA-2/3, Qwen, Kimi
replicas x English/Hindi/Arabic) as samples, ~52MB total.

The full 54-tokenizer vocab sweep (~118MB) used to produce every figure and
table in the report is not checked in — it is fully regenerable in about two
minutes:

    cd src && python3 03_train_bpe.py

All downstream numbers (out/*.json) were already computed from the full sweep
and are checked in, so the report/figures/analysis do not require regenerating
the tokenizers unless you want to re-verify them from scratch.
