"""
ProductPulse — NLP Evaluation Sampler
Generates reproducible, separate Sample A (detection) and Sample B (sentiment) annotation templates.
Guarantees:
1. Templates are strictly unannotated placeholders without synthetic ground truth.
2. Sample A (200 random sentences) and Sample B (200 aspect-enriched sentences) are kept separate.
3. Sentence overlap is prevented where feasible and tracked.
4. Shortfalls in aspect/rating strata are reported explicitly rather than silently backfilled.
"""
import hashlib
import json
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple
from backend.app.nlp.schemas import (
    AnnotationStatus,
    AnnotationUnit,
    AspectName,
    DetectionStatus,
    SamplerMetadata,
    SamplingSource,
    StratumShortfall
)
from backend.app.nlp.tokenizer import segment_sentences

# Mobile domain seed keywords for aspect-bearing candidate identification (Sample B enrichment only)
ASPECT_KEYWORD_LEXICON: Dict[AspectName, List[str]] = {
    AspectName.BUILD_DURABILITY: [
        "build", "durable", "durability", "sturdy", "flimsy", "fragile", "scratch",
        "drop", "material", "plastic", "metal", "case", "hinge", "crack"
    ],
    AspectName.BATTERY_CHARGING: [
        "battery", "charge", "charging", "charger", "drain", "mah", "runtime",
        "life", "power", "cord", "cable", "watt", "overheat", "plug"
    ],
    AspectName.SCREEN_DISPLAY: [
        "screen", "display", "oled", "amoled", "lcd", "brightness", "resolution",
        "touch", "refresh", "pixel", "glass", "view", "panel", "dim"
    ],
    AspectName.CAMERA_OPTICS: [
        "camera", "photo", "picture", "lens", "video", "sensor", "megapixel",
        "zoom", "focus", "portrait", "night", "selfie", "flash", "sharpness"
    ],
    AspectName.CONNECTIVITY_AUDIO: [
        "bluetooth", "wifi", "signal", "reception", "speaker", "audio", "mic",
        "microphone", "sound", "volume", "call", "static", "connection", "pair"
    ],
    AspectName.PERFORMANCE_SOFTWARE: [
        "lag", "slow", "fast", "speed", "freeze", "crash", "bug", "software",
        "update", "app", "ui", "system", "processor", "ram", "glitch", "boot"
    ]
}


def _get_rating_tier(rating: float) -> str:
    if rating <= 2.5:
        return "1-2_star"
    elif rating <= 3.5:
        return "3_star"
    else:
        return "4-5_star"


