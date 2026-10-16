import React from 'react';

interface StarRatingProps {
  rating: number | null;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export const StarRating: React.FC<StarRatingProps> = ({
  rating,
  size = 'md',
  showLabel = true,
}) => {
  if (rating === null || rating === undefined) {
    return (
      <span className="text-xs text-slate-400 italic">No ratings</span>
    );
  }

  const normalized = Math.max(0, Math.min(5, rating));
  const rounded = Math.round(normalized * 10) / 10;

  const starSizes = {
    sm: 'w-3.5 h-3.5',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  return (
    <div
      className="inline-flex items-center gap-1.5"
      title="Source customer-provided rating (unpredicted customer review, 1.0 - 5.0)"
      aria-label={`Customer rating: ${rounded} out of 5 stars`}
    >
      <div className="flex items-center text-amber-400" aria-hidden="true">
        {[1, 2, 3, 4, 5].map((starIndex) => {
          const fillPercentage = Math.max(0, Math.min(100, (normalized - (starIndex - 1)) * 100));

          return (
            <div key={starIndex} className={`relative ${starSizes[size]}`}>
              {/* Background empty star */}
              <svg
                className={`${starSizes[size]} text-slate-200 fill-current`}
                viewBox="0 0 20 20"
              >
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
              {/* Foreground filled star with clip */}
              {fillPercentage > 0 && (
                <div
                  className="absolute inset-0 overflow-hidden"
                  style={{ width: `${fillPercentage}%` }}
                >
                  <svg
                    className={`${starSizes[size]} text-amber-400 fill-current`}
                    viewBox="0 0 20 20"
                  >
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                </div>
              )}
            </div>
          );
        })}
      </div>
      {showLabel && (
        <span className="text-xs font-semibold text-slate-700">
          {rounded.toFixed(1)}
        </span>
      )}
    </div>
  );
};
