import { useEffect, useState } from "react";
import "./NutritionAnalysis.css";

const API_BASE_URL = "http://127.0.0.1:8000";

const nutrientLabels = {
  calories: "Calories",
  sugar: "Sugar",
  sodium: "Sodium",
  total_fat: "Total Fat",
  saturated_fat: "Saturated Fat",
  trans_fat: "Trans Fat",
  protein: "Protein",
  fiber: "Fiber",
};

function NutritionAnalysis({ productId, onBack }) {
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        setLoading(true);
        setError("");

        const response = await fetch(
          `${API_BASE_URL}/analysis/nutrition/${productId}`
        );

        if (!response.ok) {
          throw new Error("Unable to load nutrition analysis.");
        }

        const data = await response.json();
        setAnalysisData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (productId) {
      fetchAnalysis();
    }
  }, [productId]);

  const getLevelClass = (level) => {
    if (level === "LOW") {
      return "level-low";
    }

    if (level === "MODERATE") {
      return "level-moderate";
    }

    if (level === "HIGH") {
      return "level-high";
    }

    return "level-unknown";
  };

  const formatValue = (value) => {
    if (value === null || value === undefined) {
      return "No data available";
    }

    return value;
  };

  if (loading) {
    return (
      <div className="analysis-page">
        <div className="analysis-message">
          Loading nutrition analysis...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analysis-page">
        <div className="analysis-message error-message">
          {error}
        </div>

        <button
          className="back-button"
          onClick={onBack}
        >
          Back to Product
        </button>
      </div>
    );
  }

  return (
    <div className="analysis-page">

      <div className="analysis-container">

        <button
          className="back-button"
          onClick={onBack}
        >
          Back to Product
        </button>

        <div className="analysis-header">
          <p className="page-label">NUTRITION ANALYSIS</p>

          <h1>{analysisData.product_name}</h1>

          <p>
            Nutrition contribution analysis based on the project's
            reference values.
          </p>
        </div>

        <div className="analysis-grid">

          {Object.entries(analysisData.analysis).map(
            ([nutrientName, nutrient]) => {

              const label =
                nutrientLabels[nutrientName] || nutrientName;

              const hasPercentage =
                nutrient.percentage !== null &&
                nutrient.percentage !== undefined;

              return (
                <div
                  className="analysis-card"
                  key={nutrientName}
                >

                  <div className="card-top">
                    <h2>{label}</h2>

                    <span
                      className={`level-badge ${getLevelClass(
                        nutrient.level
                      )}`}
                    >
                      {nutrient.level === "NO_REFERENCE"
                        ? "NO REFERENCE"
                        : nutrient.level}
                    </span>
                  </div>

                  <div className="nutrient-value">
                    {formatValue(nutrient.value)}

                    {nutrient.value !== null &&
                      nutrient.value !== undefined &&
                      nutrient.unit && (
                        <span className="unit">
                          {" "}
                          {nutrient.unit}
                        </span>
                      )}
                  </div>

                  <div className="analysis-details">

                    <div>
                      <span>Reference</span>

                      <strong>
                        {nutrient.reference_value !== null
                          ? `${nutrient.reference_value} ${nutrient.unit}`
                          : "Not available"}
                      </strong>
                    </div>

                    <div>
                      <span>Contribution</span>

                      <strong>
                        {hasPercentage
                          ? `${nutrient.percentage}%`
                          : "Not available"}
                      </strong>
                    </div>

                  </div>

                  {nutrient.description && (
                    <p className="nutrient-description">
                      {nutrient.description}
                    </p>
                  )}

                </div>
              );
            }
          )}

        </div>

        <div className="analysis-note">

          <h2>About this analysis</h2>

          <p>
            The contribution percentage shows how much one serving
            contributes to the selected reference value.
          </p>

          <p>
            LOW, MODERATE, and HIGH are project-defined analytical
            categories and are not medical diagnoses.
          </p>

        </div>

      </div>

    </div>
  );
}

export default NutritionAnalysis;