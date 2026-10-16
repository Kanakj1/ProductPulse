"""
ProductPulse — Product Schemas
Pydantic v2 schemas for product catalogue and detail endpoints.
"""
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parent_asin: str = Field(description="Unique parent ASIN identifying the canonical catalog product")
    title: Optional[str] = Field(default=None, description="Product catalog title (NULL if metadata pending)")
    brand: Optional[str] = Field(default=None, description="Product brand name (NULL if metadata pending)")
    price: Optional[float] = Field(default=None, description="Product catalog price in USD (NULL if metadata pending)")
    main_category: str = Field(default="Cell_Phones_and_Accessories", description="Product category domain lock")
    has_metadata: bool = Field(default=False, description="Whether catalog metadata has been ingested")
    review_count: int = Field(default=0, ge=0, description="Total genuine reviews in database for this product")
    avg_rating: Optional[float] = Field(default=None, description="Average source customer star rating (1.0 - 5.0)")


class ProductListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_products: int = Field(ge=0, description="Total count of products matching catalog criteria")
    limit: int = Field(ge=1, le=100, description="Maximum number of items returned in this page")
    offset: int = Field(ge=0, description="Zero-based offset into the total product list")
    rating_basis: str = Field(
        default="source_star_rating (1.0 - 5.0, unpredicted customer reviews)",
        description="Explicit methodological disclosure: ratings reflect source reviewer scores, not NLP predictions",
    )
    items: List[ProductSummary] = Field(description="List of product summaries for the requested page")


class RatingDistribution(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stars_5: int = Field(default=0, ge=0, description="Count of 5-star source reviews")
    stars_4: int = Field(default=0, ge=0, description="Count of 4-star source reviews")
    stars_3: int = Field(default=0, ge=0, description="Count of 3-star source reviews")
    stars_2: int = Field(default=0, ge=0, description="Count of 2-star source reviews")
    stars_1: int = Field(default=0, ge=0, description="Count of 1-star source reviews")


class ProductAspectSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    aspect: str = Field(description="Canonical aspect identifier")
    aspect_label: str = Field(description="Human-readable aspect label")
    review_count: int = Field(ge=0, description="Distinct reviews discussing this aspect for this product")
    avg_rating: float = Field(ge=1.0, le=5.0, description="Average star rating for reviews discussing this aspect")
    total_helpful_votes: int = Field(default=0, ge=0, description="Helpful votes for reviews discussing this aspect")
    low_rating_count: int = Field(default=0, ge=0, description="Count of 1-2 star reviews mentioning this aspect")
    med_rating_count: int = Field(default=0, ge=0, description="Count of 3 star reviews mentioning this aspect")
    high_rating_count: int = Field(default=0, ge=0, description="Count of 4-5 star reviews mentioning this aspect")


class ProductDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parent_asin: str = Field(description="Unique parent ASIN identifying the canonical catalog product")
    title: Optional[str] = Field(default=None, description="Product catalog title")
    brand: Optional[str] = Field(default=None, description="Product brand name")
    price: Optional[float] = Field(default=None, description="Product catalog price in USD")
    main_category: str = Field(default="Cell_Phones_and_Accessories", description="Product category domain lock")
    has_metadata: bool = Field(default=False, description="Whether catalog metadata has been ingested")
    metadata_notice: str = Field(
        default="Product metadata (title, brand, price) is pending metadata ingestion. Review aggregate statistics are fully computed.",
        description="Disclosure of metadata ingestion status",
    )
    variants: List[str] = Field(default_factory=list, description="List of specific SKU variant ASINs belonging to this product")
    review_count: int = Field(default=0, ge=0, description="Total genuine reviews in database for this product")
    avg_rating: Optional[float] = Field(default=None, description="Average source customer star rating (1.0 - 5.0)")
    rating_basis: str = Field(
        default="source_star_rating (1.0 - 5.0, unpredicted customer reviews)",
        description="Explicit methodological disclosure: ratings reflect source reviewer scores, not NLP predictions",
    )
    rating_distribution: RatingDistribution = Field(description="Histogram of source customer star ratings")
    total_helpful_votes: int = Field(default=0, ge=0, description="Total helpful votes across all reviews for this product")
    verified_purchase_count: int = Field(default=0, ge=0, description="Count of reviews marked verified purchase")
    has_images_count: int = Field(default=0, ge=0, description="Count of reviews containing customer images")
    first_review_utc: Optional[str] = Field(default=None, description="ISO-8601 UTC timestamp of earliest review")
    latest_review_utc: Optional[str] = Field(default=None, description="ISO-8601 UTC timestamp of latest review")
    aspect_metrics: List[ProductAspectSummary] = Field(
        default_factory=list,
        description="Authentic aspect metrics from Hadoop MapReduce (part-00000) for this product"
    )
