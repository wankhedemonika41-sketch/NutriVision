import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { timezoneOffset } from "../auth/history";
import { BarList, GRADE_COLORS, GradeBar, TrendChart } from "../components/Charts";
import "./History.css";

const PERIODS = [
  [7, "Last 7 days"],
  [30, "Last 30 days"],
  [90, "Last 90 days"],
];

const SOURCE_LABELS = { product: "Opened", barcode: "Barcode", label: "Label" };

const PAGE_SIZE = 20;

const formatWhen = (iso) =>
  new Date(iso).toLocaleString("en-IN", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });

function Change({ change, days }) {
  if (change === null || change === undefined) {
    return <small>No earlier period to compare with</small>;
  }

  if (change >= 3) {
    return <small className="nv-up">&#9650; {change} points vs previous {days} days</small>;
  }

  if (change <= -3) {
    return <small className="nv-down">&#9660; {Math.abs(change)} points vs previous {days} days</small>;
  }

  return <small>About the same as the previous {days} days</small>;
}

function History({ onNavigate }) {
  const { authFetch } = useAuth();

  const [days, setDays] = useState(7);
  const [summary, setSummary] = useState(null);
  const [list, setList] = useState({ total: 0, items: [] });
  const [summaryReady, setSummaryReady] = useState(false);
  const [listReady, setListReady] = useState(false);
  const [error, setError] = useState("");
  const [confirmClear, setConfirmClear] = useState(false);

  const latestSummary = useRef(0);

  const loadSummary = useCallback(async () => {
    const requestId = ++latestSummary.current;

    const response = await authFetch(
      `/history/summary?days=${days}&tz_offset=${timezoneOffset()}`
    );

    if (!response.ok) {
      throw new Error("Unable to load your report.");
    }

    const data = await response.json();

    // ignore an answer for a period the user has already switched away from
    if (requestId === latestSummary.current) {
      setSummary(data);
    }
  }, [authFetch, days]);

  const loadList = useCallback(async () => {
    const response = await authFetch(`/history?limit=${PAGE_SIZE}&offset=0`);

    if (!response.ok) {
      throw new Error("Unable to load your history.");
    }

    setList(await response.json());
  }, [authFetch]);

  const explain = (err) =>
    err.message === "Failed to fetch"
      ? "Unable to reach the server. Please make sure the backend is running."
      : err.message;

  useEffect(() => {
    let cancelled = false;

    loadSummary()
      .then(() => !cancelled && setError(""))
      .catch((err) => !cancelled && setError(explain(err)))
      .finally(() => !cancelled && setSummaryReady(true));

    return () => {
      cancelled = true;
    };
  }, [loadSummary]);

  useEffect(() => {
    let cancelled = false;

    loadList()
      .catch((err) => !cancelled && setError(explain(err)))
      .finally(() => !cancelled && setListReady(true));

    return () => {
      cancelled = true;
    };
  }, [loadList]);

  const showMore = async () => {
    try {
      const response = await authFetch(
        `/history?limit=${PAGE_SIZE}&offset=${list.items.length}`
      );

      if (!response.ok) {
        throw new Error("Unable to load more.");
      }

      const more = await response.json();

      setList((current) => ({
        total: more.total,
        items: [...current.items, ...more.items],
      }));
    } catch (err) {
      setError(err.message);
    }
  };

  const removeEntry = async (id) => {
    try {
      const response = await authFetch(`/history/${id}`, { method: "DELETE" });

      if (!response.ok && response.status !== 404) {
        throw new Error("Unable to remove this entry.");
      }

      setList((current) => ({
        total: Math.max(0, current.total - 1),
        items: current.items.filter((item) => item.id !== id),
      }));

      await loadSummary();
    } catch (err) {
      setError(err.message);
    }
  };

  const clearAll = async () => {
    try {
      const response = await authFetch("/history", { method: "DELETE" });

      if (!response.ok) {
        throw new Error("Unable to clear your history.");
      }

      setConfirmClear(false);
      setList({ total: 0, items: [] });
      await loadSummary();
    } catch (err) {
      setError(err.message);
    }
  };

  if (!summaryReady || !listReady) {
    return <div className="nv-hist"><p>Loading your report...</p></div>;
  }

  if (!summary) {
    return (
      <div className="nv-hist">
        <div className="nv-error-box" role="alert">{error || "Unable to load your report."}</div>
      </div>
    );
  }

  const nothingAtAll = summary.total === 0 && list.total === 0;

  return (
    <div className="nv-hist">

      <p className="nv-hist-label">MY REPORT</p>

      <div className="nv-hist-head">

        <h1>Your food report</h1>

        <div className="nv-periods" role="group" aria-label="Report period">
          {PERIODS.map(([value, label]) => (
            <button
              key={value}
              aria-pressed={days === value}
              onClick={() => setDays(value)}
            >
              {label}
            </button>
          ))}
        </div>

      </div>

      {error && <div className="nv-error-box" role="alert">{error}</div>}

      {nothingAtAll ? (
        <div className="nv-card nv-empty">

          <h3>Nothing here yet</h3>

          <p>
            Products you open, scan or read from a label are saved here
            automatically, and turned into a report.
          </p>

          <button onClick={() => onNavigate("search")}>Search products</button>
          <button onClick={() => onNavigate("scan")}>Scan a barcode</button>

        </div>
      ) : (
        <>
          <div className="nv-tiles">

            <div className="nv-tile">
              <span>Products checked</span>
              <strong>{summary.total}</strong>
              <small>{summary.unique_products} different product{summary.unique_products === 1 ? "" : "s"}</small>
            </div>

            <div className="nv-tile">
              <span>Average score</span>
              <strong>{summary.average_score ?? "-"}</strong>
              <Change change={summary.change} days={summary.days} />
            </div>

            <div className="nv-tile">
              <span>Grade A or B</span>
              <strong>{summary.healthy_share === null ? "-" : `${summary.healthy_share}%`}</strong>
              <small>of what you checked</small>
            </div>

            <div className="nv-tile">
              <span>Best choice</span>
              <strong>{summary.best ? summary.best.score : "-"}</strong>
              <small>{summary.best ? summary.best.product_name : "No scans in this period"}</small>
            </div>

          </div>

          {summary.insights.length > 0 && (
            <div className="nv-card">
              <h3>What stands out</h3>

              <ul className="nv-insights">
                {summary.insights.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="nv-card">
            <h3>Average score per day</h3>
            <TrendChart points={summary.daily} />
            <p className="nv-note">
              Background colours show the grades: green A (75+), light green B,
              amber C, red D (under 35).
            </p>
          </div>

          <div className="nv-two">

            <div className="nv-card">
              <h3>How your choices were graded</h3>
              <GradeBar grades={summary.grades} />
            </div>

            <div className="nv-card">
              <h3>Most common concerns</h3>
              <BarList
                color="#dc2626"
                empty="No cautionary ingredients found."
                items={summary.top_cautions.map((item) => ({
                  label: item.label,
                  count: item.count,
                }))}
              />
            </div>

          </div>

          <div className="nv-two">

            <div className="nv-card">
              <h3>Categories you checked</h3>
              <BarList
                items={summary.categories.map((item) => ({
                  label: item.category,
                  count: item.count,
                  note: item.average === null ? null : `avg score ${item.average}`,
                }))}
              />
            </div>

            <div className="nv-card">
              <h3>Average per 100 g</h3>

              <div className="nv-averages">
                <div><span>Sugar</span><strong>{summary.averages.sugar ?? "-"} g</strong></div>
                <div><span>Sodium</span><strong>{summary.averages.sodium ?? "-"} mg</strong></div>
                <div><span>Saturated fat</span><strong>{summary.averages.saturated_fat ?? "-"} g</strong></div>
                <div><span>Calories</span><strong>{summary.averages.calories ?? "-"} kcal</strong></div>
              </div>

              <p className="nv-note">
                Averages of the products you checked, not of what you ate.
              </p>
            </div>

          </div>
        </>
      )}

      {list.items.length > 0 && (
        <div className="nv-card">

          <h3>Recent history</h3>

          <ul className="nv-list">
            {list.items.map((item) => (
              <li key={item.id}>

                <span
                  className="nv-badge"
                  style={{ background: GRADE_COLORS[item.grade] || "#6b7280" }}
                  title={`Grade ${item.grade}`}
                >
                  {Math.round(item.score)}
                </span>

                <div className="nv-list-main">
                  <strong>
                    {item.product_name}
                    <span className="nv-source">{SOURCE_LABELS[item.source]}</span>
                  </strong>

                  <small>
                    {item.brand ? `${item.brand} • ` : ""}
                    {formatWhen(item.created_at)}
                  </small>
                </div>

                <button
                  className="nv-remove"
                  aria-label={`Remove ${item.product_name}`}
                  onClick={() => removeEntry(item.id)}
                >
                  Remove
                </button>

              </li>
            ))}
          </ul>

          <div className="nv-actions">

            {list.items.length < list.total && (
              <button className="nv-ghost" onClick={showMore}>
                Show more ({list.total - list.items.length} left)
              </button>
            )}

            {confirmClear ? (
              <>
                <span>Delete all {list.total} entries?</span>
                <button className="nv-danger" onClick={clearAll}>Yes, delete</button>
                <button className="nv-ghost" onClick={() => setConfirmClear(false)}>Cancel</button>
              </>
            ) : (
              <button className="nv-ghost" onClick={() => setConfirmClear(true)}>
                Clear all history
              </button>
            )}

          </div>

        </div>
      )}

      <p className="nv-note">Your history is private to your account.</p>

    </div>
  );
}

export default History;