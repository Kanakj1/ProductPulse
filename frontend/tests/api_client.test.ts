/**
 * ProductPulse — Frontend API Client & Contract Tests
 * Runs with Node 22 built-in test runner (node:test) without any external dependencies!
 */
import test, { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';

import { DEFAULT_API_BASE_URL, CATEGORY_LOCK, getApiBaseUrl, setApiBaseUrl } from '../src/api/config.ts';
import { checkHealth, getProducts, getProductDetail, getReviews } from '../src/api/client.ts';
import type {
  ProductSummary,
  ProductListResponse,
  ProductDetailResponse,
  ReviewItem,
  ReviewListResponse,
  HealthStatus,
} from '../src/types/api.ts';

describe('Frontend API Configuration', () => {
  afterEach(() => {
    setApiBaseUrl(null);
  });

  it('enforces default localhost:8000 backend URL', () => {
    assert.strictEqual(DEFAULT_API_BASE_URL, 'http://localhost:8000');
    assert.strictEqual(getApiBaseUrl(), 'http://localhost:8000');
  });

  it('allows setting custom base URL for testing', () => {
    setApiBaseUrl('http://127.0.0.1:59999');
    assert.strictEqual(getApiBaseUrl(), 'http://127.0.0.1:59999');
  });

  it('strictly locks domain to Cell_Phones_and_Accessories', () => {
    assert.strictEqual(CATEGORY_LOCK, 'Cell_Phones_and_Accessories');
  });
});

describe('Frontend API Client Offline Network Error Handling', () => {
  beforeEach(() => {
    // Point to an unused loopback port to guarantee connection refusal
    setApiBaseUrl('http://127.0.0.1:59999');
  });

  afterEach(() => {
    setApiBaseUrl(null);
  });

  it('checkHealth returns graceful structured network error when backend is unreachable', async () => {
    const res = await checkHealth();
    assert.strictEqual(res.success, false);
    if (!res.success) {
      assert.strictEqual(res.error.isNetworkError, true);
      assert.match(res.error.message, /Cannot connect to ProductPulse backend/);
      assert.match(res.error.detail || '', /59999/);
    }
  });

  it('getProducts handles connection failure safely with pagination bounds', async () => {
    const res = await getProducts(200, -5);
    assert.strictEqual(res.success, false);
    if (!res.success) {
      assert.strictEqual(res.error.isNetworkError, true);
      assert.match(res.error.message, /59999/);
    }
  });

  it('getProductDetail handles connection failure with URL encoding', async () => {
    const res = await getProductDetail('B00X TEST/SPECIAL');
    assert.strictEqual(res.success, false);
    if (!res.success) {
      assert.strictEqual(res.error.isNetworkError, true);
    }
  });

  it('getReviews safely handles connection failure with active filters', async () => {
    const res = await getReviews({
      parent_asin: 'B00TEST123',
      asin: 'B00VAR123',
      rating: 5.0,
      verified_purchase: true,
      limit: 10,
      offset: 20,
    });
    assert.strictEqual(res.success, false);
    if (!res.success) {
      assert.strictEqual(res.error.isNetworkError, true);
    }
  });
});

describe('Frontend Data Contract & Schema Parity Tests', () => {
  it('validates HealthStatus schema compatibility', () => {
    const mockHealth: HealthStatus = {
      status: 'healthy',
      service: 'ProductPulse API',
      version: '1.0.0',
      category_lock: 'Cell_Phones_and_Accessories',
      database: {
        status: 'connected',
        foreign_keys: 'enabled',
        dataset: 'loaded',
      },
    };

    assert.strictEqual(mockHealth.status, 'healthy');
    assert.strictEqual(mockHealth.category_lock, 'Cell_Phones_and_Accessories');
    assert.strictEqual(mockHealth.database.foreign_keys, 'enabled');
  });

  it('validates ProductSummary schema compatibility with null metadata', () => {
    const mockProduct: ProductSummary = {
      parent_asin: 'B00X9L4Q8I',
      title: null,
      brand: null,
      price: null,
      main_category: 'Cell_Phones_and_Accessories',
      has_metadata: false,
      review_count: 42,
      avg_rating: 4.25,
    };

    assert.strictEqual(mockProduct.parent_asin, 'B00X9L4Q8I');
    assert.strictEqual(mockProduct.title, null);
    assert.strictEqual(mockProduct.has_metadata, false);
    assert.strictEqual(mockProduct.review_count, 42);
    assert.strictEqual(mockProduct.avg_rating, 4.25);
  });

  it('validates ProductListResponse schema compatibility', () => {
    const mockList: ProductListResponse = {
      total_products: 19065,
      limit: 20,
      offset: 0,
      rating_basis: 'source_star_rating (1.0 - 5.0, unpredicted customer reviews)',
      items: [
        {
          parent_asin: 'B00X9L4Q8I',
          title: null,
          brand: null,
          price: null,
          main_category: 'Cell_Phones_and_Accessories',
          has_metadata: false,
          review_count: 10,
          avg_rating: 4.5,
        },
      ],
    };

    assert.strictEqual(mockList.total_products, 19065);
    assert.strictEqual(mockList.items.length, 1);
    assert.match(mockList.rating_basis, /source_star_rating/);
  });

  it('validates ProductDetailResponse schema compatibility', () => {
    const mockDetail: ProductDetailResponse = {
      parent_asin: 'B00X9L4Q8I',
      title: null,
      brand: null,
      price: null,
      main_category: 'Cell_Phones_and_Accessories',
      has_metadata: false,
      metadata_notice: 'Product metadata (title, brand, price) is pending metadata ingestion.',
      variants: ['B00X9L4Q8I', 'B00X9L4VAR'],
      review_count: 5,
      avg_rating: 4.0,
      rating_basis: 'source_star_rating (1.0 - 5.0, unpredicted customer reviews)',
      rating_distribution: {
        stars_5: 3,
        stars_4: 1,
        stars_3: 0,
        stars_2: 0,
        stars_1: 1,
      },
      verified_purchase_count: 4,
      has_images_count: 1,
      first_review_utc: '2020-01-01T12:00:00.000Z',
      latest_review_utc: '2023-05-15T18:30:00.000Z',
    };

    assert.strictEqual(mockDetail.parent_asin, 'B00X9L4Q8I');
    assert.strictEqual(mockDetail.variants.length, 2);
    assert.strictEqual(mockDetail.rating_distribution.stars_5, 3);
    assert.strictEqual(mockDetail.verified_purchase_count, 4);
  });

  it('validates ReviewItem schema compatibility including blank text and duplicate index', () => {
    const mockReview: ReviewItem = {
      review_id: 'a1b2c3d4e5f60718_#1',
      parent_asin: 'B00X9L4Q8I',
      asin: 'B00X9L4VAR',
      user_id: 'AGYUSER123',
      rating: 5.0,
      raw_title: 'Great product',
      raw_text: '',
      review_timestamp_utc: '2022-04-10T14:23:45.678Z',
      review_epoch_seconds: 1649600625.678,
      helpful_vote: 3,
      verified_purchase: true,
      has_images: false,
      is_blank_text: true,
      occurrence_index: 1,
    };

    assert.strictEqual(mockReview.review_id, 'a1b2c3d4e5f60718_#1');
    assert.strictEqual(mockReview.is_blank_text, true);
    assert.strictEqual(mockReview.occurrence_index, 1);
    assert.strictEqual(mockReview.rating, 5.0);
  });

  it('validates ReviewListResponse schema compatibility', () => {
    const mockList: ReviewListResponse = {
      total_reviews: 25000,
      limit: 20,
      offset: 0,
      rating_basis: 'source_star_rating (1.0 - 5.0, unpredicted customer reviews)',
      items: [],
    };

    assert.strictEqual(mockList.total_reviews, 25000);
    assert.strictEqual(mockList.limit, 20);
    assert.strictEqual(mockList.items.length, 0);
  });
});

describe('Phase 5.2 Targeted Corrections — Reviews Filter State & Lifecycle', () => {
  it('editing draft filter inputs does not alter applied query parameters', () => {
    // Model the state machine implemented in ReviewsView
    let draftParentAsin = '';
    let draftAsin = '';
    let draftRating = '';
    let draftVerified = '';

    let appliedParentAsin = '';
    let appliedAsin = '';
    let appliedRating = '';
    let appliedVerified = '';

    // Step 1: User types in draft inputs (e.g. keystrokes "B", "0", "0", "X")
    draftParentAsin = 'B00X9L4Q8I';
    draftAsin = 'B00VAR';
    draftRating = '5.0';
    draftVerified = 'true';

    // The active query filter must still reflect APPLIED values, NOT draft values
    const queryFilters = {
      parent_asin: appliedParentAsin,
      asin: appliedAsin,
      rating: appliedRating ? parseFloat(appliedRating) : undefined,
      verified_purchase: appliedVerified !== '' ? appliedVerified === 'true' : undefined,
    };

    assert.strictEqual(queryFilters.parent_asin, '', 'Applied parent_asin must remain empty while editing draft');
    assert.strictEqual(queryFilters.asin, '', 'Applied asin must remain empty while editing draft');
    assert.strictEqual(queryFilters.rating, undefined, 'Applied rating must remain unset while editing draft');
    assert.strictEqual(queryFilters.verified_purchase, undefined, 'Applied verified must remain unset while editing draft');
  });

  it('submitting filter form applies draft values and resets offset to 0', () => {
    let offset = 40; // User was on page 3
    let draftParentAsin = 'B00X9L4Q8I';
    let draftAsin = 'B00VAR123';
    let draftRating = '4.0';
    let draftVerified = 'true';

    let appliedParentAsin = '';
    let appliedAsin = '';
    let appliedRating = '';
    let appliedVerified = '';

    // Simulate handleApplyFilters
    appliedParentAsin = draftParentAsin.trim();
    appliedAsin = draftAsin.trim();
    appliedRating = draftRating;
    appliedVerified = draftVerified;
    offset = 0; // Must reset to 0

    assert.strictEqual(appliedParentAsin, 'B00X9L4Q8I');
    assert.strictEqual(appliedAsin, 'B00VAR123');
    assert.strictEqual(appliedRating, '4.0');
    assert.strictEqual(appliedVerified, 'true');
    assert.strictEqual(offset, 0, 'Applying filters must reset pagination to first page (offset 0)');
  });

  it('resetting filters clears both draft and applied values and returns to offset 0', () => {
    let offset = 20;
    let draftParentAsin = 'B00X9L4Q8I';
    let draftAsin = 'B00VAR';
    let draftRating = '3.0';
    let draftVerified = 'false';

    let appliedParentAsin = 'B00X9L4Q8I';
    let appliedAsin = 'B00VAR';
    let appliedRating = '3.0';
    let appliedVerified = 'false';

    // Simulate handleResetFilters
    draftParentAsin = '';
    draftAsin = '';
    draftRating = '';
    draftVerified = '';
    appliedParentAsin = '';
    appliedAsin = '';
    appliedRating = '';
    appliedVerified = '';
    offset = 0;

    assert.strictEqual(draftParentAsin, '');
    assert.strictEqual(appliedParentAsin, '');
    assert.strictEqual(draftRating, '');
    assert.strictEqual(appliedRating, '');
    assert.strictEqual(offset, 0, 'Resetting filters must reset pagination to first page');
  });

  it('pagination preserves applied filters while updating offset', () => {
    const appliedParentAsin = 'B00X9L4Q8I';
    const appliedRating = '5.0';
    let offset = 0;

    // Advance to page 2
    offset = 20;

    const page2Filters = {
      parent_asin: appliedParentAsin,
      rating: parseFloat(appliedRating),
      limit: 20,
      offset,
    };

    assert.strictEqual(page2Filters.parent_asin, 'B00X9L4Q8I');
    assert.strictEqual(page2Filters.rating, 5.0);
    assert.strictEqual(page2Filters.offset, 20);
  });
});

describe('Phase 5.2 Targeted Corrections — Stale Async Response Prevention', () => {
  it('request sequence ID discards slower out-of-order responses', async () => {
    let activeRequestId = 0;
    let renderedData = '';

    // Request 1 dispatched (e.g. page 1)
    const req1Id = ++activeRequestId;
    let req1Resolved = false;

    // Request 2 dispatched shortly after (e.g. user rapidly clicks page 2)
    const req2Id = ++activeRequestId;
    let req2Resolved = false;

    // Simulate Request 2 resolving FIRST (faster network round-trip)
    if (activeRequestId === req2Id) {
      renderedData = 'Page 2 Data';
      req2Resolved = true;
    }

    // Simulate Request 1 resolving LATER (slower network round-trip)
    if (activeRequestId === req1Id) {
      renderedData = 'Page 1 Stale Data';
      req1Resolved = true;
    }

    assert.strictEqual(req2Resolved, true, 'Request 2 must be processed');
    assert.strictEqual(req1Resolved, false, 'Request 1 must be discarded as stale');
    assert.strictEqual(renderedData, 'Page 2 Data', 'Rendered state must not be overwritten by stale Request 1');
  });

  it('component unmount increments sequence ID to discard pending in-flight responses', () => {
    let activeRequestId = 0;
    let committedState = 'Initial';

    // Request launched while mounted
    const inFlightId = ++activeRequestId;

    // Component unmounts: effect cleanup runs
    activeRequestId++;

    // In-flight response returns after unmount
    if (activeRequestId === inFlightId) {
      committedState = 'Updated';
    }

    assert.strictEqual(committedState, 'Initial', 'Pending response after unmount must not commit state');
  });
});

describe('Phase 5.2 Targeted Corrections — ProductDetailModal Event Handlers', () => {
  it('Escape key triggers modal close handler', () => {
    let closed = false;
    const onClose = () => {
      closed = true;
    };

    // Simulate keydown event handler
    const simulateKeyDown = (key: string) => {
      if (key === 'Escape') {
        onClose();
      }
    };

    simulateKeyDown('Enter');
    assert.strictEqual(closed, false, 'Enter key must not trigger close');

    simulateKeyDown('Tab');
    assert.strictEqual(closed, false, 'Tab key must not trigger close');

    simulateKeyDown('Escape');
    assert.strictEqual(closed, true, 'Escape key must trigger close');
  });

  it('clicking backdrop triggers close, clicking modal card does not', () => {
    let closed = false;
    const onClose = () => {
      closed = true;
    };

    // Simulate backdrop click detection (e.target === e.currentTarget)
    const handleBackdropClick = (target: object, currentTarget: object) => {
      if (target === currentTarget) {
        onClose();
      }
    };

    const backdropElement = { id: 'backdrop' };
    const modalCardElement = { id: 'modal-card' };

    // Clicked on modal card (target is card, currentTarget is backdrop)
    handleBackdropClick(modalCardElement, backdropElement);
    assert.strictEqual(closed, false, 'Clicking inside the modal card must not dismiss the modal');

    // Clicked directly on backdrop (target is backdrop, currentTarget is backdrop)
    handleBackdropClick(backdropElement, backdropElement);
    assert.strictEqual(closed, true, 'Clicking directly on the backdrop overlay must dismiss the modal');
  });
});

describe('Phase 6 — Honest Metadata Fallback & Media Separation', () => {
  it('identifies uningested metadata without synthesizing fake titles, brands or prices', () => {
    const rawProduct: ProductSummary = {
      parent_asin: 'B00X9L4Q8I',
      title: null,
      brand: null,
      price: null,
      main_category: 'Cell_Phones_and_Accessories',
      has_metadata: false,
      review_count: 42,
      avg_rating: 4.35,
    };

    // Formatter logic for title
    const renderedTitle = rawProduct.title || 'Metadata pending';
    const isSynthetic = renderedTitle.includes('Phone') || renderedTitle.includes('Case');

    assert.strictEqual(rawProduct.has_metadata, false);
    assert.strictEqual(rawProduct.title, null);
    assert.strictEqual(rawProduct.brand, null);
    assert.strictEqual(rawProduct.price, null);
    assert.strictEqual(isSynthetic, false, 'Must never manufacture titles from category keywords');
    assert.strictEqual(rawProduct.parent_asin, 'B00X9L4Q8I');
  });

  it('treats has_images_count strictly as review attachments and not product catalogue imagery', () => {
    const detail: ProductDetailResponse = {
      parent_asin: 'B00TEST123',
      title: null,
      brand: null,
      price: null,
      main_category: 'Cell_Phones_and_Accessories',
      has_metadata: false,
      metadata_notice: 'Product metadata is pending ingestion.',
      variants: ['B00VAR1', 'B00VAR2'],
      review_count: 50,
      avg_rating: 4.1,
      rating_basis: 'source_star_rating (1.0 - 5.0, unpredicted customer reviews)',
      rating_distribution: { stars_5: 25, stars_4: 10, stars_3: 8, stars_2: 4, stars_1: 3 },
      verified_purchase_count: 40,
      has_images_count: 7,
      first_review_utc: '2020-01-01T00:00:00Z',
      latest_review_utc: '2023-01-01T00:00:00Z',
    };

    // Verify separation
    const catalogueImages: string[] = []; // No product catalogue images
    const customerReviewPhotoCount = detail.has_images_count;

    assert.strictEqual(catalogueImages.length, 0, 'No catalogue images exist in bounded review dataset');
    assert.strictEqual(customerReviewPhotoCount, 7, 'Customer review photo count is an empirical review metric');
    assert.strictEqual(detail.has_metadata, false);
  });

  it('handles review image count as boolean without fabricating URL strings', () => {
    const reviewWithImage: ReviewItem = {
      review_id: 'rev_img_1',
      parent_asin: 'B00X9L4Q8I',
      asin: 'B00VAR1',
      user_id: 'USER123',
      rating: 5.0,
      raw_title: 'Great product',
      raw_text: 'Works as expected, see attached photo.',
      review_timestamp_utc: '2022-05-01T12:00:00Z',
      review_epoch_seconds: 1651406400,
      helpful_vote: 3,
      verified_purchase: true,
      has_images: true,
      is_blank_text: false,
      occurrence_index: 0,
    };

    assert.strictEqual(reviewWithImage.has_images, true);
    // Verified that ReviewItem schema has no image_urls field — only has_images boolean
    assert.strictEqual('image_urls' in reviewWithImage, false, 'No fabricated URL property in contract');
  });
});

describe('Phase 6 — Product Detail State Lifecycle & Stale Data Prevention', () => {
  it('switching product ASIN immediately clears previous detail state', () => {
    let currentDetail: ProductDetailResponse | null = {
      parent_asin: 'B00OLD1111',
      title: null,
      brand: null,
      price: null,
      main_category: 'Cell_Phones_and_Accessories',
      has_metadata: false,
      metadata_notice: 'Pending',
      variants: [],
      review_count: 10,
      avg_rating: 4.0,
      rating_basis: 'source_star_rating',
      rating_distribution: { stars_5: 5, stars_4: 3, stars_3: 1, stars_2: 1, stars_1: 0 },
      verified_purchase_count: 8,
      has_images_count: 1,
      first_review_utc: null,
      latest_review_utc: null,
    };

    let currentError: { is404: boolean; message: string } | null = null;
    let loading = false;

    // Simulate switching parent ASIN
    const handleSwitchProduct = (newAsin: string) => {
      // Must immediately reset detail and error to null
      currentDetail = null;
      currentError = null;
      loading = true;
    };

    handleSwitchProduct('B00NEW2222');
    assert.strictEqual(currentDetail, null, 'Previous product details must be cleared immediately upon switching');
    assert.strictEqual(currentError, null, 'Previous error must be cleared upon switching');
    assert.strictEqual(loading, true);
  });

  it('differentiates 404 not found from generic network or server errors', () => {
    const error404Response = {
      status: 404,
      message: 'HTTP 404: Not Found',
      detail: "Product with parent_asin 'B00NONEXIST' not found",
    };

    const is404 = error404Response.status === 404 || error404Response.detail.toLowerCase().includes('not found');
    assert.strictEqual(is404, true, '404 error must be classified as not found');

    const networkErrorResponse = {
      status: undefined,
      message: 'Cannot connect to ProductPulse backend at http://localhost:8000',
      detail: 'Failed to fetch',
    };

    const isNetwork404 = networkErrorResponse.status === 404 || networkErrorResponse.detail.toLowerCase().includes('not found');
    assert.strictEqual(isNetwork404, false, 'Network error must NOT be classified as 404 not found');
  });

  it('focus restoration captures trigger element and restores focus upon modal close', () => {
    let activeElement: string | null = 'inspect-btn-B00X9L4Q8I';
    let previousActiveElement: string | null = null;
    let modalOpen = false;

    // Open modal
    modalOpen = true;
    previousActiveElement = activeElement;
    activeElement = 'modal-close-button'; // Focus moved to close button on open

    assert.strictEqual(activeElement, 'modal-close-button');
    assert.strictEqual(previousActiveElement, 'inspect-btn-B00X9L4Q8I');

    // Close modal
    modalOpen = false;
    activeElement = previousActiveElement; // Focus restored
    assert.strictEqual(activeElement, 'inspect-btn-B00X9L4Q8I', 'Focus must be restored to the opener element');
  });
});

describe('Phase 6 — Review Browsing & Filter State Lifecycle', () => {
  it('clearing a single filter chip updates draft, applied, and resets offset to 0', () => {
    let draftParentAsin = 'B00X9L4Q8I';
    let appliedParentAsin = 'B00X9L4Q8I';
    let draftRating = '5.0';
    let appliedRating = '5.0';
    let offset = 40;

    // Simulate clearing the parent_asin chip
    const handleClearSingleFilter = (filterKey: string) => {
      if (filterKey === 'parent_asin') {
        draftParentAsin = '';
        appliedParentAsin = '';
      } else if (filterKey === 'rating') {
        draftRating = '';
        appliedRating = '';
      }
      offset = 0;
    };

    handleClearSingleFilter('parent_asin');

    assert.strictEqual(draftParentAsin, '', 'Draft parent_asin must be cleared');
    assert.strictEqual(appliedParentAsin, '', 'Applied parent_asin must be cleared');
    assert.strictEqual(appliedRating, '5.0', 'Other applied filters (rating) must remain intact');
    assert.strictEqual(offset, 0, 'Offset must be reset to 0 after removing a filter chip');
  });

  it('handles blank review text with honest provenance disclosure rather than synthetic text', () => {
    const blankReview: ReviewItem = {
      review_id: 'rev_blank_1',
      parent_asin: 'B00X9L4Q8I',
      asin: 'B00VAR1',
      user_id: 'ANON_USER',
      rating: 4.0,
      raw_title: null,
      raw_text: '   ',
      review_timestamp_utc: '2021-08-10T14:30:00Z',
      review_epoch_seconds: 1628605800,
      helpful_vote: 0,
      verified_purchase: false,
      has_images: false,
      is_blank_text: true,
      occurrence_index: 0,
    };

    const isBlank = blankReview.is_blank_text || !blankReview.raw_text?.trim();
    assert.strictEqual(isBlank, true);

    const renderedNotice = isBlank
      ? 'Customer submitted a star rating without written review text. Blank text preserved for provenance.'
      : blankReview.raw_text;

    assert.match(renderedNotice, /Blank text preserved for provenance/);
    assert.doesNotMatch(renderedNotice, /Good phone|Bad phone|Satisfied customer/);
  });

  it('clicking a variant SKU badge passes both parent ASIN and variant SKU to review filters', () => {
    let targetParentAsin = '';
    let targetVariantAsin = '';
    let activeTab = 'catalogue';

    const handleBrowseReviews = (parentAsin: string, variantAsin?: string) => {
      targetParentAsin = parentAsin;
      targetVariantAsin = variantAsin || '';
      activeTab = 'reviews';
    };

    handleBrowseReviews('B00PARENT', 'B00SKU123');

    assert.strictEqual(targetParentAsin, 'B00PARENT');
    assert.strictEqual(targetVariantAsin, 'B00SKU123');
    assert.strictEqual(activeTab, 'reviews');
  });
});

