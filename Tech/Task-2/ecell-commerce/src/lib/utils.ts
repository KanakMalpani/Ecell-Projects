export function formatCurrency(amount: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

export function slugify(text: string) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

export function generateOrderNumber() {
  const ts = Date.now().toString(36).toUpperCase();
  const rand = Math.random().toString(36).substring(2, 6).toUpperCase();
  return `EC-${ts}-${rand}`;
}

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
