import React from 'react';

interface OfflineBannerProps {
  onRetry: () => void;
  isChecking?: boolean;
  message?: string;
}

export const OfflineBanner: React.FC<OfflineBannerProps> = ({
  onRetry,
  isChecking = false,
  message = 'Backend API is currently offline or unreachable at http://localhost:8000.',
}) => {
  return (
    <div
      role="alert"
      className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-lg shadow-sm"
    >
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-start gap-3">
          <svg
            className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <div>
            <h4 className="text-sm font-semibold text-amber-900">Backend Connection Status: Offline</h4>
            <p className="text-xs text-amber-800 mt-0.5">
              {message} The user interface remains functional in read-only offline inspection mode.
            </p>
            <p className="text-xs text-amber-700 mt-1">
              <strong>Recovery guidance:</strong> When ready to connect, start the ProductPulse FastAPI service on <code className="bg-amber-100 px-1 py-0.5 rounded text-amber-900">127.0.0.1:8000</code> and click retry below. Automatic retries are disabled.
            </p>
          </div>
        </div>
        <div className="flex-shrink-0 self-end sm:self-center">
          <button
            type="button"
            onClick={onRetry}
            disabled={isChecking}
            className="inline-flex items-center px-3.5 py-1.5 text-xs font-medium text-amber-900 bg-amber-100 hover:bg-amber-200 border border-amber-300 rounded-md transition-colors disabled:opacity-50"
            aria-label="Retry connection to backend"
          >
            {isChecking ? (
              <>
                <svg className="animate-spin -ml-0.5 mr-2 h-3.5 w-3.5 text-amber-800" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                Checking...
              </>
            ) : (
              'Retry Connection'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
