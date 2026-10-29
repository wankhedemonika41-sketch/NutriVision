import HealthScoreCard from "./HealthScoreCard";

const NUTRIENT_ITEMS = [
  ["calories", "Calories", "kcal"],
  ["carbohydrates", "Carbohydrates", "g"],
  ["protein", "Protein", "g"],
  ["total_fat", "Total Fat", "g"],
  ["saturated_fat", "Saturated Fat", "g"],
  ["trans_fat", "Trans Fat", "g"],
  ["sugar", "Sugar", "g"],
  ["sodium", "Sodium", "mg"],
  ["fiber", "Fiber", "g"],
  ["cholesterol", "Cholesterol", "mg"],
];

const SEVERITY_COLORS = {
  caution: "#dc2626",
  info: "#2563eb",
  positive: "#16a34a",
};

const cardStyle = {
  border: "1px solid #e5e7eb",
  borderRadius: 12,
  padding: 16,
  marginBottom: 16,
  background: "#fff",
};

function AnalysisResult({ result }) {
  if (!result) {
    return null;
  }

  const { product, nutrition, ingredient_analysis: ingredientAnalysis } = result;

  return (
    <div style={{ textAlign: "left" }}>

      <div style={{ ...cardStyle, overflow: "hidden" }}>
        {product?.image_url && (
          <img
            src={product.image_url}
            alt={product.product_name}
            style={{ height: 80, float: "right", borderRadius: 8 }}
          />
        )}

        <small style={{ color: "#6b7280" }}>
          Source: {result.source}
        </small>

        <h2 style={{ margin: "4px 0" }}>
          {product?.product_name || "Unnamed product"}
        </h2>

        <p style={{ margin: 0, color: "#6b7280" }}>
          {product?.brand || "Brand not available"}
          {product?.category ? ` • ${product.category}` : ""}
        </p>
      </div>

      <HealthScoreCard health={result.health} />

      {nutrition && (
        <div style={cardStyle}>
          <h3 style={{ marginTop: 0 }}>Nutrition (per 100 g)</h3>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
              gap: 10,
            }}
          >
            {NUTRIENT_ITEMS.map(([key, label, unit]) => (
              <div
                key={key}
                style={{
                  background: "#f9fafb",
                  borderRadius: 8,
                  padding: 10,
                }}
              >
                <div style={{ fontSize: 12, color: "#6b7280" }}>
                  {label}
                </div>

                <strong>{nutrition[key] ?? "N/A"}</strong>{" "}
                <small>{unit}</small>
              </div>
            ))}
          </div>
        </div>
      )}

      {ingredientAnalysis && (
        <div style={cardStyle}>
          <h3 style={{ marginTop: 0 }}>Ingredients</h3>

          <p style={{ color: "#374151" }}>
            {product?.ingredients || "Ingredients information not available."}
          </p>

          {ingredientAnalysis.highlights?.length > 0 && (
            <ul style={{ paddingLeft: 18 }}>
              {ingredientAnalysis.highlights.map((item) => (
                <li
                  key={item.type}
                  style={{ color: SEVERITY_COLORS[item.severity] }}
                >
                  <strong>{item.label}</strong>: {item.note}
                </li>
              ))}
            </ul>
          )}

          {ingredientAnalysis.allergens?.length > 0 && (
            <p>
              <strong>Contains:</strong>{" "}
              {ingredientAnalysis.allergens.join(", ")}
            </p>
          )}

          <small style={{ color: "#6b7280" }}>
            {ingredientAnalysis.disclaimer}
          </small>
        </div>
      )}

    </div>
  );
}

export default AnalysisResult;