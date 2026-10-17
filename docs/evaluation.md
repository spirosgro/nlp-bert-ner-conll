# Evaluation contract

## Labels and alignment

The standard NER vocabulary is O plus B/I variants of PER, ORG, LOC and MISC.
POS vocabulary is derived from training only. Chunk vocabulary includes both
B and I for each training chunk type. Unseen evaluation labels raise an error.
No vocabulary is learned from test labels.

Only the first subword of a word is supervised and scored. Special tokens,
continuation subwords and padding carry `-100`. Sentence boundaries remain
separate in all span metrics. Gold IOB1 data may be explicitly converted to IOB2.
Predictions remain raw and are evaluated with seqeval 1.2.2, `mode="strict"`,
`scheme=IOB2`, `zero_division=0`. An orphan predicted `I-PER` is not silently
turned into a correct `B-PER`. Scores can therefore differ from permissive
conlleval-style evaluations. State the evaluator when comparing external work.

## Metrics

Token accuracy is correct word labels divided by evaluated words. Balanced
accuracy is mean recall over labels with nonzero gold support. Per-label token
precision, recall, F1 and support are diagnostics. Strict entity precision,
recall and F1 require the full span and type to match. For chunking the span
metrics refer to chunks. For POS only token metrics are produced.

When no entities are present, undefined precision/recall/F1 become zero. The
per-type entity report is empty when neither gold nor predicted tags contains
a valid span start. Non-finite JSON values are rejected at export.

## Split policy

Training reads only train and validation. The saved checkpoint maximises
validation entity F1 for NER/chunking and token accuracy for POS. Ties keep the
earliest epoch. Test evaluation loads that checkpoint rather than the final
in-memory model. It rejects files whose SHA-256 matches the train or validation
file. This byte check is not a full leakage detector: formatting changes bypass
it. Run `validate --test` before training to check exact sentence overlap across
all split pairs. Near-duplicates and document overlap still require a corpus audit.

`--allow-overlap` permits known repeated sentences after review and is recorded
in training metadata. It does not establish that the corpus is leakage-free.

## Length and input policy

Tokenisation does not truncate. Any sentence exceeding the requested limit or
model capacity stops the run. Increase the limit only within the model's
positional capacity. A production extension should use documented word-boundary
windows and reconstruct sentence-level predictions before scoring. Dropping
long sentences or scoring partial entities changes the task and must be disclosed.

Inference accepts already separated words as JSON. It returns one tag for every
word or raises an error. It does not return character offsets, confidence scores,
calibrated probabilities or merged entity objects.

## Reproducibility boundary

Python, NumPy, PyTorch and CUDA seeds are set. cuDNN benchmarking is disabled
and deterministic mode is requested. This is not a guarantee of identical
results across GPU hardware, kernels, operating systems or dependency versions.
Direct dependencies are pinned. `run.json` records their versions, data hashes,
the requested and resolved base model revision when available, and all exposed
training settings. The repository provides no claim of a replicated benchmark.
