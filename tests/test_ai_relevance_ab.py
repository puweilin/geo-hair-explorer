import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from ai_relevance_ab import calculate_metrics, hybrid_decision, normalize_assessment


class AIRelevanceABTests(unittest.TestCase):
    def test_normalizes_valid_assessment(self):
        result = normalize_assessment({
            "decision": " Include ",
            "confidence": "0.93",
            "primary_subject": "hair follicle stem cells",
            "evidence": "RNA-seq of isolated hair follicle cells",
            "reason": "Directly assayed hair follicle cells.",
        })
        self.assertEqual(result["decision"], "include")
        self.assertEqual(result["confidence"], 0.93)
        self.assertEqual(
            result["evidence"], ["RNA-seq of isolated hair follicle cells"]
        )

    def test_rejects_invalid_decision(self):
        with self.assertRaises(ValueError):
            normalize_assessment({
                "decision": "maybe",
                "confidence": 0.5,
                "evidence": [],
            })

    def test_hybrid_only_auto_decides_high_confidence_consensus(self):
        self.assertEqual(
            hybrid_decision("include", {"decision": "include", "confidence": 0.9}),
            "include",
        )
        self.assertEqual(
            hybrid_decision("include", {"decision": "exclude", "confidence": 0.99}),
            "review",
        )
        self.assertEqual(
            hybrid_decision("exclude", {"decision": "exclude", "confidence": 0.7}),
            "review",
        )
        self.assertEqual(
            hybrid_decision("review", {"decision": "include", "confidence": 0.99}),
            "review",
        )

    def test_metrics_count_false_includes_and_excludes(self):
        references = {
            "GSE1": "include",
            "GSE2": "include",
            "GSE3": "exclude",
            "GSE4": "exclude",
        }
        predictions = {
            "GSE1": "include",
            "GSE2": "exclude",
            "GSE3": "include",
            "GSE4": "review",
        }
        metrics = calculate_metrics(predictions, references)
        self.assertEqual(metrics.false_include, 1)
        self.assertEqual(metrics.false_exclude, 1)
        self.assertEqual(metrics.review, 1)
        self.assertAlmostEqual(metrics.coverage, 0.75)
        self.assertAlmostEqual(metrics.accuracy_on_decided, 1 / 3)


if __name__ == "__main__":
    unittest.main()
