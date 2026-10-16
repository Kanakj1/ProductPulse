import React from 'react';

interface NoticeBannerProps {
  title: string;
  description: string;
  variant?: 'info' | 'warning' | 'neutral';
}

export const NoticeBanner: React.FC<NoticeBannerProps> = ({
  title,
  description,
  variant = 'info',
}) => {
  const styles = {
    info: 'bg-sky-50 border-sky-200 text-sky-800',
    warning: 'bg-amber-50 border-amber-200 text-amber-800',
    neutral: 'bg-slate-100 border-slate-200 text-slate-800',
  };

  return (
    <div className={`border rounded-lg p-3 text-xs ${styles[variant]} flex items-start gap-2.5`}>
      <svg
        className="w-4 h-4 mt-0.5 flex-shrink-0 opacity-80"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <div>
        <span className="font-semibold">{title}:</span> {description}
      </div>
    </div>
  );
};
