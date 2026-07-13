/**
 * Shared Utility Functions — formatting and business logic helpers.
 *
 * ROLE IN THE APP:
 *   Pure functions used across storefront pages, admin panel, and API routes.
 *   Keeps display formatting and ID generation DRY and testable.
 *
 * PI INTERVIEW TALKING POINTS:
 *   - formatCurrency uses Intl.NumberFormat for locale-aware ₹ formatting
 *   - slugify creates URL-safe product slugs from human-readable names
 *   - generateOrderNumber combines timestamp + random for unique, readable IDs
 *   - isBannerActive encapsulates date-range + active-flag banner logic
 */

/** Format a number as Indian Rupees, e.g. 1500 → "₹1,500" */
export function formatCurrency(amount: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

/** Convert text to URL-friendly slug, e.g. "Blue T-Shirt" → "blue-t-shirt" */
export function slugify(text: string) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

/** Generate a unique order number like "EC-LK3F9A-X7B2" */
export function generateOrderNumber() {
  const ts = Date.now().toString(36).toUpperCase();
  const rand = Math.random().toString(36).substring(2, 6).toUpperCase();
  return `EC-${ts}-${rand}`;
}

/**
 * Check if a promotional banner should be shown right now.
 * Considers: active flag, startDate, and endDate.
 */
export function isBannerActive(banner: {
  active: boolean;
  startDate: Date | null;
  endDate: Date | null;
}) {
  if (!banner.active) return false;
  const now = new Date();
  if (banner.startDate && now < banner.startDate) return false;
  if (banner.endDate && now > banner.endDate) return false;
  return true;
}