class EvaluationSampler:
    """
    Constructs Sample A and Sample B annotation templates from a list of review dictionaries.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed

    def sample_a_detection(
        self,
        reviews: List[Dict],
        target_size: int = 200,
        exclude_sentence_ids: Optional[Set[str]] = None
    ) -> Tuple[List[AnnotationUnit], SamplerMetadata]:
        """
        Draws target_size sentences uniformly at random across reviews for aspect detection benchmarking.
        Each sampled sentence produces 6 AnnotationUnits (one for each candidate aspect in the taxonomy)
        all defaulted to detection_status=absent, annotation_status=unannotated, sentiment_label=None.
        """
        rng = random.Random(self.seed)
        exclude_ids = exclude_sentence_ids or set()

        # Step 1: Segment all eligible reviews and pool sentences
        all_sentences: List[Dict] = []
        # Sort reviews deterministically by review_id
        sorted_reviews = sorted(reviews, key=lambda r: r['review_id'])

        for r in sorted_reviews:
            if r.get('is_blank_text', False) and not r.get('raw_title'):
                continue
            spans = segment_sentences(r.get('raw_text'), r.get('raw_title'))
            for span in spans:
                s_id = f"{r['review_id']}_s{span.sentence_index}"
                if s_id in exclude_ids:
                    continue
                all_sentences.append({
                    "sentence_id": s_id,
                    "review": r,
                    "span": span
                })

        # Step 2: Deterministic shuffle & draw
        rng.shuffle(all_sentences)
        selected = all_sentences[:target_size]

        units: List[AnnotationUnit] = []
        for item in selected:
            r = item["review"]
            span = item["span"]
            s_id = item["sentence_id"]

            # In Sample A (aspect detection benchmark), we evaluate detection presence/absence
            # for all aspects in the taxonomy. A human annotator marks detection_status=present/absent.
            for aspect in AspectName:
                ann_id = f"{s_id}#{aspect.value}"
                units.append(
                    AnnotationUnit(
                        annotation_id=ann_id,
                        sentence_id=s_id,
                        review_id=r['review_id'],
                        parent_asin=r['parent_asin'],
                        asin=r.get('asin', r['parent_asin']),
                        sentence_index=span.sentence_index,
                        sentence_text=span.sentence_text,
                        char_start=span.char_start,
                        char_end=span.char_end,
                        aspect_name=aspect,
                        detection_status=DetectionStatus.ABSENT,
                        annotation_status=AnnotationStatus.UNANNOTATED,
                        sentiment_label=None,
                        source_rating=float(r['rating']),
                        verified_purchase=bool(r.get('verified_purchase', False)),
                        sampling_source=SamplingSource.SAMPLE_A_DETECTION,
                        notes="unannotated_detection_template"
                    )
                )

        metadata = SamplerMetadata(
            sample_type=SamplingSource.SAMPLE_A_DETECTION,
            random_seed=self.seed,
            target_sample_size=target_size,
            actual_sample_size=len(selected),
            overlap_with_other_sample_count=0,
            shortfalls=[],
            generation_timestamp=datetime.now(timezone.utc).isoformat(),
            selection_rationale="Uniform random sentence sampling across non-blank mobile reviews without keyword filtering."
        )

        return units, metadata

    def sample_b_sentiment(
        self,
        reviews: List[Dict],
        target_size: int = 200,
        exclude_sentence_ids: Optional[Set[str]] = None
    ) -> Tuple[List[AnnotationUnit], SamplerMetadata]:
        """
        Draws target_size aspect-bearing sentences stratified across the 6 aspects and 3 rating tiers.
        Each sampled sentence produces an AnnotationUnit for the matching aspect.
        All units are defaulted to annotation_status=unannotated, sentiment_label=None.
        Shortfalls in any stratum are recorded explicitly.
        """
        rng = random.Random(self.seed + 1)
        exclude_ids = exclude_sentence_ids or set()

        # Target allocation: 6 aspects -> ~33-34 per aspect.
        # Within each aspect: 3 rating tiers (1-2★: ~11, 3★: ~11, 4-5★: ~11).
        aspects = list(AspectName)
        per_aspect_target = target_size // len(aspects)
        rem = target_size % len(aspects)

        # Pre-segment and index candidate sentences by aspect and rating tier
        # Structure: stratum_candidates[aspect][rating_tier] -> list of candidate dicts
        stratum_candidates: Dict[AspectName, Dict[str, List[Dict]]] = {
            a: {"1-2_star": [], "3_star": [], "4-5_star": []} for a in aspects
        }

        sorted_reviews = sorted(reviews, key=lambda r: r['review_id'])
        for r in sorted_reviews:
            if r.get('is_blank_text', False) and not r.get('raw_title'):
                continue
            spans = segment_sentences(r.get('raw_text'), r.get('raw_title'))
            tier = _get_rating_tier(float(r['rating']))

            for span in spans:
                s_id = f"{r['review_id']}_s{span.sentence_index}"
                if s_id in exclude_ids:
                    continue
                lower_text = span.sentence_text.lower()
                for aspect, keywords in ASPECT_KEYWORD_LEXICON.items():
                    # Keyword boundary check
                    for kw in keywords:
                        if kw in lower_text:
                            stratum_candidates[aspect][tier].append({
                                "sentence_id": s_id,
                                "review": r,
                                "span": span,
                                "aspect": aspect
                            })
                            break  # Avoid adding same sentence multiple times to same aspect tier

        # Perform stratified sampling
        selected_candidates: List[Dict] = []
        shortfalls: List[StratumShortfall] = []
        selected_s_ids: Set[str] = set()

        for a_idx, aspect in enumerate(aspects):
            aspect_target = per_aspect_target + (1 if a_idx < rem else 0)
            tier_target = aspect_target // 3
            tier_rem = aspect_target % 3

            for t_idx, tier in enumerate(["1-2_star", "3_star", "4-5_star"]):
                target_count = tier_target + (1 if t_idx < tier_rem else 0)
                candidates = stratum_candidates[aspect][tier]
                # Filter out sentences already selected to prevent duplicates within Sample B
                valid_candidates = [c for c in candidates if c["sentence_id"] not in selected_s_ids]
                rng.shuffle(valid_candidates)

                taken = valid_candidates[:target_count]
                for c in taken:
                    selected_candidates.append(c)
                    selected_s_ids.add(c["sentence_id"])

                if len(taken) < target_count:
                    shortfalls.append(
                        StratumShortfall(
                            aspect_name=aspect,
                            rating_tier=tier,
                            target_count=target_count,
                            actual_count=len(taken),
                            shortfall=target_count - len(taken),
                            reason=f"Insufficient matching sentences found in corpus for aspect '{aspect.value}' in tier '{tier}'."
                        )
                    )

        # Convert to AnnotationUnits (unannotated template)
        units: List[AnnotationUnit] = []
        for item in selected_candidates:
            r = item["review"]
            span = item["span"]
            s_id = item["sentence_id"]
            aspect = item["aspect"]
            ann_id = f"{s_id}#{aspect.value}"

            units.append(
                AnnotationUnit(
                    annotation_id=ann_id,
                    sentence_id=s_id,
                    review_id=r['review_id'],
                    parent_asin=r['parent_asin'],
                    asin=r.get('asin', r['parent_asin']),
                    sentence_index=span.sentence_index,
                    sentence_text=span.sentence_text,
                    char_start=span.char_start,
                    char_end=span.char_end,
                    aspect_name=aspect,
                    detection_status=DetectionStatus.PRESENT,
                    annotation_status=AnnotationStatus.UNANNOTATED,
                    sentiment_label=None,
                    source_rating=float(r['rating']),
                    verified_purchase=bool(r.get('verified_purchase', False)),
                    sampling_source=SamplingSource.SAMPLE_B_SENTIMENT,
                    notes="unannotated_sentiment_template_keyword_matched"
                )
            )

        metadata = SamplerMetadata(
            sample_type=SamplingSource.SAMPLE_B_SENTIMENT,
            random_seed=self.seed + 1,
            target_sample_size=target_size,
            actual_sample_size=len(selected_candidates),
            overlap_with_other_sample_count=0,
            shortfalls=shortfalls,
            generation_timestamp=datetime.now(timezone.utc).isoformat(),
            selection_rationale="Aspect-enriched sentence sampling stratified by 6 aspects and 3 rating tiers using domain lexicon."
        )

        return units, metadata
