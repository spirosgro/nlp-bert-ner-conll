"""Command-line entry points; validation remains usable without ML downloads."""
import argparse
import json
from .data import read_conll, assert_disjoint


def positive_int(value):
    result = int(value)
    if result < 1:
        raise argparse.ArgumentTypeError("Must be positive")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="Validate local four-column CoNLL splits")
    train = sub.add_parser("train", help="Train with validation-only checkpoint selection")
    for p in (validate, train):
        p.add_argument("--train", required=True)
        p.add_argument("--valid", required=True)
        p.add_argument("--task", choices=["ner", "pos", "chunk"], default="ner")
        p.add_argument("--scheme", choices=["iob1", "iob2"], default="iob1")
        p.add_argument("--allow-overlap", action="store_true", help="Explicitly permit identical sentences across splits after audit")
    validate.add_argument("--test")
    train.add_argument("--model", default="google-bert/bert-base-cased")
    train.add_argument("--revision", help="Prefer an immutable Hub commit SHA")
    train.add_argument("--output", required=True, help="New run directory")
    train.add_argument("--epochs", type=positive_int, default=3)
    train.add_argument("--lr", type=float, default=1e-5)
    train.add_argument("--seed", type=int, default=42)
    train.add_argument("--max-length", type=positive_int, default=512)
    train.add_argument("--freeze-encoder", action="store_true")
    evaluation = sub.add_parser("evaluate", help="Evaluate saved best checkpoint on held-out test data")
    evaluation.add_argument("--run", required=True)
    evaluation.add_argument("--data", required=True)
    evaluation.add_argument("--output", required=True, help="New evaluation directory")
    prediction = sub.add_parser("predict", help="Predict labels for a JSON list of tokenised sentences")
    prediction.add_argument("--run", required=True)
    prediction.add_argument("--tokens", required=True)
    for p in (train, evaluation, prediction):
        p.add_argument("--batch-size", type=positive_int, default=8)
        p.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = parser.parse_args(argv)
    if args.command == "validate":
        paths = {"train": args.train, "valid": args.valid}
        if args.test:
            paths["test"] = args.test
        splits = {name: read_conll(path, args.task, args.scheme) for name, path in paths.items()}
        from itertools import combinations
        if not args.allow_overlap:
            for a, b in combinations(splits, 2):
                assert_disjoint(splits[a], splits[b])
        print(json.dumps({name: {"sentences": len(items), "words": sum(len(s.tokens) for s in items)} for name, items in splits.items()}, indent=2))
        return
    from . import engine
    if args.command == "train":
        import math
        if not math.isfinite(args.lr) or args.lr <= 0:
            parser.error("--lr must be finite and positive")
    getattr(engine, args.command)(args)


if __name__ == "__main__":
    main()
