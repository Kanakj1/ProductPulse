import React, { useEffect, useState } from 'react';
import { getProducts } from '../../api/client.ts';
import type { HealthStatus, ProductSummary } from '../../types/api.ts';
import { StarRating } from '../common/StarRating.tsx';
import { StatusBadge } from '../common/StatusBadge.tsx';
import { OfflineBanner } from '../common/OfflineBanner.tsx';

interface OverviewViewProps {
  health: HealthStatus | null;
  isHealthChecking: boolean;
  onRefreshHealth: () => void;
  onNavigateToCatalogue: () => void;
  onNavigateToReviews: () => void;
  onInspectProduct: (parentAsin: string) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  health,
  isHealthChecking,
  onRefreshHealth,
  onNavigateToCatalogue,
  onNavigateToReviews,
  onInspectProduct,
}) => {
  const [sampleProducts, setSampleProducts] = useState<ProductSummary[]>([]);
  const [totalProducts, setTotalProducts] = useState<number | null>(null);
  const [loadingSample, setLoadingSample] = useState(false);
  const [sampleError, setSampleError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoadingSample(true);
    setSampleError(null);

    // Fetch top 5 products as genuine sample
    getProducts(5, 0).then((res) => {
      if (!isMounted) return;
      setLoadingSample(false);
      if (res.success) {
        setSampleProducts(res.data.items);
        setTotalProducts(res.data.total_products);
      } else {
        setSampleError(res.error.detail || res.error.message);
      }
    });

    return () => {
      isMounted = false;
    };
  }, []);

  const isOnline = health?.status === 'healthy';

  return (
    <div className="space-y-6">
      {/* Hero Welcome Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-brand-950 text-white rounded-xl p-6 sm:p-8 shadow-sm">
        <div className="max-w-3xl space-y-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-brand-300 bg-brand-900/60 border border-brand-700/50 px-2.5 py-0.5 rounded">
              Academic BDA &amp; NLP Project
            </span>
            <span className="text-xs font-mono text-slate-400">
              Category: Cell_Phones_and_Accessories
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            ProductPulse Overview &amp; Verification
          </h1>

          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            Welcome to ProductPulse, an empirical review intelligence platform evaluating genuine Amazon customer reviews for mobile phones and accessories. All catalog data and reviewer ratings reflect verified dataset records.
          </p>

          <div className="pt-2 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={onNavigateToCatalogue}
              className="inline-flex items-center px-4 py-2 text-xs font-semibold text-slate-900 bg-white hover:bg-slate-100 rounded-md shadow-sm transition-colors"
            >
              Explore Catalogue ({totalProducts ? totalProducts.toLocaleString() : '19k+'} Products)
              <svg className="w-3.5 h-3.5 ml-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </button>

            <button
              type="button"
              onClick={onNavigateToReviews}
              className="inline-flex items-center px-4 py-2 text-xs font-semibold text-white bg-brand-600/80 hover:bg-brand-600 border border-brand-500/50 rounded-md shadow-sm transition-colors"
            >
              Browse Reviews (25,000 Sample)
            </button>
          </div>
        </div>
      </div>

      {/* Offline Alert if Backend Offline */}
      {!isOnline && (
        <OfflineBanner
          onRetry={onRefreshHealth}
          isChecking={isHealthChecking}
          message="Backend API is currently offline. Overview shows cached structures until connection is established."
        />
      )}

      {/* Real Infrastructure & Operational Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Backend & DB Health Card */}
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              System Infrastructure
            </h3>
            <span
              className={`w-2 h-2 rounded-full ${
                isOnline ? 'bg-emerald-500' : 'bg-amber-500'
              }`}
            />
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">FastAPI Backend:</span>
              <span className="font-mono font-medium text-slate-800">
                {isOnline ? 'Connected (127.0.0.1:8000)' : 'Offline / Standby'}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Database Layer:</span>
              <span className="font-mono font-medium text-slate-800">
                {health?.database.status === 'connected' ? 'SQLite (Active)' : 'Unreachable'}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Foreign Key Enforcement:</span>
              <span className="font-mono font-medium text-slate-800">
                {health?.database.foreign_keys === 'enabled' ? 'PRAGMA ON' : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Dataset Ingestion State:</span>
              <span className="font-mono font-medium text-slate-800 capitalize">
                {health?.database.dataset || 'Unknown'}
              </span>
            </div>
          </div>
        </div>

        {/* Dataset & Scope Governance Card */}
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Scope &amp; Governance
            </h3>
            <StatusBadge label="Locked" variant="info" size="sm" />
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Target Category:</span>
              <span className="font-mono font-semibold text-slate-800 text-[11px]">
                Cell_Phones_and_Accessories
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Upstream Dataset:</span>
              <span className="font-mono text-slate-800 text-[11px]">
                Amazon-Reviews-2023
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Total Ingested Reviews:</span>
              <span className="font-mono font-semibold text-slate-800">
                25,000 Verified
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Catalogue Products:</span>
              <span className="font-mono font-semibold text-slate-800">
                {totalProducts !== null ? totalProducts.toLocaleString() : '19,065'}
              </span>
            </div>
          </div>
        </div>

        {/* Phase Status & Academic Integrity Card */}
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Project Phase Progress
            </h3>
            <StatusBadge label="Phase 5" variant="success" size="sm" />
          </div>

          <div className="space-y-1.5 text-xs text-slate-600">
            <div className="flex items-center justify-between">
              <span>Phase 1–3 (Contract &amp; Schema):</span>
              <span className="text-emerald-700 font-semibold font-mono text-[11px]">Complete</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Phase 4 (FastAPI Backend):</span>
              <span className="text-emerald-700 font-semibold font-mono text-[11px]">Verified Pass</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Phase 5 (Frontend Foundation):</span>
              <span className="text-brand-600 font-semibold font-mono text-[11px]">In Progress</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Phase 7–8 (NLP Sentiment &amp; Complaints):</span>
              <span className="text-amber-600 font-medium font-mono text-[11px]">Pending Phase</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Phase 9 (Hadoop &amp; Hive BDA):</span>
              <span className="text-amber-600 font-medium font-mono text-[11px]">Pending Phase</span>
            </div>
          </div>
        </div>
      </div>

      {/* Prominent Roadmap & Non-Fabrication Notice */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="text-sm font-bold text-slate-900">
            Academic Transparency &amp; Non-Fabrication Guarantee
          </h3>
        </div>
        <p className="text-xs text-slate-600 leading-relaxed">
          ProductPulse adheres to strict academic evaluation standards. Per project constraints, we do not invent or simulate analytics metrics. Specifically:
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-slate-700 pt-1">
          <div className="bg-white p-3 rounded border border-slate-200">
            <strong className="block text-slate-900 mb-1">NLP Sentiment Analysis</strong>
            Scheduled for Phase 7. Will utilize NLTK and scikit-learn TF-IDF baseline models on genuine review text. No synthetic sentiment percentages are rendered today.
          </div>
          <div className="bg-white p-3 rounded border border-slate-200">
            <strong className="block text-slate-900 mb-1">Complaint Discovery</strong>
            Scheduled for Phase 8. Will cluster negative review excerpts into evidence-backed categories. No imaginary complaint clusters or trends are generated.
          </div>
          <div className="bg-white p-3 rounded border border-slate-200">
            <strong className="block text-slate-900 mb-1">Big Data Analytics (BDA)</strong>
            Scheduled for Phase 9. Will execute verifiable batch jobs on Hadoop Streaming and Hive. No simulated MapReduce job counts are shown.
          </div>
        </div>
      </div>

      {/* Real Top Products Sample from Catalog API */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Catalogue Highlights (Real API Sample)</h3>
            <p className="text-xs text-slate-500">Products with highest review volume in the verified 25k sample.</p>
          </div>
          <button
            type="button"
            onClick={onNavigateToCatalogue}
            className="text-xs font-semibold text-brand-600 hover:text-brand-700 hover:underline"
          >
            View Full Catalogue &rarr;
          </button>
        </div>

        {loadingSample && (
          <div className="py-8 text-center text-xs text-slate-500">
            Loading genuine catalogue sample...
          </div>
        )}

        {sampleError && (
          <div className="p-3 bg-amber-50 text-amber-800 text-xs rounded border border-amber-200">
            Unable to fetch catalogue sample: {sampleError}
          </div>
        )}

        {!loadingSample && sampleProducts.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            {sampleProducts.map((p) => (
              <div
                key={p.parent_asin}
                className="bg-slate-50 border border-slate-200 rounded-lg p-3 hover:border-slate-300 transition-colors flex flex-col justify-between"
              >
                <div>
                  <span className="font-mono text-xs font-bold text-slate-900 block truncate">
                    {p.parent_asin}
                  </span>
                  <span className="text-[10px] text-slate-400 block mb-2">
                    Metadata pending
                  </span>
                </div>

                <div className="pt-2 border-t border-slate-200/80 mt-2 space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500 text-[11px]">Reviews:</span>
                    <span className="font-mono font-semibold text-slate-800">{p.review_count}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500 text-[11px]">Rating:</span>
                    <StarRating rating={p.avg_rating} size="sm" showLabel={false} />
                  </div>
                  <button
                    type="button"
                    onClick={() => onInspectProduct(p.parent_asin)}
                    className="w-full mt-2 text-center text-[11px] font-medium text-brand-700 bg-white border border-brand-200 hover:bg-brand-50 py-1 rounded transition-colors"
                  >
                    Inspect
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
