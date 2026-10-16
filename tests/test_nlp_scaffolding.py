"""
ProductPulse — Unit Tests for NLP Scaffolding (Phase 7A)
Validates:
1. Sentence splitting, punctuation, abbreviations, blank text, and exact offset correctness.
2. Leakage-safe connected-component partitioner, duplicate-review handling, and integrity guarantees.
3. Reproducible two-part evaluation sampler, Sample A/B separation, and stratum shortfall reporting.
4. Pydantic schema validation rules and invalid state rejection.
5. Evaluation metrics engine: accounting breakdown, primary 3-class Macro-F1, 4-class confusion matrix,
   operational uncertainty rates, zero denominators, absent classes, and validation errors on missing predictions.
"""
import csv
import json
import os
import sqlite3
import unittest
from backend.app.nlp.schemas import (
    AnnotationStatus,
    AnnotationUnit,
    AspectName,
    DetectionStatus,
    SentimentLabel,
    SamplingSource
)
from backend.app.nlp.tokenizer import segment_sentences
from backend.app.nlp.partitioner import ConnectedComponentPartitioner
from backend.app.nlp.sampler import EvaluationSampler
from backend.app.nlp.metrics import (
    EvaluationValidationError,
    evaluate_detection,
    evaluate_sentiment
)


class TestSentenceTokenizer(unittest.TestCase):
    """Tests for offset-preserving sentence segmenter."""

    def test_sentence_segmentation_offsets(self):
        text = "The screen is amazing. Battery life is decent! Will it last 2 years? Hopefully."
        spans = segment_sentences(text)
        self.assertEqual(len(spans), 4)

        for span in spans:
            extracted = text[span.char_start:span.char_end]
            self.assertEqual(extracted, span.sentence_text)

        self.assertEqual(spans[0].sentence_text, "The screen is amazing.")
        self.assertEqual(spans[1].sentence_text, "Battery life is decent!")
        self.assertEqual(spans[2].sentence_text, "Will it last 2 years?")
        self.assertEqual(spans[3].sentence_text, "Hopefully.")

    def test_abbreviation_preservation(self):
        text = "It outputs 5.0v at approx. 2.5A e.g. for fast charging. Works great vs. others etc. No issues."
        spans = segment_sentences(text)
        # Should not split on decimals or abbreviations like approx., e.g., vs., etc.
        combined = " ".join(s.sentence_text for s in spans)
        self.assertIn("approx. 2.5A e.g. for fast charging.", combined)
        self.assertIn("vs. others etc.", combined)

    def test_blank_and_title_handling(self):
        # Empty string
        self.assertEqual(segment_sentences(""), [])
        self.assertEqual(segment_sentences("   \n\t  "), [])
        self.assertEqual(segment_sentences(None), [])

        # Title fallback when body is blank
        title_only_spans = segment_sentences("", raw_title="Great phone case")
        self.assertEqual(len(title_only_spans), 1)
        self.assertTrue(title_only_spans[0].is_title)
        self.assertEqual(title_only_spans[0].sentence_text, "Great phone case")
        self.assertEqual(title_only_spans[0].char_start, 0)
        self.assertEqual(title_only_spans[0].char_end, 16)


class TestPartitioner(unittest.TestCase):
    """Tests for leakage-safe connected-component partitioner."""

    def setUp(self):
        # Create a mock review dataset with 2 products, one having a duplicate review
        self.records = [
            # Product A: 3 distinct reviews + 1 duplicate of review 1
            {"review_id": "r1", "parent_asin": "P_A", "canonical_hash": "hash_1", "occurrence_index": 0},
            {"review_id": "r2", "parent_asin": "P_A", "canonical_hash": "hash_2", "occurrence_index": 0},
            {"review_id": "r3", "parent_asin": "P_A", "canonical_hash": "hash_3", "occurrence_index": 0},
            {"review_id": "r1_dup", "parent_asin": "P_A", "canonical_hash": "hash_1", "occurrence_index": 1},

            # Product B: 2 reviews
            {"review_id": "r4", "parent_asin": "P_B", "canonical_hash": "hash_4", "occurrence_index": 0},
            {"review_id": "r5", "parent_asin": "P_B", "canonical_hash": "hash_5", "occurrence_index": 0},

            # Product C: shares a duplicate review with Product D (cross-product duplicate)
            {"review_id": "r6", "parent_asin": "P_C", "canonical_hash": "hash_cross", "occurrence_index": 0},
            {"review_id": "r7", "parent_asin": "P_D", "canonical_hash": "hash_cross", "occurrence_index": 1},
        ]

    def test_leakage_safe_partitioning(self):
        partitioner = ConnectedComponentPartitioner(seed=42)
        assignments, manifest = partitioner.build_partitions(self.records)

        self.assertEqual(manifest.total_reviews, len(self.records))
        self.assertEqual(manifest.duplicate_cross_partition_violations, 0)

        # Map review_id to partition
        p_map = {a.review_id: a.partition for a in assignments}

        # 1. Duplicate r1 and r1_dup MUST be in the exact same partition
        self.assertEqual(p_map["r1"], p_map["r1_dup"])

        # 2. All reviews for Product A MUST be in the same partition
        self.assertEqual(p_map["r1"], p_map["r2"])
        self.assertEqual(p_map["r2"], p_map["r3"])

        # 3. Cross-product duplicate (Product C and Product D connected by hash_cross)
        # MUST belong to the exact same partition to avoid cross-product leakage
        self.assertEqual(p_map["r6"], p_map["r7"])

    def test_deterministic_partitions(self):
        partitioner1 = ConnectedComponentPartitioner(seed=123)
        assignments1, _ = partitioner1.build_partitions(self.records)

        partitioner2 = ConnectedComponentPartitioner(seed=123)
        assignments2, _ = partitioner2.build_partitions(self.records)

        self.assertEqual([a.partition for a in assignments1], [a.partition for a in assignments2])


