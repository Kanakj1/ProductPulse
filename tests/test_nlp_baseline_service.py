"""
ProductPulse — Baseline NLP Service Unit Tests
Verifies sentence and review analysis contracts, multi-aspect extraction,
offset preservation, and aspect-sentiment separation.
"""
import unittest

from backend.app.nlp.baseline_service import (
    RuleBasedBaselineNLPService,
    SentenceAnalysis,
    ReviewAnalysis
)
from backend.app.nlp.schemas import AspectName, DetectionStatus, SentimentLabel


class TestBaselineNLPService(unittest.TestCase):
    """Unit tests for RuleBasedBaselineNLPService."""

    def setUp(self):
        self.service = RuleBasedBaselineNLPService()

    def test_service_initialization(self):
        """Service initializes with all six canonical aspects."""
        self.assertEqual(len(self.service.all_aspects), 6)
        expected_names = {
            AspectName.BUILD_DURABILITY,
            AspectName.BATTERY_CHARGING,
            AspectName.SCREEN_DISPLAY,
            AspectName.CAMERA_OPTICS,
            AspectName.CONNECTIVITY_AUDIO,
            AspectName.PERFORMANCE_SOFTWARE
        }
        self.assertEqual(set(self.service.all_aspects), expected_names)

    def test_analyze_sentence_multi_aspect(self):
        """Sentence with multiple aspects correctly identifies each aspect and its sentiment."""
        text = "The OLED screen is bright and clear, but the battery drains fast."
        analysis: SentenceAnalysis = self.service.analyze_sentence(text, sentence_index=0)

        # Check screen_display
        screen_det = analysis.aspect_detections["screen_display"]
        self.assertEqual(screen_det.detection_status, DetectionStatus.PRESENT)
        self.assertIn("screen_display", analysis.aspect_sentiments)

        # Check battery_charging
        battery_det = analysis.aspect_detections["battery_charging"]
        self.assertEqual(battery_det.detection_status, DetectionStatus.PRESENT)
        self.assertIn("battery_charging", analysis.aspect_sentiments)

        # Check absent aspect: camera_optics
        camera_det = analysis.aspect_detections["camera_optics"]
        self.assertEqual(camera_det.detection_status, DetectionStatus.ABSENT)
        self.assertNotIn("camera_optics", analysis.aspect_sentiments)

    def test_aspect_absence_enforces_no_sentiment(self):
        """When an aspect is absent, it must NOT have an aspect sentiment entry."""
        text = "This phone case is very sturdy and rugged."
        analysis = self.service.analyze_sentence(text)

        self.assertEqual(analysis.aspect_detections["build_durability"].detection_status, DetectionStatus.PRESENT)
        self.assertIn("build_durability", analysis.aspect_sentiments)

        # All other aspects must be absent and have no sentiment
        for asp in ["battery_charging", "screen_display", "camera_optics", "connectivity_audio", "performance_software"]:
            self.assertEqual(analysis.aspect_detections[asp].detection_status, DetectionStatus.ABSENT)
            self.assertNotIn(asp, analysis.aspect_sentiments)

    def test_analyze_sentence_empty_or_whitespace(self):
        """Handles empty or whitespace text gracefully without raising errors."""
        empty_analysis = self.service.analyze_sentence("")
        self.assertEqual(empty_analysis.sentence_text, "")
        for asp in self.service.all_aspects:
            self.assertEqual(empty_analysis.aspect_detections[asp.value].detection_status, DetectionStatus.ABSENT)

        ws_analysis = self.service.analyze_sentence("   \n\t  ")
        for asp in self.service.all_aspects:
            self.assertEqual(ws_analysis.aspect_detections[asp.value].detection_status, DetectionStatus.ABSENT)

    def test_analyze_review_tokenization_and_offsets(self):
        """Review analysis segments text into sentences, preserving character offsets and indices."""
        review_text = "I love this phone case. It fits snugly and protects the phone. However, the screen protector cracked."
        review_id = "test_rev_001"
        analysis: ReviewAnalysis = self.service.analyze_review(review_text, review_id=review_id)

        self.assertEqual(analysis.review_id, review_id)
        self.assertEqual(len(analysis.sentences), 3)

        # Check sentence 1 (contains protective durability statement)
        s1 = analysis.sentences[1]
        self.assertEqual(s1.sentence_index, 1)
        self.assertEqual(review_text[s1.char_start:s1.char_end], s1.sentence_text)
        self.assertEqual(s1.aspect_detections["build_durability"].detection_status, DetectionStatus.PRESENT)

        # Check sentence 2
        s2 = analysis.sentences[2]
        self.assertEqual(s2.sentence_index, 2)
        self.assertEqual(review_text[s2.char_start:s2.char_end], s2.sentence_text)
        self.assertEqual(s2.aspect_detections["screen_display"].detection_status, DetectionStatus.PRESENT)

        # Overall present aspects in review
        self.assertIn("build_durability", analysis.present_aspects)
        self.assertIn("screen_display", analysis.present_aspects)

    def test_discourse_and_idiom_safety(self):
        """Discourse idioms do not trigger false positive aspect detections."""
        text1 = "Not at all, in my case."
        a1 = self.service.analyze_sentence(text1)
        self.assertEqual(a1.aspect_detections["build_durability"].detection_status, DetectionStatus.ABSENT)

        text2 = "I am going to focus on the phone without commenting on price."
        a2 = self.service.analyze_sentence(text2)
        self.assertEqual(a2.aspect_detections["camera_optics"].detection_status, DetectionStatus.ABSENT)

        text3 = "Plug the USB cable into a micro usb adapter."
        a3 = self.service.analyze_sentence(text3)
        self.assertEqual(a3.aspect_detections["connectivity_audio"].detection_status, DetectionStatus.ABSENT)

    def test_demo_review_1_sentiment_isolation(self):
        """Phase 7D.1/7D.2 Regression: Verifies aspect sentiment isolation without global negative leakage."""
        text = "Screen is small and phone is slow, laggy and won't charge while plugged in. I knew this was not an expensive phone but I didn't think it would be this bad."
        analysis = self.service.analyze_sentence(text)

        # Screen should be neutral objective description, NOT infected by slow/laggy/bad
        screen_sent = analysis.aspect_sentiments["screen_display"]
        self.assertEqual(screen_sent.sentiment_label, SentimentLabel.NEUTRAL)
        self.assertNotIn("slow", screen_sent.evidence)
        self.assertNotIn("laggy", screen_sent.evidence)
        self.assertNotIn("bad", screen_sent.evidence)

        # Performance should capture slow and laggy, NOT bad from subsequent sentence
        perf_sent = analysis.aspect_sentiments["performance_software"]
        self.assertEqual(perf_sent.sentiment_label, SentimentLabel.NEGATIVE)
        self.assertIn("slow", perf_sent.evidence)
        self.assertIn("laggy", perf_sent.evidence)
        self.assertNotIn("bad", perf_sent.evidence)

        # Battery charging should capture won't charge, NOT bad from subsequent sentence
        batt_sent = analysis.aspect_sentiments["battery_charging"]
        self.assertEqual(batt_sent.sentiment_label, SentimentLabel.NEGATIVE)
        self.assertIn("won't charge", batt_sent.evidence)
        self.assertNotIn("bad", batt_sent.evidence)

    def test_genuinely_negative_charging_clause(self):
        """Phase 7D.2 Regression: When 'bad' is directly connected to battery charging, it is preserved."""
        text = "The battery is bad and dies within two hours."
        analysis = self.service.analyze_sentence(text)

        self.assertEqual(analysis.aspect_detections["battery_charging"].detection_status, DetectionStatus.PRESENT)
        batt_sent = analysis.aspect_sentiments["battery_charging"]
        self.assertEqual(batt_sent.sentiment_label, SentimentLabel.NEGATIVE)
        self.assertIn("bad", batt_sent.evidence)

    def test_fit_only_vs_protection_language(self):
        """Phase 7D.2 Regression: Fit-only statements without casing/protection do NOT trigger build_durability."""
        # Generic fit/sizing: absent under taxonomy
        text_fit_only = "The colors are bright and it fits perfectly."
        analysis_fit = self.service.analyze_sentence(text_fit_only)
        self.assertEqual(analysis_fit.aspect_detections["build_durability"].detection_status, DetectionStatus.ABSENT)
        self.assertNotIn("build_durability", analysis_fit.aspect_sentiments)

        # Explicit protection / drop survival: present and positive
        text_prot = "It is light weight, fits tightly and has saved my phone 3x."
        analysis_prot = self.service.analyze_sentence(text_prot)
        self.assertEqual(analysis_prot.aspect_detections["build_durability"].detection_status, DetectionStatus.PRESENT)
        self.assertEqual(analysis_prot.aspect_sentiments["build_durability"].sentiment_label, SentimentLabel.POSITIVE)
        self.assertIn("saved my phone", analysis_prot.aspect_sentiments["build_durability"].evidence)

    def test_demo_review_2_charging_fast_disambiguation(self):
        """Phase 7D.1 Regression: 'Charges fast.' detects battery_charging but NOT performance_software."""
        text = "Charges fast."
        analysis = self.service.analyze_sentence(text)

        self.assertEqual(analysis.aspect_detections["battery_charging"].detection_status, DetectionStatus.PRESENT)
        self.assertEqual(analysis.aspect_sentiments["battery_charging"].sentiment_label, SentimentLabel.POSITIVE)

        self.assertEqual(analysis.aspect_detections["performance_software"].detection_status, DetectionStatus.ABSENT)
        self.assertNotIn("performance_software", analysis.aspect_sentiments)

    def test_demo_review_3_build_durability_extraction(self):
        """Phase 7D.1 Regression: 'fits tightly and has saved my phone' detects build_durability."""
        text = "It is light weight, fits tightly and has saved my phone 3x."
        analysis = self.service.analyze_sentence(text)

        self.assertEqual(analysis.aspect_detections["build_durability"].detection_status, DetectionStatus.PRESENT)
        self.assertEqual(analysis.aspect_sentiments["build_durability"].sentiment_label, SentimentLabel.POSITIVE)

    def test_multi_aspect_contrasting_polarities(self):
        """Phase 7D.1 Regression: Contrastive multi-aspect sentence separates positive and negative sentiments."""
        text = "The OLED screen is bright and clear, but the battery drains fast."
        analysis = self.service.analyze_sentence(text)

        # Screen display is positive
        screen_sent = analysis.aspect_sentiments["screen_display"]
        self.assertEqual(screen_sent.sentiment_label, SentimentLabel.POSITIVE)

        # Battery charging is negative (drains fast is rapid discharge)
        batt_sent = analysis.aspect_sentiments["battery_charging"]
        self.assertEqual(batt_sent.sentiment_label, SentimentLabel.NEGATIVE)

    def test_ambiguous_sentiment_within_single_aspect(self):
        """Phase 7D.1 Regression: Conflicting polarity for a single aspect returns UNCERTAIN_UNCLASSIFIED."""
        text = "The camera takes great photos during the day, but horrible ones at night."
        analysis = self.service.analyze_sentence(text)

        self.assertEqual(analysis.aspect_detections["camera_optics"].detection_status, DetectionStatus.PRESENT)
        cam_sent = analysis.aspect_sentiments["camera_optics"]
        self.assertEqual(cam_sent.sentiment_label, SentimentLabel.UNCERTAIN_UNCLASSIFIED)


    def test_phase7d3_durability_precision_checks(self):
        """Phase 7D.3 Regression: Accessory mentions alone or generic fit must NOT trigger build_durability."""
        # 1. "Can't beat the case for the price." — accessory mention alone must be ABSENT
        text_case_price = "Can't beat the case for the price."
        a1 = self.service.analyze_sentence(text_case_price)
        self.assertEqual(a1.aspect_detections["build_durability"].detection_status, DetectionStatus.ABSENT)
        self.assertNotIn("build_durability", a1.aspect_sentiments)

        # 2. "The case feels sturdy and protects my phone from drops." — explicit build/protection evidence PRESENT
        text_sturdy_prot = "The case feels sturdy and protects my phone from drops."
        a2 = self.service.analyze_sentence(text_sturdy_prot)
        self.assertEqual(a2.aspect_detections["build_durability"].detection_status, DetectionStatus.PRESENT)
        self.assertEqual(a2.aspect_sentiments["build_durability"].sentiment_label, SentimentLabel.POSITIVE)

        # 3. "It fits perfectly." — fit alone must be ABSENT
        text_fit = "It fits perfectly."
        a3 = self.service.analyze_sentence(text_fit)
        self.assertEqual(a3.aspect_detections["build_durability"].detection_status, DetectionStatus.ABSENT)
        self.assertNotIn("build_durability", a3.aspect_sentiments)

        # 4. "It has saved my phone from drops several times." — explicit protective evidence PRESENT
        text_saved = "It has saved my phone from drops several times."
        a4 = self.service.analyze_sentence(text_saved)
        self.assertEqual(a4.aspect_detections["build_durability"].detection_status, DetectionStatus.PRESENT)
        self.assertEqual(a4.aspect_sentiments["build_durability"].sentiment_label, SentimentLabel.POSITIVE)


if __name__ == "__main__":
    unittest.main()


