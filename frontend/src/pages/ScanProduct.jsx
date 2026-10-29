import { useEffect, useRef, useState } from "react";
import { Html5Qrcode } from "html5-qrcode";
import HealthScoreCard from "../components/HealthScoreCard";
import RecordScan from "../components/RecordScan";
import "./ScanProduct.css";

const API_URL = "http://127.0.0.1:8000";
const BARCODE_PATTERN = /^\d{6,14}$/;

const NUTRIENT_ITEMS = [
  ["calories", "Calories", "kcal"],
  ["carbohydrates", "Carbohydrates", "g"],
  ["protein", "Protein", "g"],
  ["total_fat", "Total Fat", "g"],
  ["saturated_fat", "Saturated Fat", "g"],
  ["sugar", "Sugar", "g"],
  ["sodium", "Sodium", "mg"],
  ["fiber", "Fiber", "g"],
];

const SEVERITY_COLORS = {
  caution: "#dc2626",
  info: "#2563eb",
  positive: "#16a34a",
};

function ScanProduct({ onBack }) {
  const [barcode, setBarcode] = useState("");
  const [scannerRunning, setScannerRunning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const scannerRef = useRef(null);

  // Camera ko band karo jab user is page se bahar jaye
  useEffect(() => {
    return () => {
      const scanner = scannerRef.current;

      if (scanner) {
        scanner
          .stop()
          .then(() => scanner.clear())
          .catch(() => {});
      }
    };
  }, []);

  const stopScanner = async () => {
    const scanner = scannerRef.current;

    scannerRef.current = null;
    setScannerRunning(false);

    if (!scanner) {
      return;
    }

    try {
      await scanner.stop();
    } catch (err) {
      console.error("Scanner stop error:", err);
    }

    try {
      scanner.clear();
    } catch (err) {
      console.error("Scanner clear error:", err);
    }
  };

  const lookupProduct = async (code) => {
    const cleaned = code.trim();

    if (!BARCODE_PATTERN.test(cleaned)) {
      setError("A barcode contains 6 to 14 digits.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(
        `${API_URL}/health-score/barcode/${cleaned}`
      );

      if (!response.ok) {
        let message = "Unable to find this product.";

        try {
          const body = await response.json();

          if (typeof body.detail === "string") {
            message = body.detail;
          }
        } catch {
          // response body was not JSON
        }

        throw new Error(message);
      }

      const data = await response.json();

      setResult(data);
    } catch (err) {
      console.error("Scan lookup error:", err);

      setError(
        err.message === "Failed to fetch"
          ? "Unable to reach the backend. Please make sure it is running."
          : err.message
      );
    } finally {
      setLoading(false);
    }
  };

  const startScanner = async () => {
    setError("");
    setResult(null);

    try {
      const scanner = new Html5Qrcode("barcode-reader");

      scannerRef.current = scanner;
      setScannerRunning(true);

      await scanner.start(
        { facingMode: "environment" },
        {
          fps: 10,
          qrbox: {
            width: 300,
            height: 150,
          },
        },
        (decodedText) => {
          // Ek hi scan ko ek baar process karo
          if (scannerRef.current !== scanner) {
            return;
          }

          setBarcode(decodedText);
          stopScanner();
          lookupProduct(decodedText);
        },
        () => {
          // Scanner is still searching for a barcode.
        }
      );
    } catch (err) {
      console.error("Camera error:", err);

      scannerRef.current = null;
      setScannerRunning(false);

      alert(
        "Unable to access the camera. Please allow camera permission."
      );
    }
  };

  const handleFindProduct = () => {
    if (!barcode.trim()) {
      setError("Please scan or enter a barcode.");
      return;
    }

    lookupProduct(barcode);
  };

  const handleReset = () => {
    setBarcode("");
    setResult(null);
    setError("");
  };

  const product = result?.product;
  const nutrition = result?.nutrition;
  const ingredientAnalysis = result?.ingredient_analysis;

  return (
    <div className="scan-page">
      <div className="scan-container">

        <button
          className="back-button"
          onClick={onBack}
        >
          Back to Home
        </button>

        <h1>Scan Your Product</h1>

        <p className="scan-description">
          Scan the barcode of your food product to get
          nutrition and ingredient analysis.
        </p>

        <div className="scanner-box">

          <div id="barcode-reader"></div>

          {!scannerRunning && (
            <>
              <h2>Barcode Scanner</h2>

              <p>
                Place the product barcode inside the camera area.
              </p>

              <button
                className="camera-button"
                onClick={startScanner}
              >
                Open Camera
              </button>
            </>
          )}

          {scannerRunning && (
            <button
              className="camera-button"
              onClick={stopScanner}
            >
              Stop Camera
            </button>
          )}

        </div>

        <div className="divider">
          <span>OR</span>
        </div>

        <div className="manual-section">

          <h2>Enter Barcode Manually</h2>

          <input
            type="text"
            inputMode="numeric"
            placeholder="Enter product barcode"
            value={barcode}
            onChange={(e) => setBarcode(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleFindProduct();
              }
            }}
          />

          <button
            className="find-button"
            onClick={handleFindProduct}
            disabled={loading}
          >
            {loading ? "Searching..." : "Find Product"}
          </button>

        </div>


        {/* ERROR */}

        {error && (
          <p
            style={{
              color: "#dc2626",
              marginTop: 16,
              textAlign: "center",
            }}
          >
            {error}
          </p>
        )}


        {/* RESULT */}

        {result && product && (
          <div style={{ marginTop: 24, textAlign: "left" }}>

            <div
              style={{
                border: "1px solid #e5e7eb",
                borderRadius: 12,
                padding: 16,
                marginBottom: 16,
                overflow: "hidden",
              }}
            >
              {product.image_url && (
                <img
                  src={product.image_url}
                  alt={product.product_name}
                  style={{
                    height: 80,
                    float: "right",
                    borderRadius: 8,
                  }}
                />
              )}

              <small style={{ color: "#6b7280" }}>
                Source: {result.source}
              </small>

              <h2 style={{ margin: "4px 0" }}>
                {product.product_name || "Unnamed product"}
              </h2>

              <p style={{ margin: 0, color: "#6b7280" }}>
                {product.brand || "Brand not available"}
                {product.category ? ` • ${product.category}` : ""}
              </p>
            </div>

            <HealthScoreCard health={result.health} />

            <RecordScan source="barcode" result={result} barcode={barcode} />

            {nutrition && (
              <div
                style={{
                  border: "1px solid #e5e7eb",
                  borderRadius: 12,
                  padding: 16,
                  marginBottom: 16,
                }}
              >
                <h3 style={{ marginTop: 0 }}>Nutrition (per 100 g)</h3>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns:
                      "repeat(auto-fit, minmax(120px, 1fr))",
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

                      <strong>
                        {nutrition[key] ?? "N/A"}
                      </strong>{" "}

                      <small>{unit}</small>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {ingredientAnalysis && (
              <div
                style={{
                  border: "1px solid #e5e7eb",
                  borderRadius: 12,
                  padding: 16,
                  marginBottom: 16,
                }}
              >
                <h3 style={{ marginTop: 0 }}>Ingredients</h3>

                <p style={{ color: "#374151" }}>
                  {product.ingredients ||
                    "Ingredients information not available."}
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

            <button
              className="find-button"
              onClick={handleReset}
            >
              Scan Another Product
            </button>

          </div>
        )}

      </div>
    </div>
  );
}

export default ScanProduct;