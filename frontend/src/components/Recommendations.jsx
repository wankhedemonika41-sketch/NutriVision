import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import "./Recommendations.css";

const GRADE_COLORS = { A: "#16a34a", B: "#65a30d", C: "#f59e0b", D: "#dc2626" };

const DIET_LABELS = {
  vegetarian: "Vegetarian",
  eggetarian: "Eggetarian",
  vegan: "Vegan",
};

const GOAL_LABELS = {
  lose_weight: "Lose weight",
  manage_sugar: "Manage sugar",
  heart_health: "Heart health",
  build_muscle: "Build muscle",
};

function Recommendations({ productId, onOpenProduct, onOpenProfile }) {
  const { authFetch } = useAuth();

  const [state, setState] = useState({ status: "loading", data: null, error: "" });

  useEffect(() => {
    let cancelled = false;

    setState({ status: "loading", data: null, error: "" });

    authFetch(`/recommendations/${productId}`)
      .then(async (response) => {
        const body = await response.json().catch(() => null);

        if (cancelled) {
          return;
        }

        if (!response.ok) {
          setState({
            status: "error",
            data: null,
            error:
              typeof body?.detail === "string"
                ? body.detail
                : "Unable to load healthier alternatives.",
          });
          return;
        }

        setState({ status: "ready", data: body, error: "" });
      })
      .catch(() => {
        if (!cancelled) {
          setState({
            status: "error",
            data: null,
            error: "Unable to reach the server.",
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [productId, authFetch]);

  const { status, data, error } = state;

  const used = data?.profile_used;

  return (
    <section className="nv-rec" aria-label="Healthier alternatives">

      <h2>Healthier alternatives</h2>

      {status === "loading" && (
        <p className="nv-rec-sub">Finding healthier alternatives...</p>
      )}

      {status === "error" && (
        <p className="nv-rec-error" role="alert">{error}</p>
      )}

      {status === "ready" && (
        <>
          {data.compared_with && (
            <p className="nv-rec-sub">Compared with {data.compared_with}.</p>
          )}

          {used?.personalised ? (
            <div className="nv-rec-chips">
              {used.diet && DIET_LABELS[used.diet] && (
                <span className="nv-chip">{DIET_LABELS[used.diet]}</span>
              )}

              {used.allergies.length > 0 && (
                <span className="nv-chip warn">
                  Avoiding: {used.allergies.join(", ")}
                </span>
              )}

              {used.goal && GOAL_LABELS[used.goal] && (
                <span className="nv-chip">Goal: {GOAL_LABELS[used.goal]}</span>
              )}
            </div>
          ) : (
            <div className="nv-rec-nudge">
              Add your allergies, diet and health goal to get personalised
              suggestions.
              <button onClick={onOpenProfile}>Set up my profile</button>
            </div>
          )}

          {data.recommendations.length === 0 ? (
            <div className="nv-rec-empty">{data.message}</div>
          ) : (
            <div className="nv-rec-list">
              {data.recommendations.map((item) => (
                <div className="nv-rec-card" key={item.id}>

                  <div>
                    <div className="nv-rec-name">{item.product_name}</div>

                    <div className="nv-rec-meta">
                      {item.brand || "Brand not available"}
                      {item.price_inr ? ` • Rs. ${item.price_inr}` : ""}
                    </div>
                  </div>

                  <div className="nv-rec-score">
                    <span
                      className="nv-rec-badge"
                      style={{ background: GRADE_COLORS[item.grade] || "#6b7280" }}
                    >
                      {Math.round(item.score)}
                    </span>

                    <span className="nv-rec-gain">+{item.score_gain} pts</span>
                  </div>

                  <div className="nv-rec-body">

                    {item.goal_match && (
                      <div className="nv-rec-goal">{item.goal_match}</div>
                    )}

                    {item.reasons.length > 0 && (
                      <ul>
                        {item.reasons.map((reason) => (
                          <li key={reason}>{reason}</li>
                        ))}
                      </ul>
                    )}

                    {(item.contains_sweetener || item.cautions.length > 0) && (
                      <div className="nv-rec-tags">
                        {item.contains_sweetener && (
                          <span className="nv-chip warn">Contains sweetener</span>
                        )}

                        {item.cautions.map((name) => (
                          <span className="nv-chip danger" key={name}>
                            {name}
                          </span>
                        ))}
                      </div>
                    )}

                    <button
                      className="nv-rec-view"
                      onClick={() => onOpenProduct(item.id)}
                    >
                      View details
                    </button>

                  </div>

                </div>
              ))}
            </div>
          )}

          {data.notes.length > 0 && (
            <ul className="nv-rec-notes">
              {data.notes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          )}

          <p className="nv-rec-foot">
            Suggestions use the health score (nutrients and ingredients per
            100 g). Diet matching is estimated from ingredient text and
            allergen detection is keyword based, so always check the pack.
          </p>
        </>
      )}

    </section>
  );
}

export default Recommendations;