/**
 * ProductPulse — API Types
 * Strictly aligned with backend FastAPI schemas in:
 * - backend/app/schemas/products.py
 * - backend/app/schemas/reviews.py
 * - backend/app/api/health.py
 */

export interface DatabaseHealth {
  status: 'connected' | 'not_connected' | 'error' | string;
  foreign_keys: 'enabled' | 'disabled' | 'unknown' | string;
  dataset: 'loaded' | 'initialized' | 'schema_pending' | 'uninitialized' | 'error' | string;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'error' | string;
  service: string;
  version: string;
  category_lock: string;
  database: DatabaseHealth;
}

export interface ProductSummary {
  parent_asin: string;
  title: string | null;
  brand: string | null;
  price: number | null;
  main_category: string;
  has_metadata: boolean;
  review_count: number;
  avg_rating: number | null;
}

export interface ProductListResponse {
  total_products: number;
  limit: number;
  offset: number;
  rating_basis: string;
  items: ProductSummary[];
}

export interface RatingDistribution {
  stars_5: number;
  stars_4: number;
  stars_3: number;
  stars_2: number;
  stars_1: number;
}

export interface ProductAspectSummary {
  aspect: string;
  aspect_label: string;
  review_count: number;
  avg_rating: number;
  total_helpful_votes: number;
  low_rating_count: number;
  med_rating_count: number;
  high_rating_count: number;
}

export interface ProductDetailResponse {
  parent_asin: string;
  title: string | null;
  brand: string | null;
  price: number | null;
  main_category: string;
  has_metadata: boolean;
  metadata_notice: string;
  variants: string[];
  review_count: number;
  avg_rating: number | null;
  rating_basis: string;
  rating_distribution: RatingDistribution;
  total_helpful_votes: number;
  verified_purchase_count: number;
  has_images_count: number;
  first_review_utc: string | null;
  latest_review_utc: string | null;
  aspect_metrics: ProductAspectSummary[];
}

export interface ReviewItem {
  review_id: string;
  parent_asin: string;
  asin: string;
  user_id: string;
  rating: number;
  raw_title: string | null;
  raw_text: string | null;
  review_timestamp_utc: string;
  review_epoch_seconds: number;
  helpful_vote: number;
  verified_purchase: boolean;
  has_images: boolean;
  is_blank_text: boolean;
  occurrence_index: number;
}

export interface ReviewListResponse {
  total_reviews: number;
  limit: number;
  offset: number;
  rating_basis: string;
  items: ReviewItem[];
}

export interface ReviewFilters {
  parent_asin?: string;
  asin?: string;
  rating?: number;
  verified_purchase?: boolean;
  limit?: number;
  offset?: number;
}

export interface ApiClientError {
  isNetworkError: boolean;
  status?: number;
  message: string;
  detail?: string;
}

export type ApiResponse<T> =
  | { success: true; data: T; error?: never }
  | { success: false; data?: never; error: ApiClientError };

// -------------------------------------------------------------
// Big Data Analytics (Hadoop & Hive) Interfaces
// -------------------------------------------------------------

export interface AnalyticsOverviewResponse {
  total_reviews_evaluated: number;
  total_products_evaluated: number;
  corpus_avg_star_rating: number;
  aspect_reviews_avg_star_rating: number;
  reviews_with_aspect_mentions: number;
  reviews_with_no_aspect: number;
  total_aspect_review_pairs: number;
  total_aspect_mentions: number;
  locked_aspect_count: number;
  locked_aspects: string[];
  dataset_scope: string;
  execution_engine: string;
  methodology_notes: string[];
}

export interface AspectVolumeItem {
  aspect: string;
  aspect_label: string;
  total_aspect_reviews: number;
  weighted_avg_rating: number;
  total_helpful_votes: number;
}

export interface AspectVolumeResponse {
  total_aspects: number;
  rating_basis: string;
  methodology: string;
  items: AspectVolumeItem[];
}

export interface TopProductAspectItem {
  parent_asin: string;
  aspect: string;
  aspect_label: string;
  aspect_review_count: number;
  product_aspect_avg_rating: number;
  total_helpful_votes: number;
}

export interface TopProductsResponse {
  total_items: number;
  rating_basis: string;
  items: TopProductAspectItem[];
}

export interface PainPointAspectItem {
  parent_asin: string;
  aspect: string;
  aspect_label: string;
  aspect_review_count: number;
  avg_rating: number;
  total_helpful_votes: number;
  sample_limitation_notice: string;
}

export interface PainPointsResponse {
  total_items: number;
  filter_criteria: string;
  scientific_disclaimer: string;
  items: PainPointAspectItem[];
}

export interface RatingBandItem {
  aspect: string;
  aspect_label: string;
  low_rating_reviews_1_to_2_stars: number;
  med_rating_reviews_3_stars: number;
  high_rating_reviews_4_to_5_stars: number;
  total_aspect_reviews: number;
  high_rating_pct: number;
  low_rating_pct: number;
}

export interface RatingBandsResponse {
  total_aspects: number;
  rating_basis: string;
  items: RatingBandItem[];
}

export interface AspectPenetrationItem {
  parent_asin: string;
  total_product_reviews: number;
  aspect: string;
  aspect_label: string;
  reviews_mentioning_aspect: number;
  aspect_review_penetration_pct: number;
  aspect_avg_rating: number;
  overall_product_avg_rating: number;
}

export interface AspectPenetrationResponse {
  total_items: number;
  semantic_note: string;
  items: AspectPenetrationItem[];
}
