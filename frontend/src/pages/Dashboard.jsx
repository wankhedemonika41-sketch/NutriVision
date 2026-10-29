import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { timezoneOffset } from "../auth/history";
import "./Dashboard.css";

const ACTIONS = [
  {
    id: "scan",
    title: "Scan a barcode",
    text: "Use the camera or type the number to look up a packaged food.",
    button: "Open scanner",
  },
  {
    id: "label",
    title: "Scan a label",
    text: "Take a photo of the ingredients and the nutrition table.",
    button: "Read a label",
  },
  {
    id: "search",
    title: "Search a product",
    text: "Browse 850+ Indian packaged foods in the NutriVision database.",
    button: "Search products",
  },
  {
    id: "compare",
    title: "Compare two products",
    text: "See which one is the healthier choice, and why.",
    button: "Compare",
  },
  {
    id: "profile",
    title: "Set up your profile",
    text: "Add your diet, allergies and health goal to get personalised healthier suggestions.",
    button: "Open profile",
  },
];

const GRADES = [
  ["A", "75 - 100", "Healthy choice", "#16a34a"],
  ["B", "55 - 74", "Okay in moderation", "#65a30d"],
  ["C", "35 - 54", "Limit this food", "#f59e0b"],
  ["D", "0 - 34", "Occasional treat only", "#dc2626"],
];

// "This week" card: numbers come from the saved scan history
function RecentActivity({ onNavigate }) {
  const { authFetch } = useAuth();

  const [summary, setSummary] = useState(null);

  useEffect(() => {
    let cancelled = false;

    authFetch(`/history/summary?days=7&tz_offset=${timezoneOffset()}`)
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => !cancelled && setSummary(data))
      .catch(() => {});

    return () => {
      cancelled = true;
    };
  }, [authFetch]);

  if (!summary) {
    return null;
  }

  return (
    <div className="nv-guide nv-activity">

      <h3>This week</h3>

      {summary.total === 0 ? (
        <p className="nv-guide-note">
          Products you open, scan or read from a label are saved
          automatically and turned into a weekly report.
        </p>
      ) : (
        <p className="nv-guide-note" data-testid="activity-line">
          You checked <strong>{summary.total}</strong>{" "}
          product{summary.total === 1 ? "" : "s"} with an average score
          of <strong>{summary.average_score}</strong>.{" "}
          {summary.insights[0]}
        </p>
      )}

      <button className="nv-link-button" onClick={() => onNavigate("history")}>
        Open my full report
      </button>

    </div>
  );
}

function Dashboard({ user, onNavigate }) {
  const firstName = (user?.name || "").split(" ")[0] || "there";

  return (
    <div className="nv-dash">

      <p className="nv-dash-label">DASHBOARD</p>

      <h1>Hello, {firstName}</h1>

      <p className="nv-dash-sub">
        What would you like to check today?
      </p>

      <RecentActivity onNavigate={onNavigate} />

      <div className="nv-action-grid">
        {ACTIONS.map((action) => (
          <div className="nv-action-card" key={action.id}>

            <h3>{action.title}</h3>

            <p>{action.text}</p>

            <button onClick={() => onNavigate(action.id)}>
              {action.button}
            </button>

          </div>
        ))}
      </div>

      <div className="nv-guide">

        <h3>How to read the Health Score</h3>

        <p className="nv-guide-note">
          The score is based on nutrients per 100 g and the ingredients.
          It is general information, not medical advice.
        </p>

        <div className="nv-guide-grid">
          {GRADES.map(([grade, range, label, color]) => (
            <div className="nv-guide-item" key={grade}>

              <span className="nv-grade" style={{ background: color }}>
                {grade}
              </span>

              <div>
                <strong>{label}</strong>
                <small>Score {range}</small>
              </div>

            </div>
          ))}
        </div>

      </div>

    </div>
  );
}

export default Dashboard;