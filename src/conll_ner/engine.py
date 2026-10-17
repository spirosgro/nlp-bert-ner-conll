"""Training and inference shared by BERT, RoBERTa, NER, POS and chunking."""
from importlib.metadata import version
from pathlib import Path
import hashlib
import json
import random
import platform

from .data import read_conll, label_vocabulary, encode_sentences, assert_disjoint
from .metrics import score_sequences


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def resolve_device(requested):
    import torch
    if requested == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA requested but unavailable")
    return torch.device("cuda" if requested == "auto" and torch.cuda.is_available() else "cpu" if requested == "auto" else requested)


def seed_everything(seed):
    import numpy as np
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True


def load_tokenizer(model_name, model_type, revision=None):
    from transformers import AutoTokenizer
    kwargs = {"add_prefix_space": True} if model_type == "roberta" else {}
    return AutoTokenizer.from_pretrained(model_name, revision=revision, use_fast=True, trust_remote_code=False, **kwargs)


def model_capacity(model, tokenizer):
    maximum = model.config.max_position_embeddings
    if model.config.model_type == "roberta":
        maximum -= model.config.pad_token_id + 1
    return min(maximum, tokenizer.model_max_length)


def freeze_encoder(model):
    for parameter in model.base_model.parameters():
        parameter.requires_grad = False


def loader(records, tokenizer, batch_size, shuffle=False):
    from torch.utils.data import DataLoader
    from transformers import DataCollatorForTokenClassification
    return DataLoader(records, batch_size=batch_size, shuffle=shuffle, num_workers=0,
                      collate_fn=DataCollatorForTokenClassification(tokenizer, label_pad_token_id=-100))


def predict_loader(model, batches, device):
    import torch
    model.eval()
    gold, predicted = [], []
    with torch.inference_mode():
        for batch in batches:
            labels = batch.pop("labels")
            logits = model(**{k: v.to(device) for k, v in batch.items()}).logits
            guesses = logits.argmax(-1).cpu().tolist()
            for truth, guess in zip(labels.tolist(), guesses):
                gold.append([model.config.id2label[t] for t in truth if t != -100])
                predicted.append([model.config.id2label[p] for t, p in zip(truth, guess) if t != -100])
    return gold, predicted


def train(args):
    import torch
    from transformers import AutoConfig, AutoModelForTokenClassification
    seed_everything(args.seed)
    device = resolve_device(args.device)
    training = read_conll(args.train, args.task, args.scheme)
    validation = read_conll(args.valid, args.task, args.scheme)
    if not args.allow_overlap:
        assert_disjoint(training, validation)
    vocabulary = label_vocabulary(training, args.task)
    config = AutoConfig.from_pretrained(args.model, revision=args.revision, trust_remote_code=False)
    if config.model_type not in {"bert", "roberta"}:
        raise ValueError("This project supports BERT and RoBERTa only")
    config.num_labels = len(vocabulary)
    config.id2label = dict(enumerate(vocabulary))
    config.label2id = {label: i for i, label in enumerate(vocabulary)}
    tokenizer = load_tokenizer(args.model, config.model_type, args.revision)
    model = AutoModelForTokenClassification.from_pretrained(
        args.model, config=config, revision=args.revision, trust_remote_code=False,
        use_safetensors=True, ignore_mismatched_sizes=True).to(device)
    if args.max_length > model_capacity(model, tokenizer):
        raise ValueError("max-length exceeds this model's positional capacity")
    train_records = encode_sentences(training, tokenizer, config.label2id, args.max_length)
    valid_records = encode_sentences(validation, tokenizer, config.label2id, args.max_length)
    if args.freeze_encoder:
        freeze_encoder(model)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    metadata = {"task": args.task, "scheme": args.scheme, "max_length": args.max_length,
                "model": args.model, "requested_revision": args.revision,
                "resolved_revision": getattr(config, "_commit_hash", None),
                "seed": args.seed, "epochs": args.epochs, "batch_size": args.batch_size,
                "learning_rate": args.lr, "weight_decay": 0.01, "gradient_clip": 1.0,
                "freeze_encoder": args.freeze_encoder, "allow_overlap": args.allow_overlap,
                "selection_metric": "token_accuracy" if args.task == "pos" else "entity_f1",
                "device": str(device), "train_sha256": sha256(args.train), "valid_sha256": sha256(args.valid),
                "train_sentences": len(training), "valid_sentences": len(validation),
                "labels": vocabulary, "python": platform.python_version(),
                "versions": {p: version(p) for p in ("torch", "transformers", "numpy", "seqeval", "scikit-learn")},
                "parameters": sum(p.numel() for p in model.parameters()),
                "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad)}
    write_json(out / "run.json", metadata)
    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=args.lr, weight_decay=0.01)
    training_batches = loader(train_records, tokenizer, args.batch_size, shuffle=True)
    validation_batches = loader(valid_records, tokenizer, args.batch_size)
    best, history = -1.0, []
    for epoch in range(1, args.epochs + 1):
        model.train()
        if args.freeze_encoder:
            model.base_model.eval()  # Frozen feature extractor has stable dropout behaviour.
        total_loss = 0.0
        for batch in training_batches:
            optimizer.zero_grad(set_to_none=True)
            loss = model(**{k: v.to(device) for k, v in batch.items()}).loss
            if not torch.isfinite(loss):
                raise ValueError("Non-finite training loss")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += loss.item()
        gold, predictions = predict_loader(model, validation_batches, device)
        metrics = score_sequences(gold, predictions, args.task)
        current = metrics[metadata["selection_metric"]]
        history.append({"epoch": epoch, "mean_batch_loss": total_loss / len(training_batches), "validation": metrics})
        print(json.dumps({"epoch": epoch, "validation_selection_score": current}), flush=True)
        if current > best:
            best = current
            model.save_pretrained(out / "best", safe_serialization=True)
            tokenizer.save_pretrained(out / "best")
            metadata["best_epoch"] = epoch
            metadata["best_validation_score"] = current
        write_json(out / "history.json", history)
        write_json(out / "run.json", metadata)
    return metadata


