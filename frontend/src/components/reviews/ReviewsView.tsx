import React, { useEffect, useState, useRef } from 'react';
import { getReviews } from '../../api/client.ts';
import type { ReviewItem, ReviewListResponse, ReviewFilters } from '../../types/api.ts';
import { StarRating } from '../common/StarRating.tsx';
import { StatusBadge } from '../common/StatusBadge.tsx';
import { Pagination } from '../common/Pagination.tsx';
import { OfflineBanner } from '../common/OfflineBanner.tsx';

interface ReviewsViewProps {
  initialParentAsin?: string;
  initialAsin?: string;
  onClearInitialFilter?: () => void;
}

export const ReviewsView: React.FC<ReviewsViewProps> = ({
  initialParentAsin,
  initialAsin,
  onClearInitialFilter,
}) => {
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [totalReviews, setTotalReviews] = useState(0);
  const [limit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [ratingBasis, setRatingBasis] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<{ isNetworkError: boolean; message: string; detail?: string } | null>(null);
  const [fetchTrigger, setFetchTrigger] = useState(0);

  // Draft filter input states (typing/selecting in inputs updates draft only)
  const [draftParentAsin, setDraftParentAsin] = useState<string>(initialParentAsin || '');
  const [draftAsin, setDraftAsin] = useState<string>(initialAsin || '');
  const [draftRating, setDraftRating] = useState<string>('');
  const [draftVerified, setDraftVerified] = useState<string>('');

  // Applied filter states (used for API query execution)
  const [appliedParentAsin, setAppliedParentAsin] = useState<string>(initialParentAsin || '');
  const [appliedAsin, setAppliedAsin] = useState<string>(initialAsin || '');
  const [appliedRating, setAppliedRating] = useState<string>('');
  const [appliedVerified, setAppliedVerified] = useState<string>('');

  // Request sequence ID to safely discard stale out-of-order responses
  const activeRequestIdRef = useRef(0);

  // Sync draft and applied when initialParentAsin or initialAsin prop changes from parent
  useEffect(() => {
    const parentVal = initialParentAsin || '';
    const asinVal = initialAsin || '';
    setDraftParentAsin(parentVal);
    setAppliedParentAsin(parentVal);
    setDraftAsin(asinVal);
    setAppliedAsin(asinVal);
    setOffset(0);
  }, [initialParentAsin, initialAsin]);

  // Fetch reviews using APPLIED filters only
  useEffect(() => {
    const requestId = ++activeRequestIdRef.current;
    setLoading(true);
    setError(null);

    const activeFilters: ReviewFilters = {
      limit,
      offset,
    };

    if (appliedParentAsin.trim()) {
      activeFilters.parent_asin = appliedParentAsin.trim();
    }
    if (appliedAsin.trim()) {
      activeFilters.asin = appliedAsin.trim();
    }
    if (appliedRating) {
      const parsedRating = parseFloat(appliedRating);
      if (!isNaN(parsedRating)) {
        activeFilters.rating = parsedRating;
      }
    }
    if (appliedVerified !== '') {
      activeFilters.verified_purchase = appliedVerified === 'true';
    }

    getReviews(activeFilters).then((res) => {
      // Discard stale out-of-order response if a newer request was dispatched
      if (activeRequestIdRef.current !== requestId) {
        return;
      }
      setLoading(false);
      if (res.success) {
        const data: ReviewListResponse = res.data;
        setReviews(data.items);
        setTotalReviews(data.total_reviews);
        setRatingBasis(data.rating_basis);
      } else {
        setError(res.error);
      }
    });

    return () => {
      // Invalidate active request on unmount or before next effect run
      activeRequestIdRef.current++;
    };
  }, [limit, offset, appliedParentAsin, appliedAsin, appliedRating, appliedVerified, fetchTrigger]);

  const handleApplyFilters = (e: React.FormEvent) => {
    e.preventDefault();
    setAppliedParentAsin(draftParentAsin.trim());
    setAppliedAsin(draftAsin.trim());
    setAppliedRating(draftRating);
    setAppliedVerified(draftVerified);
    setOffset(0);
  };

  const handleResetFilters = () => {
    setDraftParentAsin('');
    setDraftAsin('');
    setDraftRating('');
    setDraftVerified('');
    setAppliedParentAsin('');
    setAppliedAsin('');
    setAppliedRating('');
    setAppliedVerified('');
    setOffset(0);
    if (onClearInitialFilter) {
      onClearInitialFilter();
    }
  };

  const handleClearSingleFilter = (filterKey: 'parent_asin' | 'asin' | 'rating' | 'verified') => {
    if (filterKey === 'parent_asin') {
      setDraftParentAsin('');
      setAppliedParentAsin('');
      if (onClearInitialFilter) onClearInitialFilter();
    } else if (filterKey === 'asin') {
      setDraftAsin('');
      setAppliedAsin('');
    } else if (filterKey === 'rating') {
      setDraftRating('');
      setAppliedRating('');
    } else if (filterKey === 'verified') {
      setDraftVerified('');
      setAppliedVerified('');
    }
    setOffset(0);
  };

  const hasActiveFilters = Boolean(
    appliedParentAsin || appliedAsin || appliedRating || appliedVerified !== ''
  );

  return (
    <div className="space-y-6">
      {/* View Header */}
      <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <span className="text-xs font-mono font-semibold uppercase tracking-wider text-brand-700 bg-brand-50 border border-brand-200 px-2 py-0.5 rounded">
                Genuine Review Corpus
              </span>
              <span className="text-xs font-mono text-slate-500">
                Cell_Phones_and_Accessories
              </span>
              <span className="text-[11px] text-slate-400 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded font-mono">
                Sort: Epoch Recency (Desc) &rarr; Review ID (Asc)
              </span>
            </div>
            <h2 className="text-xl font-bold text-slate-900">Review Explorer</h2>
            <p className="text-xs text-slate-600 mt-1 max-w-2xl">
              Browse authentic customer reviews preserving original titles, texts, timestamps, and customer star ratings.
              Blank-text submissions and duplicate records are preserved for research fidelity.
            </p>
          </div>

          <div className="sm:text-right flex sm:flex-col justify-between items-center sm:items-end border-t sm:border-t-0 pt-2 sm:pt-0 border-slate-100">
            <span className="text-xs text-slate-500 block">Filtered Review Matches</span>
            <span className="text-xl font-bold font-mono text-slate-900">
              {totalReviews > 0 ? totalReviews.toLocaleString() : '—'}
            </span>
          </div>
        </div>

        {/* Rating & Methodological Disclosure */}
        <div className="mt-4 pt-3 border-t border-slate-100 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-slate-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>
              <strong>Rating Basis:</strong> {ratingBasis || 'source_star_rating (1.0 - 5.0, unpredicted customer reviews)'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-sky-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span>
              <strong>Media Disclosure:</strong> Review image counts represent customer attachments, not product photos.
            </span>
          </div>
        </div>
      </div>

      {/* Filter Toolbar (Backend Supported Filters Only) */}
      <form
        onSubmit={handleApplyFilters}
        className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4"
        aria-label="Review Filter Form"
      >
        <div className="flex items-center justify-between border-b border-slate-100 pb-2">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
            <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            Filter Reviews by Corpus Attributes
          </h3>
          <span className="text-[11px] text-slate-400">
            Draft filters apply on submit
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Parent ASIN */}
          <div>
            <label htmlFor="filter-parent-asin" className="block text-xs font-semibold text-slate-700 mb-1">
              Parent ASIN
            </label>
            <input
              id="filter-parent-asin"
              type="text"
              value={draftParentAsin}
              onChange={(e) => setDraftParentAsin(e.target.value)}
              placeholder="e.g. B00X..."
              className="w-full text-xs font-mono px-3 py-2 border border-slate-300 rounded-md focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
            />
          </div>

          {/* Variant ASIN */}
          <div>
            <label htmlFor="filter-variant-asin" className="block text-xs font-semibold text-slate-700 mb-1">
              Variant ASIN (SKU)
            </label>
            <input
              id="filter-variant-asin"
              type="text"
              value={draftAsin}
              onChange={(e) => setDraftAsin(e.target.value)}
              placeholder="e.g. B00..."
              className="w-full text-xs font-mono px-3 py-2 border border-slate-300 rounded-md focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
            />
          </div>

          {/* Customer Rating Filter */}
          <div>
            <label htmlFor="filter-rating" className="block text-xs font-semibold text-slate-700 mb-1">
              Customer Rating
            </label>
            <select
              id="filter-rating"
              value={draftRating}
              onChange={(e) => setDraftRating(e.target.value)}
              className="w-full text-xs px-3 py-2 border border-slate-300 rounded-md focus:border-brand-500 focus:ring-1 focus:ring-brand-500 bg-white"
            >
              <option value="">All Ratings (1.0 - 5.0)</option>
              <option value="5.0">5 Stars Only</option>
              <option value="4.0">4 Stars Only</option>
              <option value="3.0">3 Stars Only</option>
              <option value="2.0">2 Stars Only</option>
              <option value="1.0">1 Star Only</option>
            </select>
          </div>

          {/* Verified Purchase Filter */}
          <div>
            <label htmlFor="filter-verified" className="block text-xs font-semibold text-slate-700 mb-1">
              Purchase Verification
            </label>
            <select
              id="filter-verified"
              value={draftVerified}
              onChange={(e) => setDraftVerified(e.target.value)}
              className="w-full text-xs px-3 py-2 border border-slate-300 rounded-md focus:border-brand-500 focus:ring-1 focus:ring-brand-500 bg-white"
            >
              <option value="">All Reviews</option>
              <option value="true">Verified Purchase Only</option>
              <option value="false">Unverified Purchase Only</option>
            </select>
          </div>
        </div>

        <div className="flex items-center justify-between pt-2">
          <div className="text-[11px] text-slate-500">
            {hasActiveFilters ? (
              <span className="text-brand-700 font-medium">Filters currently applied</span>
            ) : (
              <span>Showing all genuine reviews across category</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleResetFilters}
              className="px-3 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400"
            >
              Reset Filters
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-1.5 text-xs font-medium text-white bg-brand-600 hover:bg-brand-700 rounded shadow-sm transition-colors disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              Apply Filters
            </button>
          </div>
        </div>
      </form>

      {/* Active Filter Chips Bar */}
      {hasActiveFilters && (
        <div className="flex items-center gap-2 flex-wrap text-xs bg-slate-100 border border-slate-200 rounded-lg p-2.5">
          <span className="font-semibold text-slate-700 text-[11px] uppercase tracking-wider">Active Filters:</span>
          {appliedParentAsin && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white border border-slate-300 text-slate-800 font-mono text-[11px] shadow-2xs">
              <span>Parent: {appliedParentAsin}</span>
              <button
                type="button"
                onClick={() => handleClearSingleFilter('parent_asin')}
                className="hover:text-rose-600 focus:outline-none"
                aria-label="Remove parent ASIN filter"
              >
                &times;
              </button>
            </span>
          )}
          {appliedAsin && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white border border-slate-300 text-slate-800 font-mono text-[11px] shadow-2xs">
              <span>Variant: {appliedAsin}</span>
              <button
                type="button"
                onClick={() => handleClearSingleFilter('asin')}
                className="hover:text-rose-600 focus:outline-none"
                aria-label="Remove variant ASIN filter"
              >
                &times;
              </button>
            </span>
          )}
          {appliedRating && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white border border-slate-300 text-slate-800 text-[11px] shadow-2xs">
              <span>{appliedRating} Stars</span>
              <button
                type="button"
                onClick={() => handleClearSingleFilter('rating')}
                className="hover:text-rose-600 focus:outline-none"
                aria-label="Remove rating filter"
              >
                &times;
              </button>
            </span>
          )}
          {appliedVerified !== '' && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white border border-slate-300 text-slate-800 text-[11px] shadow-2xs">
              <span>{appliedVerified === 'true' ? 'Verified Purchase' : 'Unverified Purchase'}</span>
              <button
                type="button"
                onClick={() => handleClearSingleFilter('verified')}
                className="hover:text-rose-600 focus:outline-none"
                aria-label="Remove verification filter"
              >
                &times;
              </button>
            </span>
          )}
          <button
            type="button"
            onClick={handleResetFilters}
            className="text-[11px] font-medium text-brand-700 hover:text-brand-900 underline ml-auto"
          >
            Clear all
          </button>
        </div>
      )}

      {/* Recoverable Error Banner */}
      {error && (
        <OfflineBanner
          onRetry={() => setFetchTrigger((n) => n + 1)}
          isChecking={loading}
          message={error.detail || error.message}
        />
      )}

      {/* Reviews List */}
      <div className="space-y-4">
        {/* Loading State */}
        {loading && (
          <div className="bg-white border border-slate-200 rounded-lg p-16 flex flex-col items-center justify-center text-slate-500" role="status" aria-live="polite">
            <svg className="animate-spin h-8 w-8 text-brand-600 mb-3" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            <p className="text-sm font-medium">Fetching genuine reviews matching filters...</p>
            <span className="sr-only">Loading reviews</span>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && reviews.length === 0 && (
          <div className="bg-white border border-slate-200 rounded-lg p-16 text-center text-slate-500 space-y-3">
            <svg className="w-12 h-12 text-slate-300 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h4 className="text-sm font-semibold text-slate-800">No genuine reviews match the selected criteria</h4>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              No records in the 25,000-review sample matched the active combination of parent ASIN, variant ASIN, rating, and verification filters.
            </p>
            {hasActiveFilters && (
              <div className="pt-2">
                <button
                  type="button"
                  onClick={handleResetFilters}
                  className="px-4 py-2 text-xs font-medium text-brand-700 bg-brand-50 hover:bg-brand-100 border border-brand-200 rounded-md transition-colors"
                >
                  Reset All Filters
                </button>
              </div>
            )}
          </div>
        )}

        {/* Loaded Reviews Stream */}
        {!loading && reviews.map((rev) => (
          <article
            key={rev.review_id}
            className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm hover:border-slate-300 transition-colors space-y-3"
            aria-labelledby={`review-title-${rev.review_id}`}
          >
            {/* Review Card Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2.5 flex-wrap">
                <StarRating rating={rev.rating} size="sm" />
                <h3 id={`review-title-${rev.review_id}`} className="text-xs font-bold text-slate-900 break-words">
                  {rev.raw_title ? (
                    rev.raw_title
                  ) : (
                    <span className="text-slate-400 italic font-normal">Untitled (No headline provided by reviewer)</span>
                  )}
                </h3>
              </div>

              <div className="flex items-center gap-1.5 flex-wrap text-xs">
                {rev.verified_purchase && (
                  <StatusBadge label="Verified Purchase" variant="success" size="sm" />
                )}
                {rev.has_images && (
                  <span
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-sky-200 bg-sky-50 text-sky-700 text-xs"
                    title="Customer attached photo(s) to this review. Image URLs were not distributed in this dataset sample."
                  >
                    <svg className="w-3 h-3 text-sky-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <span>Customer Photos Attached</span>
                  </span>
                )}
                {rev.occurrence_index > 0 && (
                  <StatusBadge
                    label={`Duplicate Occurrence #${rev.occurrence_index}`}
                    variant="warning"
                    size="sm"
                  />
                )}
              </div>
            </div>

            {/* Review Body Text with Honest Blank-Text Handling */}
            <div className="text-xs text-slate-700 leading-relaxed">
              {rev.is_blank_text || !rev.raw_text?.trim() ? (
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-md text-slate-500 italic flex items-center gap-2">
                  <svg className="w-4 h-4 text-slate-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Customer submitted a star rating without written review text. Blank text preserved for provenance.</span>
                </div>
              ) : (
                <p className="whitespace-pre-line break-words">{rev.raw_text}</p>
              )}
            </div>

            {/* Review Provenance & Metadata Footer */}
            <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-500 font-mono">
              <div className="flex items-center gap-3 flex-wrap">
                <span>
                  Parent ASIN:{' '}
                  <button
                    type="button"
                    onClick={() => {
                      setDraftParentAsin(rev.parent_asin);
                      setAppliedParentAsin(rev.parent_asin);
                      setOffset(0);
                    }}
                    className="font-semibold text-brand-700 hover:underline"
                    title="Filter by this parent ASIN"
                  >
                    {rev.parent_asin}
                  </button>
                </span>
                <span>
                  Variant SKU:{' '}
                  <button
                    type="button"
                    onClick={() => {
                      setDraftAsin(rev.asin);
                      setAppliedAsin(rev.asin);
                      setOffset(0);
                    }}
                    className="font-semibold text-slate-700 hover:text-brand-700 hover:underline"
                    title="Filter by this specific SKU"
                  >
                    {rev.asin}
                  </button>
                </span>
                <span className="truncate max-w-[180px]" title={`Anonymized reviewer user_id: ${rev.user_id}`}>
                  Reviewer: <strong className="text-slate-600">{rev.user_id}</strong>
                </span>
              </div>

              <div className="flex items-center gap-3">
                {rev.helpful_vote > 0 && (
                  <span className="text-slate-600 font-sans font-medium bg-slate-100 px-2 py-0.5 rounded text-[11px]" title="Raw count of helpful votes from other customers">
                    {rev.helpful_vote} {rev.helpful_vote === 1 ? 'helpful vote' : 'helpful votes'}
                  </span>
                )}
                <time
                  dateTime={rev.review_timestamp_utc}
                  title={`Epoch: ${rev.review_epoch_seconds}s (Unix millisecond precision)`}
                  className="text-slate-400"
                >
                  {rev.review_timestamp_utc.replace('T', ' ').replace('Z', ' UTC')}
                </time>
              </div>
            </div>
          </article>
        ))}

        {/* Pagination Controls */}
        {!loading && reviews.length > 0 && (
          <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
            <Pagination
              totalItems={totalReviews}
              limit={limit}
              offset={offset}
              onPageChange={(newOffset) => setOffset(newOffset)}
              itemName="reviews"
            />
          </div>
        )}
      </div>
    </div>
  );
};