class TestEvaluationSampler(unittest.TestCase):
    """Tests for reproducible evaluation sampler."""

    def setUp(self):
        # 60 reviews: 20 in 1-2 star, 20 in 3 star, 20 in 4-5 star
        # All mention battery and screen, none mention camera, audio, software, or build
        self.mock_reviews = []
        for i in range(60):
            if i < 20:
                rating = 1.0
            elif i < 40:
                rating = 3.0
            else:
                rating = 5.0

            self.mock_reviews.append({
                "review_id": f"rev_{i}",
                "parent_asin": f"B00{i:04d}",
                "asin": f"B00{i:04d}",
                "rating": rating,
                "raw_text": f"This is review {i}. The battery life is great and the screen is sharp.",
                "raw_title": "Good product",
                "verified_purchase": True,
                "is_blank_text": False
            })

    def test_sample_a_generation(self):
        sampler = EvaluationSampler(seed=42)
        units, meta = sampler.sample_a_detection(self.mock_reviews, target_size=10)

        # 10 sentences * 6 candidate aspects = 60 AnnotationUnits
        self.assertEqual(len(units), 60)
        self.assertEqual(meta.actual_sample_size, 10)
        for u in units:
            self.assertEqual(u.annotation_status, AnnotationStatus.UNANNOTATED)
            self.assertIsNone(u.sentiment_label)
            self.assertEqual(u.sampling_source, SamplingSource.SAMPLE_A_DETECTION)

    def test_sample_b_stratification_and_shortfall(self):
        sampler = EvaluationSampler(seed=42)
        # We request 60 units (10 per aspect)
        units, meta = sampler.sample_b_sentiment(self.mock_reviews, target_size=60)

        # Reviews only mention battery and screen, so other 4 aspects will have recorded shortfalls
        self.assertGreater(len(meta.shortfalls), 0)
        shortfall_aspects = {sf.aspect_name for sf in meta.shortfalls}
        # Unmentioned aspects must be recorded in shortfalls
        self.assertIn(AspectName.CAMERA_OPTICS, shortfall_aspects)
        self.assertIn(AspectName.CONNECTIVITY_AUDIO, shortfall_aspects)
        self.assertIn(AspectName.PERFORMANCE_SOFTWARE, shortfall_aspects)
        self.assertIn(AspectName.BUILD_DURABILITY, shortfall_aspects)

        for u in units:
            self.assertEqual(u.annotation_status, AnnotationStatus.UNANNOTATED)
            self.assertIsNone(u.sentiment_label)
            self.assertEqual(u.detection_status, DetectionStatus.PRESENT)
            self.assertEqual(u.sampling_source, SamplingSource.SAMPLE_B_SENTIMENT)

    def test_sample_a_b_overlap_prevention_and_unannotated_templates(self):
        """Asserts exclude_sentence_ids guarantees zero sentence overlap between Sample A and B, and templates are unannotated."""
        sampler = EvaluationSampler(seed=100)
        # Generate Sample A
        units_a, meta_a = sampler.sample_a_detection(self.mock_reviews, target_size=15)
        sentence_ids_a = {u.sentence_id for u in units_a}
        self.assertEqual(len(sentence_ids_a), 15)

        # Generate Sample B excluding sentence IDs already selected in Sample A
        units_b, meta_b = sampler.sample_b_sentiment(
            self.mock_reviews,
            target_size=20,
            exclude_sentence_ids=sentence_ids_a
        )
        sentence_ids_b = {u.sentence_id for u in units_b}

        # Assert zero overlap between Sample A and Sample B sentences
        overlap = sentence_ids_a.intersection(sentence_ids_b)
        self.assertEqual(len(overlap), 0, f"Expected 0 overlapping sentences, found: {overlap}")

        # Assert all generated templates remain unannotated with null sentiment labels
        for u in units_a:
            self.assertEqual(u.annotation_status, AnnotationStatus.UNANNOTATED)
            self.assertIsNone(u.sentiment_label)
        for u in units_b:
            self.assertEqual(u.annotation_status, AnnotationStatus.UNANNOTATED)
            self.assertIsNone(u.sentiment_label)


class TestSchemasValidation(unittest.TestCase):
    """Tests Pydantic schema validation rules."""

    def test_invalid_label_combinations(self):
        # 1. DetectionStatus.ABSENT cannot have a SentimentLabel
        with self.assertRaises(ValueError):
            AnnotationUnit(
                annotation_id="test#battery_charging",
                sentence_id="rev1_s0",
                review_id="rev1",
                parent_asin="B001",
                asin="B001",
                sentence_index=0,
                sentence_text="No mention.",
                char_start=0,
                char_end=11,
                aspect_name=AspectName.BATTERY_CHARGING,
                detection_status=DetectionStatus.ABSENT,
                annotation_status=AnnotationStatus.ANNOTATED,
                sentiment_label=SentimentLabel.POSITIVE,  # INVALID: absent aspect cannot have sentiment
                source_rating=5.0,
                sampling_source=SamplingSource.SAMPLE_A_DETECTION
            )

        # 2. AnnotationStatus.UNANNOTATED cannot already carry a SentimentLabel
        with self.assertRaises(ValueError):
            AnnotationUnit(
                annotation_id="test#battery_charging",
                sentence_id="rev1_s0",
                review_id="rev1",
                parent_asin="B001",
                asin="B001",
                sentence_index=0,
                sentence_text="Battery was great.",
                char_start=0,
                char_end=18,
                aspect_name=AspectName.BATTERY_CHARGING,
                detection_status=DetectionStatus.PRESENT,
                annotation_status=AnnotationStatus.UNANNOTATED,
                sentiment_label=SentimentLabel.POSITIVE,  # INVALID: unannotated template cannot have label
                source_rating=5.0,
                sampling_source=SamplingSource.SAMPLE_B_SENTIMENT
            )

        # 3. Annotated + Present must have a SentimentLabel
        with self.assertRaises(ValueError):
            AnnotationUnit(
                annotation_id="test#battery_charging",
                sentence_id="rev1_s0",
                review_id="rev1",
                parent_asin="B001",
                asin="B001",
                sentence_index=0,
                sentence_text="Battery was great.",
                char_start=0,
                char_end=18,
                aspect_name=AspectName.BATTERY_CHARGING,
                detection_status=DetectionStatus.PRESENT,
                annotation_status=AnnotationStatus.ANNOTATED,
                sentiment_label=None,  # INVALID: annotated present aspect must provide label
                source_rating=5.0,
                sampling_source=SamplingSource.SAMPLE_B_SENTIMENT
            )


