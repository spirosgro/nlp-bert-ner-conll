# CoNLL data preparation

Supply English CoNLL-2003 files locally under `data/raw/`:

```text
data/raw/train.txt
data/raw/valid.txt
data/raw/test.txt
```

Each nonempty data line must contain exactly four whitespace-separated fields:
word, POS tag, chunk tag, NER tag. Blank lines separate sentences. A `-DOCSTART-`
marker closes the previous sentence and is not fed to the model. Tabs, repeated
spaces, a UTF-8 BOM and an absent final newline are supported.

The original scripts referenced a Kaggle distribution named
`alaakhaled/conll003-englishversion`. That reference records provenance; this
repository does not verify that mirror's contents or redistribute its files.
Consult the [shared-task paper](https://aclanthology.org/W03-0419/) for dataset
context and your provider for current access and redistribution terms. Store
the provider, retrieval date, encoding, split names and original hashes with
your private experiment record. Do not derive new splits from a merged corpus.

Check whether your provider uses IOB1 or IOB2. For NER and chunking, `--scheme
iob1` converts sentence-initial and type-changing `I-X` gold tags to `B-X` while
preserving explicit `B-X` boundaries. `--scheme iob2` validates that convention
and rejects orphan `I-X` labels. POS labels are not converted. There is no
automatic scheme guessing. If chunk and NER columns use different conventions,
choose the scheme for the task being run.

Run `conll-ner validate` before expensive training. Duplicate sentence text
across splits causes an error by default, including short repeated newswire
headings. Audit these and, if retaining the official split, record the reason
for `--allow-overlap`. Do not silently change the standard evaluation set to
improve scores. The override is recorded in training metadata.

`data/raw/`, `runs/` and model weights are ignored by Git. The authored fixtures
in `examples/` may be published. Raw model predictions can reproduce corpus
text, so keep them local unless you have verified publication rights.
