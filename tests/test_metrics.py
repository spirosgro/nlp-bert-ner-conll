import unittest
import json
from conll_ner.metrics import score_sequences


class MetricsTests(unittest.TestCase):
    def test_entity_boundary_error_despite_high_token_accuracy(self):
        gold = [["O"] * 8 + ["B-PER", "I-PER"]]
        pred = [["O"] * 8 + ["B-PER", "O"]]
        metrics = score_sequences(gold, pred)
        self.assertAlmostEqual(metrics["token_accuracy"], 0.9)
        self.assertEqual(metrics["entity_f1"], 0.0)

    def test_sentence_boundaries_prevent_entity_merging(self):
        tags = [["B-PER"], ["B-PER"]]
        self.assertEqual(score_sequences(tags, tags)["entity_per_type"]["PER"]["support"], 2)

    def test_predictions_are_not_repaired_before_strict_scoring(self):
        metrics = score_sequences([["B-PER", "I-PER"]], [["I-PER", "I-PER"]])
        self.assertEqual(metrics["entity_f1"], 0.0)

    def test_balanced_accuracy_is_macro_recall_on_present_gold_labels(self):
        metrics = score_sequences([["NN"] * 9 + ["VB"]], [["NN"] * 10], "pos")
        self.assertAlmostEqual(metrics["balanced_accuracy"], 0.5)
        self.assertNotIn("entity_f1", metrics)

    def test_misalignment_rejected(self):
        with self.assertRaises(ValueError):
            score_sequences([["O"]], [["O", "O"]])

    def test_no_entities_returns_zero_f1(self):
        result = score_sequences([["O"]], [["O"]])
        self.assertEqual(result["entity_f1"], 0.0)
        json.dumps(result, allow_nan=False)

    def test_entity_report_is_valid_json(self):
        json.dumps(score_sequences([["B-PER", "O"]], [["B-PER", "O"]]), allow_nan=False)


if __name__ == "__main__":
    unittest.main()
