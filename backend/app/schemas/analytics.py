"""
ProductPulse — Analytics Schemas
Pydantic v2 schemas for Hadoop MapReduce & Apache Hive Big Data Analytics endpoints.
"""
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AnalyticsOverviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_reviews_evaluated: int = Field(default=25000, description="Total reviews analyzed in local sample corpus")
    total_products_evaluated: int = Field(default=19065, description="Total catalog products represented in sample")
    corpus_avg_star_rating: float = Field(default=4.1655, description="Exact average customer star rating across all 25,000 reviews")
    aspect_reviews_avg_star_rating: float = Field(default=4.1299, description="Exact average customer star rating across the 16,409 aspect-discussing reviews")
    reviews_with_aspect_mentions: int = Field(description="Unique reviews discussing at least one locked aspect")
    reviews_with_no_aspect: int = Field(description="Unique reviews where no locked aspect keywords were detected")
    total_aspect_review_pairs: int = Field(default=26029, description="Total aspect-review pairs summed across all 6 aspects")
    total_aspect_mentions: int = Field(default=26029, description="Legacy alias for total_aspect_review_pairs")
    locked_aspect_count: int = Field(default=6, description="Number of domain-locked mobile aspect categories")
    locked_aspects: List[str] = Field(description="Canonical identifiers for the 6 domain aspects")
    dataset_scope: str = Field(
        default="Amazon Reviews 2023: Cell_Phones_and_Accessories (25k stratified sample)",
        description="Dataset provenance and coverage scope disclosure"
    )
    execution_engine: str = Field(
        default="Hadoop Streaming 3.3.6 MapReduce + Apache Hive 3.1.3",
        description="Authentic distributed analytics engine used to generate data"
    )
    methodology_notes: List[str] = Field(description="Methodological limitations and interpretation disclosures")


class AspectVolumeItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    aspect: str = Field(description="Canonical aspect identifier")
    aspect_label: str = Field(description="Human-readable aspect title")
    total_aspect_reviews: int = Field(ge=0, description="Distinct reviews discussing this aspect")
    weighted_avg_rating: float = Field(ge=1.0, le=5.0, description="Exact review-weighted average customer star rating")
    total_helpful_votes: int = Field(ge=0, description="Total helpful votes accumulated by reviews discussing this aspect")


class AspectVolumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_aspects: int = Field(ge=0, description="Number of aspects reported (always 6)")
    rating_basis: str = Field(
        default="Customer star rating (1.0 - 5.0, unpredicted source reviews)",
        description="Rating basis disclosure"
    )
    methodology: str = Field(
        default="Deterministic rule-based mapper with distinct-review deduplication per aspect",
        description="Aspect extraction methodology disclosure"
    )
    items: List[AspectVolumeItem] = Field(description="Aspect volume aggregates")


class TopProductAspectItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parent_asin: str = Field(description="Canonical parent ASIN")
    aspect: str = Field(description="Canonical aspect identifier")
    aspect_label: str = Field(description="Human-readable aspect title")
    aspect_review_count: int = Field(ge=0, description="Distinct reviews for this product discussing this aspect")
    product_aspect_avg_rating: float = Field(ge=1.0, le=5.0, description="Average star rating for this product-aspect")
    total_helpful_votes: int = Field(ge=0, description="Helpful votes for reviews discussing this product-aspect")


class TopProductsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_items: int = Field(ge=0, description="Number of product-aspect pairs returned")
    rating_basis: str = Field(
        default="Customer star rating (1.0 - 5.0, unpredicted source reviews)",
        description="Rating basis disclosure"
    )
    items: List[TopProductAspectItem] = Field(description="Top products ranked by aspect review volume")


class PainPointAspectItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parent_asin: str = Field(description="Canonical parent ASIN")
    aspect: str = Field(description="Canonical aspect identifier")
    aspect_label: str = Field(description="Human-readable aspect title")
    aspect_review_count: int = Field(ge=0, description="Distinct reviews for this product discussing this aspect")
    avg_rating: float = Field(ge=1.0, le=5.0, description="Average customer star rating for this product-aspect")
    total_helpful_votes: int = Field(ge=0, description="Helpful votes accumulated by these reviews")


class PainPointsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_items: int = Field(ge=0, description="Number of potential pain point rows returned")
    filter_criteria: str = Field(
        default="Minimum 5 distinct aspect reviews (review_count >= 5), ranked by avg_rating ASC",
        description="Filter and threshold disclosure"
    )
    scientific_disclaimer: str = Field(
        default="Low-rated aspect discussions indicate potential customer friction/pain points within this 25k review sample, not verified hardware defects or recalls.",
        description="Mandatory scientific disclaimer distinguishing ratings from verified defects"
    )
    items: List[PainPointAspectItem] = Field(description="Lowest-rated product aspects")


class RatingBandItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    aspect: str = Field(description="Canonical aspect identifier")
    aspect_label: str = Field(description="Human-readable aspect title")
    low_rating_reviews_1_to_2_stars: int = Field(ge=0, description="Reviews with 1.0 - 2.0 stars")
    med_rating_reviews_3_stars: int = Field(ge=0, description="Reviews with 3.0 stars")
    high_rating_reviews_4_to_5_stars: int = Field(ge=0, description="Reviews with 4.0 - 5.0 stars")
    total_aspect_reviews: int = Field(ge=0, description="Total distinct reviews for this aspect")
    high_rating_pct: float = Field(ge=0.0, le=100.0, description="Percentage of high-star reviews (4-5 stars)")
    low_rating_pct: float = Field(ge=0.0, le=100.0, description="Percentage of low-star reviews (1-2 stars)")


class RatingBandsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_aspects: int = Field(ge=0, description="Number of aspects reported (always 6)")
    rating_basis: str = Field(
        default="Customer star ratings (1-2 low, 3 medium, 4-5 high), NOT NLP text sentiment",
        description="Rating band interpretation disclosure"
    )
    items: List[RatingBandItem] = Field(description="Rating band distributions by aspect")


class AspectPenetrationItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parent_asin: str = Field(description="Canonical parent ASIN")
    total_product_reviews: int = Field(ge=1, description="Total distinct reviews for this product in dataset")
    aspect: str = Field(description="Canonical aspect identifier")
    aspect_label: str = Field(description="Human-readable aspect title")
    reviews_mentioning_aspect: int = Field(ge=0, description="Distinct reviews for this product discussing this aspect")
    aspect_review_penetration_pct: float = Field(
        ge=0.0, le=100.0,
        description="Proportion of product reviews discussing this aspect: (reviews_mentioning_aspect / total_product_reviews) * 100"
    )
    aspect_avg_rating: float = Field(ge=1.0, le=5.0, description="Average rating for aspect reviews of this product")
    overall_product_avg_rating: float = Field(ge=1.0, le=5.0, description="Overall average rating across all reviews for this product")


class AspectPenetrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_items: int = Field(ge=0, description="Number of product-aspect penetration rows returned")
    semantic_note: str = Field(
        default="Penetration % is the proportion of distinct reviews for a product that mention this aspect. Strictly bounded [0.0%, 100.0%].",
        description="Verification note confirming distinct-review penetration semantics"
    )
    items: List[AspectPenetrationItem] = Field(description="Product-level aspect penetration records")
