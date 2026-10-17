# Experiment plan

Use the same official dataset splits for every comparison. Validate all splits
first. Select a task-appropriate scheme from your data provider. Run IDs below
are examples; use a new directory for every seed and configuration.

| Experiment | Model | Task | Change |
|---|---|---|---|
| Uncased baseline | google-bert/bert-base-uncased | ner | Full fine-tuning |
| Cased comparison | google-bert/bert-base-cased | ner | Matching cased tokenizer |
| Frozen ablation | google-bert/bert-base-uncased | ner | Classifier-only training |
| RoBERTa comparison | FacebookAI/roberta-base | ner | Byte-level tokenizer |
| POS adaptation | google-bert/bert-base-uncased | pos | Second input column |
| Chunk adaptation | google-bert/bert-base-uncased | chunk | Third input column |

```bash
conll-ner train --train data/raw/train.txt --valid data/raw/valid.txt --model google-bert/bert-base-uncased --output runs/uncased-s42
conll-ner train --train data/raw/train.txt --valid data/raw/valid.txt --model google-bert/bert-base-cased --output runs/cased-s42
conll-ner train --train data/raw/train.txt --valid data/raw/valid.txt --model google-bert/bert-base-uncased --freeze-encoder --output runs/frozen-s42
conll-ner train --train data/raw/train.txt --valid data/raw/valid.txt --model FacebookAI/roberta-base --output runs/roberta-s42
conll-ner train --train data/raw/train.txt --valid data/raw/valid.txt --model google-bert/bert-base-uncased --task pos --output runs/pos-s42
conll-ner train --train data/raw/train.txt --valid data/raw/valid.txt --model google-bert/bert-base-uncased --task chunk --output runs/chunk-s42
```

Defaults: three epochs, batch size eight, learning rate 1e-5, seed 42, maximum
length 512, IOB1 gold normalisation. Add `--scheme iob2` when appropriate.
Add `--revision <commit-sha>` for an immutable upstream model revision.
Tokenisation differs between BERT and RoBERTa; rejecting long sentences ensures
coverage problems are visible before fitting. Audit any length preprocessing
before selecting configurations and keep the scoring set consistent.

The optimiser is AdamW with weight decay 0.01 and gradient clipping at 1.0.
There is no learning-rate scheduler, automatic mixed precision, early stopping,
resume support or automatic hyperparameter search in this edition. CUDA selects
full-precision training. This avoids introducing an untested AMP path.

Choose hyperparameters using validation only. Once the protocol is fixed, run
held-out evaluation for every planned seed and report mean and dispersion. Do not
choose the best seed by test score. Use `--seed 43` and `--seed 44`, for example,
with distinct run IDs. Do not combine POS accuracy with NER F1 in a single ranking.

```bash
conll-ner evaluate --run runs/cased-s42 --data data/raw/test.txt --output runs/cased-s42-test
```

For publication, copy reviewed aggregate metrics and settings into a separate
results record. Do not commit `runs/` wholesale, model weights, or prediction
text without checking external data rights. Historical values in `results/`
must not be overwritten with unlabeled new results.
