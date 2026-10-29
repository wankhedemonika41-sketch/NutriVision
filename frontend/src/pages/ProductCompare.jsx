import { useState } from "react";
import "./ScanProduct.css";

const API_URL = "http://127.0.0.1:8000";

const GRADE_COLORS = { A: "#16a34a", B: "#65a30d", C: "#f59e0b", D: "#dc2626" };
const RISK_COLORS = { LOW: "#16a34a", MEDIUM: "#f59e0b", HIGH: "#dc2626" };
const FLAG_COLORS = { caution: "#dc2626", info: "#2563eb", positive: "#16a34a" };

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

const WIN = { background: "#dcfce7", fontWeight: 700 };

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


/* ------------------------------------------------------------------ */
/* One product picker                                                  */
/* ------------------------------------------------------------------ */

function ProductPicker({ title, selected, onSelect, otherId }) {
  const [text, setText] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const search = async () => {
    if (!text.trim()) {
      setMessage("Type a product name.");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const response = await fetch(
        `${API_URL}/products/search?q=${encodeURIComponent(text.trim())}`
      );

      if (!response.ok) {
        throw new Error("Search failed.");
      }

      const data = await response.json();

      setResults(data.slice(0, 8));

      if (data.length === 0) {
        setMessage("No products found.");
      }
    } catch (err) {
      console.error("Search error:", err);
      setMessage("Unable to reach the backend. Please make sure it is running.");
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const choose = (product) => {
    onSelect(product);
    setResults([]);
    setText("");
    setMessage("");
  };

  return (
    <div style={{ ...boxStyle, flex: "1 1 280px", minWidth: 0 }}>

      <h3 style={{ marginTop: 0 }}>{title}</h3>

      {selected ? (
        <div
          style={{
            background: "#f0fdf4",
            border: "1px solid #bbf7d0",
            borderRadius: 8,
            padding: 10,
            marginBottom: 10,
          }}
        >
          <strong>{selected.product_name}</strong>

          <div style={{ color: "#6b7280", fontSize: 13 }}>
            {selected.brand || "Brand not available"}
            {selected.category ? ` • ${selected.category}` : ""}
          </div>

          <button
            className="camera-button"
            style={{ marginTop: 8 }}
            onClick={() => onSelect(null)}
          >
            Change
          </button>
        </div>
      ) : (
        <>
          <div style={{ display: "flex", gap: 8 }}>
            <input
              type="text"
              placeholder="Search a product"
              style={inputStyle}
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  search();
                }
              }}
            />

            <button
              className="find-button"
              style={{ width: "auto", whiteSpace: "nowrap" }}
              onClick={search}
              disabled={loading}
            >
              {loading ? "..." : "Search"}
            </button>
          </div>

          {message && (
            <p style={{ color: "#b45309", fontSize: 13 }}>{message}</p>
          )}

          {results.length > 0 && (
            <ul style={{ listStyle: "none", padding: 0, margin: "10px 0 0" }}>
              {results.map((product) => (
                <li key={product.id}>
                  <button
                    onClick={() => choose(product)}
                    disabled={product.id === otherId}
                    style={{
                      width: "100%",
                      textAlign: "left",
                      padding: "8px 10px",
                      marginBottom: 6,
                      borderRadius: 8,
                      border: "1px solid #e5e7eb",
                      background: product.id === otherId ? "#f3f4f6" : "#fff",
                      color: "#111827",
                      cursor: product.id === otherId ? "not-allowed" : "pointer",
                    }}
                  >
                    <strong>{product.product_name}</strong>

                    <div style={{ color: "#6b7280", fontSize: 12 }}>
                      {product.brand || "Brand not available"}
                      {product.category ? ` • ${product.category}` : ""}
                      {product.id === otherId ? " (already chosen)" : ""}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </>
      )}

    </div>
  );
}


/* ------------------------------------------------------------------ */
/* Result pieces                                                       */
/* ------------------------------------------------------------------ */

function ScoreBadge({ side, isWinner }) {
  const color = GRADE_COLORS[side.grade] || "#6b7280";

  return (
    <div
      style={{
        flex: "1 1 200px",
        textAlign: "center",
        padding: 12,
        borderRadius: 12,
        border: isWinner ? "2px solid #16a34a" : "1px solid #e5e7eb",
        background: isWinner ? "#f0fdf4" : "#fff",
      }}
    >
      {isWinner && (
        <div style={{ color: "#16a34a", fontWeight: 700, fontSize: 12 }}>
          HEALTHIER CHOICE
        </div>
      )}

      <div
        style={{
          width: 76,
          height: 76,
          borderRadius: "50%",
          background: color,
          color: "#fff",
          margin: "8px auto",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <strong style={{ fontSize: 24 }}>
          {side.score === null ? "N/A" : Math.round(side.score)}
        </strong>
        {side.score !== null && <span style={{ fontSize: 10 }}>/ 100</span>}
      </div>

      <strong>{side.product_name}</strong>

      <div style={{ color: "#6b7280", fontSize: 13 }}>
        {side.score !== null
          ? `Grade ${side.grade} • ${side.label}`
          : side.unavailable_reason || "Score not available"}
      </div>
    </div>
  );
}

function Flags({ flags }) {
  if (!flags || flags.length === 0) {
    return <span style={{ color: "#6b7280" }}>None found</span>;
  }

  return (
    <ul style={{ margin: 0, paddingLeft: 18 }}>
      {flags.map((flag) => (
        <li key={flag.label} style={{ color: FLAG_COLORS[flag.severity] }}>
          {flag.label}
        </li>
      ))}
    </ul>
  );
}


/* ------------------------------------------------------------------ */
/* Page                                                                */
/* ------------------------------------------------------------------ */

function ProductCompare({ onBack }) {
  const [first, setFirst] = useState(null);
  const [second, setSecond] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const choose = (setter) => (product) => {
    setter(product);
    setResult(null);
    setError("");
  };

  const compare = async () => {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(
        `${API_URL}/compare?a=${first.id}&b=${second.id}`
      );

      const body = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(errorMessage(body, "Unable to compare these products."));
      }

      setResult(body);
    } catch (err) {
      console.error("Compare error:", err);

      setError(
        err.message === "Failed to fetch"
          ? "Unable to reach the backend. Please make sure it is running."
          : err.message
      );
    } finally {
      setLoading(false);
    }
  };

  const cellStyle = (row, side) => (row.better === side ? WIN : {});

  return (
    <div className="scan-page">
      <div className="scan-container">

        <button className="back-button" onClick={onBack}>
          Back to Home
        </button>

        <h1>Compare Products</h1>

        <p className="scan-description">
          Pick two products to see which one is the healthier choice,
          and why.
        </p>

        <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
          <ProductPicker
            title="Product 1"
            selected={first}
            onSelect={choose(setFirst)}
            otherId={second?.id}
          />

          <ProductPicker
            title="Product 2"
            selected={second}
            onSelect={choose(setSecond)}
            otherId={first?.id}
          />
        </div>

        <button
          className="find-button"
          onClick={compare}
          disabled={!first || !second || loading}
        >
          {loading ? "Comparing..." : "Compare"}
        </button>

        {error && (
          <p style={{ color: "#dc2626", textAlign: "center" }}>{error}</p>
        )}


        {result && (
          <div style={{ marginTop: 24, textAlign: "left" }}>

            <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 16 }}>
              <ScoreBadge side={result.a} isWinner={result.winner === "a"} />
              <ScoreBadge side={result.b} isWinner={result.winner === "b"} />
            </div>

            <div style={boxStyle}>
              <h3 style={{ marginTop: 0 }}>Verdict</h3>

              <p style={{ margin: "0 0 8px" }}>{result.summary}</p>

              {result.reasons.length > 0 && (
                <ul style={{ margin: 0, paddingLeft: 18 }}>
                  {result.reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              )}
            </div>

            <div style={{ ...boxStyle, overflowX: "auto" }}>
              <h3 style={{ marginTop: 0 }}>Nutrition (per 100 g)</h3>

              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ textAlign: "left", color: "#6b7280" }}>
                    <th style={{ padding: 8 }}>Nutrient</th>
                    <th style={{ padding: 8 }}>{result.a.product_name}</th>
                    <th style={{ padding: 8 }}>{result.b.product_name}</th>
                  </tr>
                </thead>

                <tbody>
                  {result.nutrition.map((row) => (
                    <tr key={row.key} style={{ borderTop: "1px solid #e5e7eb" }}>
                      <td style={{ padding: 8 }}>
                        {row.label} <small>({row.unit})</small>
                      </td>
                      <td style={{ padding: 8, ...cellStyle(row, "a") }}>
                        {row.a ?? "N/A"}
                      </td>
                      <td style={{ padding: 8, ...cellStyle(row, "b") }}>
                        {row.b ?? "N/A"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <small style={{ color: "#6b7280" }}>
                Green = healthier value. Carbohydrates are not judged.
              </small>
            </div>

            <div style={{ ...boxStyle, overflowX: "auto" }}>
              <h3 style={{ marginTop: 0 }}>Indicative risk levels</h3>

              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <tbody>
                  {result.risks.map((risk) => (
                    <tr key={risk.key} style={{ borderTop: "1px solid #e5e7eb" }}>
                      <td style={{ padding: 8 }}>{risk.label}</td>
                      <td
                        style={{
                          padding: 8,
                          color: RISK_COLORS[risk.a],
                          fontWeight: 700,
                        }}
                      >
                        {risk.a ?? "N/A"}
                      </td>
                      <td
                        style={{
                          padding: 8,
                          color: RISK_COLORS[risk.b],
                          fontWeight: 700,
                        }}
                      >
                        {risk.b ?? "N/A"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div style={boxStyle}>
              <h3 style={{ marginTop: 0 }}>Ingredient flags</h3>

              <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
                <div style={{ flex: "1 1 200px" }}>
                  <strong>{result.a.product_name}</strong>
                  <Flags flags={result.a.flags} />
                </div>

                <div style={{ flex: "1 1 200px" }}>
                  <strong>{result.b.product_name}</strong>
                  <Flags flags={result.b.flags} />
                </div>
              </div>
            </div>

            <p style={{ fontSize: 12, color: "#6b7280" }}>{result.disclaimer}</p>

          </div>
        )}

      </div>
    </div>
  );
}

export default ProductCompare;