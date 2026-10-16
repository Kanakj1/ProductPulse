"""
Regression tests for Phase 7C.2 targeted heuristic corrections in auto-draft annotations.
Verifies that rule-based false positives and missing keyword patterns are corrected.
"""

import unittest
from backend.app.nlp.schemas import AspectName
from scripts.generate_auto_draft_annotations import detect_aspect, detect_sentiment, SentimentLabel


class TestAutoDraftHeuristics(unittest.TestCase):
    """Focused regression tests for the 6 approved heuristic corrections."""

    def test_fix_1_micro_usb_not_matched_as_microphone(self):
        """Fix 1: Micro and micro USB should not match microphone/audio rules."""
        # False positives to prevent
        s1 = "plug in a USBC cable into a micro usb adapter."
        pres1, rat1, _ = detect_aspect(s1, AspectName.CONNECTIVITY_AUDIO)
        self.assertFalse(pres1, f"Expected False for '{s1}', got {pres1} ({rat1})")

        s2 = "The micro SD slot works fine."
        pres2, rat2, _ = detect_aspect(s2, AspectName.CONNECTIVITY_AUDIO)
        self.assertFalse(pres2, f"Expected False for '{s2}', got {pres2} ({rat2})")

        # True positives that MUST still match
        s3 = "The mic on this headset is crystal clear."
        pres3, rat3, _ = detect_aspect(s3, AspectName.CONNECTIVITY_AUDIO)
        self.assertTrue(pres3, f"Expected True for '{s3}', got {pres3} ({rat3})")

        s4 = "The microphone cuts out during calls."
        pres4, rat4, _ = detect_aspect(s4, AspectName.CONNECTIVITY_AUDIO)
        self.assertTrue(pres4, f"Expected True for '{s4}', got {pres4} ({rat4})")

    def test_fix_2_listing_photos_and_videoid_not_matched_as_camera(self):
        """Fix 2: Listing-photo idioms and video metadata tokens must not trigger camera."""
        # Metadata tokens and review photo attachment idioms to prevent
        s1 = "[[VIDEOID:c6f086c3be47d41801639b5c71d61c97]] This case is designed for max phone protection."
        pres1, rat1, _ = detect_aspect(s1, AspectName.CAMERA_OPTICS)
        self.assertFalse(pres1, f"Expected False for '{s1}', got {pres1} ({rat1})")

        s2 = "Picture included.<br />The case itself seems well made..."
        pres2, rat2, _ = detect_aspect(s2, AspectName.CAMERA_OPTICS)
        self.assertFalse(pres2, f"Expected False for '{s2}', got {pres2} ({rat2})")

        s3 = "It was not the brand that was shown in the picture."
        pres3, rat3, _ = detect_aspect(s3, AspectName.CAMERA_OPTICS)
        self.assertFalse(pres3, f"Expected False for '{s3}', got {pres3} ({rat3})")

        s4 = "The blue 'skin' that you see in the picture bubbled on the first day..."
        pres4, rat4, _ = detect_aspect(s4, AspectName.CAMERA_OPTICS)
        self.assertFalse(pres4, f"Expected False for '{s4}', got {pres4} ({rat4})")

        # Genuine camera/photo sentences that MUST still match
        s5 = "The camera takes blurry photos in low light."
        pres5, rat5, _ = detect_aspect(s5, AspectName.CAMERA_OPTICS)
        self.assertTrue(pres5, f"Expected True for '{s5}', got {pres5} ({rat5})")

        s6 = "The idea is that you clip this onto your camera and snap pictures."
        pres6, rat6, _ = detect_aspect(s6, AspectName.CAMERA_OPTICS)
        self.assertTrue(pres6, f"Expected True for '{s6}', got {pres6} ({rat6})")

    def test_fix_3_discourse_focus_not_matched_as_camera(self):
        """Fix 3: Generic discourse use of 'focus' must not trigger camera detection."""
        s1 = "I purchased this phone ... so am going to focus on the phone without commenting on price..."
        pres1, rat1, _ = detect_aspect(s1, AspectName.CAMERA_OPTICS)
        self.assertFalse(pres1, f"Expected False for '{s1}', got {pres1} ({rat1})")

        s2 = "Our primary focus was finding a reliable phone for our parents."
        pres2, rat2, _ = detect_aspect(s2, AspectName.CAMERA_OPTICS)
        self.assertFalse(pres2, f"Expected False for '{s2}', got {pres2} ({rat2})")

        # Genuine optical focus that MUST still match
        s3 = "The autofocus on this lens is amazingly sharp."
        pres3, rat3, _ = detect_aspect(s3, AspectName.CAMERA_OPTICS)
        self.assertTrue(pres3, f"Expected True for '{s3}', got {pres3} ({rat3})")

        s4 = "The camera has trouble focusing in dark rooms."
        pres4, rat4, _ = detect_aspect(s4, AspectName.CAMERA_OPTICS)
        self.assertTrue(pres4, f"Expected True for '{s4}', got {pres4} ({rat4})")

    def test_fix_4_durability_case_idiom_exclusion(self):
        """Fix 4: Idiomatic expressions with 'case' must be excluded from build_durability."""
        # Idioms to exclude
        s1 = "Not at all, in my case."
        pres1, rat1, _ = detect_aspect(s1, AspectName.BUILD_DURABILITY)
        self.assertFalse(pres1, f"Expected False for '{s1}', got {pres1} ({rat1})")

        s2 = "In this case, the product was defective."
        pres2, rat2, _ = detect_aspect(s2, AspectName.BUILD_DURABILITY)
        self.assertFalse(pres2, f"Expected False for '{s2}', got {pres2} ({rat2})")

        s3 = "Just in case, I bought a backup."
        pres3, rat3, _ = detect_aspect(s3, AspectName.BUILD_DURABILITY)
        self.assertFalse(pres3, f"Expected False for '{s3}', got {pres3} ({rat3})")

        s4 = "In either case, it arrived quickly."
        pres4, rat4, _ = detect_aspect(s4, AspectName.BUILD_DURABILITY)
        self.assertFalse(pres4, f"Expected False for '{s4}', got {pres4} ({rat4})")

        # Real phone cases that MUST still match
        s5 = "Very nice cell phone case!"
        pres5, rat5, _ = detect_aspect(s5, AspectName.BUILD_DURABILITY)
        self.assertTrue(pres5, f"Expected True for '{s5}', got {pres5} ({rat5})")

        s6 = "This case was an amazingly low price."
        pres6, rat6, _ = detect_aspect(s6, AspectName.BUILD_DURABILITY)
        self.assertTrue(pres6, f"Expected True for '{s6}', got {pres6} ({rat6})")

        s7 = "The Otterbox case fits great."
        pres7, rat7, _ = detect_aspect(s7, AspectName.BUILD_DURABILITY)
        self.assertTrue(pres7, f"Expected True for '{s7}', got {pres7} ({rat7})")

    def test_fix_5_physical_smooth_texture_not_matched_as_performance(self):
        """Fix 5: Physical texture phrases must not trigger performance_software detection."""
        # Physical material feel to exclude from performance
        s1 = "It’s really comfortable to hold and has a nice texture - not so smooth that it slips out of my hands."
        pres1, rat1, _ = detect_aspect(s1, AspectName.PERFORMANCE_SOFTWARE)
        self.assertFalse(pres1, f"Expected False for '{s1}', got {pres1} ({rat1})")

        s2 = "The glitter back is coated so it has a smooth texture."
        pres2, rat2, _ = detect_aspect(s2, AspectName.PERFORMANCE_SOFTWARE)
        self.assertFalse(pres2, f"Expected False for '{s2}', got {pres2} ({rat2})")

        s3 = "as the paint slowly chips it will eventually chip further up the band."
        pres3, rat3, _ = detect_aspect(s3, AspectName.PERFORMANCE_SOFTWARE)
        self.assertFalse(pres3, f"Expected False for '{s3}', got {pres3} ({rat3})")

        # Genuine software performance that MUST still match
        s4 = "The phone UI is incredibly smooth and snappy."
        pres4, rat4, _ = detect_aspect(s4, AspectName.PERFORMANCE_SOFTWARE)
        self.assertTrue(pres4, f"Expected True for '{s4}', got {pres4} ({rat4})")

        s5 = "Apps launch fast with zero lag."
        pres5, rat5, _ = detect_aspect(s5, AspectName.PERFORMANCE_SOFTWARE)
        self.assertTrue(pres5, f"Expected True for '{s5}', got {pres5} ({rat5})")

    def test_fix_6_bounded_connectivity_audio_patterns(self):
        """Fix 6: Bounded headset, pairing, and connection patterns must trigger connectivity/audio."""
        s1 = "The connection is like having a headset connected at all time."
        pres1, rat1, _ = detect_aspect(s1, AspectName.CONNECTIVITY_AUDIO)
        self.assertTrue(pres1, f"Expected True for '{s1}', got {pres1} ({rat1})")

        s2 = "Bluetooth pairing was instant with my car."
        pres2, rat2, _ = detect_aspect(s2, AspectName.CONNECTIVITY_AUDIO)
        self.assertTrue(pres2, f"Expected True for '{s2}', got {pres2} ({rat2})")

        s3 = "The speaker sound is loud and clear."
        pres3, rat3, _ = detect_aspect(s3, AspectName.CONNECTIVITY_AUDIO)
        self.assertTrue(pres3, f"Expected True for '{s3}', got {pres3} ({rat3})")

        # "safe and sound" idiom MUST be excluded
        s4 = "You can’t even tell it’s on your phone—u til you drop the phone and this is cracked and your actual phone screen is safe and sound!"
        pres4, rat4, _ = detect_aspect(s4, AspectName.CONNECTIVITY_AUDIO)
        self.assertFalse(pres4, f"Expected False for '{s4}', got {pres4} ({rat4})")


if __name__ == "__main__":
    unittest.main()
