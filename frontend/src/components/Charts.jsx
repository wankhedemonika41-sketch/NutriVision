import "./Charts.css";

export const GRADE_COLORS = {
  A: "#16a34a",
  B: "#65a30d",
  C: "#f59e0b",
  D: "#dc2626",
};

const shortDate = (iso) =>
  new Date(`${iso}T00:00:00`).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
  });

/**
 * Average health score per day.
 * points: [{ date: "2026-10-24", count: 2, average: 63.5 | null }]
 * The coloured bands match the grades (D below 35, C 35-55, B 55-75, A 75+).
 */
export function TrendChart({ points }) {
  const withData = points.filter((p) => p.average !== null);

  if (withData.length === 0) {
    return <div className="nv-empty-chart">No scans in this period yet.</div>;
  }

  const W = 640;
  const H = 210;
  const left = 34;
  const right = 12;
  const top = 12;
  const bottom = 26;

  const x = (index) =>
    points.length === 1
      ? (left + W - right) / 2
      : left + (index / (points.length - 1)) * (W - left - right);

  const y = (score) => top + (1 - score / 100) * (H - top - bottom);

  const coords = points
    .map((p, index) => (p.average === null ? null : [x(index), y(p.average), p, index]))
    .filter(Boolean);

  const line = coords.map(([cx, cy]) => `${cx},${cy}`).join(" ");

  const bands = [
    ["#fee2e2", 0, 35],
    ["#fef3c7", 35, 55],
    ["#ecfccb", 55, 75],
    ["#dcfce7", 75, 100],
  ];

  const labelAt = [0, Math.floor((points.length - 1) / 2), points.length - 1];

  return (
    <svg
      className="nv-chart"
      viewBox={`0 0 ${W} ${H}`}
      role="img"
      aria-label="Average health score of the products you checked, per day"
    >
      {bands.map(([color, from, to]) => (
        <rect
          key={from}
          x={left}
          width={W - left - right}
          y={y(to)}
          height={y(from) - y(to)}
          fill={color}
        />
      ))}

      {[0, 50, 100].map((tick) => (
        <text key={tick} x={left - 6} y={y(tick) + 4} textAnchor="end">
          {tick}
        </text>
      ))}

      {[...new Set(labelAt)].map((index) => (
        <text
          key={index}
          x={x(index)}
          y={H - 6}
          textAnchor={index === 0 ? "start" : index === points.length - 1 ? "end" : "middle"}
        >
          {shortDate(points[index].date)}
        </text>
      ))}

      {coords.length > 1 && (
        <polyline points={line} fill="none" stroke="#1f6b4a" strokeWidth="2.5" />
      )}

      {coords.map(([cx, cy, p]) => (
        <circle key={p.date} cx={cx} cy={cy} r="4.5" fill="#123d2c" stroke="#fff" strokeWidth="1.5">
          <title>{`${shortDate(p.date)}: average ${p.average} (${p.count} product${p.count === 1 ? "" : "s"})`}</title>
        </circle>
      ))}
    </svg>
  );
}

/** One bar split by grade, plus a legend. grades: { A: 3, B: 1, C: 0, D: 2 } */
export function GradeBar({ grades }) {
  const total = Object.values(grades).reduce((sum, n) => sum + n, 0);

  if (total === 0) {
    return <div className="nv-empty-chart">No data yet.</div>;
  }

  return (
    <>
      <div
        className="nv-gradebar"
        role="img"
        aria-label={`Grades: ${Object.entries(grades).map(([g, n]) => `${g} ${n}`).join(", ")}`}
      >
        {Object.entries(grades)
          .filter(([, count]) => count > 0)
          .map(([grade, count]) => (
            <span
              key={grade}
              style={{ width: `${(count / total) * 100}%`, background: GRADE_COLORS[grade] }}
            >
              {count / total >= 0.08 ? grade : ""}
            </span>
          ))}
      </div>

      <div className="nv-legend">
        {Object.entries(grades).map(([grade, count]) => (
          <span key={grade}>
            <i style={{ background: GRADE_COLORS[grade] }} />
            Grade {grade}: <strong>{count}</strong>
          </span>
        ))}
      </div>
    </>
  );
}

/** Horizontal bars. items: [{ label, count, note? }] */
export function BarList({ items, color = "#1f6b4a", empty = "Nothing to show yet." }) {
  if (items.length === 0) {
    return <div className="nv-empty-chart">{empty}</div>;
  }

  const max = Math.max(...items.map((item) => item.count), 1);

  return (
    <ul className="nv-barlist">
      {items.map((item) => (
        <li key={item.label}>
          <div>
            <span>
              {item.label}
              {item.note && <small> • {item.note}</small>}
            </span>

            <strong>{item.count}</strong>
          </div>

          <div className="nv-bartrack">
            <div
              className="nv-barfill"
              style={{ width: `${(item.count / max) * 100}%`, background: color }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}