def load_run(run, device):
    from transformers import AutoModelForTokenClassification
    run = Path(run)
    metadata = json.loads((run / "run.json").read_text(encoding="utf-8"))
    model = AutoModelForTokenClassification.from_pretrained(run / "best", local_files_only=True,
                                                          trust_remote_code=False, use_safetensors=True).to(device)
    tokenizer = load_tokenizer(str(run / "best"), model.config.model_type)
    return metadata, model, tokenizer


def evaluate(args):
    device = resolve_device(args.device)
    metadata, model, tokenizer = load_run(args.run, device)
    digest = sha256(args.data)
    if digest in {metadata["train_sha256"], metadata["valid_sha256"]}:
        raise ValueError("Evaluation file matches training or validation bytes. Supply a held-out test split.")
    sentences = read_conll(args.data, metadata["task"], metadata["scheme"])
    records = encode_sentences(sentences, tokenizer, model.config.label2id, metadata["max_length"])
    gold, predictions = predict_loader(model, loader(records, tokenizer, args.batch_size), device)
    results = {"split": "test", "data_sha256": digest, "checkpoint_sha256": sha256(Path(args.run) / "best" / "model.safetensors"),
               "metrics": score_sequences(gold, predictions, metadata["task"])}
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / "metrics.json", results)
    rows = [{"sentence_index": i, "tokens": s.tokens, "gold": g, "predicted": p,
             "error_indices": [j for j, (a, b) in enumerate(zip(g, p)) if a != b]}
            for i, (s, g, p) in enumerate(zip(sentences, gold, predictions))]
    with (out / "predictions.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(results, indent=2))
    return results


def predict(args):
    from .data import Sentence
    device = resolve_device(args.device)
    metadata, model, tokenizer = load_run(args.run, device)
    items = json.loads(Path(args.tokens).read_text(encoding="utf-8"))
    if not isinstance(items, list) or not items or any(not isinstance(s, list) or not s or any(not isinstance(w, str) or not w or any(c.isspace() for c in w) for w in s) for s in items):
        raise ValueError("Input must be a nonempty JSON list of nonempty lists of individual word strings")
    dummy = metadata["labels"][0]
    records = encode_sentences([Sentence(s, [dummy] * len(s)) for s in items], tokenizer, model.config.label2id, metadata["max_length"])
    _, predictions = predict_loader(model, loader(records, tokenizer, args.batch_size), device)
    for tokens, tags in zip(items, predictions):
        print(json.dumps({"tokens": tokens, "tags": tags}, ensure_ascii=False))
