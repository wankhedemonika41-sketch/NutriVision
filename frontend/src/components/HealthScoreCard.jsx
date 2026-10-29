const GRADE_COLORS = { A: "#16a34a", B: "#65a30d", C: "#f59e0b", D: "#dc2626" };
const RISK_COLORS = { LOW: "#16a34a", MEDIUM: "#f59e0b", HIGH: "#dc2626" };
const RISK_TITLES = {
  diabetes_risk: "Diabetes (sugar)",
  heart_risk: "Heart (fat)",
  blood_pressure_risk: "Blood pressure (sodium)",
  obesity_risk: "Obesity (energy)",
};

export default function HealthScoreCard({ health }) {
  if (!health) return null;

  if (!health.available) {
    return <p style={{ color: "#6b7280" }}>{health.reason}</p>;
  }

  const color = GRADE_COLORS[health.grade] || "#6b7280";

  return (
    <div style={{ border: "1px solid #e5e7eb", borderRadius: 12, padding: 16, margin: "16px 0" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        <div style={{
          width: 84, height: 84, borderRadius: "50%", background: color,
          color: "#fff", display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center",
        }}>
          <strong style={{ fontSize: 26 }}>{Math.round(health.score)}</strong>
          <span style={{ fontSize: 11 }}>/ 100</span>
        </div>
        <div>
          <h3 style={{ margin: 0 }}>Health Score: Grade {health.grade}</h3>
          <p style={{ margin: "4px 0", color: "#374151" }}>{health.label}</p>
          <small style={{ color: "#6b7280" }}>Method: {health.method}</small>
        </div>
      </div>

      {health.reasons?.length > 0 && (
        <>
          <h4 style={{ marginBottom: 6 }}>Why this score?</h4>
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            {health.reasons.map((r) => (
              <li key={r.feature} style={{ color: r.direction === "raises" ? "#16a34a" : "#dc2626" }}>
                {r.label}: {r.direction === "raises" ? "better" : "worse"} than an average product ({r.impact > 0 ? "+" : ""}{r.impact} points)
              </li>
            ))}
          </ul>
        </>
      )}

      <h4 style={{ marginBottom: 6 }}>Indicative risk levels</h4>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 8 }}>
        {Object.entries(health.risks).map(([key, risk]) => (
          <div key={key} style={{ borderLeft: `4px solid ${RISK_COLORS[risk.level]}`, padding: "4px 10px", background: "#f9fafb" }}>
            <strong>{RISK_TITLES[key]}: {risk.level}</strong>
            <div style={{ fontSize: 12, color: "#6b7280" }}>{risk.reason}</div>
          </div>
        ))}
      </div>

      <p style={{ fontSize: 12, color: "#6b7280", marginBottom: 0 }}>{health.disclaimer}</p>
    </div>
  );
}