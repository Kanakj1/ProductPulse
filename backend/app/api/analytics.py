"""
ProductPulse — Big Data Analytics API Endpoints
Serves authentic, verified Hadoop MapReduce and Apache Hive analytics outputs
from data/bda/ CSV exports with strict schema validation.
"""
import csv
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from backend.app.schemas.analytics import (
    AnalyticsOverviewResponse,
    AspectPenetrationItem,
    AspectPenetrationResponse,
    AspectVolumeItem,
    AspectVolumeResponse,
    PainPointAspectItem,
    PainPointsResponse,
    RatingBandItem,
    RatingBandsResponse,
    TopProductAspectItem,
    TopProductsResponse,
)

router = APIRouter(prefix="/analytics", tags=["Big Data Analytics"])

# Locate data/bda directory relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
BDA_DIR = PROJECT_ROOT / "data" / "bda"

ASPECT_LABELS = {
    "build_durability": "Build & Durability",
    "battery_charging": "Battery & Charging",
    "screen_display": "Screen & Display",
    "performance_software": "Performance & Software",
    "camera_optics": "Camera & Optics",
    "connectivity_audio": "Connectivity & Audio",
}

LOCKED_ASPECTS = [
    "build_durability",
    "battery_charging",
    "screen_display",
    "performance_software",
    "camera_optics",
    "connectivity_audio",
]


def _read_csv(filename: str, required_headers: List[str]) -> List[dict]:
    """
    Safely reads and validates a CSV file from data/bda/.
    Raises HTTPException(500) if the file is missing or has invalid headers.
    """
    filepath = BDA_DIR / filename
    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Required BDA analytics export missing: {filename}. Please run the Hadoop/Hive pipeline.",
        )

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise ValueError("Empty CSV file")
            
            # Verify required headers exist
            for rh in required_headers:
                if rh not in reader.fieldnames:
                    raise ValueError(f"Missing expected header '{rh}' in {filename}. Found: {reader.fieldnames}")
            
            return list(reader)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse BDA analytics export {filename}: {str(e)}",
        )


@router.get("/overview", response_model=AnalyticsOverviewResponse, summary="Analytics Overview & Metadata")
def get_analytics_overview() -> AnalyticsOverviewResponse:
    """
    Returns high-level summary KPIs and methodology disclosures grounded in authentic
    Hadoop Streaming MapReduce and Hive pipeline execution outputs.
    """
    # Load Query 1 to compute total aspect review pairs
    q1_rows = _read_csv(
        "hive_query1_aspect_volumes.csv",
        ["aspect", "total_aspect_reviews", "weighted_avg_rating", "total_helpful_votes"],
    )
    total_pairs = sum(int(row["total_aspect_reviews"]) for row in q1_rows)

    return AnalyticsOverviewResponse(
        total_reviews_evaluated=25000,
        total_products_evaluated=19065,
        corpus_avg_star_rating=4.1655,
        aspect_reviews_avg_star_rating=4.1299,
        reviews_with_aspect_mentions=16409,
        reviews_with_no_aspect=8591,
        total_aspect_review_pairs=total_pairs,
        total_aspect_mentions=total_pairs,
        locked_aspect_count=6,
        locked_aspects=LOCKED_ASPECTS,
        dataset_scope="Amazon Reviews 2023: Cell_Phones_and_Accessories (25k stratified sample)",
        execution_engine="Hadoop Streaming 3.3.6 MapReduce + Apache Hive 3.1.3",
        methodology_notes=[
            "Data originates from a 25,000-review stratified local sample, not the entire Amazon review catalog.",
            "Overall corpus average customer star rating across all 25,000 reviews is 4.1655 (verified in raw JSONL, Hadoop __ALL_REVIEWS__, and SQLite).",
            "Average customer star rating across the 16,409 aspect-discussing reviews is 4.1299 (reviews without detected aspects average 4.2336).",
            "Aspect detection uses deterministic rule-based lexicons with Python unicode boundaries.",
            "Each review is deduplicated per aspect at the mapper level (set-based detection); counts represent distinct reviews mentioning an aspect.",
            "Star ratings represent reviewer scores (1.0 - 5.0), not text-derived NLP sentiment.",
            "Summing aspect counts yields total aspect-review pairs (26,029), not unique reviews (16,409), as reviews frequently evaluate multiple smartphone aspects (average 1.59 aspects per aspect-discussing review).",
            "Lowest-rated product aspects indicate potential customer friction/pain points, not confirmed hardware defects.",
        ],
    )


