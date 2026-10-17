import React, { useState } from 'react';
import type { RatingDistribution } from '../../types/api.ts';

export interface RatingPoint {
  period: string; // e.g. "2021-03"
  label: string;  // e.g. "Mar 2021"
  avgRating: number;
  reviewCount: number;
}

interface ProductRatingTrendChartProps {
  trendData: RatingPoint[];
  ratingDistribution?: RatingDistribution | null;
  totalReviews?: number;
  loading?: boolean;
}

export const ProductRatingTrendChart: React.FC<ProductRatingTrendChartProps> = ({
  trendData,
  ratingDistribution,
  totalReviews = 0,
  loading = false,
}) => {
  const [hoveredPoint, setHoveredPoint] = useState<RatingPoint | null>(null);
  const [hoveredCoord, setHoveredCoord] = useState<{ x: number; y: number } | null>(null);

  if (loading) {
    return (
      <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 flex flex-col items-center justify-center min-h-[120px] text-slate-400">
        <div className="w-5 h-5 border-2 border-brand-600 border-t-transparent rounded-full animate-spin mb-2" />
        <span className="text-xs">Computing rating metrics...</span>
      </div>
    );
  }

  // Determine if we have sufficient timeline data (at least 2 distinct periods to show a meaningful trend)
  const hasTimeline = trendData && trendData.length >= 2;

  // Determine if rating distribution is available and has non-zero reviews
  const distCounts = ratingDistribution ? [
    ratingDistribution.stars_5 || 0,
    ratingDistribution.stars_4 || 0,
    ratingDistribution.stars_3 || 0,
    ratingDistribution.stars_2 || 0,
    ratingDistribution.stars_1 || 0,
  ] : [];
  const distTotalReviews = distCounts.reduce((acc, c) => acc + c, 0) || totalReviews || 0;
  const hasDistribution = distTotalReviews > 0;

  // 1. If we have sufficient timeline data (>= 2 periods), display the sleek line chart
  if (hasTimeline) {
    const width = 640;
    const height = 140;
    const paddingLeft = 34;
    const paddingRight = 20;
    const paddingTop = 14;
    const paddingBottom = 24;

    const chartW = width - paddingLeft - paddingRight;
    const chartH = height - paddingTop - paddingBottom;

    const yMin = 1.0;
    const yMax = 5.0;

    const getX = (index: number) => {
      return paddingLeft + (index / (trendData.length - 1)) * chartW;
    };

    const getY = (rating: number) => {
      const clamped = Math.max(yMin, Math.min(yMax, rating));
      return paddingTop + chartH - ((clamped - yMin) / (yMax - yMin)) * chartH;
    };

    const points = trendData.map((d, i) => ({
      x: getX(i),
      y: getY(d.avgRating),
      data: d,
    }));

    const pathD = points.reduce(
      (acc, p, i) => `${acc} ${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`,
      ''
    );

    const areaD = `${pathD} L ${points[points.length - 1].x.toFixed(1)} ${(paddingTop + chartH).toFixed(1)} L ${points[0].x.toFixed(1)} ${(paddingTop + chartH).toFixed(1)} Z`;

    const totalPeriodReviews = trendData.reduce((acc, d) => acc + d.reviewCount, 0);
    const weightedSum = trendData.reduce((acc, d) => acc + d.avgRating * d.reviewCount, 0);
    const periodAvg = totalPeriodReviews > 0 ? (weightedSum / totalPeriodReviews).toFixed(2) : '—';
    const firstPeriod = trendData[0].label;
    const lastPeriod = trendData[trendData.length - 1].label;

    const xTicks = [
      0,
      Math.floor((trendData.length - 1) * 0.25),
      Math.floor((trendData.length - 1) * 0.5),
      Math.floor((trendData.length - 1) * 0.75),
      trendData.length - 1,
    ].filter((idx, pos, arr) => arr.indexOf(idx) === pos);

    return (
      <div className="bg-slate-50/70 border border-slate-200/90 rounded-xl p-4 space-y-2.5">
        {/* Header bar */}
        <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-200/70">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-brand-500 animate-pulse" aria-hidden="true" />
            <h3 className="text-xs font-bold text-slate-900 tracking-tight">
              Customer Star Rating Timeline
            </h3>
            <span className="text-[10px] text-slate-500 font-mono bg-white px-1.5 py-0.5 rounded border border-slate-200">
              {trendData.length} monthly intervals
            </span>
          </div>

          <div className="flex items-center gap-3 text-[11px] text-slate-500">
            <span>
              Span: <strong className="font-mono text-slate-700">{firstPeriod}</strong> – <strong className="font-mono text-slate-700">{lastPeriod}</strong>
            </span>
            <span className="hidden sm:inline text-slate-300">|</span>
            <span className="hidden sm:inline">
              Period Mean: <strong className="font-mono text-amber-600">{periodAvg} ★</strong>
            </span>
          </div>
        </div>

        {/* SVG Chart */}
        <div className="relative w-full overflow-hidden">
          <svg
            viewBox={`0 0 ${width} ${height}`}
            className="w-full h-auto overflow-visible select-none"
            preserveAspectRatio="xMidYMid meet"
            role="img"
            aria-label={`Rating trend over time from ${firstPeriod} to ${lastPeriod}`}
          >
            <defs>
              <linearGradient id="brandLineGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#0267c7" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#0267c7" stopOpacity="0.01" />
              </linearGradient>
              <linearGradient id="strokeGrad" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#0c85eb" />
                <stop offset="100%" stopColor="#0267c7" />
              </linearGradient>
            </defs>

            {/* Horizontal Gridlines & Y-Axis Labels */}
            {[1, 2, 3, 4, 5].map((star) => {
              const y = getY(star);
              return (
                <g key={star}>
                  <line
                    x1={paddingLeft}
                    y1={y}
                    x2={width - paddingRight}
                    y2={y}
                    stroke="#e2e8f0"
                    strokeWidth="1"
                    strokeDasharray={star === 1 || star === 5 ? undefined : '2,2'}
                  />
                  <text
                    x={paddingLeft - 5}
                    y={y + 3.5}
                    textAnchor="end"
                    fontSize="9"
                    fontFamily="ui-monospace, monospace"
                    className="fill-slate-400 font-medium"
                  >
                    {star}.0
                  </text>
                </g>
              );
            })}

            {/* Shaded Area under Curve */}
            <path d={areaD} fill="url(#brandLineGrad)" />

            {/* Trend Line */}
            <path
              d={pathD}
              fill="none"
              stroke="url(#strokeGrad)"
              strokeWidth="2.25"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Data Points */}
            {points.map((p) => {
              const isHovered = hoveredPoint?.period === p.data.period;
              return (
                <g
                  key={p.data.period}
                  onMouseEnter={() => {
                    setHoveredPoint(p.data);
                    setHoveredCoord({ x: p.x, y: p.y });
                  }}
                  onMouseLeave={() => {
                    setHoveredPoint(null);
                    setHoveredCoord(null);
                  }}
                  className="cursor-pointer"
                >
                  <circle
                    cx={p.x}
                    cy={p.y}
                    r={isHovered ? 5.5 : points.length > 25 ? 2.5 : 3.5}
                    className={`transition-all duration-150 ${
                      isHovered
                        ? 'fill-amber-400 stroke-brand-700 stroke-2'
                        : 'fill-white stroke-brand-600 stroke-[1.75]'
                    }`}
                  />
                </g>
              );
            })}

            {/* X-Axis Ticks & Labels */}
            {xTicks.map((idx) => {
              const pt = points[idx];
              if (!pt) return null;
              return (
                <text
                  key={pt.data.period}
                  x={pt.x}
                  y={paddingTop + chartH + 15}
                  textAnchor={idx === 0 ? 'start' : idx === trendData.length - 1 ? 'end' : 'middle'}
                  fontSize="9"
                  fontFamily="ui-monospace, monospace"
                  className="fill-slate-500 font-medium"
                >
                  {pt.data.label}
                </text>
              );
            })}
          </svg>

          {/* Floating Tooltip */}
          {hoveredPoint && hoveredCoord && (
            <div
              className="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-full pb-2 transition-all duration-75"
              style={{
                left: `${(hoveredCoord.x / width) * 100}%`,
                top: `${(hoveredCoord.y / height) * 100}%`,
              }}
            >
              <div className="bg-slate-900 text-white text-[11px] rounded-lg shadow-lg px-2.5 py-1.5 whitespace-nowrap space-y-0.5 border border-slate-700">
                <div className="font-semibold text-slate-200 flex items-center justify-between gap-3">
                  <span>{hoveredPoint.label}</span>
                  <span className="text-amber-400 font-mono font-bold">
                    {hoveredPoint.avgRating.toFixed(2)} ★
                  </span>
                </div>
                <div className="text-[10px] text-slate-400 font-mono">
                  {hoveredPoint.reviewCount} {hoveredPoint.reviewCount === 1 ? 'review' : 'reviews'} in period
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer note */}
        <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-slate-200/60">
          <span>Source: Verified customer submission timestamps</span>
          <span className="font-mono">Scale: 1.0 – 5.0 ★</span>
        </div>
      </div>
    );
  }

  // 2. Fallback: Compact Horizontal Rating Distribution Bar Chart
  if (hasDistribution && ratingDistribution) {
    const starLevels = [
      { stars: 5, count: ratingDistribution.stars_5 || 0, color: 'bg-emerald-500', barBg: 'bg-emerald-50' },
      { stars: 4, count: ratingDistribution.stars_4 || 0, color: 'bg-teal-500', barBg: 'bg-teal-50' },
      { stars: 3, count: ratingDistribution.stars_3 || 0, color: 'bg-amber-400', barBg: 'bg-amber-50' },
      { stars: 2, count: ratingDistribution.stars_2 || 0, color: 'bg-orange-400', barBg: 'bg-orange-50' },
      { stars: 1, count: ratingDistribution.stars_1 || 0, color: 'bg-rose-500', barBg: 'bg-rose-50' },
    ];

    const maxCount = Math.max(...starLevels.map((s) => s.count), 1);

    return (
      <div className="bg-slate-50/70 border border-slate-200/90 rounded-xl p-4 space-y-3">
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-200/70">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" aria-hidden="true" />
            <h3 className="text-xs font-bold text-slate-900 tracking-tight">
              Customer Rating Distribution
            </h3>
            <span className="text-[10px] text-slate-500 font-mono bg-white px-1.5 py-0.5 rounded border border-slate-200">
              {distTotalReviews.toLocaleString()} {distTotalReviews === 1 ? 'review' : 'reviews'}
            </span>
          </div>

          <span className="text-[11px] text-slate-500">
            Empirical 1★ to 5★ breakdown
          </span>
        </div>

        {/* Compact Horizontal Bars */}
        <div className="space-y-1.5 pt-0.5">
          {starLevels.map(({ stars, count, color }) => {
            const pct = distTotalReviews > 0 ? (count / distTotalReviews) * 100 : 0;
            const barWidth = maxCount > 0 ? Math.max(count > 0 ? 3 : 0, (count / maxCount) * 100) : 0;

            return (
              <div key={stars} className="flex items-center gap-2.5 text-xs">
                <span className="w-9 font-mono font-semibold text-slate-700 flex items-center gap-1 text-[11px] shrink-0">
                  {stars} <span className="text-amber-500">★</span>
                </span>

                <div className="flex-1 bg-slate-200/70 h-2.5 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${color}`}
                    style={{ width: `${barWidth}%` }}
                    title={`${stars}★: ${count} reviews (${pct.toFixed(1)}%)`}
                  />
                </div>

                <div className="w-20 text-right font-mono text-[11px] text-slate-600 shrink-0">
                  <span className="font-semibold text-slate-800">{count}</span>
                  <span className="text-slate-400 ml-1 text-[10px]">({pct.toFixed(1)}%)</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-slate-200/60">
          <span>Source: Genuine customer star ratings across all sample evaluations</span>
          <span className="font-mono">Total: {distTotalReviews}</span>
        </div>
      </div>
    );
  }

  // 3. Small, unobtrusive empty state when neither timeline nor distribution is available
  return (
    <div className="bg-slate-50/50 border border-slate-200/60 rounded-lg py-2.5 px-3 flex items-center justify-between text-xs text-slate-400">
      <div className="flex items-center gap-2">
        <svg className="w-4 h-4 text-slate-300 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="text-[11px] text-slate-500">No rating history recorded for this product yet.</span>
      </div>
      <span className="text-[10px] font-mono text-slate-400">0 reviews</span>
    </div>
  );
};
