"""Token diagnostics and strict span metrics, retaining sentence boundaries."""
from collections import Counter


def score_sequences(gold, predicted, task="ner"):
    if not gold or len(gold) != len(predicted):
        raise ValueError("Gold and predictions must contain the same nonzero number of sentences")
    if any(not g or len(g) != len(p) for g, p in zip(gold, predicted)):
        raise ValueError("Gold and predictions must align token by token in every sentence")
    support, correct, predicted_count = Counter(), Counter(), Counter()
    for truth, guess in zip(gold, predicted):
        for actual, result in zip(truth, guess):
            support[actual] += 1
            predicted_count[result] += 1
            correct[actual] += actual == result
    total = sum(support.values())
    per_label = {}
    for label in sorted(support.keys() | predicted_count.keys()):
        precision = correct[label] / predicted_count[label] if predicted_count[label] else 0.0
        recall = correct[label] / support[label] if support[label] else 0.0
        per_label[label] = {"precision": precision, "recall": recall,
                            "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
                            "support": support[label]}
    result = {"tokens": total, "sentences": len(gold),
              "token_accuracy": sum(correct.values()) / total,
              "balanced_accuracy": sum(correct[t] / support[t] for t in support) / len(support),
              "token_per_label": per_label}
    if task != "pos":
        from seqeval.metrics import classification_report, precision_score, recall_score, f1_score
        from seqeval.scheme import IOB2
        options = {"mode": "strict", "scheme": IOB2, "zero_division": 0}
        has_span_start = any(t.startswith("B-") for s in gold + predicted for t in s)
        report = classification_report(gold, predicted, output_dict=True, **options) if has_span_start else {}
        report = {name: {key: int(value) if key == "support" else float(value)
                         for key, value in row.items()} for name, row in report.items()}
        result.update({"entity_precision": precision_score(gold, predicted, **options),
                       "entity_recall": recall_score(gold, predicted, **options),
                       "entity_f1": f1_score(gold, predicted, **options),
                       "entity_per_type": report})
    return result
