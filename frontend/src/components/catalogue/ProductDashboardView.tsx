import React, { useEffect, useState, useCallback } from 'react';
import { getProductDetail, getReviews } from '../../api/client.ts';
import type { ProductDetailResponse, ReviewListResponse } from '../../types/api.ts';
import { StarRating } from '../common/StarRating.tsx';
import { StatusBadge } from '../common/StatusBadge.tsx';
import { Pagination } from '../common/Pagination.tsx';
import { ProductRatingTrendChart, type RatingPoint } from './ProductRatingTrendChart.tsx';

interface ProductDashboardViewProps {
  parentAsin: string;
  onBack: () => void;
  onSelectProductForReviews: (parentAsin: string, variantAsin?: string) => void;
}

export const ProductDashboardView: React.FC<ProductDashboardViewProps> = ({
  parentAsin,
  onBack,
  onSelectProductForReviews,
}) => {
  const [detail, setDetail] = useState<ProductDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(true);
  const [detailError, setDetailError] = useState<string | null>(null);

  // Reviews state for Section D
  const [reviewsData, setReviewsData] = useState<ReviewListResponse | null>(null);
  const [reviewsLoading, setReviewsLoading] = useState(false);
  const [reviewsOffset, setReviewsOffset] = useState(0);
  const reviewsLimit = 5;

  // Rating timeline state for the trend chart
  const [trendData, setTrendData] = useState<RatingPoint[]>([]);
  const [trendLoading, setTrendLoading] = useState(false);

  const fetchDetail = useCallback(async () => {
    setDetailLoading(true);
    setDetailError(null);
    const res = await getProductDetail(parentAsin);
    setDetailLoading(false);
    if (res.success) {
      setDetail(res.data);
    } else {
      setDetailError(res.error.message || 'Failed to load product details');
    }
  }, [parentAsin]);

  const fetchReviews = useCallback(async (offset: number) => {
    setReviewsLoading(true);
    const res = await getReviews({
      parent_asin: parentAsin,
      limit: reviewsLimit,
      offset,
    });
    setReviewsLoading(false);
    if (res.success) {
      setReviewsData(res.data);
    }
  }, [parentAsin]);

  const fetchTrend = useCallback(async () => {
    setTrendLoading(true);
    // Fetch up to 100 actual reviews for this parent ASIN to compute real timeline data points
    const res = await getReviews({
      parent_asin: parentAsin,
      limit: 100,
      offset: 0,
    });
    setTrendLoading(false);

    if (res.success && res.data.items && res.data.items.length > 0) {
      const monthMap = new Map<string, { sum: number; count: number }>();

      res.data.items.forEach((rev) => {
        if (!rev.review_timestamp_utc) return;
        const ym = rev.review_timestamp_utc.slice(0, 7); // e.g. "2021-03"
        const existing = monthMap.get(ym) || { sum: 0, count: 0 };
        existing.sum += rev.rating;
        existing.count += 1;
        monthMap.set(ym, existing);
      });

      const sortedPeriods = Array.from(monthMap.keys()).sort();
      const points: RatingPoint[] = sortedPeriods.map((ym) => {
        const item = monthMap.get(ym)!;
        const [year, month] = ym.split('-');
        const dateObj = new Date(parseInt(year, 10), parseInt(month, 10) - 1, 1);
        const label = dateObj.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });

        return {
          period: ym,
          label,
          avgRating: Math.round((item.sum / item.count) * 100) / 100,
          reviewCount: item.count,
        };
      });

      setTrendData(points);
    } else {
      setTrendData([]);
    }
  }, [parentAsin]);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    fetchDetail();
    setReviewsOffset(0);
    fetchReviews(0);
    fetchTrend();
  }, [fetchDetail, fetchReviews, fetchTrend]);

  const handleReviewsPageChange = (newOffset: number) => {
    setReviewsOffset(newOffset);
    fetchReviews(newOffset);
  };

  const formatDate = (isoString: string | null) => {
    if (!isoString) return '—';
    try {
      return new Date(isoString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn pb-12">
      {/* Top Navigation & Breadcrumbs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onBack}
            className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 hover:text-slate-900 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400"
            aria-label="Return to product catalogue"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Products Catalogue
          </button>
          <div className="hidden sm:flex items-center text-xs text-slate-400 gap-2">
            <span>/</span>
            <span className="font-mono text-slate-600">{parentAsin}</span>
          </div>
        </div>

        <button
          type="button"
          onClick={() => onSelectProductForReviews(parentAsin)}
          className="inline-flex items-center justify-center gap-2 px-3.5 py-1.5 text-xs font-semibold text-brand-700 bg-brand-50 hover:bg-brand-100 border border-brand-200 rounded-lg transition-colors"
        >
          <span>Browse in Review Explorer</span>
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
          </svg>
        </button>
      </div>

      {/* Loading State */}
      {detailLoading && (
        <div className="bg-white border border-slate-200 rounded-xl p-16 flex flex-col items-center justify-center text-slate-500 shadow-sm">
          <div className="w-10 h-10 border-4 border-brand-600 border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-sm font-medium text-slate-700">Loading Product Analytics...</p>
          <p className="text-xs text-slate-400 mt-1">Fetching metadata and aspect metrics for {parentAsin}</p>
        </div>
      )}

      {/* Error State */}
      {!detailLoading && detailError && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-8 text-center max-w-xl mx-auto space-y-3">
          <div className="w-10 h-10 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto text-lg font-bold">!</div>
          <h3 className="text-sm font-semibold text-red-900">Unable to Load Product</h3>
          <p className="text-xs text-red-700">{detailError}</p>
          <button
            type="button"
            onClick={fetchDetail}
            className="mt-2 px-3.5 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-medium rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loaded Content */}
      {!detailLoading && detail && (
        <>
          {/* ========================================================= */}
          {/* Section A: Product Overview & Core KPIs */}
          {/* ========================================================= */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-6">
            <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6 pb-6 border-b border-slate-100">
              <div className="space-y-2 max-w-3xl">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-700 bg-slate-100 border border-slate-200 px-2.5 py-1 rounded">
                    ASIN: {detail.parent_asin}
                  </span>
                  <span className="text-xs font-medium text-slate-600 bg-slate-50 border border-slate-200 px-2.5 py-1 rounded">
                    Category: {detail.main_category}
                  </span>
                  {detail.brand && (
                    <span className="text-xs font-medium text-brand-800 bg-brand-50 border border-brand-200 px-2.5 py-1 rounded">
                      Brand: {detail.brand}
                    </span>
                  )}
                  {detail.has_metadata && (
                    <StatusBadge
                      label="Catalog Metadata Available"
                      variant="success"
                      size="sm"
                    />
                  )}
                </div>

                <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
                  {detail.title ? (
                    detail.title
                  ) : (
                    <span className="font-mono text-slate-900">{detail.parent_asin || 'ASIN unavailable'}</span>
                  )}
                </h1>
              </div>

              <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 lg:w-72 shrink-0 space-y-2">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block">
                  Customer Star Rating
                </span>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-amber-600">
                    {detail.avg_rating !== null ? detail.avg_rating.toFixed(2) : '—'}
                  </span>
                  <span className="text-sm font-medium text-slate-500">/ 5.0</span>
                </div>
                <div>
                  <StarRating rating={detail.avg_rating} size="md" showLabel={false} />
                </div>
                <span className="text-[11px] text-slate-500 block pt-1 border-t border-slate-200/60">
                  Based on {detail.review_count.toLocaleString()} genuine reviews
                </span>
              </div>
            </div>

            {/* KPI Stat Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-slate-50 border border-slate-200/80 rounded-lg p-3.5">
                <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block">Total Reviews</span>
                <span className="text-xl font-bold text-slate-900 mt-1 block">
                  {detail.review_count.toLocaleString()}
                </span>
                <span className="text-[11px] text-slate-500 mt-0.5 block">Customer evaluations</span>
              </div>

              <div className="bg-slate-50 border border-slate-200/80 rounded-lg p-3.5">
                <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block">Helpful Votes</span>
                <span className="text-xl font-bold text-slate-900 mt-1 block">
                  {(detail.total_helpful_votes || 0).toLocaleString()}
                </span>
                <span className="text-[11px] text-slate-500 mt-0.5 block">Community feedback</span>
              </div>

              <div className="bg-slate-50 border border-slate-200/80 rounded-lg p-3.5">
                <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block">Verified Purchases</span>
                <span className="text-xl font-bold text-slate-900 mt-1 block">
                  {detail.verified_purchase_count.toLocaleString()}
                </span>
                <span className="text-[11px] text-slate-500 mt-0.5 block">
                  {detail.review_count > 0
                    ? `${((detail.verified_purchase_count / detail.review_count) * 100).toFixed(1)}% verified`
                    : '—'}
                </span>
              </div>

              <div className="bg-slate-50 border border-slate-200/80 rounded-lg p-3.5">
                <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block">Variant SKUs</span>
                <span className="text-xl font-bold text-slate-900 mt-1 block">
                  {detail.variants.length}
                </span>
                <span className="text-[11px] text-slate-500 mt-0.5 block">Colors / configurations</span>
              </div>
            </div>

            {/* Variant ASINs if present */}
            {detail.variants.length > 0 && (
              <div className="pt-2">
                <span className="text-xs font-semibold text-slate-700 block mb-2">Associated Child SKUs:</span>
                <div className="flex flex-wrap gap-1.5">
                  {detail.variants.map((v) => (
                    <button
                      key={v}
                      type="button"
                      onClick={() => onSelectProductForReviews(detail.parent_asin, v)}
                      className="px-2 py-0.5 text-xs font-mono bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 rounded transition-colors"
                      title={`Filter reviews for SKU ${v}`}
                    >
                      {v}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Customer Rating Trend Over Time Chart or Distribution */}
            <div className="pt-2">
              <ProductRatingTrendChart
                trendData={trendData}
                ratingDistribution={detail.rating_distribution}
                totalReviews={detail.review_count}
                loading={trendLoading}
              />
            </div>
          </div>

          {/* ========================================================= */}
          {/* Section B: Rating Distribution & Review Activity */}
          {/* ========================================================= */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Rating Breakdown 1★ - 5★ */}
            <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div>
                  <h2 className="text-base font-bold text-slate-900">Customer Star Rating Distribution</h2>
                  <p className="text-xs text-slate-500 mt-0.5">Empirical breakdown of 1★ to 5★ customer reviews</p>
                </div>
                <span className="text-xs font-mono text-slate-500">
                  {detail.review_count.toLocaleString()} Total
                </span>
              </div>

              <div className="space-y-3 pt-1">
                {[5, 4, 3, 2, 1].map((stars) => {
                  const key = `stars_${stars}` as keyof typeof detail.rating_distribution;
                  const count = detail.rating_distribution[key] || 0;
                  const percentage = detail.review_count > 0 ? (count / detail.review_count) * 100 : 0;

                  return (
                    <div key={stars} className="flex items-center gap-3 text-xs">
                      <span className="w-14 font-semibold text-slate-700 flex items-center gap-1">
                        {stars} <span className="text-amber-500">★</span>
                      </span>
                      <div className="flex-1 bg-slate-100 h-3 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            stars >= 4 ? 'bg-emerald-500' : stars === 3 ? 'bg-amber-400' : 'bg-rose-500'
                          }`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                      <div className="w-24 text-right font-mono text-slate-600">
                        <span>{count.toLocaleString()}</span>
                        <span className="text-slate-400 ml-1.5">({percentage.toFixed(1)}%)</span>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                <span>Disposition Baseline: Source unpredicted customer ratings</span>
                <span>Scale: 1.0 (Lowest) to 5.0 (Highest)</span>
              </div>
            </div>

            {/* Review Activity & Metadata Details */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
              <h2 className="text-base font-bold text-slate-900 pb-3 border-b border-slate-100">
                Review Provenance
              </h2>

              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-slate-500 block">First Review Recorded</span>
                  <span className="font-semibold text-slate-800 font-mono mt-0.5 block">
                    {formatDate(detail.first_review_utc)}
                  </span>
                </div>

                <div>
                  <span className="text-slate-500 block">Latest Review Recorded</span>
                  <span className="font-semibold text-slate-800 font-mono mt-0.5 block">
                    {formatDate(detail.latest_review_utc)}
                  </span>
                </div>

                <div>
                  <span className="text-slate-500 block">Customer Media Attachments</span>
                  <span className="font-semibold text-slate-800 mt-0.5 block">
                    {detail.has_images_count} reviews with user photos
                  </span>
                  <span className="text-[11px] text-slate-400 block mt-0.5">
                    User review photos, not official catalog photography
                  </span>
                </div>

                <div>
                  <span className="text-slate-500 block">Primary Database Table</span>
                  <span className="font-mono text-slate-700 bg-slate-50 px-2 py-0.5 rounded border border-slate-200 inline-block mt-0.5 text-[11px]">
                    products + reviews
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* ========================================================= */}
          {/* Section C: Aspect Analytics (Authentic Hadoop MapReduce) */}
          {/* ========================================================= */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-brand-50 text-brand-700 border border-brand-200">
                    Aspect Intelligence
                  </span>
                  <span className="text-xs text-slate-500 font-mono">
                    Hadoop MapReduce 3.3.6
                  </span>
                </div>
                <h2 className="text-lg font-bold text-slate-900">
                  Individual Aspect Analytics
                </h2>
                <p className="text-xs text-slate-600 mt-0.5">
                  Empirical sentiment and discussion volume aggregated for this product across the 6 locked mobile taxonomy aspects.
                </p>
              </div>

              <span className="text-xs font-mono text-slate-500 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 shrink-0">
                Aspect Discussions: {detail.aspect_metrics?.length || 0} / 6
              </span>
            </div>

            {detail.aspect_metrics && detail.aspect_metrics.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {detail.aspect_metrics.map((asp) => {
                  const totalAspectReviews = asp.review_count;
                  const penetrationPct = detail.review_count > 0
                    ? ((totalAspectReviews / detail.review_count) * 100).toFixed(1)
                    : '0';

                  const highPct = totalAspectReviews > 0 ? (asp.high_rating_count / totalAspectReviews) * 100 : 0;
                  const medPct = totalAspectReviews > 0 ? (asp.med_rating_count / totalAspectReviews) * 100 : 0;
                  const lowPct = totalAspectReviews > 0 ? (asp.low_rating_count / totalAspectReviews) * 100 : 0;

                  return (
                    <div
                      key={asp.aspect}
                      className="bg-slate-50 border border-slate-200/90 rounded-xl p-4 space-y-3.5 hover:border-brand-300 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h3 className="text-sm font-bold text-slate-900">
                            {asp.aspect_label}
                          </h3>
                          <span className="text-[11px] font-mono text-slate-400 block mt-0.5">
                            {asp.aspect}
                          </span>
                        </div>
                        <span className="text-xs font-extrabold text-amber-600 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded">
                          {asp.avg_rating.toFixed(2)} ★
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-xs bg-white p-2.5 rounded-lg border border-slate-200/60">
                        <div>
                          <span className="text-[10px] uppercase text-slate-400 font-semibold block">Mentions</span>
                          <span className="font-bold text-slate-800 font-mono">{asp.review_count.toLocaleString()}</span>
                          <span className="text-[10px] text-slate-500 block">({penetrationPct}% of reviews)</span>
                        </div>
                        <div>
                          <span className="text-[10px] uppercase text-slate-400 font-semibold block">Helpful Votes</span>
                          <span className="font-bold text-slate-800 font-mono">{asp.total_helpful_votes.toLocaleString()}</span>
                          <span className="text-[10px] text-slate-500 block">votes cast</span>
                        </div>
                      </div>

                      {/* Stacked Sentiment / Rating Band Bar */}
                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between text-[11px] text-slate-500">
                          <span>Rating Band Breakdown</span>
                          <span>{totalAspectReviews} reviews</span>
                        </div>
                        <div className="w-full h-2.5 bg-slate-200 rounded-full overflow-hidden flex">
                          <div
                            className="bg-emerald-500 h-full"
                            style={{ width: `${highPct}%` }}
                            title={`High (4-5★): ${asp.high_rating_count} reviews (${highPct.toFixed(1)}%)`}
                          />
                          <div
                            className="bg-amber-400 h-full"
                            style={{ width: `${medPct}%` }}
                            title={`Medium (3★): ${asp.med_rating_count} reviews (${medPct.toFixed(1)}%)`}
                          />
                          <div
                            className="bg-rose-500 h-full"
                            style={{ width: `${lowPct}%` }}
                            title={`Low / Friction (1-2★): ${asp.low_rating_count} reviews (${lowPct.toFixed(1)}%)`}
                          />
                        </div>
                        <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-0.5">
                          <span className="text-emerald-700 font-semibold">{asp.high_rating_count} Pos</span>
                          <span className="text-amber-700 font-semibold">{asp.med_rating_count} Med</span>
                          <span className="text-rose-700 font-semibold">{asp.low_rating_count} Neg</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-8 text-center space-y-2">
                <svg className="w-8 h-8 text-slate-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h4 className="text-sm font-semibold text-slate-800">
                  No aspect discussions detected in sample reviews for this product
                </h4>
                <p className="text-xs text-slate-500 max-w-md mx-auto">
                  None of the 6 locked aspect keyword sets (Battery, Camera, Display, Performance, Build, Audio) appeared in the sampled customer reviews for this specific product ASIN.
                </p>
              </div>
            )}

            <div className="bg-blue-50/70 border border-blue-200/70 rounded-lg p-3 text-xs text-blue-800 flex items-start gap-2.5">
              <svg className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <strong>Aspect Sentiment Provenance:</strong> Aspect ratings reflect the average star ratings of reviews containing explicit aspect keyword mentions extracted by genuine Hadoop MapReduce batch jobs.
              </div>
            </div>
          </div>

          {/* ========================================================= */}
          {/* Section D: Customer Reviews for this Product */}
          {/* ========================================================= */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
              <div>
                <h2 className="text-lg font-bold text-slate-900">
                  Customer Reviews for this Product
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Direct customer opinions and submissions for ASIN <span className="font-mono font-semibold">{detail.parent_asin}</span>
                </p>
              </div>

              <button
                type="button"
                onClick={() => onSelectProductForReviews(detail.parent_asin)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-brand-700 bg-brand-50 hover:bg-brand-100 border border-brand-200 rounded-lg transition-colors shrink-0"
              >
                <span>Filter all reviews in Explorer</span>
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>

            {reviewsLoading && (
              <div className="py-12 flex flex-col items-center justify-center text-slate-400">
                <div className="w-6 h-6 border-2 border-brand-600 border-t-transparent rounded-full animate-spin mb-2" />
                <span className="text-xs">Fetching reviews...</span>
              </div>
            )}

            {!reviewsLoading && reviewsData && reviewsData.items.length === 0 && (
              <div className="py-8 text-center text-slate-500 text-xs">
                No reviews found for this product.
              </div>
            )}

            {!reviewsLoading && reviewsData && reviewsData.items.length > 0 && (
              <div className="space-y-4">
                {reviewsData.items.map((rev) => (
                  <div
                    key={`${rev.review_id}-${rev.occurrence_index}`}
                    className="bg-slate-50 border border-slate-200/80 rounded-xl p-4.5 space-y-2.5"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <StarRating rating={rev.rating} size="sm" />
                        {rev.verified_purchase && (
                          <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
                            Verified Purchase
                          </span>
                        )}
                        {rev.asin !== rev.parent_asin && (
                          <span className="text-[10px] font-mono text-slate-600 bg-slate-200/60 px-1.5 py-0.5 rounded">
                            Variant: {rev.asin}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-3 text-xs text-slate-500">
                        <span>{formatDate(rev.review_timestamp_utc)}</span>
                        {rev.helpful_vote > 0 && (
                          <span className="font-semibold text-slate-700 bg-white border border-slate-200 px-2 py-0.5 rounded text-[11px]">
                            {rev.helpful_vote} helpful {rev.helpful_vote === 1 ? 'vote' : 'votes'}
                          </span>
                        )}
                      </div>
                    </div>

                    {rev.raw_title && (
                      <h4 className="text-sm font-semibold text-slate-900">
                        {rev.raw_title}
                      </h4>
                    )}

                    {rev.raw_text ? (
                      <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-line">
                        {rev.raw_text}
                      </p>
                    ) : (
                      <p className="text-xs text-slate-400 italic">
                        No customer review text provided (rating-only submission).
                      </p>
                    )}

                    <div className="flex items-center justify-between pt-1 text-[11px] text-slate-400 font-mono">
                      <span>User ID: {rev.user_id.slice(0, 14)}...</span>
                      <span>Review ID: {rev.review_id.slice(0, 16)}...</span>
                    </div>
                  </div>
                ))}

                {/* Reviews Pagination */}
                <div className="pt-2">
                  <Pagination
                    totalItems={reviewsData.total_reviews}
                    limit={reviewsLimit}
                    offset={reviewsOffset}
                    onPageChange={handleReviewsPageChange}
                    itemName="reviews"
                  />
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};
