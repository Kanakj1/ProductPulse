/**
 * ProductPulse — Centralized API Configuration
 */

// Default backend URL per ARCHITECTURE.md and PROJECT_SPEC.md
export const DEFAULT_API_BASE_URL = 'http://localhost:8000';

// Permitted Category Lock
export const CATEGORY_LOCK = 'Cell_Phones_and_Accessories';

let customBaseUrl: string | null = null;

/**
 * Sets a custom API base URL (useful for testing or staging overrides).
 */
export function setApiBaseUrl(url: string | null): void {
  customBaseUrl = url;
}

/**
 * Resolves the active API base URL.
 * Checks for custom override, then Vite runtime environment override, then falls back to DEFAULT_API_BASE_URL.
 */
export function getApiBaseUrl(): string {
  if (customBaseUrl) {
    return customBaseUrl;
  }
  try {
    if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL) {
      return import.meta.env.VITE_API_BASE_URL as string;
    }
  } catch {
    // Fallback if import.meta is unavailable
  }
  return DEFAULT_API_BASE_URL;
}
