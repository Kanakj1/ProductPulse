import React from 'react';

interface PaginationProps {
  totalItems: number;
  limit: number;
  offset: number;
  onPageChange: (newOffset: number) => void;
  itemName?: string;
}

export const Pagination: React.FC<PaginationProps> = ({
  totalItems,
  limit,
  offset,
  onPageChange,
  itemName = 'records',
}) => {
  if (totalItems <= 0) return null;

  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.max(1, Math.ceil(totalItems / limit));
  const startItem = offset + 1;
  const endItem = Math.min(offset + limit, totalItems);

  const canGoPrev = offset > 0;
  const canGoNext = offset + limit < totalItems;

  const handlePrev = () => {
    if (canGoPrev) {
      onPageChange(Math.max(0, offset - limit));
    }
  };

  const handleNext = () => {
    if (canGoNext) {
      onPageChange(offset + limit);
    }
  };

  return (
    <nav
      className="flex flex-col sm:flex-row items-center justify-between gap-3 px-4 py-3 bg-white border border-slate-200 rounded-lg shadow-sm"
      aria-label="Pagination Navigation"
    >
      <div className="text-xs text-slate-600">
        Showing <span className="font-medium text-slate-900">{startItem.toLocaleString()}</span> to{' '}
        <span className="font-medium text-slate-900">{endItem.toLocaleString()}</span> of{' '}
        <span className="font-medium text-slate-900">{totalItems.toLocaleString()}</span> {itemName}
      </div>

      <div className="flex items-center gap-2">
        <span className="text-xs text-slate-500 mr-2">
          Page {currentPage} of {totalPages}
        </span>
        <button
          type="button"
          onClick={handlePrev}
          disabled={!canGoPrev}
          className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          aria-label="Go to previous page"
        >
          <svg className="w-3.5 h-3.5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Previous
        </button>

        <button
          type="button"
          onClick={handleNext}
          disabled={!canGoNext}
          className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          aria-label="Go to next page"
        >
          Next
          <svg className="w-3.5 h-3.5 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </nav>
  );
};
