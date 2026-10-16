"""
ProductPulse — Reviews API Endpoint
Implements paginated review retrieval with parameterized filtering.
"""
import sqlite3
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query

from backend.app.schemas.reviews import ReviewItem, ReviewListResponse
from backend.db.connection import get_db

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("", response_model=ReviewListResponse, summary="List Reviews")
def list_reviews(
    limit: int = Query(default=20, ge=1, le=100, description="Items per page (1-100)"),
    offset: int = Query(default=0, ge=0, description="Offset into review results"),
    parent_asin: Optional[str] = Query(default=None, description="Filter reviews by product parent_asin"),
    asin: Optional[str] = Query(default=None, description="Filter reviews by specific variant asin"),
    rating: Optional[float] = Query(default=None, ge=1.0, le=5.0, description="Filter by exact source star rating"),
    verified_purchase: Optional[bool] = Query(default=None, description="Filter by verified purchase status"),
    db: sqlite3.Connection = Depends(get_db),
) -> ReviewListResponse:
    """
    Returns genuine reviews matching the specified filter criteria.
    Results are ordered deterministically by recency (review_epoch_seconds DESC, then review_id ASC).
    All database queries use strict parameterization to prevent SQL injection.
    """
    conditions: List[str] = []
    params: List[Any] = []

    if parent_asin is not None and parent_asin.strip():
        conditions.append("parent_asin = ?")
        params.append(parent_asin.strip())

    if asin is not None and asin.strip():
        conditions.append("asin = ?")
        params.append(asin.strip())

    if rating is not None:
        conditions.append("rating = ?")
        params.append(rating)

    if verified_purchase is not None:
        conditions.append("verified_purchase = ?")
        params.append(1 if verified_purchase else 0)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    cur = db.cursor()

    # 1. Count matching records
    count_sql = f"SELECT COUNT(*) FROM reviews {where_clause};"
    cur.execute(count_sql, tuple(params))
    total_count = cur.fetchone()[0]

    # 2. Fetch paginated slice
    select_sql = f"""
        SELECT 
            review_id, parent_asin, asin, user_id, rating,
            raw_title, raw_text, review_timestamp_utc, review_epoch_seconds,
            helpful_vote, verified_purchase, has_images, is_blank_text,
            occurrence_index
        FROM reviews
        {where_clause}
        ORDER BY review_epoch_seconds DESC, review_id ASC
        LIMIT ? OFFSET ?;
    """
    query_params = list(params) + [limit, offset]
    cur.execute(select_sql, tuple(query_params))
    rows = cur.fetchall()

    items = [
        ReviewItem(
            review_id=row["review_id"],
            parent_asin=row["parent_asin"],
            asin=row["asin"],
            user_id=row["user_id"],
            rating=row["rating"],
            raw_title=row["raw_title"],
            raw_text=row["raw_text"],
            review_timestamp_utc=row["review_timestamp_utc"],
            review_epoch_seconds=row["review_epoch_seconds"],
            helpful_vote=row["helpful_vote"],
            verified_purchase=bool(row["verified_purchase"]),
            has_images=bool(row["has_images"]),
            is_blank_text=bool(row["is_blank_text"]),
            occurrence_index=row["occurrence_index"],
        )
        for row in rows
    ]

    return ReviewListResponse(
        total_reviews=total_count,
        limit=limit,
        offset=offset,
        items=items,
    )
