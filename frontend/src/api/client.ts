/**
 * ProductPulse — API Client
 * Clean, fetch-based HTTP client for ProductPulse FastAPI backend.
 * Never executes tight retry loops. Gracefully intercepts network failures.
 */

import { getApiBaseUrl } from './config.ts';
import type {
  ApiResponse,
  ApiClientError,
  HealthStatus,
  ProductListResponse,
  ProductDetailResponse,
  ReviewListResponse,
  ReviewFilters,
} from '../types/api.ts';

/**
 * Helper to safely execute a fetch request and map errors to structured ApiResponse.
 */
async function safeFetch<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Accept': 'application/json',
        ...(options?.headers || {}),
      },
    });

    if (!response.ok) {
      let detail = '';
      try {
        const errorJson = await response.json();
        detail = errorJson.detail || errorJson.message || JSON.stringify(errorJson);
      } catch {
        detail = await response.text().catch(() => '');
      }

      const error: ApiClientError = {
        isNetworkError: false,
        status: response.status,
        message: `HTTP ${response.status}: ${response.statusText || 'Request failed'}`,
        detail: detail || undefined,
      };

      return { success: false, error };
    }

    const data: T = await response.json();
    return { success: true, data };
  } catch (err: unknown) {
    const errMessage = err instanceof Error ? err.message : String(err);
    const error: ApiClientError = {
      isNetworkError: true,
      message: `Cannot connect to ProductPulse backend at ${baseUrl}`,
      detail: `${errMessage}. Ensure FastAPI is running at ${baseUrl} and CORS allows http://localhost:5173.`,
    };
    return { success: false, error };
  }
}

/**
 * Checks system and database health status via GET /api/health
 */
export async function checkHealth(): Promise<ApiResponse<HealthStatus>> {
  return safeFetch<HealthStatus>('/api/health');
}

/**
 * Fetches paginated catalog products via GET /api/products
 * @param limit Page size (default 20, max 100)
 * @param offset Record offset (default 0)
 */
export async function getProducts(
  limit: number = 20,
  offset: number = 0
): Promise<ApiResponse<ProductListResponse>> {
  const boundedLimit = Math.max(1, Math.min(100, limit));
  const boundedOffset = Math.max(0, offset);
  const query = new URLSearchParams({
    limit: String(boundedLimit),
    offset: String(boundedOffset),
  });

  return safeFetch<ProductListResponse>(`/api/products?${query.toString()}`);
}

/**
 * Fetches full product details and source rating distribution via GET /api/products/{parent_asin}
 */
export async function getProductDetail(
  parentAsin: string
): Promise<ApiResponse<ProductDetailResponse>> {
  const safeAsin = encodeURIComponent(parentAsin.trim());
  return safeFetch<ProductDetailResponse>(`/api/products/${safeAsin}`);
}

/**
 * Fetches paginated, filtered reviews via GET /api/reviews
 */
export async function getReviews(
  filters: ReviewFilters = {}
): Promise<ApiResponse<ReviewListResponse>> {
  const params = new URLSearchParams();

  if (filters.parent_asin && filters.parent_asin.trim()) {
    params.set('parent_asin', filters.parent_asin.trim());
  }

  if (filters.asin && filters.asin.trim()) {
    params.set('asin', filters.asin.trim());
  }

  if (filters.rating !== undefined && filters.rating !== null && !isNaN(filters.rating)) {
    params.set('rating', String(filters.rating));
  }

  if (filters.verified_purchase !== undefined && filters.verified_purchase !== null) {
    params.set('verified_purchase', String(filters.verified_purchase));
  }

  const limit = filters.limit ? Math.max(1, Math.min(100, filters.limit)) : 20;
  const offset = filters.offset ? Math.max(0, filters.offset) : 0;
  params.set('limit', String(limit));
  params.set('offset', String(offset));

  return safeFetch<ReviewListResponse>(`/api/reviews?${params.toString()}`);
}

// -------------------------------------------------------------
// Big Data Analytics (Hadoop & Hive) Endpoints
// -------------------------------------------------------------

/**
 * Fetches high-level BDA overview metrics & methodology disclosures via GET /api/analytics/overview
 */
export async function getAnalyticsOverview(): Promise<ApiResponse<import('../types/api.ts').AnalyticsOverviewResponse>> {
  return safeFetch('/api/analytics/overview');
}

/**
 * Fetches Query 1 overall aspect volumes and weighted ratings via GET /api/analytics/aspect-volumes
 */
export async function getAspectVolumes(): Promise<ApiResponse<import('../types/api.ts').AspectVolumeResponse>> {
  return safeFetch('/api/analytics/aspect-volumes');
}

/**
 * Fetches Query 2 top products by aspect review count via GET /api/analytics/top-products
 */
export async function getTopProducts(
  aspect?: string,
  parentAsin?: string
): Promise<ApiResponse<import('../types/api.ts').TopProductsResponse>> {
  const params = new URLSearchParams();
  if (aspect && aspect.trim()) params.set('aspect', aspect.trim());
  if (parentAsin && parentAsin.trim()) params.set('parent_asin', parentAsin.trim());
  const queryStr = params.toString() ? `?${params.toString()}` : '';
  return safeFetch(`/api/analytics/top-products${queryStr}`);
}

/**
 * Fetches Query 3 lowest-rated product aspects (potential customer pain points) via GET /api/analytics/pain-points
 */
export async function getPainPoints(
  aspect?: string,
  parentAsin?: string
): Promise<ApiResponse<import('../types/api.ts').PainPointsResponse>> {
  const params = new URLSearchParams();
  if (aspect && aspect.trim()) params.set('aspect', aspect.trim());
  if (parentAsin && parentAsin.trim()) params.set('parent_asin', parentAsin.trim());
  const queryStr = params.toString() ? `?${params.toString()}` : '';
  return safeFetch(`/api/analytics/pain-points${queryStr}`);
}

/**
 * Fetches Query 4 star rating-band distributions via GET /api/analytics/rating-bands
 */
export async function getRatingBands(): Promise<ApiResponse<import('../types/api.ts').RatingBandsResponse>> {
  return safeFetch('/api/analytics/rating-bands');
}

/**
 * Fetches Query 5 product-level aspect penetration percentages via GET /api/analytics/aspect-penetration
 */
export async function getAspectPenetration(
  aspect?: string,
  parentAsin?: string
): Promise<ApiResponse<import('../types/api.ts').AspectPenetrationResponse>> {
  const params = new URLSearchParams();
  if (aspect && aspect.trim()) params.set('aspect', aspect.trim());
  if (parentAsin && parentAsin.trim()) params.set('parent_asin', parentAsin.trim());
  const queryStr = params.toString() ? `?${params.toString()}` : '';
  return safeFetch(`/api/analytics/aspect-penetration${queryStr}`);
}
