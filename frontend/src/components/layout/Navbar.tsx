import React, { useState } from 'react';
import type { HealthStatus } from '../../types/api.ts';

export type NavigationTab =
  | 'overview'
  | 'catalogue'
  | 'reviews'
  | 'sentiment'
  | 'complaints'
  | 'bda';

interface NavbarProps {
  activeTab: NavigationTab;
  onSelectTab: (tab: NavigationTab) => void;
  health: HealthStatus | null;
  isHealthChecking: boolean;
  onRefreshHealth: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  onSelectTab,
  health,
  isHealthChecking,
  onRefreshHealth,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const tabs: { id: NavigationTab; label: string; badge?: string }[] = [
    { id: 'catalogue', label: 'Products' },
    { id: 'bda', label: 'Review Analytics' },
    { id: 'reviews', label: 'Customer Reviews' },
    { id: 'overview', label: 'About & Methodology' },
  ];

  const isOnline = health?.status === 'healthy';

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Category Lock */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => onSelectTab('overview')}
              className="flex items-center gap-2.5 text-left focus:outline-none"
              aria-label="ProductPulse Dashboard Home"
            >
              <div className="w-9 h-9 rounded-lg bg-brand-600 flex items-center justify-center text-white shadow-sm font-bold text-lg">
                P
              </div>
              <div>
                <span className="text-base font-bold text-slate-900 tracking-tight block">
                  ProductPulse
                </span>
                <span className="text-[10px] text-slate-500 font-mono tracking-wider block uppercase">
                  Analytics Platform
                </span>
              </div>
            </button>

            <span className="hidden md:inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-600 border border-slate-200 ml-2">
              Domain: Cell_Phones_and_Accessories
            </span>
          </div>

          {/* Desktop Navigation Links */}
          <nav className="hidden lg:flex items-center space-x-1" aria-label="Main Navigation">
            {tabs.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => onSelectTab(tab.id)}
                  className={`px-3 py-2 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5 ${
                    isActive
                      ? 'bg-slate-100 text-brand-700 font-semibold shadow-inner'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                  aria-current={isActive ? 'page' : undefined}
                >
                  {tab.label}
                  {tab.badge && (
                    <span
                      className={`text-[9px] px-1.5 py-0.2 rounded font-mono ${
                        isActive
                          ? 'bg-brand-100 text-brand-800'
                          : 'bg-slate-100 text-slate-500'
                      }`}
                    >
                      {tab.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* Right: Backend Connection Status Pill */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onRefreshHealth}
              disabled={isHealthChecking}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
                isHealthChecking
                  ? 'bg-slate-50 text-slate-500 border-slate-200'
                  : isOnline
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100'
                  : 'bg-amber-50 text-amber-800 border-amber-200 hover:bg-amber-100'
              }`}
              title="Click to re-check backend status (single check, no automatic loop)"
              aria-label={`Backend connection status: ${
                isHealthChecking ? 'checking' : isOnline ? 'connected' : 'offline'
              }. Click to refresh.`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  isHealthChecking
                    ? 'bg-slate-400 animate-pulse'
                    : isOnline
                    ? 'bg-emerald-500'
                    : 'bg-amber-500'
                }`}
              />
              <span className="hidden sm:inline">
                {isHealthChecking
                  ? 'Checking...'
                  : isOnline
                  ? 'Backend: Online'
                  : 'Backend: Offline'}
              </span>
            </button>

            {/* Mobile Hamburger Button */}
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-md"
              aria-label="Toggle mobile menu"
              aria-expanded={mobileMenuOpen}
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-slate-200 bg-white px-4 pt-2 pb-3 space-y-1">
          <div className="pb-2 mb-2 border-b border-slate-100">
            <span className="text-xs text-slate-500">
              Domain Lock: <strong className="text-slate-700">Cell_Phones_and_Accessories</strong>
            </span>
          </div>
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => {
                  onSelectTab(tab.id);
                  setMobileMenuOpen(false);
                }}
                className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium flex items-center justify-between ${
                  isActive
                    ? 'bg-slate-100 text-brand-700 font-semibold'
                    : 'text-slate-600 hover:bg-slate-50'
                }`}
              >
                <span>{tab.label}</span>
                {tab.badge && (
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-500 font-mono">
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </header>
  );
};