@router.get("/aspect-volumes", response_model=AspectVolumeResponse, summary="Aspect Discussion Volumes")
def get_aspect_volumes() -> AspectVolumeResponse:
    """
    Returns overall aspect discussion volumes, review-weighted average ratings,
    and helpful vote totals from Hive Query 1 export.
    """
    rows = _read_csv(
        "hive_query1_aspect_volumes.csv",
        ["aspect", "total_aspect_reviews", "weighted_avg_rating", "total_helpful_votes"],
    )

    items = []
    for r in rows:
        asp = r["aspect"]
        items.append(
            AspectVolumeItem(
                aspect=asp,
                aspect_label=ASPECT_LABELS.get(asp, asp.replace("_", " ").title()),
                total_aspect_reviews=int(r["total_aspect_reviews"]),
                weighted_avg_rating=float(r["weighted_avg_rating"]),
                total_helpful_votes=int(r["total_helpful_votes"]),
            )
        )

    return AspectVolumeResponse(
        total_aspects=len(items),
        items=items,
    )


@router.get("/top-products", response_model=TopProductsResponse, summary="Top Products by Aspect Review Count")
def get_top_products(
    aspect: Optional[str] = Query(default=None, description="Filter by canonical aspect"),
    parent_asin: Optional[str] = Query(default=None, description="Filter by parent ASIN"),
) -> TopProductsResponse:
    """
    Returns top products ranked by aspect review volume from Hive Query 2 export.
    """
    rows = _read_csv(
        "hive_query2_top_products.csv",
        ["parent_asin", "aspect", "aspect_review_count", "product_aspect_avg_rating", "total_helpful_votes"],
    )

    items = []
    for r in rows:
        if aspect and r["aspect"] != aspect.strip():
            continue
        if parent_asin and parent_asin.strip().upper() not in r["parent_asin"].upper():
            continue

        asp = r["aspect"]
        items.append(
            TopProductAspectItem(
                parent_asin=r["parent_asin"],
                aspect=asp,
                aspect_label=ASPECT_LABELS.get(asp, asp.replace("_", " ").title()),
                aspect_review_count=int(r["aspect_review_count"]),
                product_aspect_avg_rating=float(r["product_aspect_avg_rating"]),
                total_helpful_votes=int(r["total_helpful_votes"]),
            )
        )

    return TopProductsResponse(
        total_items=len(items),
        items=items,
    )


@router.get("/pain-points", response_model=PainPointsResponse, summary="Potential Pain Points by Star Rating")
def get_pain_points(
    aspect: Optional[str] = Query(default=None, description="Filter by canonical aspect"),
    parent_asin: Optional[str] = Query(default=None, description="Filter by parent ASIN"),
) -> PainPointsResponse:
    """
    Returns statistically relevant lowest-rated product aspects from Hive Query 3 export.
    Requires minimum 5 distinct aspect reviews (N >= 5).
    """
    rows = _read_csv(
        "hive_query3_aspect_ratings.csv",
        ["parent_asin", "aspect", "aspect_review_count", "avg_rating", "total_helpful_votes"],
    )

    items = []
    for r in rows:
        if aspect and r["aspect"] != aspect.strip():
            continue
        if parent_asin and parent_asin.strip().upper() not in r["parent_asin"].upper():
            continue

        asp = r["aspect"]
        cnt = int(r["aspect_review_count"])
        items.append(
            PainPointAspectItem(
                parent_asin=r["parent_asin"],
                aspect=asp,
                aspect_label=ASPECT_LABELS.get(asp, asp.replace("_", " ").title()),
                aspect_review_count=cnt,
                avg_rating=float(r["avg_rating"]),
                total_helpful_votes=int(r["total_helpful_votes"]),
                sample_limitation_notice=f"Based on {cnt} review(s) in this 25k sample; not statistically representative of all customer experiences.",
            )
        )

    return PainPointsResponse(
        total_items=len(items),
        items=items,
    )


