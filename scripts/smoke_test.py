"""Offline integration checks using tiny randomly initialised transformers, not benchmark results."""
from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import redirect_stdout
import io
import json
import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from transformers import BertConfig, BertForTokenClassification, BertTokenizerFast
from transformers import RobertaConfig, RobertaForTokenClassification, RobertaTokenizerFast
from tokenizers import ByteLevelBPETokenizer
from conll_ner.cli import main
from conll_ner.engine import freeze_encoder

ROOT = Path(__file__).resolve().parents[1]


def smoke():
    torch.set_num_threads(1)
    torch.manual_seed(42)
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        bert_path = root / "tiny-bert"
        bert_path.mkdir()
        words = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]", "Alice", "Morgan", "visits", "Paris", ".",
                 "Northstar", "Labs", "hires", "French", "engineers", "Berlin", "hosts"]
        (bert_path / "vocab.txt").write_text("\n".join(words) + "\n", encoding="utf-8")
        tokenizer = BertTokenizerFast(vocab_file=str(bert_path / "vocab.txt"), do_lower_case=False, model_max_length=64)
        tokenizer.save_pretrained(bert_path)
        tiny = BertForTokenClassification(BertConfig(vocab_size=len(tokenizer), hidden_size=24,
                    num_hidden_layers=1, num_attention_heads=2, intermediate_size=32, max_position_embeddings=64, num_labels=9))
        tiny.save_pretrained(bert_path, safe_serialization=True)
        freeze_encoder(tiny)
        assert all(not p.requires_grad for p in tiny.base_model.parameters())
        assert all(p.requires_grad for p in tiny.classifier.parameters())
        roberta_path = root / "tiny-roberta"
        roberta_path.mkdir()
        bpe = ByteLevelBPETokenizer()
        bpe.train_from_iterator([" ".join(words[5:])], vocab_size=280, special_tokens=["<s>", "<pad>", "</s>", "<unk>", "<mask>"])
        bpe.save_model(str(roberta_path))
        rt = RobertaTokenizerFast(vocab_file=str(roberta_path / "vocab.json"), merges_file=str(roberta_path / "merges.txt"), add_prefix_space=True, model_max_length=128)
        rt.save_pretrained(roberta_path)
        RobertaForTokenClassification(RobertaConfig(vocab_size=len(rt), hidden_size=24, num_hidden_layers=1,
                    num_attention_heads=2, intermediate_size=32, max_position_embeddings=130, num_labels=9)).save_pretrained(roberta_path)
        cases = [("ner", False, bert_path), ("ner", True, bert_path), ("pos", False, bert_path),
                 ("chunk", False, bert_path), ("ner", False, roberta_path)]
        for index, (task, frozen, model) in enumerate(cases):
            run = root / f"run-{index}"
            command = ["train", "--train", str(ROOT / "examples/train.conll"), "--valid", str(ROOT / "examples/valid.conll"),
                       "--task", task, "--scheme", "iob2", "--model", str(model), "--output", str(run), "--epochs", "1",
                       "--max-length", "64" if model == bert_path else "128", "--batch-size", "2", "--device", "cpu"]
            if frozen:
                command += ["--freeze-encoder"]
            with redirect_stdout(io.StringIO()):
                main(command)
                main(["evaluate", "--run", str(run), "--data", str(ROOT / "examples/test.conll"), "--output", str(root / f"eval-{index}"), "--device", "cpu"])
            predictions = io.StringIO()
            with redirect_stdout(predictions):
                main(["predict", "--run", str(run), "--tokens", str(ROOT / "examples/tokens.json"), "--device", "cpu"])
            for line in predictions.getvalue().splitlines():
                row = json.loads(line)
                assert len(row["tokens"]) == len(row["tags"])
            history = json.loads((run / "history.json").read_text())
            assert len(history) == 1 and history[0]["validation"]["tokens"] == 10
            try:
                with redirect_stdout(io.StringIO()):
                    main(["evaluate", "--run", str(run), "--data", str(ROOT / "examples/train.conll"), "--output", str(root / "must-not-exist")])
            except ValueError as error:
                assert "matches training" in str(error)
            else:
                raise AssertionError("Training split was incorrectly accepted as test data")
            print(f"PASS: {model.name}, task={task}, frozen={frozen}: train/save/reload/evaluate/predict")
    print("Offline integration checks passed. No pretrained weights or benchmark data were used.")


if __name__ == "__main__":
    smoke()
