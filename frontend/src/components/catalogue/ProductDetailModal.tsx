import React, { useEffect, useState, useRef } from 'react';
import { getProductDetail } from '../../api/client.ts';
import type { ProductDetailResponse } from '../../types/api.ts';
import { StarRating } from '../common/StarRating.tsx';
import { StatusBadge } from '../common/StatusBadge.tsx';

interface ProductDetailModalProps {
  parentAsin: string | null;
  isOpen: boolean;
  onClose: () => void;
  onBrowseReviews: (parentAsin: string, variantAsin?: string) => void;
}

export const ProductDetailModal: React.FC<ProductDetailModalProps> = ({
  parentAsin,
  isOpen,
  onClose,
  onBrowseReviews,
}) => {
  const [loading, setLoading] = useState(false);
  const [detail, setDetail] = useState<ProductDetailResponse | null>(null);
  const [error, setError] = useState<{ is404: boolean; message: string; detail?: string } | null>(null);
  const [retryTrigger, setRetryTrigger] = useState(0);

  // Accessibility refs for focus management
  const closeButtonRef = useRef<HTMLButtonElement | null>(null);
  const previousActiveElementRef = useRef<HTMLElement | null>(null);
  const modalCardRef = useRef<HTMLDivElement | null>(null);

  // Store trigger element on open and restore focus when closed/unmounted
  useEffect(() => {
    if (isOpen) {
      previousActiveElementRef.current = document.activeElement as HTMLElement | null;
      const focusTimer = setTimeout(() => {
        closeButtonRef.current?.focus();
      }, 0);

      return () => {
        clearTimeout(focusTimer);
        previousActiveElementRef.current?.focus();
      };
    }
  }, [isOpen]);

  // Keyboard Escape key dismissal
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  // Handle backdrop click dismissal (only when clicking directly on overlay)
  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  // Fetch product detail — immediately clears stale detail to prevent cross-product leakage
  useEffect(() => {
    if (!isOpen || !parentAsin) {
      setDetail(null);
      setError(null);
      return;
    }

    // Immediately clear previous product data so stale details are never displayed
    setDetail(null);
    setError(null);
    setLoading(true);

    let isMounted = true;

    getProductDetail(parentAsin).then((res) => {
      if (!isMounted) return;
      setLoading(false);
      if (res.success) {
        setDetail(res.data);
      } else {
        const status = res.error.status;
        const is404 = status === 404 || (res.error.detail || '').toLowerCase().includes('not found');
        setError({
          is404,
          message: res.error.message,
          detail: res.error.detail,
        });
      }
    });

    return () => {
      isMounted = false;
    };
  }, [isOpen, parentAsin, retryTrigger]);

  if (!isOpen || !parentAsin) return null;

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 sm:p-6"
      role="dialog"
      aria-modal="true"
      aria-labelledby="product-modal-title"
      aria-describedby="product-modal-desc"
      onClick={handleBackdropClick}
    >
      <div
        ref={modalCardRef}
        tabIndex={-1}
        className="bg-white rounded-xl shadow-2xl max-w-2xl w-full border border-slate-200 overflow-hidden flex flex-col max-h-[90vh] focus:outline-none"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div>
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <span className="text-xs font-mono text-slate-500">Product Identifier</span>
              <StatusBadge
                label={detail?.has_metadata ? 'Metadata Present' : 'Metadata Pending Ingestion'}
                variant={detail?.has_metadata ? 'success' : 'neutral'}
                size="sm"
              />
              <span className="text-[11px] font-mono text-slate-400">
                Cell_Phones_and_Accessories
              </span>
            </div>
            <h3 id="product-modal-title" className="text-base font-bold font-mono text-slate-900 break-all">
              {parentAsin}
            </h3>
          </div>
          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-200 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500"
            aria-label="Close product detail modal"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Modal Content */}
        <div id="product-modal-desc" className="p-6 overflow-y-auto space-y-6">
          {/* Loading State */}
          {loading && (
            <div className="py-16 flex flex-col items-center justify-center text-slate-500" role="status" aria-live="polite">
              <svg className="animate-spin h-8 w-8 text-brand-600 mb-3" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <p className="text-sm font-medium">Loading genuine product details from database...</p>
              <span className="sr-only">Loading product details</span>
            </div>
          )}

          {/* 404 Not Found State */}
          {!loading && error?.is404 && (
            <div className="py-12 text-center space-y-3">
              <div className="w-12 h-12 bg-amber-50 text-amber-600 rounded-full flex items-center justify-center mx-auto border border-amber-200">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h4 className="text-base font-bold text-slate-900">Product Not Found in Catalogue</h4>
              <p className="text-xs text-slate-600 max-w-md mx-auto">
                No product record matching parent ASIN <strong className="font-mono text-slate-800">{parentAsin}</strong> was
                found in the active <span className="font-mono">Cell_Phones_and_Accessories</span> database sample.
              </p>
              <div className="pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 transition-colors"
                >
                  Return to Catalogue
                </button>
              </div>
            </div>
          )}

          {/* General API / Network Error State */}
          {!loading && error && !error.is404 && (
            <div className="bg-rose-50 border border-rose-200 rounded-lg p-4 text-xs text-rose-800 space-y-2">
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-rose-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <strong className="font-semibold">Failed to retrieve product details:</strong>
              </div>
              <p>{error.detail || error.message}</p>
              <button
                type="button"
                onClick={() => setRetryTrigger((n) => n + 1)}
                className="mt-2 inline-flex items-center px-3 py-1.5 text-xs font-medium text-rose-700 bg-rose-100 hover:bg-rose-200 rounded transition-colors"
              >
                Retry Request
              </button>
            </div>
          )}

          {/* Loaded Product Details */}
          {!loading && detail && (
            <>
              {/* Honest Metadata Notice & Media Fallback Box */}
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-3">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded bg-slate-200 border border-slate-300 flex items-center justify-center text-slate-400 flex-shrink-0" aria-hidden="true">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div className="text-xs text-slate-600 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-800">Catalogue Media Status:</span>
                      <StatusBadge label="Pending Metadata Ingestion" variant="neutral" size="sm" />
                    </div>
                    <p className="leading-relaxed">
                      {detail.metadata_notice}
                    </p>
                    <p className="text-[11px] text-slate-500 italic">
                      * Honesty policy: Review-attached photos submitted by customers are not product catalogue photos and are not used as product imagery.
                    </p>
                  </div>
                </div>
              </div>

              {/* Stats Summary Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                  <span className="text-[10px] font-semibold text-slate-500 block uppercase tracking-wider">Total Reviews</span>
                  <span className="text-xl font-bold font-mono text-slate-900">{detail.review_count.toLocaleString()}</span>
                  <span className="text-[10px] text-slate-400 block mt-0.5">genuine corpus records</span>
                </div>

                <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                  <span className="text-[10px] font-semibold text-slate-500 block uppercase tracking-wider">Source Rating</span>
                  <div className="mt-1">
                    <StarRating rating={detail.avg_rating} size="sm" />
                  </div>
                  <span className="text-[10px] text-slate-400 block mt-0.5">customer star avg</span>
                </div>

                <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                  <span className="text-[10px] font-semibold text-slate-500 block uppercase tracking-wider">Verified Purchases</span>
                  <span className="text-xl font-bold font-mono text-emerald-700">
                    {detail.verified_purchase_count.toLocaleString()}
                  </span>
                  <span className="text-[10px] text-emerald-600 block mt-0.5">
                    {detail.review_count > 0 ? `${((detail.verified_purchase_count / detail.review_count) * 100).toFixed(0)}% of reviews` : '0%'}
                  </span>
                </div>

                <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                  <span className="text-[10px] font-semibold text-slate-500 block uppercase tracking-wider">Customer Photos</span>
                  <span className="text-xl font-bold font-mono text-slate-800">
                    {detail.has_images_count.toLocaleString()}
                  </span>
                  <span className="text-[10px] text-slate-400 block mt-0.5">review attachments</span>
                </div>
              </div>

              {/* Star Rating Distribution Histogram */}
              <div className="bg-white border border-slate-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                    Customer Star Rating Distribution (1.0 - 5.0)
                  </h4>
                  <span className="text-[11px] font-mono text-slate-500">
                    N = {detail.review_count.toLocaleString()} reviews
                  </span>
                </div>
                <div className="space-y-2.5">
                  {[
                    { star: 5, count: detail.rating_distribution.stars_5, color: 'bg-emerald-500' },
                    { star: 4, count: detail.rating_distribution.stars_4, color: 'bg-emerald-400' },
                    { star: 3, count: detail.rating_distribution.stars_3, color: 'bg-amber-400' },
                    { star: 2, count: detail.rating_distribution.stars_2, color: 'bg-orange-400' },
                    { star: 1, count: detail.rating_distribution.stars_1, color: 'bg-rose-400' },
                  ].map((row) => {
                    const percentage = detail.review_count > 0 ? (row.count / detail.review_count) * 100 : 0;
                    return (
                      <div key={row.star} className="flex items-center gap-3 text-xs">
                        <span className="w-12 font-medium text-slate-600 flex items-center gap-1">
                          {row.star} <span className="text-amber-400">&starf;</span>
                        </span>
                        <div className="flex-1 bg-slate-100 rounded-full h-2.5 overflow-hidden">
                          <div
                            className={`${row.color} h-2.5 rounded-full transition-all duration-300`}
                            style={{ width: `${percentage}%` }}
                            role="progressbar"
                            aria-valuenow={row.count}
                            aria-valuemin={0}
                            aria-valuemax={detail.review_count}
                          />
                        </div>
                        <span className="w-20 text-right text-slate-500 font-mono text-[11px]">
                          {row.count.toLocaleString()} ({percentage.toFixed(0)}%)
                        </span>
                      </div>
                    );
                  })}
                </div>
                <div className="mt-3 pt-2 border-t border-slate-100 text-[10px] text-slate-500">
                  <p>
                    <strong>Methodological Disclosure:</strong> {detail.rating_basis}.
                    Scores reflect raw star ratings submitted by Amazon customers. They are unpredicted customer opinions, not NLP sentiment classifications.
                  </p>
                </div>
              </div>

              {/* Temporal Review Coverage */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs bg-slate-50 p-3 rounded-lg border border-slate-200">
                <div>
                  <span className="text-slate-500 block text-[11px] font-semibold uppercase">Earliest Review in Sample</span>
                  <span className="font-mono text-slate-800 font-medium">
                    {detail.first_review_utc ? detail.first_review_utc.replace('T', ' ').replace('Z', ' UTC') : 'Not available'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[11px] font-semibold uppercase">Latest Review in Sample</span>
                  <span className="font-mono text-slate-800 font-medium">
                    {detail.latest_review_utc ? detail.latest_review_utc.replace('T', ' ').replace('Z', ' UTC') : 'Not available'}
                  </span>
                </div>
              </div>

              {/* Associated Product Variants (SKUs) */}
              <div className="bg-white border border-slate-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                    Associated Variant ASINs ({detail.variants.length})
                  </h4>
                  <span className="text-[11px] text-slate-400">
                    Click SKU to filter reviews
                  </span>
                </div>
                <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto p-1 border border-slate-100 rounded bg-slate-50">
                  {detail.variants.map((sku) => (
                    <button
                      key={sku}
                      type="button"
                      onClick={() => {
                        onClose();
                        onBrowseReviews(parentAsin, sku);
                      }}
                      className="inline-flex items-center px-2 py-1 rounded text-xs font-mono bg-white hover:bg-brand-50 hover:text-brand-700 hover:border-brand-300 text-slate-700 border border-slate-200 transition-colors shadow-2xs"
                      title={`Filter reviews for variant SKU ${sku}`}
                    >
                      <span>{sku}</span>
                      <svg className="w-3 h-3 ml-1 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400"
          >
            Close
          </button>

          {detail && (
            <button
              type="button"
              onClick={() => {
                onClose();
                onBrowseReviews(parentAsin);
              }}
              className="inline-flex items-center px-4 py-2 text-xs font-medium text-white bg-brand-600 hover:bg-brand-700 rounded-md shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              Browse All Reviews for this Product
              <svg className="w-3.5 h-3.5 ml-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