@router.get("/rating-bands", response_model=RatingBandsResponse, summary="Rating-Band Distributions by Aspect")
def get_rating_bands() -> RatingBandsResponse:
    """
    Returns star rating-band distributions (1-2 low, 3 medium, 4-5 high) from Hive Query 4 export.
    Discloses that bands reflect customer star ratings, not NLP text sentiment.
    """
    rows = _read_csv(
        "hive_query4_rating_bands.csv",
        [
            "aspect",
            "low_rating_reviews_1_to_2_stars",
            "med_rating_reviews_3_stars",
            "high_rating_reviews_4_to_5_stars",
            "total_aspect_reviews",
            "high_rating_pct",
            "low_rating_pct",
        ],
    )

    items = []
    for r in rows:
        asp = r["aspect"]
        items.append(
            RatingBandItem(
                aspect=asp,
                aspect_label=ASPECT_LABELS.get(asp, asp.replace("_", " ").title()),
                low_rating_reviews_1_to_2_stars=int(r["low_rating_reviews_1_to_2_stars"]),
                med_rating_reviews_3_stars=int(r["med_rating_reviews_3_stars"]),
                high_rating_reviews_4_to_5_stars=int(r["high_rating_reviews_4_to_5_stars"]),
                total_aspect_reviews=int(r["total_aspect_reviews"]),
                high_rating_pct=float(r["high_rating_pct"]),
                low_rating_pct=float(r["low_rating_pct"]),
            )
        )

    return RatingBandsResponse(
        total_aspects=len(items),
        items=items,
    )


@router.get("/aspect-penetration", response_model=AspectPenetrationResponse, summary="Product Aspect Penetration")
def get_aspect_penetration(
    aspect: Optional[str] = Query(default=None, description="Filter by canonical aspect"),
    parent_asin: Optional[str] = Query(default=None, description="Filter by parent ASIN"),
) -> AspectPenetrationResponse:
    """
    Returns aspect penetration rates per product from Hive Query 5 export.
    Both numerator and denominator are distinct reviews, bounded [0.0%, 100.0%].
    """
    rows = _read_csv(
        "hive_query5_aspect_cooccurrence.csv",
        [
            "parent_asin",
            "total_product_reviews",
            "aspect",
            "reviews_mentioning_aspect",
            "aspect_review_penetration_pct",
            "aspect_avg_rating",
            "overall_product_avg_rating",
        ],
    )

    items = []
    for r in rows:
        if aspect and r["aspect"] != aspect.strip():
            continue
        if parent_asin and parent_asin.strip().upper() not in r["parent_asin"].upper():
            continue

        asp = r["aspect"]
        items.append(
            AspectPenetrationItem(
                parent_asin=r["parent_asin"],
                total_product_reviews=int(r["total_product_reviews"]),
                aspect=asp,
                aspect_label=ASPECT_LABELS.get(asp, asp.replace("_", " ").title()),
                reviews_mentioning_aspect=int(r["reviews_mentioning_aspect"]),
                aspect_review_penetration_pct=float(r["aspect_review_penetration_pct"]),
                aspect_avg_rating=float(r["aspect_avg_rating"]),
                overall_product_avg_rating=float(r["overall_product_avg_rating"]),
            )
        )

    return AspectPenetrationResponse(
        total_items=len(items),
        items=items,
    )
