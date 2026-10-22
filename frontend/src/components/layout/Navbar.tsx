import React, { useState } from 'react';
import type { HealthStatus } from '../../types/api.ts';
import { Logo } from '../common/Logo.tsx';

export type NavigationTab =
  | 'home'
  | 'catalogue'
  | 'bda'
  | 'reviews'
  | 'overview'
  | 'sentiment'
  | 'complaints';

interface NavbarProps {
  activeTab: NavigationTab;
  onSelectTab: (tab: NavigationTab) => void;
  health?: HealthStatus | null;
  isHealthChecking?: boolean;
  onRefreshHealth?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  onSelectTab,
  health: _health,
  isHealthChecking: _isHealthChecking,
  onRefreshHealth: _onRefreshHealth,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const tabs: { id: NavigationTab; label: string; badge?: string }[] = [
    { id: 'home', label: 'Home' },
    { id: 'catalogue', label: 'Products' },
    { id: 'bda', label: 'Review Analytics' },
    { id: 'reviews', label: 'Customer Reviews' },
    { id: 'overview', label: 'About & Methodology' },
  ];

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Redesigned Brand Logo */}
          <div className="flex items-center">
            <button
              type="button"
              onClick={() => onSelectTab('home')}
              className="flex items-center text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded-lg"
              aria-label="ProductPulse Dashboard Home"
            >
              <Logo size="md" />
            </button>
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

          {/* Right Controls / Mobile Menu Trigger */}
          <div className="flex items-center gap-2">
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
