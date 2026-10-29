// Helpers for saving what the user looked at (scan history).

const numberOrNull = (value) =>
  typeof value === "number" && Number.isFinite(value) ? value : null;

/**
 * Turns a result shown on screen (barcode scan or label scan) into the
 * snapshot the server stores. Returns null when there is no health score,
 * so nothing is saved for products we could not score.
 */
export function snapshotFromResult(source, result, barcode) {
  const health = result?.health;

  if (!health?.available) {
    return null;
  }

  const product = result.product || {};
  const per = health.per_100g || {};

  const code = String(barcode ?? product.barcode ?? "").trim();

  return {
    source,
    barcode: source !== "label" && /^\d{6,14}$/.test(code) ? code : null,
    product_name: product.product_name || "Unnamed product",
    brand: product.brand || null,
    category: product.category || null,
    score: health.score,
    grade: health.grade,
    calories: numberOrNull(per.calories),
    sugar: numberOrNull(per.sugar),
    sodium: numberOrNull(per.sodium),
    saturated_fat: numberOrNull(per.saturated_fat),
    protein: numberOrNull(per.protein),
    fiber: numberOrNull(per.fiber),
    cautions: (result.ingredient_analysis?.highlights || [])
      .filter((item) => item.severity === "caution")
      .map((item) => item.label),
  };
}

// Minutes the user's clock is ahead of UTC (India = 330)
export const timezoneOffset = () => -new Date().getTimezoneOffset();