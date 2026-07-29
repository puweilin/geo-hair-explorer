import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from relevance_filter import assess_relevance
from update_data import passes_stage1_filter


class RelevanceFilterTests(unittest.TestCase):
    def test_rejects_drug_indication_mention(self):
        result = assess_relevance({
            "Title": "Differentiation therapy for renal cell carcinoma",
            "Summary": (
                "Minoxidil, an FDA-approved drug for androgenetic alopecia, "
                "induced differentiation of renal carcinoma cells."
            ),
            "Overall_Design": "PLOD2 knockout in 786-O renal carcinoma cells.",
        })
        self.assertEqual(result.decision, "exclude")
        self.assertIn("drug_indication", result.incidental_signals)

    def test_rejects_alopecia_as_adverse_event(self):
        result = assess_relevance({
            "Title": "Immune response in hepatocellular carcinoma",
            "Summary": "Common adverse events included alopecia and skin rash.",
            "Overall_Design": "PBMC single-cell RNA-seq from treated patients.",
        })
        self.assertEqual(result.decision, "exclude")
        self.assertIn("adverse_event", result.incidental_signals)

    def test_includes_direct_hair_follicle_samples(self):
        result = assess_relevance({
            "Title": "Non-invasive biomarkers for substance use disorder",
            "Summary": "RNA sequencing profiled transcripts from hair follicle cells.",
            "Overall_Design": "RNA was extracted from hair follicles in three groups.",
        })
        self.assertEqual(result.decision, "include")
        self.assertIn("hair_follicle", result.design_terms)

    def test_includes_alopecia_study_using_blood(self):
        result = assess_relevance({
            "Title": "Peripheral immune cells in patients with alopecia areata",
            "Summary": "We profiled circulating immune cells across disease severity.",
            "Overall_Design": "PBMC scRNA-seq from alopecia areata and controls.",
        })
        self.assertEqual(result.decision, "include")

    def test_scalp_alone_requires_review(self):
        result = assess_relevance({
            "Title": "Epigenetic memory in cultured fibroblasts",
            "Summary": "We compared scalp-derived and dura-derived fibroblasts.",
            "Overall_Design": "RNA-seq of matched scalp and dura fibroblast cultures.",
        })
        self.assertEqual(result.decision, "review")

    def test_rejects_other_skin_appendage_comparison(self):
        result = assess_relevance({
            "Title": "Sweat gland development requires an eccrine niche",
            "Summary": "One epidermal program is shared with hair follicles.",
            "Overall_Design": "snRNA-seq of eccrine-forming ventral skin.",
        })
        self.assertEqual(result.decision, "exclude")

    def test_rejects_unrelated_tissue_despite_alopecia_in_title(self):
        result = assess_relevance({
            "Title": "RNA-seq of human lens with cataracts, alopecia, and microdontia",
            "Summary": "RNA-seq was used to diagnose a rare syndrome.",
            "Overall_Design": "Lens transcriptome from a pediatric patient.",
        })
        self.assertEqual(result.decision, "exclude")

    def test_rejects_hair_title_when_assay_is_foreskin_nhek(self):
        result = assess_relevance({
            "Title": "IRX5 promotes activation of hair follicle stem cells",
            "Summary": "The broader study investigates hair cycle initiation.",
            "Overall_Design": (
                "Normal Human Epidermal Keratinocytes from neonatal foreskin "
                "were transfected with IRX5 siRNA for RNA-seq."
            ),
        })
        self.assertEqual(result.decision, "exclude")
        self.assertIn("non_hair_epidermal_culture", result.off_topic_signals)

    def test_rejects_skin_cancer_assay_with_hair_only_in_broad_title(self):
        result = assess_relevance({
            "Title": "Myeloid cells control skin carcinogenesis and hair growth",
            "Summary": "The study evaluates cutaneous chemical carcinogenesis.",
            "Overall_Design": (
                "RNA-seq of chemically induced skin lesions and adjacent skin."
            ),
        })
        self.assertEqual(result.decision, "exclude")
        self.assertIn("skin_carcinogenesis", result.off_topic_signals)

    def test_rejects_hair_follicle_as_sensory_neuron_anatomy(self):
        result = assess_relevance({
            "Title": "Transcriptional profiling of cutaneous C-LTMRs",
            "Summary": (
                "Hair follicle-innervating C-LTMRs convey pleasant touch. "
                "Purified neuronal subsets were analyzed by RNA sequencing."
            ),
            "Overall_Design": "RNA-seq of FACS-sorted sensory neurons.",
        })
        self.assertEqual(result.decision, "exclude")
        self.assertIn("sensory_neuron", result.off_topic_signals)

    def test_stage1_keeps_embryonic_hair_development(self):
        record = {
            "title": "Embryonic skin hair follicle morphogenesis",
            "summary": "Hair follicle placodes were profiled in mouse embryos.",
        }
        self.assertTrue(passes_stage1_filter(record))

    def test_stage1_rejects_ovarian_follicle_ambiguity(self):
        record = {
            "title": "Granulosa cells in the ovarian follicle",
            "summary": "The study mentions alopecia only in the clinical history.",
        }
        self.assertFalse(passes_stage1_filter(record))

if __name__ == "__main__":
    unittest.main()
