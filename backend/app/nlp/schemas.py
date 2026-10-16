"""
ProductPulse — NLP Scaffolding Schemas
Type definitions and Pydantic models for aspect-based sentiment analysis evaluation units,
partition manifests, and evaluation metrics reports.
"""
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class AspectName(str, Enum):
    """The 6 locked aspects for the Mobile Phones & Accessories domain."""
    BUILD_DURABILITY = "build_durability"
    BATTERY_CHARGING = "battery_charging"
    SCREEN_DISPLAY = "screen_display"
    CAMERA_OPTICS = "camera_optics"
    CONNECTIVITY_AUDIO = "connectivity_audio"
    PERFORMANCE_SOFTWARE = "performance_software"


class DetectionStatus(str, Enum):
    """Aspect detection status in a sentence."""
    PRESENT = "present"
    ABSENT = "absent"


class AnnotationStatus(str, Enum):
    """Annotation lifecycle status."""
    UNANNOTATED = "unannotated"
    ANNOTATED = "annotated"


class SentimentLabel(str, Enum):
    """Aspect sentiment classification label."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    UNCERTAIN_UNCLASSIFIED = "uncertain/unclassified"


class SamplingSource(str, Enum):
    """Origin evaluation benchmark sample."""
    SAMPLE_A_DETECTION = "sample_a_detection"
    SAMPLE_B_SENTIMENT = "sample_b_sentiment"


class SentenceSpan(BaseModel):
    """Verbatim sentence segment with exact character offsets into original review text."""
    model_config = ConfigDict(frozen=True)

    sentence_index: int = Field(ge=0, description="0-based sentence index within review")
    sentence_text: str = Field(description="Verbatim text of the segmented sentence")
    char_start: int = Field(ge=0, description="Character start offset in original raw review text")
    char_end: int = Field(ge=0, description="Character end offset in original raw review text")
    is_title: bool = Field(default=False, description="True if this sentence was derived from raw_title fallback")


class AnnotationUnit(BaseModel):
    """
    Atomic annotation and evaluation unit: (sentence_id, aspect_name).
    Maintains decoupled detection status, annotation status, and sentiment label.
    """
    model_config = ConfigDict(from_attributes=True)

    annotation_id: str = Field(description="Unique deterministic ID: {sentence_id}#{aspect_name}")
    sentence_id: str = Field(description="Deterministic ID: {review_id}_s{sentence_index}")
    review_id: str = Field(description="Parent review ID (reviews.review_id)")
    parent_asin: str = Field(description="Parent ASIN grouping the product variants")
    asin: str = Field(description="Specific SKU variant ASIN")
    sentence_index: int = Field(ge=0, description="0-based sentence index")
    sentence_text: str = Field(description="Verbatim sentence text")
    char_start: int = Field(ge=0, description="Character start offset in raw review text")
    char_end: int = Field(ge=0, description="Character end offset in raw review text")
    aspect_name: AspectName = Field(description="Target mobile phone aspect")
    detection_status: DetectionStatus = Field(
        default=DetectionStatus.ABSENT,
        description="Whether this aspect is present or absent in this sentence"
    )
    annotation_status: AnnotationStatus = Field(
        default=AnnotationStatus.UNANNOTATED,
        description="Whether a human annotator has reviewed this unit"
    )
    sentiment_label: Optional[SentimentLabel] = Field(
        default=None,
        description="Sentiment label. Must be None if detection_status == absent."
    )
    source_rating: float = Field(ge=1.0, le=5.0, description="Source customer star rating (1.0-5.0)")
    verified_purchase: bool = Field(default=False, description="Whether purchase was verified by Amazon")
    sampling_source: SamplingSource = Field(description="Which evaluation benchmark sample generated this unit")
    notes: Optional[str] = Field(default=None, description="Annotator notes or edge-case flags")

    @model_validator(mode="after")
    def validate_state_consistency(self) -> "AnnotationUnit":
        # Rule 1: If detection_status == absent, sentiment_label must be None. An absent aspect cannot have a sentiment label.
        if self.detection_status == DetectionStatus.ABSENT and self.sentiment_label is not None:
            raise ValueError(
                f"Invalid state: aspect '{self.aspect_name.value}' is absent but has sentiment_label '{self.sentiment_label.value}'. "
                "An absent aspect must not be assigned a sentiment label."
            )
        # Rule 2: If annotated and aspect is present in Sample B (sentiment benchmark), sentiment_label must be provided.
        # (Sample A is strictly an aspect detection benchmark and does not evaluate sentiment).
        if self.annotation_status == AnnotationStatus.ANNOTATED and self.detection_status == DetectionStatus.PRESENT:
            if self.sampling_source == SamplingSource.SAMPLE_B_SENTIMENT and self.sentiment_label is None:
                raise ValueError(
                    f"Invalid state: unit is marked annotated and aspect '{self.aspect_name.value}' is present in Sample B, "
                    "but sentiment_label is None."
                )
        # Rule 3: If unannotated, sentiment_label should default to None in generated templates.
        if self.annotation_status == AnnotationStatus.UNANNOTATED and self.sentiment_label is not None:
            raise ValueError(
                "Invalid state: unit is marked unannotated but already carries a sentiment_label. "
                "Generated templates must remain unannotated without synthetic sentiment labels."
            )
        return self


class PartitionAssignment(BaseModel):
    """Assignment details for a single dataset record."""
    review_id: str
    parent_asin: str
    canonical_hash: str
    occurrence_index: int
    cluster_id: str
    partition: str = Field(description="'train' | 'val' | 'test'")


class PartitionManifest(BaseModel):
    """Auditable manifest of leakage-safe connected-component partitioning."""
    random_seed: int
    salt: str
    total_reviews: int
    total_parent_asins: int
    total_clusters: int
    train_reviews: int
    val_reviews: int
    test_reviews: int
    train_pct: float
    val_pct: float
    test_pct: float
    cluster_size_distribution: Dict[str, int] = Field(
        description="Counts of clusters by size range (e.g. '1', '2-5', '6-20', '21+')"
    )
    duplicate_reviews_count: int
    duplicate_cross_partition_violations: int = 0
    generated_at: str


class StratumShortfall(BaseModel):
    """Explicitly recorded shortfall when sampling strata lack sufficient records."""
    aspect_name: AspectName
    rating_tier: str = Field(description="'1-2_star' | '3_star' | '4-5_star'")
    target_count: int
    actual_count: int
    shortfall: int
    reason: str


class SamplerMetadata(BaseModel):
    """Metadata detailing the reproducible sampling parameters and results."""
    sample_type: SamplingSource
    random_seed: int
    target_sample_size: int
    actual_sample_size: int
    overlap_with_other_sample_count: int = 0
    shortfalls: List[StratumShortfall] = Field(default_factory=list)
    generation_timestamp: str
    selection_rationale: str
