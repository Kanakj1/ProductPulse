"""
ProductPulse — Product API Endpoints
Implements paginated catalogue browsing and detailed product statistics.
"""
from pathlib import Path
import sqlite3
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.schemas.products import (
    ProductAspectSummary,
    ProductDetailResponse,
    ProductListResponse,
    ProductSummary,
    RatingDistribution,
)
from backend.db.connection import get_db

router = APIRouter(prefix="/products", tags=["Products"])

PROJECT_ROOT = Path(__file__).resolve().parents[3]
HADOOP_OUTPUT_FILE = PROJECT_ROOT / "data" / "bda" / "hadoop_output" / "part-00000"

ASPECT_LABELS = {
    "build_durability": "Build & Durability",
    "battery_charging": "Battery & Charging",
    "screen_display": "Screen & Display",
    "performance_software": "Performance & Software",
    "camera_optics": "Camera & Optics",
    "connectivity_audio": "Connectivity & Audio",
}


@router.get("", response_model=ProductListResponse, summary="List Products")
def list_products(
    limit: int = Query(default=20, ge=1, le=100, description="Items per page (1-100)"),
    offset: int = Query(default=0, ge=0, description="Offset into catalog results"),
    db: sqlite3.Connection = Depends(get_db),
) -> ProductListResponse:
    """
    Returns a paginated list of catalog products from the Mobile Phones & Accessories dataset.
    Products are sorted deterministically by review count descending, then parent ASIN ascending.
    """
    cur = db.cursor()

    # Total product count
    cur.execute("SELECT COUNT(*) FROM products;")
    total_count = cur.fetchone()[0]

    # Paginated query with review counts and average ratings
    cur.execute(
        """
        SELECT 
            p.parent_asin,
            p.title,
            p.brand,
            p.price,
            p.main_category,
            p.has_metadata,
            COUNT(r.review_id) AS review_count,
            ROUND(AVG(r.rating), 2) AS avg_rating
        FROM products p
        LEFT JOIN reviews r ON p.parent_asin = r.parent_asin
        GROUP BY p.parent_asin
        ORDER BY review_count DESC, p.parent_asin ASC
        LIMIT ? OFFSET ?;
        """,
        (limit, offset),
    )
    rows = cur.fetchall()

    items = [
        ProductSummary(
            parent_asin=row["parent_asin"],
            title=row["title"],
            brand=row["brand"],
            price=row["price"],
            main_category=row["main_category"],
            has_metadata=bool(row["has_metadata"]),
            review_count=row["review_count"] or 0,
            avg_rating=row["avg_rating"],
        )
        for row in rows
    ]

    return ProductListResponse(
        total_products=total_count,
        limit=limit,
        offset=offset,
        items=items,
    )


@router.get("/{parent_asin}", response_model=ProductDetailResponse, summary="Get Product Details")
def get_product(
    parent_asin: str,
    db: sqlite3.Connection = Depends(get_db),
) -> ProductDetailResponse:
    """
    Retrieves detailed catalog information, SKU variants, and empirical rating statistics
    for a single product identified by parent_asin.
    """
    cleaned_asin = parent_asin.strip()
    cur = db.cursor()

    # 1. Fetch base product record
    cur.execute(
        """
        SELECT parent_asin, title, brand, price, main_category, has_metadata, created_at
        FROM products
        WHERE parent_asin = ?;
        """,
        (cleaned_asin,),
    )
    prod = cur.fetchone()
    if not prod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with parent_asin '{cleaned_asin}' not found",
        )

    # 2. Fetch associated variant ASINs
    cur.execute(
        """
        SELECT asin FROM product_variants
        WHERE parent_asin = ?
        ORDER BY asin ASC;
        """,
        (cleaned_asin,),
    )
    variants = [r[0] for r in cur.fetchall()]

    # 3. Compute empirical aggregate statistics from genuine reviews
    cur.execute(
        """
        SELECT 
            COUNT(*) AS review_count,
            ROUND(AVG(rating), 2) AS avg_rating,
            SUM(CASE WHEN rating >= 4.5 THEN 1 ELSE 0 END) AS stars_5,
            SUM(CASE WHEN rating >= 3.5 AND rating < 4.5 THEN 1 ELSE 0 END) AS stars_4,
            SUM(CASE WHEN rating >= 2.5 AND rating < 3.5 THEN 1 ELSE 0 END) AS stars_3,
            SUM(CASE WHEN rating >= 1.5 AND rating < 2.5 THEN 1 ELSE 0 END) AS stars_2,
            SUM(CASE WHEN rating < 1.5 THEN 1 ELSE 0 END) AS stars_1,
            SUM(verified_purchase) AS verified_purchase_count,
            SUM(has_images) AS has_images_count,
            COALESCE(SUM(helpful_vote), 0) AS total_helpful_votes,
            MIN(review_timestamp_utc) AS first_review_utc,
            MAX(review_timestamp_utc) AS latest_review_utc
        FROM reviews
        WHERE parent_asin = ?;
        """,
        (cleaned_asin,),
    )
    stats_row = cur.fetchone()

    rating_dist = RatingDistribution(
        stars_5=stats_row["stars_5"] or 0,
        stars_4=stats_row["stars_4"] or 0,
        stars_3=stats_row["stars_3"] or 0,
        stars_2=stats_row["stars_2"] or 0,
        stars_1=stats_row["stars_1"] or 0,
    )

    # 4. Extract genuine Hadoop MapReduce aspect metrics for this product if available
    aspect_metrics: List[ProductAspectSummary] = []
    if HADOOP_OUTPUT_FILE.exists():
        try:
            with open(HADOOP_OUTPUT_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split("\t")
                    if len(parts) >= 8 and parts[0] == cleaned_asin:
                        aspect_key = parts[1]
                        if not aspect_key.startswith("__") and aspect_key in ASPECT_LABELS:
                            aspect_metrics.append(
                                ProductAspectSummary(
                                    aspect=aspect_key,
                                    aspect_label=ASPECT_LABELS[aspect_key],
                                    review_count=int(parts[2]),
                                    avg_rating=float(parts[3]),
                                    total_helpful_votes=int(parts[4]),
                                    low_rating_count=int(parts[5]),
                                    med_rating_count=int(parts[6]),
                                    high_rating_count=int(parts[7]),
                                )
                            )
        except Exception:
            pass

    return ProductDetailResponse(
        parent_asin=prod["parent_asin"],
        title=prod["title"],
        brand=prod["brand"],
        price=prod["price"],
        main_category=prod["main_category"],
        has_metadata=bool(prod["has_metadata"]),
        variants=variants,
        review_count=stats_row["review_count"] or 0,
        avg_rating=stats_row["avg_rating"],
        rating_distribution=rating_dist,
        total_helpful_votes=stats_row["total_helpful_votes"] or 0,
        verified_purchase_count=stats_row["verified_purchase_count"] or 0,
        has_images_count=stats_row["has_images_count"] or 0,
        first_review_utc=stats_row["first_review_utc"],
        latest_review_utc=stats_row["latest_review_utc"],
        aspect_metrics=aspect_metrics,
    )