class TestMetricsEngine(unittest.TestCase):
    """Tests evaluation metrics calculations, edge cases, and accounting."""

    def test_accounting_breakdown_and_unannotated_rejection(self):
        # 100% unannotated records must raise EvaluationValidationError
        unannotated_data = [
            {
                "annotation_id": f"ann_{i}",
                "annotation_status": "unannotated",
                "detection_status": "present",
                "gold_sentiment": None,
                "predicted_sentiment": None
            }
            for i in range(10)
        ]
        with self.assertRaises(EvaluationValidationError):
            evaluate_sentiment(unannotated_data)

    def test_sentiment_macro_f1_math_and_uncertainty(self):
        # Create a mock dataset with:
        # - 1 unannotated record (excluded from performance)
        # - 1 absent aspect record (excluded from sentiment)
        # - 1 gold uncertain record
        # - 6 eligible records: 2 pos (1 pred pos, 1 pred uncertain), 2 neu (2 pred neu), 2 neg (1 pred neg, 1 pred pos)
        mock_data = [
            {"annotation_status": "unannotated", "detection_status": "present", "gold_sentiment": None, "predicted_sentiment": None},
            {"annotation_status": "annotated", "detection_status": "absent", "gold_sentiment": None, "predicted_sentiment": None},
            # Gold uncertain: model predicts uncertain (concordant)
            {"annotation_status": "annotated", "detection_status": "present", "gold_sentiment": "uncertain/unclassified", "predicted_sentiment": "uncertain/unclassified"},
            # Eligible units:
            {"annotation_status": "annotated", "detection_status": "present", "gold_sentiment": "positive", "predicted_sentiment": "positive"},
            {"annotation_status": "annotated", "detection_status": "present", "gold_sentiment": "positive", "predicted_sentiment": "uncertain/unclassified"}, # Miss for positive!
            {"annotation_status": "annotated", "detection_status": "present", "gold_sentiment": "neutral", "predicted_sentiment": "neutral"},
            {"annotation_status": "annotated", "detection_status": "present", "gold_sentiment": "neutral", "predicted_sentiment": "neutral"},
            {"annotation_status": "annotated", "detection_status": "present", "gold_sentiment": "negative", "predicted_sentiment": "negative"},
            {"annotation_status": "annotated", "detection_status": "present", "gold_sentiment": "negative", "predicted_sentiment": "positive"}, # FP for positive, FN for neg
        ]

        report = evaluate_sentiment(mock_data)

        # Check accounting breakdown
        self.assertEqual(report.accounting.total_records, 9)
        self.assertEqual(report.accounting.unannotated_count, 1)
        self.assertEqual(report.accounting.excluded_absent_count, 1)
        self.assertEqual(report.accounting.annotated_aspect_present_count, 7) # S_diagnostic
        self.assertEqual(report.accounting.gold_uncertain_count, 1)
        self.assertEqual(report.accounting.eligible_3class_gold_count, 6) # S_eligible

        # Check per-class metrics:
        # Positive:
        # Gold = 2. Predictions = 1 'pos' (correct), 1 'pos' (false alarm from neg). TP=1, FP=1, FN=1 (due to uncertain prediction).
        # Prec = 1/(1+1) = 0.5. Rec = 1/(1+1) = 0.5. F1 = 0.5
        pos_m = report.per_class_metrics["positive"]
        self.assertEqual(pos_m.true_positives, 1)
        self.assertEqual(pos_m.false_positives, 1)
        self.assertEqual(pos_m.false_negatives, 1)
        self.assertEqual(pos_m.precision, 0.5)
        self.assertEqual(pos_m.recall, 0.5)
        self.assertEqual(pos_m.f1_score, 0.5)

        # Neutral:
        # Gold = 2. Predictions = 2 'neu'. TP=2, FP=0, FN=0.
        # Prec = 1.0, Rec = 1.0, F1 = 1.0
        neu_m = report.per_class_metrics["neutral"]
        self.assertEqual(neu_m.true_positives, 2)
        self.assertEqual(neu_m.false_positives, 0)
        self.assertEqual(neu_m.false_negatives, 0)
        self.assertEqual(neu_m.precision, 1.0)
        self.assertEqual(neu_m.recall, 1.0)
        self.assertEqual(neu_m.f1_score, 1.0)

        # Negative:
        # Gold = 2. Predictions = 1 'neg', 1 'pos'. TP=1, FP=0, FN=1.
        # Prec = 1.0, Rec = 0.5, F1 = 2*(1*0.5)/(1.5) = 1/1.5 = 0.6667
        neg_m = report.per_class_metrics["negative"]
        self.assertEqual(neg_m.true_positives, 1)
        self.assertEqual(neg_m.false_positives, 0)
        self.assertEqual(neg_m.false_negatives, 1)
        self.assertEqual(neg_m.precision, 1.0)
        self.assertEqual(neg_m.recall, 0.5)
        self.assertAlmostEqual(neg_m.f1_score, 0.6667, places=4)

        # 3-Class Macro-F1 = (0.5 + 1.0 + 0.6667) / 3 = 2.1667 / 3 = 0.7222
        self.assertAlmostEqual(report.primary_3class_macro_f1, 0.7222, places=4)

        # Uncertainty Rates:
        # Pred uncertainty on eligible set: 1 uncertain pred out of 6 eligible = 1/6 = 0.1667
        self.assertAlmostEqual(report.pred_uncertainty_rate_eligible, 0.1667, places=4)

        # Overall pred uncertainty: 2 uncertain preds out of 7 diagnostic = 2/7 = 0.2857
        self.assertAlmostEqual(report.pred_uncertainty_rate_overall, 0.2857, places=4)

        # Gold uncertainty prevalence: 1 out of 7 diagnostic = 1/7 = 0.1429
        self.assertAlmostEqual(report.gold_uncertainty_prevalence, 0.1429, places=4)

        # 4x4 Confusion Matrix checks
        m = report.confusion_matrix_4x4
        self.assertEqual(m["positive"]["positive"], 1)
        self.assertEqual(m["positive"]["uncertain/unclassified"], 1)
        self.assertEqual(m["neutral"]["neutral"], 2)
        self.assertEqual(m["negative"]["negative"], 1)
        self.assertEqual(m["negative"]["positive"], 1)
        self.assertEqual(m["uncertain/unclassified"]["uncertain/unclassified"], 1)

    def test_missing_prediction_rejection(self):
        # Missing prediction on annotated unit must raise EvaluationValidationError
        bad_data = [
            {
                "annotation_status": "annotated",
                "detection_status": "present",
                "gold_sentiment": "positive",
                "predicted_sentiment": None # Missing!
            }
        ]
        with self.assertRaises(EvaluationValidationError):
            evaluate_sentiment(bad_data)

    def test_zero_denominator_handling(self):
        # Class with zero true instances and zero predictions should yield 0.0 without division error
        zero_data = [
            {"annotation_status": "annotated", "detection_status": "present", "gold_sentiment": "positive", "predicted_sentiment": "positive"},
        ]
        report = evaluate_sentiment(zero_data)
        self.assertEqual(report.per_class_metrics["neutral"].precision, 0.0)
        self.assertEqual(report.per_class_metrics["neutral"].recall, 0.0)
        self.assertEqual(report.per_class_metrics["neutral"].f1_score, 0.0)

    def test_evaluate_detection_metrics_and_zero_denominators(self):
        """Tests evaluate_detection with known TP, FP, FN, TN and zero denominators across aspects."""
        mock_detection_data = [
            # battery_charging: Gold=present, Pred=present (TP)
            {"aspect_name": AspectName.BATTERY_CHARGING, "gold_detection": "present", "predicted_detection": "present"},
            # battery_charging: Gold=present, Pred=absent (FN)
            {"aspect_name": AspectName.BATTERY_CHARGING, "gold_detection": "present", "predicted_detection": "absent"},
            # battery_charging: Gold=absent, Pred=present (FP)
            {"aspect_name": AspectName.BATTERY_CHARGING, "gold_detection": "absent", "predicted_detection": "present"},
            # screen_display: Gold=present, Pred=present (TP)
            {"aspect_name": AspectName.SCREEN_DISPLAY, "gold_detection": "present", "predicted_detection": "present"},
            # screen_display: Gold=absent, Pred=absent (TN)
            {"aspect_name": AspectName.SCREEN_DISPLAY, "gold_detection": "absent", "predicted_detection": "absent"},
            # Other 4 aspects (camera, audio, software, durability) have zero true instances and zero predictions
            {"aspect_name": AspectName.CAMERA_OPTICS, "gold_detection": "absent", "predicted_detection": "absent"},
            {"aspect_name": AspectName.CONNECTIVITY_AUDIO, "gold_detection": "absent", "predicted_detection": "absent"},
            {"aspect_name": AspectName.PERFORMANCE_SOFTWARE, "gold_detection": "absent", "predicted_detection": "absent"},
            {"aspect_name": AspectName.BUILD_DURABILITY, "gold_detection": "absent", "predicted_detection": "absent"},
        ]

        report = evaluate_detection(mock_detection_data)
        self.assertEqual(report.total_evaluated_spans, len(mock_detection_data))

        # Check battery_charging metrics:
        # TP=1, FP=1, FN=1.
        # Precision = 1/(1+1) = 0.5. Recall = 1/(1+1) = 0.5. F1 = 0.5
        bat = report.per_aspect_metrics["battery_charging"]
        self.assertEqual(bat.true_positives, 1)
        self.assertEqual(bat.false_positives, 1)
        self.assertEqual(bat.false_negatives, 1)
        self.assertEqual(bat.precision, 0.5)
        self.assertEqual(bat.recall, 0.5)
        self.assertEqual(bat.f1_score, 0.5)

        # Check screen_display metrics:
        # TP=1, FP=0, FN=0.
        # Precision = 1.0, Recall = 1.0, F1 = 1.0
        screen = report.per_aspect_metrics["screen_display"]
        self.assertEqual(screen.true_positives, 1)
        self.assertEqual(screen.false_positives, 0)
        self.assertEqual(screen.false_negatives, 0)
        self.assertEqual(screen.precision, 1.0)
        self.assertEqual(screen.recall, 1.0)
        self.assertEqual(screen.f1_score, 1.0)

        # Check zero denominator aspect (camera_optics):
        # TP=0, FP=0, FN=0. Prec=0.0, Rec=0.0, F1=0.0
        cam = report.per_aspect_metrics["camera_optics"]
        self.assertEqual(cam.true_positives, 0)
        self.assertEqual(cam.false_positives, 0)
        self.assertEqual(cam.false_negatives, 0)
        self.assertEqual(cam.precision, 0.0)
        self.assertEqual(cam.recall, 0.0)
        self.assertEqual(cam.f1_score, 0.0)

        # Macro-F1 across all 6 aspects:
        # F1s: battery=0.5, screen=1.0, camera=0.0, audio=0.0, software=0.0, durability=0.0
        # Macro-F1 = (0.5 + 1.0 + 0 + 0 + 0 + 0) / 6 = 1.5 / 6 = 0.25
        self.assertEqual(report.macro_f1_detection, 0.25)

    def test_evaluate_detection_mixed_annotated_unannotated_integrity(self):
        """
        Verifies that mixing unannotated records into detection evaluation:
        1. Leaves per-aspect precision, recall, F1, and support completely unchanged.
        2. Leaves macro_f1_detection completely unchanged.
        3. Excludes unannotated records from all eligible denominators.
        """
        annotated_records = [
            {"aspect_name": AspectName.BATTERY_CHARGING, "annotation_status": "annotated", "gold_detection": "present", "predicted_detection": "present"},
            {"aspect_name": AspectName.BATTERY_CHARGING, "annotation_status": "annotated", "gold_detection": "present", "predicted_detection": "absent"},
            {"aspect_name": AspectName.BATTERY_CHARGING, "annotation_status": "annotated", "gold_detection": "absent", "predicted_detection": "present"},
            {"aspect_name": AspectName.SCREEN_DISPLAY, "annotation_status": "annotated", "gold_detection": "present", "predicted_detection": "present"},
            {"aspect_name": AspectName.SCREEN_DISPLAY, "annotation_status": "annotated", "gold_detection": "absent", "predicted_detection": "absent"},
            {"aspect_name": AspectName.CAMERA_OPTICS, "annotation_status": "annotated", "gold_detection": "absent", "predicted_detection": "absent"},
            {"aspect_name": AspectName.CONNECTIVITY_AUDIO, "annotation_status": "annotated", "gold_detection": "absent", "predicted_detection": "absent"},
            {"aspect_name": AspectName.PERFORMANCE_SOFTWARE, "annotation_status": "annotated", "gold_detection": "absent", "predicted_detection": "absent"},
            {"aspect_name": AspectName.BUILD_DURABILITY, "annotation_status": "annotated", "gold_detection": "absent", "predicted_detection": "absent"},
        ]

        # Base report on purely annotated gold data
        base_report = evaluate_detection(annotated_records)

        # Mix in unannotated records across multiple aspects
        unannotated_records = [
            {"aspect_name": AspectName.BATTERY_CHARGING, "annotation_status": "unannotated", "gold_detection": "absent", "predicted_detection": "present"},
            {"aspect_name": AspectName.BATTERY_CHARGING, "annotation_status": "unannotated", "gold_detection": "present", "predicted_detection": "present"},
            {"aspect_name": AspectName.SCREEN_DISPLAY, "annotation_status": "unannotated", "gold_detection": "absent", "predicted_detection": "absent"},
            {"aspect_name": AspectName.CAMERA_OPTICS, "annotation_status": "unannotated", "gold_detection": "present", "predicted_detection": "absent"},
            {"aspect_name": AspectName.BUILD_DURABILITY, "annotation_status": "unannotated", "gold_detection": "absent", "predicted_detection": "present"},
        ]
        mixed_records = annotated_records + unannotated_records

        mixed_report = evaluate_detection(mixed_records)

        # Assert macro_f1_detection is identical
        self.assertEqual(mixed_report.macro_f1_detection, base_report.macro_f1_detection)

        # Assert every per-aspect metric and denominator is identical
        for aspect_name, base_class_metrics in base_report.per_aspect_metrics.items():
            mixed_class_metrics = mixed_report.per_aspect_metrics[aspect_name]
            self.assertEqual(mixed_class_metrics.true_positives, base_class_metrics.true_positives)
            self.assertEqual(mixed_class_metrics.false_positives, base_class_metrics.false_positives)
            self.assertEqual(mixed_class_metrics.false_negatives, base_class_metrics.false_negatives)
            self.assertEqual(mixed_class_metrics.support, base_class_metrics.support)
            self.assertEqual(mixed_class_metrics.precision, base_class_metrics.precision)
            self.assertEqual(mixed_class_metrics.recall, base_class_metrics.recall)
            self.assertEqual(mixed_class_metrics.f1_score, base_class_metrics.f1_score)

    def test_evaluate_detection_all_unannotated_raises_validation_error(self):
        """Verifies that submitting 100% unannotated templates to evaluate_detection raises EvaluationValidationError."""
        all_unannotated = [
            {"aspect_name": AspectName.BATTERY_CHARGING, "annotation_status": "unannotated", "gold_detection": "absent", "predicted_detection": "present"},
            {"aspect_name": AspectName.SCREEN_DISPLAY, "annotation_status": "unannotated", "gold_detection": "absent", "predicted_detection": "absent"},
            {"aspect_name": AspectName.CAMERA_OPTICS, "annotation_status": "unannotated", "gold_detection": "present", "predicted_detection": "absent"},
        ]
        with self.assertRaises(EvaluationValidationError) as cm:
            evaluate_detection(all_unannotated)
        self.assertIn("100% of submitted records are unannotated templates", str(cm.exception))


