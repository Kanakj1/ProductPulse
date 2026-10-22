import React, { useState } from 'react';
import { getProductDetail } from '../../api/client.ts';

interface HomeViewProps {
  onSearchSuccess: (parentAsin: string) => void;
  onNavigateToCatalogue: () => void;
  onNavigateToReviews: () => void;
}

export const HomeView: React.FC<HomeViewProps> = ({
  onSearchSuccess,
  onNavigateToCatalogue,
  onNavigateToReviews,
}) => {
  const [asinInput, setAsinInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isNetworkError, setIsNetworkError] = useState(false);

  const sampleAsins = ['B073R68TSH', 'B01415QHYW', 'B07P9S6R9Y', 'B00PGJWYJ0'];

  const executeSearch = async (asinToSearch: string) => {
    const trimmed = asinToSearch.trim();
    if (!trimmed) {
      setErrorMsg('Please enter an Amazon ASIN to search.');
      setIsNetworkError(false);
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    setIsNetworkError(false);

    try {
      const res = await getProductDetail(trimmed);
      setLoading(false);

      if (res.success && res.data) {
        onSearchSuccess(res.data.parent_asin);
      } else {
        if (res.error?.isNetworkError) {
          setIsNetworkError(true);
          setErrorMsg(res.error.message || 'Cannot connect to ProductPulse backend service.');
        } else if (res.error?.status === 404) {
          setIsNetworkError(false);
          setErrorMsg(`No product found matching ASIN "${trimmed}". Please verify the ASIN or browse the products catalogue.`);
        } else {
          setIsNetworkError(false);
          setErrorMsg(res.error?.message || `No product records found for ASIN "${trimmed}".`);
        }
      }
    } catch (err: unknown) {
      setLoading(false);
      setIsNetworkError(true);
      setErrorMsg(err instanceof Error ? err.message : 'An unexpected error occurred while searching for the product.');
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    executeSearch(asinInput);
  };

  const handleSelectSample = (asin: string) => {
    setAsinInput(asin);
    executeSearch(asin);
  };

  return (
    <div className="space-y-10 py-2 sm:py-6 animate-fadeIn">
      {/* ========================================================= */}
      {/* Dark Navy Hero Section */}
      {/* ========================================================= */}
      <section
        className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-950 via-slate-900 to-brand-950 text-white p-6 sm:p-10 lg:p-14 shadow-xl border border-slate-800"
        aria-labelledby="hero-heading"
      >
        {/* Subtle decorative background grid pattern */}
        <div
          className="absolute inset-0 opacity-10 pointer-events-none"
          style={{
            backgroundImage: 'radial-gradient(#38bdf8 1px, transparent 1px)',
            backgroundSize: '24px 24px',
          }}
          aria-hidden="true"
        />

        <div className="relative z-10 max-w-3xl mx-auto text-center space-y-6">
          {/* Eyebrow Label */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-900/60 border border-brand-700/50 text-[11px] font-mono tracking-widest text-sky-400 uppercase font-semibold">
            <span className="w-2 h-2 rounded-full bg-sky-400 animate-pulse" aria-hidden="true" />
            Amazon Review Intelligence
          </div>

          {/* Prominent Heading */}
          <h1
            id="hero-heading"
            className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white leading-tight font-sans"
          >
            Search Amazon Product Reviews by ASIN
          </h1>

          {/* Subtitle / Description */}
          <p className="text-sm sm:text-base text-slate-300 leading-relaxed max-w-2xl mx-auto font-sans">
            Explore genuine customer reviews, unpredicted star ratings, and empirical MapReduce aspect insights across thousands of verified mobile phones and accessories.
          </p>

          {/* Large High-Contrast ASIN Search Form */}
          <form onSubmit={handleSubmit} className="pt-2 max-w-2xl mx-auto">
            <div className="flex flex-col sm:flex-row items-stretch gap-2.5 bg-slate-900/90 p-2 rounded-xl border border-slate-700/80 shadow-2xl backdrop-blur-sm">
              <div className="relative flex-1">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <input
                  type="text"
                  value={asinInput}
                  onChange={(e) => {
                    setAsinInput(e.target.value);
                    if (errorMsg) setErrorMsg(null);
                  }}
                  placeholder="Enter Amazon ASIN (e.g., B073R68TSH)"
                  className="w-full pl-11 pr-4 py-3 text-sm sm:text-base bg-slate-800 text-white placeholder-slate-400 rounded-lg border border-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500 font-mono transition-all"
                  aria-label="Enter Amazon ASIN to search"
                  disabled={loading}
                  autoComplete="off"
                  spellCheck="false"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 text-sm font-bold text-white bg-brand-600 hover:bg-brand-500 active:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg shadow-md transition-all font-sans shrink-0 focus:outline-none focus:ring-2 focus:ring-sky-400"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin w-4 h-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    <span>Searching...</span>
                  </>
                ) : (
                  <>
                    <span>Search ASIN</span>
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                  </>
                )}
              </button>
            </div>

            {/* Inline Error Message */}
            {errorMsg && (
              <div
                className={`mt-3 p-3 rounded-lg text-xs text-left flex items-start gap-2.5 ${
                  isNetworkError
                    ? 'bg-rose-950/80 border border-rose-800 text-rose-200'
                    : 'bg-amber-950/80 border border-amber-800 text-amber-200'
                }`}
                role="alert"
              >
                <svg className="w-4 h-4 shrink-0 mt-0.5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div className="flex-1">
                  <span>{errorMsg}</span>
                  {isNetworkError && (
                    <button
                      type="button"
                      onClick={() => executeSearch(asinInput)}
                      className="ml-2 font-bold underline hover:text-white"
                    >
                      Retry
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Sample ASIN shortcuts */}
            <div className="mt-4 flex flex-wrap items-center justify-center gap-2 text-xs text-slate-400">
              <span className="text-[11px] text-slate-400 font-sans">Try popular products:</span>
              {sampleAsins.map((asin) => (
                <button
                  key={asin}
                  type="button"
                  onClick={() => handleSelectSample(asin)}
                  className="px-2 py-0.5 bg-slate-800/80 hover:bg-slate-700 text-sky-300 border border-slate-700 rounded font-mono text-[11px] transition-colors"
                >
                  {asin}
                </button>
              ))}
            </div>
          </form>

          {/* Quick Action Navigation Links */}
          <div className="pt-4 flex flex-wrap items-center justify-center gap-3">
            <button
              type="button"
              onClick={onNavigateToCatalogue}
              className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-colors shadow-sm"
            >
              <svg className="w-4 h-4 text-sky-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
              </svg>
              <span>Browse Products</span>
            </button>

            <button
              type="button"
              onClick={onNavigateToReviews}
              className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-slate-300 hover:text-white bg-slate-900/60 hover:bg-slate-800/80 border border-slate-700/60 rounded-lg transition-colors"
            >
              <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              <span>Browse All Reviews</span>
            </button>
          </div>
        </div>
      </section>

      {/* ========================================================= */}
      {/* Feature Highlights Grid */}
      {/* ========================================================= */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6" aria-label="Platform Highlights">
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-lg bg-sky-50 border border-sky-100 flex items-center justify-center text-brand-600">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h2 className="text-base font-bold text-slate-900">Individual Product Analytics</h2>
          <p className="text-xs text-slate-600 leading-relaxed">
            Inspect dedicated product dashboards featuring genuine star ratings, verified purchase rates, child SKU configurations, and customer rating timelines.
          </p>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <h2 className="text-base font-bold text-slate-900">Hadoop &amp; Hive Aspect Insights</h2>
          <p className="text-xs text-slate-600 leading-relaxed">
            Examine aspect sentiment and discussion density across the 6 locked mobile taxonomy aspects (Battery, Camera, Display, Performance, Build, Audio).
          </p>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-base font-bold text-slate-900">Non-Fabrication Policy</h2>
          <p className="text-xs text-slate-600 leading-relaxed">
            Grounded 100% in genuine Amazon customer evaluations from the official McAuley-Lab 2023 dataset. Zero simulated ratings or synthetic product titles.
          </p>
        </div>
      </section>
    </div>
  );
};
