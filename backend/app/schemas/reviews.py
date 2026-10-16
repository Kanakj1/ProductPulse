"""
ProductPulse — Review Schemas
Pydantic v2 schemas for genuine review querying endpoints.
"""
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ReviewItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    review_id: str = Field(description="Deterministic review primary key (hash or hash_#<occurrence>)")
    parent_asin: str = Field(description="Parent ASIN grouping the product variants")
    asin: str = Field(description="Specific SKU variant ASIN evaluated by the reviewer")
    user_id: str = Field(description="Anonymized customer identifier")
    rating: float = Field(ge=1.0, le=5.0, description="Source customer star rating")
    raw_title: Optional[str] = Field(default=None, description="Review headline title as written by customer")
    raw_text: Optional[str] = Field(default=None, description="Review body text as written by customer")
    review_timestamp_utc: str = Field(description="Full-precision ISO-8601 UTC timestamp")
    review_epoch_seconds: float = Field(description="Unix epoch seconds with millisecond decimals")
    helpful_vote: int = Field(default=0, ge=0, description="Helpful vote count from customers")
    verified_purchase: bool = Field(description="Whether the review was from an Amazon verified purchase")
    has_images: bool = Field(description="Whether the customer attached genuine product photos")
    is_blank_text: bool = Field(description="Whether the review body was blank/whitespace only")
    occurrence_index: int = Field(default=0, ge=0, description="Deduplication occurrence index (0 = first seen)")


class ReviewListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_reviews: int = Field(ge=0, description="Total count of reviews matching the filter criteria")
    limit: int = Field(ge=1, le=100, description="Maximum number of items returned in this page")
    offset: int = Field(ge=0, description="Zero-based offset into the filtered reviews list")
    rating_basis: str = Field(
        default="source_star_rating (1.0 - 5.0, unpredicted customer reviews)",
        description="Explicit methodological disclosure: ratings reflect source reviewer scores, not NLP predictions",
    )
    items: List[ReviewItem] = Field(description="List of genuine reviews matching the query")
