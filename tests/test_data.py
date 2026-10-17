from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from conll_ner.data import (Sentence, normalise_bio, read_conll, label_vocabulary,
                            align_first_subwords, encode_sentences, assert_disjoint)


class DataTests(unittest.TestCase):
    def test_iob1_normalisation_preserves_adjacent_entities(self):
        self.assertEqual(normalise_bio(["I-PER", "I-PER", "B-PER", "O", "I-ORG"], "iob1"),
                         ["B-PER", "I-PER", "B-PER", "O", "B-ORG"])

    def test_iob2_rejects_orphan_inside(self):
        with self.assertRaises(ValueError):
            normalise_bio(["O", "I-LOC"], "iob2")

    def test_parser_whitespace_document_boundary_eof(self):
        with TemporaryDirectory() as d:
            path = Path(d) / "input.txt"
            path.write_text("Alice\tNNP B-NP I-PER\n-DOCSTART- -X- -X- O\nBerlin  NNP B-NP I-LOC", encoding="utf-8")
            self.assertEqual(read_conll(path), [Sentence(["Alice"], ["B-PER"]), Sentence(["Berlin"], ["B-LOC"])])

    def test_parser_rejects_bad_columns_and_empty(self):
        with TemporaryDirectory() as d:
            path = Path(d) / "input.txt"
            for value in ("Alice NNP O", "", "Alice NNP B-NP B-PER EXTRA"):
                path.write_text(value, encoding="utf-8")
                with self.assertRaises(ValueError):
                    read_conll(path)

    def test_alignment_masks_special_and_continuation(self):
        result = align_first_subwords([None, 0, 0, 1, None], ["B-PER", "O"], {"B-PER": 1, "O": 0})
        self.assertEqual(result, [-100, 1, -100, 0, -100])

    def test_alignment_rejects_missing_words_and_unknown_labels(self):
        for ids, tags in [([None, 0, None], ["O", "O"]), ([0], ["B-UNSEEN"])]:
            with self.assertRaises(ValueError):
                align_first_subwords(ids, tags, {"O": 0})

    def test_fixed_ner_vocabulary_and_unknown_entity(self):
        self.assertEqual(len(label_vocabulary([Sentence(["a"], ["O"])], "ner")), 9)
        with self.assertRaises(ValueError):
            label_vocabulary([Sentence(["a"], ["B-SECRET"])], "ner")

    def test_split_overlap_checks_tokens_not_annotations(self):
        with self.assertRaises(ValueError):
            assert_disjoint([Sentence(["Alice"], ["B-PER"])], [Sentence(["Alice"], ["O"])])

    def test_overlength_is_not_silently_truncated(self):
        def fake_tokenizer(*args, **kwargs):
            self.assertFalse(kwargs["truncation"])
            return {"input_ids": [0] * 129}
        with self.assertRaisesRegex(ValueError, "129 subwords"):
            encode_sentences([Sentence(["a"], ["O"])], fake_tokenizer, {"O": 0}, 128)


if __name__ == "__main__":
    unittest.main()
