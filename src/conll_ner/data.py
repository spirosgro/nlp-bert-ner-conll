"""Strict CoNLL parsing and explicit BIO normalisation, with no ML dependencies."""
from dataclasses import dataclass
from pathlib import Path

TASK_COLUMNS = {"pos": 1, "chunk": 2, "ner": 3}
NER_LABELS = ["O"] + [f"{prefix}-{entity}" for entity in ("PER", "ORG", "LOC", "MISC") for prefix in ("B", "I")]


@dataclass(frozen=True)
class Sentence:
    tokens: list[str]
    labels: list[str]


def normalise_bio(labels: list[str], scheme: str) -> list[str]:
    """Convert IOB1 to IOB2 or validate IOB2. Only gold labels are normalised."""
    if scheme not in {"iob1", "iob2"}:
        raise ValueError("scheme must be iob1 or iob2")
    output = []
    previous = None
    for label in labels:
        if label == "O":
            previous = None
            output.append(label)
            continue
        if len(label) < 3 or label[:2] not in {"B-", "I-"}:
            raise ValueError(f"Invalid BIO label: {label!r}")
        entity = label[2:]
        if label.startswith("I-") and previous != entity:
            if scheme == "iob2":
                raise ValueError(f"Invalid IOB2 transition to {label!r}")
            label = "B-" + entity
        output.append(label)
        previous = entity
    return output


def read_conll(path: str | Path, task: str = "ner", scheme: str = "iob1") -> list[Sentence]:
    if task not in TASK_COLUMNS:
        raise ValueError(f"Unknown task: {task}")
    sentences, tokens, labels = [], [], []

    def flush():
        if tokens:
            tags = labels.copy() if task == "pos" else normalise_bio(labels, scheme)
            sentences.append(Sentence(tokens.copy(), tags))
            tokens.clear()
            labels.clear()

    with Path(path).open(encoding="utf-8-sig") as handle:
        for number, line in enumerate(handle, 1):
            fields = line.split()
            if not fields or fields[0] == "-DOCSTART-":
                flush()
                continue
            if len(fields) != 4:
                raise ValueError(f"{Path(path).name}:{number}: expected exactly four columns, got {len(fields)}")
            tokens.append(fields[0])
            labels.append(fields[TASK_COLUMNS[task]])
    flush()
    if not sentences:
        raise ValueError(f"No sentences in {path}")
    return sentences


def label_vocabulary(sentences: list[Sentence], task: str) -> list[str]:
    observed = {tag for sentence in sentences for tag in sentence.labels}
    if task == "ner":
        unexpected = observed - set(NER_LABELS)
        if unexpected:
            raise ValueError(f"Unexpected CoNLL NER labels: {sorted(unexpected)}")
        return NER_LABELS.copy()
    if task == "chunk":
        entities = sorted({tag[2:] for tag in observed if tag != "O"})
        return ["O"] + [f"{p}-{entity}" for entity in entities for p in ("B", "I")]
    return sorted(observed)


def assert_disjoint(train: list[Sentence], valid: list[Sentence]) -> None:
    """Catch identical token sequences across splits, regardless of their annotations."""
    overlap = {tuple(s.tokens) for s in train} & {tuple(s.tokens) for s in valid}
    if overlap:
        raise ValueError(f"Found {len(overlap)} identical sentences across splits. Audit them or explicitly allow overlap.")


def align_first_subwords(word_ids: list[int | None], labels: list[str], label2id: dict[str, int]) -> list[int]:
    unknown = set(labels) - set(label2id)
    if unknown:
        raise ValueError(f"Labels absent from training vocabulary: {sorted(unknown)}")
    ids, seen = [], set()
    for word in word_ids:
        if word is None:
            ids.append(-100)
            continue
        if word < 0 or word >= len(labels):
            raise ValueError("Tokenizer returned a word index outside the sentence")
        ids.append(-100 if word in seen else label2id[labels[word]])
        seen.add(word)
    if seen != set(range(len(labels))):
        raise ValueError("Tokenizer dropped words. Silent truncation is not supported.")
    return ids


def encode_sentences(sentences, tokenizer, label2id, max_length):
    records = []
    for index, sentence in enumerate(sentences):
        encoded = tokenizer(sentence.tokens, is_split_into_words=True, truncation=False)
        if len(encoded["input_ids"]) > max_length:
            raise ValueError(f"Sentence {index} has {len(encoded['input_ids'])} subwords including special tokens; limit is {max_length}. Increase the limit within model capacity or preprocess explicitly.")
        encoded["labels"] = align_first_subwords(encoded.word_ids(), sentence.labels, label2id)
        records.append(dict(encoded))
    return records
