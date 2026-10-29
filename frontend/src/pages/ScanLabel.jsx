import { useEffect, useState } from "react";
import AnalysisResult from "../components/AnalysisResult";
import RecordScan from "../components/RecordScan";
import "./ScanProduct.css";

const API_URL = "http://127.0.0.1:8000";

const FIELDS = [
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

const REQUIRED = ["calories", "sugar", "sodium"];

const boxStyle = {
  background: "#fff",
  border: "1px solid #e5e7eb",
  borderRadius: 12,
  padding: 16,
  marginBottom: 16,
  textAlign: "left",
};

const inputStyle = {
  width: "100%",
  padding: "8px 10px",
  borderRadius: 8,
  border: "1px solid #d1d5db",
  background: "#fff",
  color: "#111827",
  boxSizing: "border-box",
};

function errorMessage(body, fallback) {
  const detail = body?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((d) => d.msg).join(". ");
  }

  return fallback;
}

function ScanLabel({ onBack }) {
  const [step, setStep] = useState("upload");        // upload | review | result
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [ocr, setOcr] = useState(null);
  const [form, setForm] = useState(null);
  const [result, setResult] = useState(null);

  // preview ka memory cleanup
  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const handleFile = (event) => {
    const chosen = event.target.files?.[0];

    if (!chosen) {
      return;
    }

    setFile(chosen);
    setPreviewUrl(URL.createObjectURL(chosen));
    setError("");
  };

  const readLabel = async () => {
    if (!file) {
      setError("Please choose or take a photo of the label first.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const data = new FormData();
      data.append("file", file);

      const response = await fetch(`${API_URL}/ocr/scan`, {
        method: "POST",
        body: data,
      });

      const body = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(errorMessage(body, "Unable to read the label."));
      }

      const nutrition = {};

      FIELDS.forEach(([key]) => {
        nutrition[key] = body.nutrition[key] ?? "";
      });

      setOcr(body);
      setForm({
        product_name: "",
        category: "",
        ingredients: body.ingredients || "",
        basis: body.basis,
        serving_size_g: body.serving_size_g ?? "",
        nutrition,
      });
      setStep("review");
    } catch (err) {
      console.error("OCR error:", err);

      setError(
        err.message === "Failed to fetch"
          ? "Unable to reach the backend. Please make sure it is running."
          : err.message
      );
    } finally {
      setLoading(false);
    }
  };

  const setNutrition = (key, value) => {
    setForm((current) => ({
      ...current,
      nutrition: { ...current.nutrition, [key]: value },
    }));
  };

  const analyze = async () => {
    const missing = REQUIRED.filter((key) => form.nutrition[key] === "");

    if (missing.length > 0) {
      setError(
        `Please fill in: ${missing.join(", ")}. These are needed for the health score.`
      );
      return;
    }

    const nutrition = {};

    FIELDS.forEach(([key]) => {
      const raw = form.nutrition[key];
      nutrition[key] = raw === "" ? null : Number(raw);
    });

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/ocr/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_name: form.product_name,
          category: form.category || null,
          ingredients: form.ingredients || null,
          nutrition,
          basis: form.basis,
          serving_size_g:
            form.serving_size_g === "" ? null : Number(form.serving_size_g),
        }),
      });

      const body = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(errorMessage(body, "Unable to analyse the label."));
      }

      setResult(body);
      setStep("result");
    } catch (err) {
      console.error("Analyse error:", err);

      setError(
        err.message === "Failed to fetch"
          ? "Unable to reach the backend. Please make sure it is running."
          : err.message
      );
    } finally {
      setLoading(false);
    }
  };

  const startOver = () => {
    setStep("upload");
    setFile(null);
    setPreviewUrl("");
    setOcr(null);
    setForm(null);
    setResult(null);
    setError("");
  };

  return (
    <div className="scan-page">
      <div className="scan-container">

        <button className="back-button" onClick={onBack}>
          Back to Home
        </button>

        <h1>Scan Food Label</h1>

        <p className="scan-description">
          Take a photo of the ingredients and nutrition table. We read the
          text, you check it, and then we analyse it.
        </p>

        {error && (
          <p style={{ color: "#dc2626", textAlign: "center" }}>
            {error}
          </p>
        )}


        {/* STEP 1: UPLOAD */}

        {step === "upload" && (
          <div style={boxStyle}>

            <h3 style={{ marginTop: 0 }}>1. Add a photo</h3>

            <input
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handleFile}
              style={{ marginBottom: 12 }}
            />

            {previewUrl && (
              <img
                src={previewUrl}
                alt="Label preview"
                style={{
                  display: "block",
                  maxWidth: "100%",
                  maxHeight: 320,
                  borderRadius: 8,
                  marginBottom: 12,
                }}
              />
            )}

            <p style={{ color: "#6b7280", fontSize: 13 }}>
              Tips: keep the label flat and straight, use good light, and
              come close so the text fills the photo.
            </p>

            <button
              className="find-button"
              onClick={readLabel}
              disabled={loading || !file}
            >
              {loading ? "Reading label..." : "Read Label"}
            </button>

          </div>
        )}


        {/* STEP 2: REVIEW */}

        {step === "review" && form && ocr && (
          <div>

            <div style={boxStyle}>

              <h3 style={{ marginTop: 0 }}>2. Check what we read</h3>

              <p style={{ color: "#6b7280", margin: "0 0 8px" }}>
                OCR engine: {ocr.engine} • Confidence: {ocr.confidence}%.
                OCR can misread digits, so please compare with your photo.
              </p>

              {previewUrl && (
                <img
                  src={previewUrl}
                  alt="Label"
                  style={{
                    display: "block",
                    maxWidth: "100%",
                    maxHeight: 220,
                    borderRadius: 8,
                  }}
                />
              )}

              {ocr.warnings.length > 0 && (
                <ul style={{ color: "#b45309", paddingLeft: 18 }}>
                  {ocr.warnings.map((warning) => (
                    <li key={warning}>{warning}</li>
                  ))}
                </ul>
              )}

              <details style={{ marginTop: 8 }}>
                <summary>Show raw OCR text</summary>
                <pre
                  style={{
                    whiteSpace: "pre-wrap",
                    fontSize: 12,
                    background: "#f9fafb",
                    padding: 8,
                    borderRadius: 8,
                  }}
                >
                  {ocr.raw_text}
                </pre>
              </details>

            </div>

            <div style={boxStyle}>

              <h3 style={{ marginTop: 0 }}>Product (optional)</h3>

              <label>
                Product name
                <input
                  type="text"
                  style={inputStyle}
                  value={form.product_name}
                  onChange={(e) =>
                    setForm({ ...form, product_name: e.target.value })
                  }
                />
              </label>

              <label style={{ display: "block", marginTop: 10 }}>
                Category (e.g. BISCUIT, SNACKS, JUICE)
                <input
                  type="text"
                  style={inputStyle}
                  value={form.category}
                  onChange={(e) =>
                    setForm({ ...form, category: e.target.value })
                  }
                />
              </label>

            </div>

            <div style={boxStyle}>

              <h3 style={{ marginTop: 0 }}>Nutrition values</h3>

              <div style={{ marginBottom: 12 }}>
                <label style={{ marginRight: 16 }}>
                  <input
                    type="radio"
                    name="basis"
                    checked={form.basis === "100g"}
                    onChange={() => setForm({ ...form, basis: "100g" })}
                  />{" "}
                  Values are per 100 g
                </label>

                <label>
                  <input
                    type="radio"
                    name="basis"
                    checked={form.basis === "serving"}
                    onChange={() => setForm({ ...form, basis: "serving" })}
                  />{" "}
                  Values are per serving
                </label>
              </div>

              {form.basis === "serving" && (
                <label style={{ display: "block", marginBottom: 12 }}>
                  Serving size (g)
                  <input
                    type="number"
                    min="0"
                    step="any"
                    style={inputStyle}
                    value={form.serving_size_g}
                    onChange={(e) =>
                      setForm({ ...form, serving_size_g: e.target.value })
                    }
                  />
                </label>
              )}

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    "repeat(auto-fit, minmax(150px, 1fr))",
                  gap: 10,
                }}
              >
                {FIELDS.map(([key, label, unit]) => (
                  <label key={key}>
                    {label} ({unit})
                    {REQUIRED.includes(key) ? " *" : ""}
                    <input
                      type="number"
                      min="0"
                      step="any"
                      style={inputStyle}
                      value={form.nutrition[key]}
                      onChange={(e) => setNutrition(key, e.target.value)}
                    />
                  </label>
                ))}
              </div>

              <small style={{ color: "#6b7280" }}>
                * needed for the health score
              </small>

            </div>

            <div style={boxStyle}>

              <h3 style={{ marginTop: 0 }}>Ingredients</h3>

              <textarea
                rows={5}
                style={inputStyle}
                value={form.ingredients}
                onChange={(e) =>
                  setForm({ ...form, ingredients: e.target.value })
                }
                placeholder="Type or correct the ingredients list"
              />

            </div>

            <button
              className="find-button"
              onClick={analyze}
              disabled={loading}
            >
              {loading ? "Analysing..." : "Analyse"}
            </button>

            <button
              className="camera-button"
              onClick={startOver}
              style={{ marginLeft: 8 }}
            >
              New photo
            </button>

          </div>
        )}


        {/* STEP 3: RESULT */}

        {step === "result" && result && (
          <div>

            <AnalysisResult result={result} />

            <RecordScan source="label" result={result} />

            <button
              className="find-button"
              onClick={() => setStep("review")}
            >
              Edit values
            </button>

            <button
              className="camera-button"
              onClick={startOver}
              style={{ marginLeft: 8 }}
            >
              Scan another label
            </button>

          </div>
        )}

      </div>
    </div>
  );
}

export default ScanLabel;