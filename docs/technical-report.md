# BERT sequence labelling on CoNLL-2003

## Purpose and evidence

This project studies how a pretrained transformer can label individual words
with entity, part-of-speech or phrase-chunk tags. The original coursework
contains seven scripts: baseline NER, qualitative predictions, cased BERT,
frozen BERT, POS, chunking and RoBERTa. The public implementation makes the
experiments configurable and strengthens their evaluation.

The original report records token accuracy and balanced accuracy. The report
values are historical observations, not independently verified outputs of the
new implementation. No original trained weights, complete prediction files,
environment lock or run logs were supplied in the inspected archive. The new
offline tests exercise software behaviour with small random models and authored
sentences; they do not reproduce those observations.

## Baseline NER and class imbalance

The baseline uses BERT base uncased with a linear token-classification head.
The source specifies AdamW, learning rate 1e-5, three epochs and batch size eight.
Its reported test accuracy is 97.2% and balanced accuracy is 82.3%. The large
gap is consistent with uneven class frequencies, but without predictions the
source's explanations cannot be independently checked.

Token accuracy counts correctly tagged words. Balanced accuracy averages
per-class recall and makes rare labels more visible. Neither requires an entire
entity to have the correct boundaries and type. The public implementation
therefore adds strict IOB2 span precision, recall and F1 for NER and chunking.
For POS, it retains token metrics because POS categories are not entity spans.

## Word and subword alignment

A word may be split into several WordPiece or byte-level BPE pieces. Each word
has one gold label, so only its first subword receives that label. Continuation
pieces, padding and special tokens use target value `-100` and are excluded from
loss and scoring. The tokenizer's `word_ids()` supplies the mapping.

The public code checks that every input word survives tokenisation. It rejects
overlong sequences rather than cutting words and filling missing predictions
with `O`. The original qualitative helper did use such an `O` fallback; it could
turn a coverage failure into a seemingly confident prediction. Batch padding
is now dynamic, which avoids padding every short sentence to a global limit.

## Cased and uncased comparison

The source reports 97.4% token accuracy and 84.2% balanced accuracy for cased
BERT, compared with 97.2% and 82.3% for uncased BERT. Capitalisation is a plausible
signal for entity recognition, but these runs are not a controlled causal study.
The source baseline leaves maximum length to the tokenizer, while the cased
script explicitly uses 128. The scripts do not consistently seed training.
These differences, separate pretrained vocabularies and the absence of repeated
runs limit the strength of any claim about the advantage of casing.

The public comparison uses the same requested maximum length, splits, seed,
learning rate and batch size. It records resolved model revision when available.
Even these controls do not isolate casing alone because the pretrained models
are different. Multi-seed mean and variability are still needed.

## Frozen encoder

The frozen experiment disables gradients for the transformer and trains only
the classifier. The source describes a decline, especially for rare labels,
but provides no numeric frozen-encoder result in the extracted report text.
The public results file leaves those values null.

The public frozen mode also keeps the base encoder in evaluation mode during
training, disabling its dropout while the classifier remains trainable. This is
a deliberate difference from the original script, which calls `model.train()`
for the full network even after freezing weights. It makes the feature-extractor
interpretation explicit, but prevents claims of bit-for-bit reproduction.

## POS and phrase chunking

POS tagging uses the second CoNLL column and creates its label vocabulary from
training data only. The source reports 98.8% accuracy and 95.6% balanced accuracy.
These figures are not evidence that POS is universally easier than NER: the
tasks use different labels, distributions and evaluation objectives.

Chunking uses the third column. The original report explains the adaptation
without supplying a numeric result. The public implementation normalises the
selected gold tag scheme and evaluates exact chunk spans. It rejects unknown
labels rather than silently masking them as `-100`.

## RoBERTa

The source includes a RoBERTa base experiment but no measured comparison in the
report. Its discussion of likely improvements is a hypothesis. The public
repository makes no claim that RoBERTa wins.

Pretokenised input to the fast RoBERTa tokenizer requires `add_prefix_space=True`
for the supported Transformers version. The source omits that argument. The
public implementation sets it explicitly and tests the RoBERTa path with a local
byte-level tokenizer and small random encoder.

## Qualitative analysis

The original narrative describes confusion between LOC and ORG for “Brussels”,
and an incorrect MISC label for “Tuesday”. Those observations are retained here
as reported examples; their raw predictions were unavailable. Metonymy and
annotation conventions are possible explanations, not demonstrated causes.
In particular, an error on a day name does not show that a base model learned
another dataset's NER labels.

The new evaluator exports every sentence's tokens, gold tags, predicted tags
and error indices. An analyst can then distinguish boundary errors, wrong entity
types, missed entities and false positives. Exports stay under ignored run
directories because they may contain third-party corpus text.

## What has improved

Experiments share a package and CLI, use explicit input paths, keep test evaluation
outside training, save the best validation checkpoint, and record versions and
file hashes. Tests cover malformed input, sentence boundaries, BIO conversion,
subword masking, omitted words, whole-entity errors and complete model round trips.

The remaining evidence gap is a fresh benchmark run. Publishing strict entity F1
for several seeds, dataset provenance, immutable model revisions and run metadata
would make the scientific comparison substantially stronger. No level of README
polish can substitute for those measurements.

## References

See the [reference list](../references/README.md) for BERT, RoBERTa, CoNLL-2003,
the pinned Transformers documentation and the seqeval evaluation implementation.
