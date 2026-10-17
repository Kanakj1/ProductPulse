import React, { useEffect, useState, useRef } from 'react';
import { getProducts } from '../../api/client.ts';
import type { ProductSummary, ProductListResponse } from '../../types/api.ts';
import { StarRating } from '../common/StarRating.tsx';
import { Pagination } from '../common/Pagination.tsx';
import { OfflineBanner } from '../common/OfflineBanner.tsx';
import { ProductDashboardView } from './ProductDashboardView.tsx';

interface ProductCatalogueViewProps {
  onSelectProductForReviews: (parentAsin: string, variantAsin?: string) => void;
  selectedProductAsin?: string | null;
  onSelectProduct?: (parentAsin: string | null) => void;
}

export const ProductCatalogueView: React.FC<ProductCatalogueViewProps> = ({
  onSelectProductForReviews,
  selectedProductAsin,
  onSelectProduct,
}) => {
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [totalProducts, setTotalProducts] = useState(0);
  const [limit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [ratingBasis, setRatingBasis] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<{ isNetworkError: boolean; message: string; detail?: string } | null>(null);
  const [fetchTrigger, setFetchTrigger] = useState(0);

  // Local selection state for dashboard view if not strictly controlled from parent
  const [localSelectedAsin, setLocalSelectedAsin] = useState<string | null>(null);
  const activeProductAsin = selectedProductAsin !== undefined ? selectedProductAsin : localSelectedAsin;

  // Request sequence ID to safely discard stale out-of-order responses
  const activeRequestIdRef = useRef(0);

  useEffect(() => {
    const requestId = ++activeRequestIdRef.current;
    setLoading(true);
    setError(null);

    getProducts(limit, offset).then((res) => {
      // Discard stale out-of-order response if a newer request was dispatched
      if (activeRequestIdRef.current !== requestId) {
        return;
      }
      setLoading(false);
      if (res.success) {
        const data: ProductListResponse = res.data;
        setProducts(data.items);
        setTotalProducts(data.total_products);
        setRatingBasis(data.rating_basis);
      } else {
        setError(res.error);
      }
    });

    return () => {
      // Invalidate active request on unmount or before next effect run
      activeRequestIdRef.current++;
    };
  }, [limit, offset, fetchTrigger]);

  const handlePageChange = (newOffset: number) => {
    setOffset(newOffset);
  };

  const handleOpenProductDashboard = (parentAsin: string) => {
    setLocalSelectedAsin(parentAsin);
    if (onSelectProduct) {
      onSelectProduct(parentAsin);
    }
  };

  const handleBackToCatalogue = () => {
    setLocalSelectedAsin(null);
    if (onSelectProduct) {
      onSelectProduct(null);
    }
  };

  const handleRetry = () => {
    setFetchTrigger((n) => n + 1);
  };

  // If a product is currently selected, render the dedicated Individual Product Dashboard
  if (activeProductAsin) {
    return (
      <ProductDashboardView
        parentAsin={activeProductAsin}
        onBack={handleBackToCatalogue}
        onSelectProductForReviews={onSelectProductForReviews}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* View Header */}
      <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <span className="text-xs font-mono font-semibold uppercase tracking-wider text-brand-700 bg-brand-50 border border-brand-200 px-2 py-0.5 rounded">
                Official Dataset
              </span>
              <span className="text-xs font-mono text-slate-500">
                Cell_Phones_and_Accessories
              </span>
              <span className="text-[11px] text-slate-400 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded font-mono">
                Deterministic Order: Reviews (Desc) &rarr; ASIN (Asc)
              </span>
            </div>
            <h2 className="text-xl font-bold text-slate-900">Product Catalogue</h2>
            <p className="text-xs text-slate-600 mt-1 max-w-2xl">
              Authentic mobile phones and accessory products catalogued from genuine customer reviews.
              Click any product to explore its dedicated individual dashboard, customer ratings, and MapReduce aspect analytics.
            </p>
          </div>

          <div className="sm:text-right flex sm:flex-col justify-between items-center sm:items-end border-t sm:border-t-0 pt-2 sm:pt-0 border-slate-100">
            <span className="text-xs text-slate-500 block">Total Catalogue Products</span>
            <span className="text-xl font-bold font-mono text-slate-900">
              {totalProducts > 0 ? totalProducts.toLocaleString() : '—'}
            </span>
          </div>
        </div>

        {/* Rating Basis Disclosure Banner */}
        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center gap-2 text-xs text-slate-500">
          <svg className="w-4 h-4 text-slate-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>
            <strong>Rating Basis:</strong> {ratingBasis || 'source_star_rating (1.0 - 5.0, unpredicted customer reviews)'}
          </span>
        </div>
      </div>

      {/* Recoverable Error Banner */}
      {error && (
        <OfflineBanner
          onRetry={handleRetry}
          isChecking={loading}
          message={error.detail || error.message}
        />
      )}

      {/* Main Content Area */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
        {/* Loading State */}
        {loading && (
          <div className="py-20 flex flex-col items-center justify-center text-slate-500" role="status" aria-live="polite">
            <svg className="animate-spin h-8 w-8 text-brand-600 mb-3" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            <p className="text-sm font-medium">Fetching catalogue products from API...</p>
            <span className="sr-only">Loading products</span>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && products.length === 0 && (
          <div className="py-16 text-center text-slate-500">
            <svg className="w-12 h-12 text-slate-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
            <h4 className="text-sm font-semibold text-slate-800">No products found in catalogue</h4>
            <p className="text-xs text-slate-500 mt-1">
              Verify database connection or reload the catalogue.
            </p>
            <button
              type="button"
              onClick={handleRetry}
              className="mt-4 px-3 py-1.5 text-xs font-medium text-brand-700 bg-brand-50 hover:bg-brand-100 border border-brand-200 rounded transition-colors"
            >
              Reload Catalogue
            </button>
          </div>
        )}

        {/* Loaded Product Content */}
        {!loading && products.length > 0 && (
          <>
            {/* Desktop Table View (Hidden on mobile < 640px) */}
            <div className="hidden sm:block overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
                  <tr>
                    <th scope="col" className="px-4 py-3">Product Name & Category</th>
                    <th scope="col" className="px-4 py-3">Canonical ASIN</th>
                    <th scope="col" className="px-4 py-3 text-right">Genuine Reviews</th>
                    <th scope="col" className="px-4 py-3 text-right">Source Customer Rating</th>
                    <th scope="col" className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 bg-white">
                  {products.map((product) => (
                    <tr
                      key={product.parent_asin}
                      className="hover:bg-slate-50/80 transition-colors group cursor-pointer"
                      onClick={() => handleOpenProductDashboard(product.parent_asin)}
                    >
                      {/* Product Name & Identifier */}
                      <td className="px-4 py-3.5 max-w-sm">
                        <div className="flex flex-col">
                          <span className="font-semibold text-slate-900 group-hover:text-brand-600 transition-colors text-sm">
                            {product.title ? (
                              product.title
                            ) : (
                              <span className="font-mono text-slate-900">{product.parent_asin || 'ASIN unavailable'}</span>
                            )}
                          </span>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-[11px] text-slate-400 font-mono">
                              Category: {product.main_category}
                            </span>
                          </div>
                        </div>
                      </td>

                      {/* Canonical ASIN & Brand */}
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-slate-700 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded">
                            {product.parent_asin || 'ASIN unavailable'}
                          </span>
                          {product.brand && (
                            <span className="text-[11px] text-slate-500 font-medium">
                              Brand: {product.brand}
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Genuine Review Count */}
                      <td className="px-4 py-3.5 whitespace-nowrap text-right font-mono font-semibold text-slate-800">
                        {product.review_count.toLocaleString()}
                      </td>

                      {/* Average Customer Star Rating */}
                      <td className="px-4 py-3.5 whitespace-nowrap text-right">
                        <div className="flex justify-end">
                          <StarRating rating={product.avg_rating} size="sm" />
                        </div>
                      </td>

                      {/* Action Buttons */}
                      <td
                        className="px-4 py-3.5 whitespace-nowrap text-right space-x-2"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <button
                          type="button"
                          onClick={() => handleOpenProductDashboard(product.parent_asin)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-brand-700 bg-brand-50 hover:bg-brand-100 border border-brand-200 rounded transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500"
                          aria-label={`Open product dashboard for ${product.parent_asin}`}
                        >
                          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                          </svg>
                          <span>Dashboard</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => onSelectProductForReviews(product.parent_asin)}
                          className="inline-flex items-center px-2.5 py-1 text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent hover:border-slate-200 rounded transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400"
                          aria-label={`Browse reviews for ${product.parent_asin}`}
                        >
                          Reviews
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile Card View (Shown on screens < 640px to eliminate horizontal scrolling) */}
            <div className="block sm:hidden divide-y divide-slate-200">
              {products.map((product) => (
                <div
                  key={product.parent_asin}
                  className="p-4 space-y-3 cursor-pointer hover:bg-slate-50 transition-colors"
                  onClick={() => handleOpenProductDashboard(product.parent_asin)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="font-semibold text-slate-900 text-sm block">
                        {product.title ? product.title : (
                          <span className="font-mono">{product.parent_asin || 'ASIN unavailable'}</span>
                        )}
                      </span>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[11px] text-slate-400 font-mono">
                          {product.main_category}
                        </span>
                      </div>
                    </div>
                    <span className="font-mono text-xs font-bold text-slate-700 bg-slate-100 border border-slate-200 px-1.5 py-0.5 rounded shrink-0">
                      {product.parent_asin || 'ASIN unavailable'}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs text-slate-600 bg-slate-50 p-2.5 rounded border border-slate-100">
                    <div>
                      <span className="text-[10px] uppercase text-slate-400 block font-semibold">Genuine Reviews</span>
                      <span className="font-mono font-bold text-slate-800">{product.review_count.toLocaleString()}</span>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] uppercase text-slate-400 block font-semibold">Source Rating</span>
                      <StarRating rating={product.avg_rating} size="sm" />
                    </div>
                  </div>

                  <div
                    className="flex items-center justify-end gap-2 pt-1"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <button
                      type="button"
                      onClick={() => handleOpenProductDashboard(product.parent_asin)}
                      className="flex-1 py-1.5 text-xs font-semibold text-center text-brand-700 bg-brand-50 hover:bg-brand-100 border border-brand-200 rounded transition-colors"
                      aria-label={`Open product dashboard for ${product.parent_asin}`}
                    >
                      View Dashboard
                    </button>
                    <button
                      type="button"
                      onClick={() => onSelectProductForReviews(product.parent_asin)}
                      className="flex-1 py-1.5 text-xs font-medium text-center text-slate-700 bg-slate-100 hover:bg-slate-200 rounded transition-colors"
                      aria-label={`Browse reviews for ${product.parent_asin}`}
                    >
                      Browse Reviews
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination Controls */}
            <div className="p-4 border-t border-slate-200">
              <Pagination
                totalItems={totalProducts}
                limit={limit}
                offset={offset}
                onPageChange={handlePageChange}
                itemName="products"
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
};
