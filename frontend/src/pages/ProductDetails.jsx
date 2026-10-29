import { useEffect, useState } from "react";
import { API_URL } from "../config";
import HealthScoreCard from "../components/HealthScoreCard";
import Recommendations from "../components/Recommendations";
import RecordScan from "../components/RecordScan";
import "./ProductDetails.css";

function ProductDetails({
  productId,
  onBack,
  onAnalyze,
  onOpenProduct,
  onOpenProfile,
}) {
  const [productDetails, setProductDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [health, setHealth] = useState(null);
  const [healthFor, setHealthFor] = useState(null);   // which product `health` belongs to
  const [healthLoading, setHealthLoading] = useState(false);
  const [healthError, setHealthError] = useState("");

  useEffect(() => {
    if (!productId) {
      return;
    }

    let cancelled = false;

    window.scrollTo({ top: 0 });

    const fetchProductDetails = async () => {
      try {
        setLoading(true);
        setError("");

        const response = await fetch(
          `${API_URL}/products/details/${productId}`
        );

        if (!response.ok) {
          throw new Error("Unable to fetch product details.");
        }

        const data = await response.json();

        if (!cancelled) {
          setProductDetails(data);
        }
      } catch (err) {
        console.error("Product details error:", err);

        if (!cancelled) {
          setError(
            "Unable to load product details. Please make sure the backend is running."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    const fetchHealthScore = async () => {
      try {
        setHealthLoading(true);
        setHealthError("");
        setHealth(null);

        const response = await fetch(
          `${API_URL}/health-score/product/${productId}`
        );

        if (response.status === 404) {
          throw new Error(
            "Health score is not available for this product."
          );
        }

        if (!response.ok) {
          throw new Error("Unable to calculate the health score.");
        }

        const data = await response.json();

        if (!cancelled) {
          setHealth(data);
          setHealthFor(productId);
        }
      } catch (err) {
        console.error("Health score error:", err);

        if (!cancelled) {
          setHealthError(err.message);
        }
      } finally {
        if (!cancelled) {
          setHealthLoading(false);
        }
      }
    };

    fetchProductDetails();
    fetchHealthScore();

    return () => {
      cancelled = true;
    };
  }, [productId]);

  if (loading) {
    return (
      <div className="product-details-page">
        <div className="product-details-container">
          <p className="details-message">
            Loading product details...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="product-details-page">
        <div className="product-details-container">
          <button
            className="back-button"
            onClick={onBack}
          >
            Back to Search
          </button>

          <p className="details-error">
            {error}
          </p>
        </div>
      </div>
    );
  }

  if (!productDetails) {
    return null;
  }

  const product = productDetails.product;
  const nutrition = productDetails.nutrition;

  return (
    <div className="product-details-page">
      <div className="product-details-container">

        <button
          className="back-button"
          onClick={onBack}
        >
          Back to Search
        </button>

        <div className="details-header">
          <p className="details-label">
            PRODUCT DETAILS
          </p>

          <h1>{product.product_name}</h1>

          <p className="details-brand">
            {product.brand || "Brand not available"}
          </p>
        </div>

        <div className="details-grid">

          <section className="details-card">

            <h2>Product Information</h2>

            <div className="info-list">

              <div className="info-row">
                <span>Product Name</span>
                <strong>
                  {product.product_name || "Not available"}
                </strong>
              </div>

              <div className="info-row">
                <span>Brand</span>
                <strong>
                  {product.brand || "Not available"}
                </strong>
              </div>

              <div className="info-row">
                <span>Category</span>
                <strong>
                  {product.category || "Not available"}
                </strong>
              </div>

              <div className="info-row">
                <span>Sub Category</span>
                <strong>
                  {product.sub_category || "Not available"}
                </strong>
              </div>

              <div className="info-row">
                <span>Serving Size</span>
                <strong>
                  {product.serving_size || "Not available"}
                </strong>
              </div>

              <div className="info-row">
                <span>Price</span>
                <strong>
                  {product.price_inr
                    ? `Rs. ${product.price_inr}`
                    : "Not available"}
                </strong>
              </div>

            </div>

          </section>

          <section className="details-card">

            <h2>Ingredients</h2>

            <p className="ingredients-text">
              {product.ingredients || "Ingredients information not available."}
            </p>

          </section>

        </div>


        {/* HEALTH SCORE */}

        <section className="health-section">

          {healthLoading && (
            <p className="details-message">
              Calculating health score...
            </p>
          )}

          {!healthLoading && healthError && (
            <p className="details-message">
              {healthError}
            </p>
          )}

          {!healthLoading && health && (
            <HealthScoreCard health={health} />
          )}

          {!healthLoading && health?.available && healthFor === productId && (
            <RecordScan key={productId} source="product" productId={productId} />
          )}

        </section>


        {/* HEALTHIER ALTERNATIVES */}

        {nutrition && (
          <Recommendations
            productId={productId}
            onOpenProduct={onOpenProduct}
            onOpenProfile={onOpenProfile}
          />
        )}


        <section className="nutrition-section">

          <div className="section-heading">
            <p className="details-label">
              NUTRITION INFORMATION
            </p>

            <h2>Nutrition Facts</h2>

            <p>
              Nutritional values available in the database
              for this product.
            </p>
          </div>

          {!nutrition ? (
            <div className="nutrition-unavailable">
              Nutrition information is not available
              for this product.
            </div>
          ) : (
            <div className="nutrition-grid">

              <div className="nutrition-card">
                <span>Calories</span>
                <strong>
                  {nutrition.calories ?? "N/A"}
                </strong>
                <small>kcal</small>
              </div>

              <div className="nutrition-card">
                <span>Carbohydrates</span>
                <strong>
                  {nutrition.carbohydrates ?? "N/A"}
                </strong>
                <small>g</small>
              </div>

              <div className="nutrition-card">
                <span>Protein</span>
                <strong>
                  {nutrition.protein ?? "N/A"}
                </strong>
                <small>g</small>
              </div>

              <div className="nutrition-card">
                <span>Total Fat</span>
                <strong>
                  {nutrition.total_fat ?? "N/A"}
                </strong>
                <small>g</small>
              </div>

              <div className="nutrition-card">
                <span>Saturated Fat</span>
                <strong>
                  {nutrition.saturated_fat ?? "N/A"}
                </strong>
                <small>g</small>
              </div>

              <div className="nutrition-card">
                <span>Trans Fat</span>
                <strong>
                  {nutrition.trans_fat ?? "N/A"}
                </strong>
                <small>g</small>
              </div>

              <div className="nutrition-card">
                <span>Sugar</span>
                <strong>
                  {nutrition.sugar ?? "N/A"}
                </strong>
                <small>g</small>
              </div>

              <div className="nutrition-card">
                <span>Sodium</span>
                <strong>
                  {nutrition.sodium ?? "N/A"}
                </strong>
                <small>mg</small>
              </div>

              <div className="nutrition-card">
                <span>Fiber</span>
                <strong>
                  {nutrition.fiber ?? "N/A"}
                </strong>
                <small>g</small>
              </div>

              <div className="nutrition-card">
                <span>Cholesterol</span>
                <strong>
                  {nutrition.cholesterol ?? "N/A"}
                </strong>
                <small>mg</small>
              </div>

              <div className="nutrition-card">
                <span>Calcium</span>
                <strong>
                  {nutrition.calcium ?? "N/A"}
                </strong>
                <small>mg</small>
              </div>

              <div className="nutrition-card">
                <span>Iron</span>
                <strong>
                  {nutrition.iron ?? "N/A"}
                </strong>
                <small>mg</small>
              </div>

              <div className="nutrition-card vitamin-card">
                <span>Vitamin</span>
                <strong>
                  {nutrition.vitamin || "N/A"}
                </strong>
              </div>

            </div>
          )}

        </section>


        {/* ANALYZE NUTRITION BUTTON */}

        <div className="analysis-action">

          <button
            className="primary-button"
            onClick={onAnalyze}
          >
            Analyze Nutrition
          </button>

        </div>

      </div>
    </div>
  );
}

export default ProductDetails;