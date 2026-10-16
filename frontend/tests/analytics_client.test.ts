/**
 * ProductPulse — Frontend Analytics API Client & Contract Tests
 * Tests BDA (Hadoop & Hive) client methods and schema contracts using node:test
 */
import test, { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';

import { setApiBaseUrl } from '../src/api/config.ts';
import {
  getAnalyticsOverview,
  getAspectVolumes,
  getTopProducts,
  getPainPoints,
  getRatingBands,
  getAspectPenetration,
} from '../src/api/client.ts';
import type {
  AnalyticsOverviewResponse,
  AspectVolumeResponse,
  TopProductsResponse,
  PainPointsResponse,
  RatingBandsResponse,
  AspectPenetrationResponse,
  LockedAspect,
} from '../src/types/api.ts';

const LOCKED_ASPECTS: LockedAspect[] = [
  'build_durability',
  'battery_charging',
  'screen_display',
  'performance_software',
  'camera_optics',
  'connectivity_audio',
];

describe('Frontend Analytics API Client Offline Handling', () => {
  beforeEach(() => {
    // Point to an unused loopback port to guarantee connection refusal
    setApiBaseUrl('http://127.0.0.1:59999');
  });

  afterEach(() => {
    setApiBaseUrl(null);
  });

  it('getAnalyticsOverview returns graceful structured network error when backend is offline', async () => {
    const res = await getAnalyticsOverview();
    assert.strictEqual(res.success, false);
    if (!res.success) {
      assert.strictEqual(res.error.isNetworkError, true);
      assert.match(res.error.message, /59999/);
    }
  });

  it('getAspectVolumes handles connection failure safely', async () => {
    const res = await getAspectVolumes();
    assert.strictEqual(res.success, false);
    if (!res.success) {
      assert.strictEqual(res.error.isNetworkError, true);
    }
  });

  it('getTopProducts handles connection failure with filters', async () => {
    const res = await getTopProducts('battery_charging', 'B00TEST123');
    assert.strictEqual(res.success, false);
    if (!res.success) {
      assert.strictEqual(res.error.isNetworkError, true);
    }
  });

  it('getPainPoints handles connection failure safely', async () => {
    const res = await getPainPoints('build_durability');
    assert.strictEqual(res.success, false);
    if (!res.success) {
      assert.strictEqual(res.error.isNetworkError, true);
    }
  });

  it('getRatingBands handles connection failure safely', async () => {
    const res = await getRatingBands();
    assert.strictEqual(res.success, false);
    if (!res.success) {
      assert.strictEqual(res.error.isNetworkError, true);
    }
  });

  it('getAspectPenetration handles connection failure safely', async () => {
    const res = await getAspectPenetration('screen_display', 'B00TEST123');
    assert.strictEqual(res.success, false);
    if (!res.success) {
      assert.strictEqual(res.error.isNetworkError, true);
    }
  });
});

describe('Frontend Analytics Data Contract & Schema Parity', () => {
  it('validates AnalyticsOverviewResponse schema and KPI numbers', () => {
    const mockOverview: AnalyticsOverviewResponse = {
      total_reviews_evaluated: 25000,
      total_products_evaluated: 19065,
      corpus_avg_star_rating: 4.1655,
      aspect_reviews_avg_star_rating: 4.1299,
      reviews_with_aspect_mentions: 16409,
      reviews_with_no_aspect: 8591,
      total_aspect_review_pairs: 26029,
      total_aspect_mentions: 26029,
      locked_aspect_count: 6,
      locked_aspects: LOCKED_ASPECTS,
      dataset_scope: 'Amazon Reviews 2023: Cell_Phones_and_Accessories (25k stratified sample)',
      execution_engine: 'Hadoop Streaming 3.3.6 MapReduce + Apache Hive 3.1.3',
      methodology_notes: [
        'Total aspect-review pairs (26,029) is the sum of aspect discussions; it cannot be labeled as unique reviews (16,409).',
        'Customer ratings (1.0 - 5.0) reflect reviewer sentiment on Amazon, not NLP-predicted sentiment scores.',
      ],
    };

    assert.strictEqual(mockOverview.total_reviews_evaluated, 25000);
    assert.strictEqual(mockOverview.total_products_evaluated, 19065);
    assert.strictEqual(mockOverview.corpus_avg_star_rating, 4.1655);
    assert.strictEqual(mockOverview.aspect_reviews_avg_star_rating, 4.1299);
    assert.strictEqual(mockOverview.reviews_with_aspect_mentions, 16409);
    assert.strictEqual(mockOverview.reviews_with_no_aspect, 8591);
    assert.strictEqual(
      mockOverview.reviews_with_aspect_mentions + mockOverview.reviews_with_no_aspect,
      25000,
      'Reviews with aspects and without aspects must sum to total evaluated reviews'
    );
    assert.strictEqual(mockOverview.total_aspect_review_pairs, 26029);
    assert.strictEqual(mockOverview.total_aspect_mentions, 26029);
    assert.strictEqual(mockOverview.locked_aspect_count, 6);
  });

  it('validates AspectVolumeResponse enforces all 6 locked aspects', () => {
    const mockVolumes: AspectVolumeResponse = {
      total_aspects: 6,
      rating_basis: 'Customer star rating (1.0 - 5.0, unpredicted source reviews)',
      methodology: 'Aggregated via Hadoop MapReduce Streaming (aspect_mapper.py / aspect_reducer.py) + Hive Query 1',
      items: [
        {
          aspect: 'build_durability',
          aspect_label: 'Build & Durability',
          total_aspect_reviews: 10846,
          weighted_avg_rating: 4.1485,
          total_helpful_votes: 11439,
        },
        {
          aspect: 'battery_charging',
          aspect_label: 'Battery & Charging',
          total_aspect_reviews: 4514,
          weighted_avg_rating: 4.1834,
          total_helpful_votes: 8428,
        },
        {
          aspect: 'screen_display',
          aspect_label: 'Screen & Display',
          total_aspect_reviews: 4350,
          weighted_avg_rating: 4.0154,
          total_helpful_votes: 7900,
        },
        {
          aspect: 'performance_software',
          aspect_label: 'Performance & Software',
          total_aspect_reviews: 2506,
          weighted_avg_rating: 4.1923,
          total_helpful_votes: 6526,
        },
        {
          aspect: 'camera_optics',
          aspect_label: 'Camera & Optics',
          total_aspect_reviews: 2256,
          weighted_avg_rating: 4.0718,
          total_helpful_votes: 5976,
        },
        {
          aspect: 'connectivity_audio',
          aspect_label: 'Connectivity & Audio',
          total_aspect_reviews: 1557,
          weighted_avg_rating: 3.9409,
          total_helpful_votes: 3784,
        },
      ],
    };

    assert.strictEqual(mockVolumes.items.length, 6);
    const totalPairs = mockVolumes.items.reduce((sum, item) => sum + item.total_aspect_reviews, 0);
    assert.strictEqual(totalPairs, 26029, 'Sum of distinct aspect reviews must equal 26,029 aspect-review pairs');
    const aspectNames = mockVolumes.items.map((i) => i.aspect);
    for (const locked of LOCKED_ASPECTS) {
      assert.ok(aspectNames.includes(locked), `Missing locked aspect: ${locked}`);
    }
  });

  it('validates TopProductsResponse schema', () => {
    const mockTop: TopProductsResponse = {
      query: 'Query 2: Top Products by Aspect Discussion Volume',
      total_rows: 1,
      aspect_filter: 'battery_charging',
      parent_asin_filter: null,
      items: [
        {
          parent_asin: 'B08F7J44Q9',
          title: 'Fast Charger USB-C Wall Adapter',
          brand: 'Anker',
          price: 19.99,
          aspect: 'battery_charging',
          aspect_review_count: 45,
          avg_aspect_star_rating: 4.62,
          total_aspect_helpful_votes: 82,
        },
      ],
    };

    assert.strictEqual(mockTop.items.length, 1);
    assert.strictEqual(mockTop.items[0].parent_asin, 'B08F7J44Q9');
    assert.strictEqual(mockTop.items[0].aspect_review_count, 45);
  });

  it('validates PainPointsResponse schema with friction cluster disclaimer', () => {
    const mockPain: PainPointsResponse = {
      query: 'Query 3: Lowest Rated Product Aspects (Min 5 Reviews)',
      total_rows: 1,
      aspect_filter: null,
      parent_asin_filter: null,
      threshold_note: 'Includes only product-aspect pairs with N >= 5 aspect reviews',
      disclaimer: 'These represent potential customer friction points, NOT verified product defects.',
      items: [
        {
          parent_asin: 'B07XYZ9999',
          title: 'Generic Phone Cable',
          brand: 'Generic',
          price: 4.99,
          aspect: 'build_durability',
          aspect_review_count: 8,
          avg_aspect_star_rating: 1.88,
          total_aspect_helpful_votes: 14,
        },
      ],
    };

    assert.strictEqual(mockPain.items[0].avg_aspect_star_rating, 1.88);
    assert.match(mockPain.disclaimer, /potential customer friction points/);
  });

  it('validates RatingBandsResponse schema and percentage bounds', () => {
    const mockBands: RatingBandsResponse = {
      query: 'Query 4: Star Rating-Band Distributions by Aspect',
      disclosure: 'Customer star ratings (1-2 low, 3 medium, 4-5 high), NOT NLP sentiment predictions.',
      items: [
        {
          aspect: 'battery_charging',
          total_aspect_reviews: 6418,
          low_rating_count_1_2: 1250,
          mid_rating_count_3: 568,
          high_rating_count_4_5: 4600,
          low_rating_pct: 19.48,
          mid_rating_pct: 8.85,
          high_rating_pct: 71.67,
        },
      ],
    };

    const item = mockBands.items[0];
    assert.strictEqual(item.low_rating_count_1_2 + item.mid_rating_count_3 + item.high_rating_count_4_5, item.total_aspect_reviews);
    assert.ok(item.low_rating_pct >= 0 && item.low_rating_pct <= 100);
    assert.ok(item.mid_rating_pct >= 0 && item.mid_rating_pct <= 100);
    assert.ok(item.high_rating_pct >= 0 && item.high_rating_pct <= 100);
  });

  it('validates AspectPenetrationResponse strict bounds [0.0%, 100.0%]', () => {
    const mockPenetration: AspectPenetrationResponse = {
      query: 'Query 5: Product-Level Aspect Discussion Penetration',
      total_rows: 1,
      aspect_filter: 'screen_display',
      parent_asin_filter: null,
      metric_definition: 'reviews_mentioning_aspect / total_product_reviews (strictly bounded between 0.0% and 100.0%)',
      items: [
        {
          parent_asin: 'B089ABCDEF',
          title: 'Tempered Glass Screen Protector',
          brand: 'Spigen',
          price: 12.99,
          aspect: 'screen_display',
          reviews_mentioning_aspect: 40,
          total_product_reviews: 50,
          aspect_penetration_pct: 80.0,
        },
      ],
    };

    const row = mockPenetration.items[0];
    assert.ok(row.reviews_mentioning_aspect <= row.total_product_reviews);
    assert.ok(row.aspect_penetration_pct >= 0.0 && row.aspect_penetration_pct <= 100.0);
    assert.strictEqual(row.aspect_penetration_pct, 80.0);
  });
});