class TestReconciliationTool(unittest.TestCase):
    """Tests for Phase 7B annotation reconciliation safeguards, provenance hardening, and SQLite verification."""

    def setUp(self):
        import sqlite3
        import tempfile
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "mock_productpulse.db")
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE reviews (
                review_id TEXT PRIMARY KEY,
                canonical_hash TEXT,
                occurrence_index INTEGER DEFAULT 0,
                parent_asin TEXT,
                asin TEXT,
                rating REAL,
                raw_title TEXT,
                raw_text TEXT
            );
        """)
        cur.execute("""
            INSERT INTO reviews (review_id, canonical_hash, occurrence_index, parent_asin, asin, rating, raw_title, raw_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("rev1", "hash_rev1", 0, "B001", "B001", 3.0, "Decent phone", "Battery life is decent but screen is dim."))
        cur.execute("""
            INSERT INTO reviews (review_id, canonical_hash, occurrence_index, parent_asin, asin, rating, raw_title, raw_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("rev_b1", "hash_b1", 0, "B001", "B001", 5.0, "Great battery", "Battery life is great."))
        cur.execute("""
            INSERT INTO reviews (review_id, canonical_hash, occurrence_index, parent_asin, asin, rating, raw_title, raw_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("rev_b2", "hash_b2", 0, "B002", "B002", 1.0, "Screen issue", "Not about screen at all."))
        cur.execute("""
            INSERT INTO reviews (review_id, canonical_hash, occurrence_index, parent_asin, asin, rating, raw_title, raw_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("rev_title_only", "hash_title", 0, "B003", "B003", 4.0, "Title as single sentence fallback", ""))
        conn.commit()
        conn.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_sample_a_reconciliation_blank_and_completed(self):
        import csv
        import json
        import os
        from scripts.reconcile_annotations import reconcile_sample_a

        canon_path = os.path.join(self.temp_dir.name, "canon_a.jsonl")
        units = []
        for asp in AspectName:
            units.append({
                "annotation_id": f"rev1_s0#{asp.value}",
                "sentence_id": "rev1_s0",
                "review_id": "rev1",
                "parent_asin": "B001",
                "asin": "B001",
                "sentence_index": 0,
                "sentence_text": "Battery life is decent but screen is dim.",
                "char_start": 0,
                "char_end": 41,
                "aspect_name": asp.value,
                "detection_status": "absent",
                "annotation_status": "unannotated",
                "sentiment_label": None,
                "source_rating": 3.0,
                "verified_purchase": True,
                "sampling_source": "sample_a_detection",
                "notes": None
            })
        with open(canon_path, "w", encoding="utf-8") as f:
            for u in units:
                f.write(json.dumps(u) + "\n")

        # Create human CSV with battery=1, screen=1, camera=0, others blank
        csv_path = os.path.join(self.temp_dir.name, "human_a.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "sentence_id", "review_id", "parent_asin", "asin", "source_rating", "sentence_text",
                "build_durability", "battery_charging", "screen_display",
                "camera_optics", "connectivity_audio", "performance_software", "annotator_notes"
            ])
            writer.writerow([
                "rev1_s0", "rev1", "B001", "B001", "3.0", "Battery life is decent but screen is dim.",
                "", "1", "present", "0", "", "", "human note"
            ])

        out_path = os.path.join(self.temp_dir.name, "reconciled_a.jsonl")
        summary = reconcile_sample_a(csv_path, canon_path, out_path, db_path=self.db_path)

        self.assertEqual(summary["completed_decisions"], 3)  # battery=1, screen=present, camera=0
        self.assertEqual(summary["unannotated_decisions"], 3)  # durability, audio, software blank

        # Verify reconciled records
        reconciled = []
        with open(out_path, "r", encoding="utf-8") as f:
            for l in f:
                reconciled.append(json.loads(l.strip()))

        rec_map = {r["aspect_name"]: r for r in reconciled}
        # Battery -> annotated, present
        self.assertEqual(rec_map["battery_charging"]["annotation_status"], "annotated")
        self.assertEqual(rec_map["battery_charging"]["detection_status"], "present")
        # Screen -> annotated, present
        self.assertEqual(rec_map["screen_display"]["annotation_status"], "annotated")
        self.assertEqual(rec_map["screen_display"]["detection_status"], "present")
        # Camera -> annotated, absent
        self.assertEqual(rec_map["camera_optics"]["annotation_status"], "annotated")
        self.assertEqual(rec_map["camera_optics"]["detection_status"], "absent")
        # Audio -> unannotated, absent
        self.assertEqual(rec_map["connectivity_audio"]["annotation_status"], "unannotated")
        self.assertEqual(rec_map["connectivity_audio"]["detection_status"], "absent")

    def test_sample_b_reconciliation_presence_and_absence(self):
        import csv
        import json
        import os
        from scripts.reconcile_annotations import reconcile_sample_b

        canon_path = os.path.join(self.temp_dir.name, "canon_b.jsonl")
        units = [
            # Unit 1: battery
            {
                "annotation_id": "rev_b1_s0#battery_charging",
                "sentence_id": "rev_b1_s0",
                "review_id": "rev_b1",
                "parent_asin": "B001",
                "asin": "B001",
                "sentence_index": 0,
                "sentence_text": "Battery life is great.",
                "char_start": 0,
                "char_end": 22,
                "aspect_name": "battery_charging",
                "detection_status": "present",
                "annotation_status": "unannotated",
                "sentiment_label": None,
                "source_rating": 5.0,
                "verified_purchase": True,
                "sampling_source": "sample_b_sentiment",
                "notes": None
            },
            # Unit 2: screen
            {
                "annotation_id": "rev_b2_s0#screen_display",
                "sentence_id": "rev_b2_s0",
                "review_id": "rev_b2",
                "parent_asin": "B002",
                "asin": "B002",
                "sentence_index": 0,
                "sentence_text": "Not about screen at all.",
                "char_start": 0,
                "char_end": 24,
                "aspect_name": "screen_display",
                "detection_status": "present",
                "annotation_status": "unannotated",
                "sentiment_label": None,
                "source_rating": 1.0,
                "verified_purchase": True,
                "sampling_source": "sample_b_sentiment",
                "notes": None
            }
        ]
        with open(canon_path, "w", encoding="utf-8") as f:
            for u in units:
                f.write(json.dumps(u) + "\n")

        # Create CSV: Unit 1 confirmed present with positive sentiment; Unit 2 confirmed absent with blank sentiment
        csv_path = os.path.join(self.temp_dir.name, "human_b.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "annotation_id", "sentence_id", "review_id", "parent_asin", "asin",
                "source_rating", "sentence_text", "target_aspect",
                "aspect_confirmed", "human_sentiment", "annotator_notes"
            ])
            writer.writerow([
                "rev_b1_s0#battery_charging", "rev_b1_s0", "rev_b1", "B001", "B001",
                "5.0", "Battery life is great.", "battery_charging",
                "1", "positive", ""
            ])
            writer.writerow([
                "rev_b2_s0#screen_display", "rev_b2_s0", "rev_b2", "B002", "B002",
                "1.0", "Not about screen at all.", "screen_display",
                "0", "", ""  # Absent aspect correctly has blank sentiment
            ])

        out_path = os.path.join(self.temp_dir.name, "reconciled_b.jsonl")
        summary = reconcile_sample_b(csv_path, canon_path, out_path, db_path=self.db_path)

        self.assertEqual(summary["completed_records"], 2)
        self.assertEqual(summary["confirmed_present"], 1)
        self.assertEqual(summary["confirmed_absent"], 1)

        reconciled = []
        with open(out_path, "r", encoding="utf-8") as f:
            for l in f:
                reconciled.append(json.loads(l.strip()))

        # Unit 1 is present and positive
        self.assertEqual(reconciled[0]["detection_status"], "present")
        self.assertEqual(reconciled[0]["annotation_status"], "annotated")
        self.assertEqual(reconciled[0]["sentiment_label"], "positive")

        # Unit 2 is absent and null sentiment
        self.assertEqual(reconciled[1]["detection_status"], "absent")
        self.assertEqual(reconciled[1]["annotation_status"], "annotated")
        self.assertIsNone(reconciled[1]["sentiment_label"])

    def test_text_alteration_aborts_reconciliation(self):
        import csv
        import json
        import os
        from scripts.reconcile_annotations import reconcile_sample_b, ReconciliationError

        canon_path = os.path.join(self.temp_dir.name, "canon_b.jsonl")
        unit = {
            "annotation_id": "rev_b1_s0#battery_charging",
            "sentence_id": "rev_b1_s0",
            "review_id": "rev_b1",
            "parent_asin": "B001",
            "asin": "B001",
            "sentence_index": 0,
            "sentence_text": "Battery life is great.",
            "char_start": 0,
            "char_end": 22,
            "aspect_name": "battery_charging",
            "detection_status": "present",
            "annotation_status": "unannotated",
            "sentiment_label": None,
            "source_rating": 5.0,
            "verified_purchase": True,
            "sampling_source": "sample_b_sentiment",
            "notes": None
        }
        with open(canon_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(unit) + "\n")

        # Human accidentally modified text in CSV
        csv_path = os.path.join(self.temp_dir.name, "human_b.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "annotation_id", "sentence_id", "review_id", "parent_asin", "asin",
                "source_rating", "sentence_text", "target_aspect",
                "aspect_confirmed", "human_sentiment", "annotator_notes"
            ])
            writer.writerow([
                "rev_b1_s0#battery_charging", "rev_b1_s0", "rev_b1", "B001", "B001",
                "5.0", "Battery life is TERRIBLE.", "battery_charging",  # ALTERED!
                "1", "positive", ""
            ])

        out_path = os.path.join(self.temp_dir.name, "reconciled_b.jsonl")
        with self.assertRaises(ReconciliationError):
            reconcile_sample_b(csv_path, canon_path, out_path, db_path=self.db_path)

    def test_absent_aspect_with_sentiment_is_rejected(self):
        import csv
        import json
        import os
        from scripts.reconcile_annotations import reconcile_sample_b, ReconciliationError

        canon_path = os.path.join(self.temp_dir.name, "canon_b.jsonl")
        unit = {
            "annotation_id": "rev_b1_s0#battery_charging",
            "sentence_id": "rev_b1_s0",
            "review_id": "rev_b1",
            "parent_asin": "B001",
            "asin": "B001",
            "sentence_index": 0,
            "sentence_text": "Battery life is great.",
            "char_start": 0,
            "char_end": 22,
            "aspect_name": "battery_charging",
            "detection_status": "present",
            "annotation_status": "unannotated",
            "sentiment_label": None,
            "source_rating": 5.0,
            "verified_purchase": True,
            "sampling_source": "sample_b_sentiment",
            "notes": None
        }
        with open(canon_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(unit) + "\n")

        # Human entered aspect_confirmed=0 (absent) but also entered human_sentiment='positive'
        csv_path = os.path.join(self.temp_dir.name, "human_b.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "annotation_id", "sentence_id", "review_id", "parent_asin", "asin",
                "source_rating", "sentence_text", "target_aspect",
                "aspect_confirmed", "human_sentiment", "annotator_notes"
            ])
            writer.writerow([
                "rev_b1_s0#battery_charging", "rev_b1_s0", "rev_b1", "B001", "B001",
                "5.0", "Battery life is great.", "battery_charging",
                "0", "positive", ""  # INVALID: absent aspect cannot have sentiment
            ])

        out_path = os.path.join(self.temp_dir.name, "reconciled_b.jsonl")
        with self.assertRaises(ReconciliationError):
            reconcile_sample_b(csv_path, canon_path, out_path, db_path=self.db_path)

    def test_refuse_overwrite_without_flag(self):
        import csv
        import json
        import os
        from scripts.reconcile_annotations import reconcile_sample_b

        canon_path = os.path.join(self.temp_dir.name, "canon_b.jsonl")
        unit = {
            "annotation_id": "rev_b1_s0#battery_charging",
            "sentence_id": "rev_b1_s0",
            "review_id": "rev_b1",
            "parent_asin": "B001",
            "asin": "B001",
            "sentence_index": 0,
            "sentence_text": "Battery life is great.",
            "char_start": 0,
            "char_end": 22,
            "aspect_name": "battery_charging",
            "detection_status": "present",
            "annotation_status": "unannotated",
            "sentiment_label": None,
            "source_rating": 5.0,
            "verified_purchase": True,
            "sampling_source": "sample_b_sentiment",
            "notes": None
        }
        with open(canon_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(unit) + "\n")

        csv_path = os.path.join(self.temp_dir.name, "human_b.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "annotation_id", "sentence_id", "review_id", "parent_asin", "asin",
                "source_rating", "sentence_text", "target_aspect",
                "aspect_confirmed", "human_sentiment", "annotator_notes"
            ])
            writer.writerow([
                "rev_b1_s0#battery_charging", "rev_b1_s0", "rev_b1", "B001", "B001",
                "5.0", "Battery life is great.", "battery_charging",
                "1", "positive", ""
            ])

        out_path = os.path.join(self.temp_dir.name, "existing_out.jsonl")
        with open(out_path, "w") as f:
            f.write("existing\n")

        with self.assertRaises(FileExistsError):
            reconcile_sample_b(csv_path, canon_path, out_path, db_path=self.db_path, overwrite=False)

    def test_csv_tampered_review_id_raises_error(self):
        """Asserts that tampering with review_id in CSV raises ReconciliationError."""
        import csv
        import json
        import os
        from scripts.reconcile_annotations import reconcile_sample_a, ReconciliationError

        canon_path = os.path.join(self.temp_dir.name, "canon_tamper_rev.jsonl")
        unit = {
            "annotation_id": "rev1_s0#battery_charging",
            "sentence_id": "rev1_s0",
            "review_id": "rev1",
            "parent_asin": "B001",
            "asin": "B001",
            "sentence_index": 0,
            "sentence_text": "Battery life is decent but screen is dim.",
            "char_start": 0,
            "char_end": 41,
            "aspect_name": "battery_charging",
            "detection_status": "absent",
            "annotation_status": "unannotated",
            "sentiment_label": None,
            "source_rating": 3.0,
            "verified_purchase": True,
            "sampling_source": "sample_a_detection",
            "notes": None
        }
        with open(canon_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(unit) + "\n")

        csv_path = os.path.join(self.temp_dir.name, "human_tamper_rev.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "sentence_id", "review_id", "parent_asin", "asin", "source_rating", "sentence_text",
                "battery_charging"
            ])
            writer.writerow([
                "rev1_s0", "tampered_review_id", "B001", "B001", "3.0", "Battery life is decent but screen is dim.",
                "1"
            ])

        out_path = os.path.join(self.temp_dir.name, "out_tamper_rev.jsonl")
        with self.assertRaises(ReconciliationError) as cm:
            reconcile_sample_a(csv_path, canon_path, out_path, db_path=self.db_path)
        self.assertIn("review_id", str(cm.exception))
        self.assertIn("mismatch", str(cm.exception))

    def test_csv_tampered_parent_asin_raises_error(self):
        """Asserts that tampering with parent_asin in CSV raises ReconciliationError."""
        import csv
        import json
        import os
        from scripts.reconcile_annotations import reconcile_sample_a, ReconciliationError

        canon_path = os.path.join(self.temp_dir.name, "canon_tamper_asin.jsonl")
        unit = {
            "annotation_id": "rev1_s0#battery_charging",
            "sentence_id": "rev1_s0",
            "review_id": "rev1",
            "parent_asin": "B001",
            "asin": "B001",
            "sentence_index": 0,
            "sentence_text": "Battery life is decent but screen is dim.",
            "char_start": 0,
            "char_end": 41,
            "aspect_name": "battery_charging",
            "detection_status": "absent",
            "annotation_status": "unannotated",
            "sentiment_label": None,
            "source_rating": 3.0,
            "verified_purchase": True,
            "sampling_source": "sample_a_detection",
            "notes": None
        }
        with open(canon_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(unit) + "\n")

        csv_path = os.path.join(self.temp_dir.name, "human_tamper_asin.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "sentence_id", "review_id", "parent_asin", "asin", "source_rating", "sentence_text",
                "battery_charging"
            ])
            writer.writerow([
                "rev1_s0", "rev1", "TAMPERED_PARENT", "B001", "3.0", "Battery life is decent but screen is dim.",
                "1"
            ])

        out_path = os.path.join(self.temp_dir.name, "out_tamper_asin.jsonl")
        with self.assertRaises(ReconciliationError) as cm:
            reconcile_sample_a(csv_path, canon_path, out_path, db_path=self.db_path)
        self.assertIn("parent_asin", str(cm.exception))
        self.assertIn("mismatch", str(cm.exception))

    def test_csv_tampered_source_rating_raises_error(self):
        """Asserts that altering source_rating in CSV raises ReconciliationError."""
        import csv
        import json
        import os
        from scripts.reconcile_annotations import reconcile_sample_a, ReconciliationError

        canon_path = os.path.join(self.temp_dir.name, "canon_tamper_rating.jsonl")
        unit = {
            "annotation_id": "rev1_s0#battery_charging",
            "sentence_id": "rev1_s0",
            "review_id": "rev1",
            "parent_asin": "B001",
            "asin": "B001",
            "sentence_index": 0,
            "sentence_text": "Battery life is decent but screen is dim.",
            "char_start": 0,
            "char_end": 41,
            "aspect_name": "battery_charging",
            "detection_status": "absent",
            "annotation_status": "unannotated",
            "sentiment_label": None,
            "source_rating": 3.0,
            "verified_purchase": True,
            "sampling_source": "sample_a_detection",
            "notes": None
        }
        with open(canon_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(unit) + "\n")

        csv_path = os.path.join(self.temp_dir.name, "human_tamper_rating.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "sentence_id", "review_id", "parent_asin", "asin", "source_rating", "sentence_text",
                "battery_charging"
            ])
            writer.writerow([
                "rev1_s0", "rev1", "B001", "B001", "5.0", "Battery life is decent but screen is dim.",
                "1"
            ])

        out_path = os.path.join(self.temp_dir.name, "out_tamper_rating.jsonl")
        with self.assertRaises(ReconciliationError) as cm:
            reconcile_sample_a(csv_path, canon_path, out_path, db_path=self.db_path)
        self.assertIn("source_rating", str(cm.exception))
        self.assertIn("mismatch", str(cm.exception))

    def test_csv_tampered_canonical_hash_and_occurrence_index(self):
        """Asserts that tampering with canonical_hash or occurrence_index in CSV raises ReconciliationError."""
        import csv
        import json
        import os
        from scripts.reconcile_annotations import reconcile_sample_a, ReconciliationError

        canon_path = os.path.join(self.temp_dir.name, "canon_tamper_meta.jsonl")
        unit = {
            "annotation_id": "rev1_s0#battery_charging",
            "sentence_id": "rev1_s0",
            "review_id": "rev1",
            "parent_asin": "B001",
            "asin": "B001",
            "sentence_index": 0,
            "sentence_text": "Battery life is decent but screen is dim.",
            "char_start": 0,
            "char_end": 41,
            "aspect_name": "battery_charging",
            "detection_status": "absent",
            "annotation_status": "unannotated",
            "sentiment_label": None,
            "source_rating": 3.0,
            "verified_purchase": True,
            "sampling_source": "sample_a_detection",
            "canonical_hash": "hash_rev1",
            "occurrence_index": 0,
            "notes": None
        }
        with open(canon_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(unit) + "\n")

        # 1. Tamper canonical_hash
        csv_path = os.path.join(self.temp_dir.name, "human_tamper_hash.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "sentence_id", "review_id", "parent_asin", "asin", "source_rating", "sentence_text",
                "canonical_hash", "occurrence_index", "battery_charging"
            ])
            writer.writerow([
                "rev1_s0", "rev1", "B001", "B001", "3.0", "Battery life is decent but screen is dim.",
                "hash_TAMPERED", "0", "1"
            ])

        out_path = os.path.join(self.temp_dir.name, "out_tamper_hash.jsonl")
        with self.assertRaises(ReconciliationError) as cm:
            reconcile_sample_a(csv_path, canon_path, out_path, db_path=self.db_path)
        self.assertIn("canonical_hash", str(cm.exception))
        self.assertIn("mismatch", str(cm.exception))

        # 2. Tamper occurrence_index
        csv_path2 = os.path.join(self.temp_dir.name, "human_tamper_occ.csv")
        with open(csv_path2, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "sentence_id", "review_id", "parent_asin", "asin", "source_rating", "sentence_text",
                "canonical_hash", "occurrence_index", "battery_charging"
            ])
            writer.writerow([
                "rev1_s0", "rev1", "B001", "B001", "3.0", "Battery life is decent but screen is dim.",
                "hash_rev1", "99", "1"
            ])

        with self.assertRaises(ReconciliationError) as cm:
            reconcile_sample_a(csv_path2, canon_path, out_path, db_path=self.db_path, overwrite=True)
        self.assertIn("occurrence_index", str(cm.exception))
        self.assertIn("mismatch", str(cm.exception))

    def test_sample_b_tampered_target_aspect_raises_error(self):
        """Asserts that tampering with target_aspect in Sample B CSV raises ReconciliationError."""
        import csv
        import json
        import os
        from scripts.reconcile_annotations import reconcile_sample_b, ReconciliationError

        canon_path = os.path.join(self.temp_dir.name, "canon_tamper_aspect.jsonl")
        unit = {
            "annotation_id": "rev_b1_s0#battery_charging",
            "sentence_id": "rev_b1_s0",
            "review_id": "rev_b1",
            "parent_asin": "B001",
            "asin": "B001",
            "sentence_index": 0,
            "sentence_text": "Battery life is great.",
            "char_start": 0,
            "char_end": 22,
            "aspect_name": "battery_charging",
            "detection_status": "present",
            "annotation_status": "unannotated",
            "sentiment_label": None,
            "source_rating": 5.0,
            "verified_purchase": True,
            "sampling_source": "sample_b_sentiment",
            "notes": None
        }
        with open(canon_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(unit) + "\n")

        csv_path = os.path.join(self.temp_dir.name, "human_tamper_aspect.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "annotation_id", "sentence_id", "review_id", "parent_asin", "asin",
                "source_rating", "sentence_text", "target_aspect",
                "aspect_confirmed", "human_sentiment", "annotator_notes"
            ])
            writer.writerow([
                "rev_b1_s0#battery_charging", "rev_b1_s0", "rev_b1", "B001", "B001",
                "5.0", "Battery life is great.", "screen_display",  # TAMPERED ASPECT!
                "1", "positive", ""
            ])

        out_path = os.path.join(self.temp_dir.name, "out_tamper_aspect.jsonl")
        with self.assertRaises(ReconciliationError) as cm:
            reconcile_sample_b(csv_path, canon_path, out_path, db_path=self.db_path)
        self.assertIn("target_aspect", str(cm.exception))
        self.assertIn("mismatch", str(cm.exception))

    def test_sqlite_verification_success_with_body_and_title_fallback(self):
        """Asserts that SQLite source text verification succeeds on both body text and title fallback."""
        import csv
        import json
        import os
        from scripts.reconcile_annotations import reconcile_sample_a

        canon_path = os.path.join(self.temp_dir.name, "canon_sql_ok.jsonl")
        units = [
            # Unit 1: body text
            {
                "annotation_id": "rev1_s0#battery_charging",
                "sentence_id": "rev1_s0",
                "review_id": "rev1",
                "parent_asin": "B001",
                "asin": "B001",
                "sentence_index": 0,
                "sentence_text": "Battery life is decent but screen is dim.",
                "char_start": 0,
                "char_end": 41,
                "aspect_name": "battery_charging",
                "detection_status": "absent",
                "annotation_status": "unannotated",
                "sentiment_label": None,
                "source_rating": 3.0,
                "verified_purchase": True,
                "sampling_source": "sample_a_detection",
                "notes": None
            },
            # Unit 2: title fallback
            {
                "annotation_id": "rev_title_only_s0#build_durability",
                "sentence_id": "rev_title_only_s0",
                "review_id": "rev_title_only",
                "parent_asin": "B003",
                "asin": "B003",
                "sentence_index": 0,
                "sentence_text": "Title as single sentence fallback",
                "char_start": 0,
                "char_end": 33,
                "aspect_name": "build_durability",
                "detection_status": "absent",
                "annotation_status": "unannotated",
                "sentiment_label": None,
                "source_rating": 4.0,
                "verified_purchase": True,
                "sampling_source": "sample_a_detection",
                "notes": None
            }
        ]
        with open(canon_path, "w", encoding="utf-8") as f:
            for u in units:
                f.write(json.dumps(u) + "\n")

        csv_path = os.path.join(self.temp_dir.name, "human_sql_ok.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "sentence_id", "review_id", "parent_asin", "asin", "source_rating", "sentence_text",
                "battery_charging", "build_durability"
            ])
            writer.writerow([
                "rev1_s0", "rev1", "B001", "B001", "3.0", "Battery life is decent but screen is dim.",
                "1", ""
            ])
            writer.writerow([
                "rev_title_only_s0", "rev_title_only", "B003", "B003", "4.0", "Title as single sentence fallback",
                "", "0"
            ])

        out_path = os.path.join(self.temp_dir.name, "out_sql_ok.jsonl")
        summary = reconcile_sample_a(csv_path, canon_path, out_path, db_path=self.db_path)
        self.assertEqual(summary["total_units"], 2)
        self.assertEqual(summary["completed_decisions"], 2)

    def test_sqlite_missing_review_id_aborts_reconciliation(self):
        """Asserts that a canonical unit referencing a missing review ID in SQLite raises ReconciliationError."""
        import csv
        import json
        import os
        from scripts.reconcile_annotations import reconcile_sample_a, ReconciliationError

        canon_path = os.path.join(self.temp_dir.name, "canon_missing_rev.jsonl")
        unit = {
            "annotation_id": "ghost_rev_s0#battery_charging",
            "sentence_id": "ghost_rev_s0",
            "review_id": "ghost_review_id",  # NOT in SQLite
            "parent_asin": "B001",
            "asin": "B001",
            "sentence_index": 0,
            "sentence_text": "Battery life is decent but screen is dim.",
            "char_start": 0,
            "char_end": 41,
            "aspect_name": "battery_charging",
            "detection_status": "absent",
            "annotation_status": "unannotated",
            "sentiment_label": None,
            "source_rating": 3.0,
            "verified_purchase": True,
            "sampling_source": "sample_a_detection",
            "notes": None
        }
        with open(canon_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(unit) + "\n")

        csv_path = os.path.join(self.temp_dir.name, "human_missing_rev.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "sentence_id", "review_id", "parent_asin", "asin", "source_rating", "sentence_text",
                "battery_charging"
            ])
            writer.writerow([
                "ghost_rev_s0", "ghost_review_id", "B001", "B001", "3.0", "Battery life is decent but screen is dim.",
                "1"
            ])

        out_path = os.path.join(self.temp_dir.name, "out_missing_rev.jsonl")
        with self.assertRaises(ReconciliationError) as cm:
            reconcile_sample_a(csv_path, canon_path, out_path, db_path=self.db_path)
        self.assertIn("review_id 'ghost_review_id' not found in database", str(cm.exception))

    def test_sqlite_sentence_offset_text_mismatch_aborts_reconciliation(self):
        """Asserts that if SQLite review text at char_start:char_end does not match sentence_text, reconciliation aborts."""
        import csv
        import json
        import os
        from scripts.reconcile_annotations import reconcile_sample_a, ReconciliationError

        canon_path = os.path.join(self.temp_dir.name, "canon_slice_mismatch.jsonl")
        unit = {
            "annotation_id": "rev1_s0#battery_charging",
            "sentence_id": "rev1_s0",
            "review_id": "rev1",
            "parent_asin": "B001",
            "asin": "B001",
            "sentence_index": 0,
            # Database has "Battery life is decent but screen is dim." at [0:41]
            "sentence_text": "Battery life is TERRIBLE and completely unusable.",  # MISMATCH!
            "char_start": 0,
            "char_end": 41,
            "aspect_name": "battery_charging",
            "detection_status": "absent",
            "annotation_status": "unannotated",
            "sentiment_label": None,
            "source_rating": 3.0,
            "verified_purchase": True,
            "sampling_source": "sample_a_detection",
            "notes": None
        }
        with open(canon_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(unit) + "\n")

        csv_path = os.path.join(self.temp_dir.name, "human_slice_mismatch.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "sentence_id", "review_id", "parent_asin", "asin", "source_rating", "sentence_text",
                "battery_charging"
            ])
            writer.writerow([
                "rev1_s0", "rev1", "B001", "B001", "3.0", "Battery life is TERRIBLE and completely unusable.",
                "1"
            ])

        out_path = os.path.join(self.temp_dir.name, "out_slice_mismatch.jsonl")
        with self.assertRaises(ReconciliationError) as cm:
            reconcile_sample_a(csv_path, canon_path, out_path, db_path=self.db_path)
        self.assertIn("sentence text mismatch", str(cm.exception))

    def test_sqlite_invalid_offsets_abort_reconciliation(self):
        """Asserts that invalid offsets (negative, inverted, or exceeding length) raise ReconciliationError."""
        import json
        import os
        from scripts.reconcile_annotations import verify_sentence_provenance_against_db, ReconciliationError

        # 1. char_end exceeds text length
        unit_exceed = {
            "sentence_id": "rev1_s0",
            "review_id": "rev1",
            "sentence_text": "Battery",
            "char_start": 0,
            "char_end": 99999
        }
        with self.assertRaises(ReconciliationError) as cm:
            verify_sentence_provenance_against_db(self.db_path, [unit_exceed])
        self.assertIn("Invalid character offsets", str(cm.exception))

        # 2. char_start is negative
        unit_neg = {
            "sentence_id": "rev1_s0",
            "review_id": "rev1",
            "sentence_text": "Battery",
            "char_start": -5,
            "char_end": 10
        }
        with self.assertRaises(ReconciliationError) as cm:
            verify_sentence_provenance_against_db(self.db_path, [unit_neg])
        self.assertIn("Invalid character offsets", str(cm.exception))

        # 3. inverted offsets (start > end)
        unit_inv = {
            "sentence_id": "rev1_s0",
            "review_id": "rev1",
            "sentence_text": "Battery",
            "char_start": 20,
            "char_end": 10
        }
        with self.assertRaises(ReconciliationError) as cm:
            verify_sentence_provenance_against_db(self.db_path, [unit_inv])
        self.assertIn("Invalid character offsets", str(cm.exception))

    def test_sqlite_missing_db_file_aborts_reconciliation(self):
        """Asserts that providing a nonexistent database path raises ReconciliationError."""
        from scripts.reconcile_annotations import verify_sentence_provenance_against_db, ReconciliationError

        with self.assertRaises(ReconciliationError) as cm:
            verify_sentence_provenance_against_db("nonexistent_path/missing.db", [{"sentence_id": "s1"}])
        self.assertIn("Verification database not found", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
