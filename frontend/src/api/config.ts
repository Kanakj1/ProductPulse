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
 * Checks for custom override, then Vite runtime environment override,
 * then browser runtime host resolution (using Vite proxy or matching loopback host),
 * then falls back to DEFAULT_API_BASE_URL.
 */
export function getApiBaseUrl(): string {
  if (customBaseUrl !== null) {
    return customBaseUrl;
  }
  try {
    if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL !== undefined) {
      return import.meta.env.VITE_API_BASE_URL as string;
    }
  } catch {
    // Fallback if import.meta is unavailable
  }

  // Browser runtime host resolution
  if (typeof window !== 'undefined' && window.location) {
    // If served from Vite dev server (port 5173) with /api proxy, use same-origin relative path
    if (window.location.port === '5173') {
      return '';
    }
    // If accessing via 127.0.0.1, match the IPv4 host to avoid IPv6 localhost resolution mismatch
    if (window.location.hostname === '127.0.0.1') {
      return 'http://127.0.0.1:8000';
    }
  }

  return DEFAULT_API_BASE_URL;
}
