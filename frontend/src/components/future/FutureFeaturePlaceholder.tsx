import React from 'react';

interface FutureFeaturePlaceholderProps {
  title: string;
  phaseTag: string;
  category: string;
  description: string;
  scheduledMilestones: string[];
  scientificConstraints: string[];
}

export const FutureFeaturePlaceholder: React.FC<FutureFeaturePlaceholderProps> = ({
  title,
  phaseTag,
  category,
  description,
  scheduledMilestones,
  scientificConstraints,
}) => {
  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-4 mb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono font-semibold uppercase tracking-wider text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded">
                {phaseTag} — Planned
              </span>
              <span className="text-xs font-mono text-slate-500">
                Scope: {category}
              </span>
            </div>
            <h2 className="text-xl font-bold text-slate-900">{title}</h2>
          </div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200 self-start sm:self-auto">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            Not Yet Implemented
          </div>
        </div>

        <p className="text-sm text-slate-600 leading-relaxed mb-4">
          {description}
        </p>

        <div className="bg-slate-50 border border-slate-200 rounded-md p-3.5 text-xs text-slate-600">
          <strong className="text-slate-800">Academic Transparency Policy:</strong> ProductPulse strictly prohibits fabricating NLP predictions, mock sentiment charts, or fictitious Big Data execution counts. This section is reserved for verified outputs following future phase completion.
        </div>
      </div>

      {/* Grid of Planned Technical Specifications */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Planned Implementation Steps */}
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
            <svg className="w-4 h-4 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
            Planned Technical Deliverables
          </h3>
          <ul className="space-y-2 text-xs text-slate-600">
            {scheduledMilestones.map((milestone, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-brand-600 font-bold">•</span>
                <span>{milestone}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Scientific Constraints & Guardrails */}
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
            <svg className="w-4 h-4 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Scientific &amp; Methodological Guardrails
          </h3>
          <ul className="space-y-2 text-xs text-slate-600">
            {scientificConstraints.map((constraint, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-amber-600 font-bold">•</span>
                <span>{constraint}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};
