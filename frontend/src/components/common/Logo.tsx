import React from 'react';

interface LogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
}

export const Logo: React.FC<LogoProps> = ({
  className = '',
  size = 'md',
  showText = true,
}) => {
  const iconSizes = {
    sm: 'w-7 h-7',
    md: 'w-9 h-9',
    lg: 'w-11 h-11',
  };

  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      {/* Brand Icon: Deep navy rounded container with waveform / trendline data pulse */}
      <div
        className={`${iconSizes[size]} rounded-lg bg-gradient-to-br from-slate-900 via-brand-900 to-brand-800 flex items-center justify-center shadow-sm border border-brand-700/30 shrink-0 p-1.5`}
        aria-hidden="true"
      >
        <svg
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full"
        >
          {/* Subtle background grid accent */}
          <path
            d="M4 16H28M16 4V28"
            stroke="#1e3a8a"
            strokeWidth="0.75"
            strokeDasharray="2 2"
            opacity="0.4"
          />
          {/* Dynamic pulse / trend-line motif */}
          <path
            d="M3 17.5L8 17.5L11 11L14 23L18 7L22 20L25 15L29 15"
            stroke="url(#pulse-gradient)"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Active pulse node indicator */}
          <circle cx="18" cy="7" r="2.2" fill="#38bdf8" />
          <circle cx="18" cy="7" r="1.1" fill="#ffffff" />
          <defs>
            <linearGradient id="pulse-gradient" x1="3" y1="15" x2="29" y2="15" gradientUnits="userSpaceOnUse">
              <stop stopColor="#38bdf8" />
              <stop offset="0.5" stopColor="#60a5fa" />
              <stop offset="1" stopColor="#93c5fd" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      {showText && (
        <div className="leading-tight">
          <div className="flex items-center">
            <span className="text-base font-bold text-slate-900 tracking-tight">
              Product<span className="text-brand-600">Pulse</span>
            </span>
          </div>
          <span className="text-[10px] text-slate-500 font-mono tracking-wider block uppercase">
            Analytics Platform
          </span>
        </div>
      )}
    </div>
  );
};
