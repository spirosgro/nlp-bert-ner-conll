# Verification record

Verified locally on 16 October 2026 on Windows, CPU, Python 3.12. The environment
used PyTorch 2.6.0+cpu, Transformers 4.57.1, NumPy 2.2.6, seqeval 1.2.2 and
scikit-learn 1.7.2. Direct dependency versions are recorded in `pyproject.toml`;
transitive dependencies are not completely locked.

## Completed checks

- **16 unit tests passed.** Coverage includes four-column parsing, document and
  sentence boundaries, IOB conversion, unknown labels, first-subword masking,
  length rejection, split overlap, strict entity boundaries, balanced accuracy,
  invalid predicted BIO tags, and JSON-serialisable metrics.
- **Five offline integration scenarios passed:** BERT NER, frozen BERT NER,
  BERT POS, BERT chunking and RoBERTa NER. Each scenario trained one epoch,
  saved a checkpoint, reloaded it, evaluated a separate synthetic split and
  emitted word-aligned predictions. Each rejected a byte-identical training
  file supplied as test data. Frozen mode also checks parameter gradient flags.
- Package installation and the CLI were exercised in a separate virtual
  environment. The release checker validates local links, Python syntax,
  JSON/SVG files and selected publication hygiene rules.

The integration models are tiny, randomly initialised and created locally.
Their scores have no benchmark meaning. Fixture sentences are authored for this
repository and are not copied from the CoNLL corpus. The checkpoint classifier
resize warnings for POS/chunking are expected: these tasks have different labels.

An integration test found a NumPy integer in the entity report that could not
be encoded as JSON. The public implementation explicitly converts report values
to native Python types, with a regression test for this export path.

## Not verified

- Full training with pretrained BERT/RoBERTa on a licensed CoNLL dataset.
- Reproduction of the historical coursework scores, entity F1 for those runs,
  or stability across training seeds.
- CUDA execution, macOS execution or all supported Python minor versions.
- Hosted GitHub Actions execution: the workflow is supplied, but its first
  remote run happens after publication. A local pass is not a hosted CI result.

Run the commands in the [README](../README.md) to repeat the checks. The CI
workflow uses Ubuntu and Python 3.12, so its first run additionally checks a
different operating system. Network access is needed to install dependencies;
the model integration test itself runs offline.
