/**
 * BodyVizMap  –  realistic full-body educational illustration
 *
 * Data source: the `analysis` prop from NutritionAnalysis.jsx
 * (GET /analysis/nutrition/:id).  No new API calls are made.
 *
 * The SVG draws a detailed front-facing human figure with:
 *   – recognisable face (eyes, brows, ears, nose, mouth)
 *   – neck, shoulders, arms with hands and fingers
 *   – torso with surface muscle shading
 *   – pelvis / hip region
 *   – legs, knees, calves, ankles, feet
 *   – internal-system silhouettes (heart, lungs, liver, stomach,
 *     intestine, kidneys, brain) drawn as semi-transparent shapes
 *     visible through the torso / head
 *
 * Each region is highlighted only when the project has a reliable
 * nutrient value for it.  Highlight intensity mirrors the project's
 * own LOW / MODERATE / HIGH categories.
 *
 * Educational disclaimer: this is not a diagnosis or medical advice.
 */

import { useEffect, useRef, useState } from "react";
import "./BodyVizMap.css";

// ─────────────────────────────────────────────────────────────────────────────
// Nutrient → body-system mapping  (unchanged from previous version)
// ─────────────────────────────────────────────────────────────────────────────

const SYSTEM_DEFS = [
  {
    id: "brain",
    label: "Brain & Energy",
    nutrients: ["calories", "sugar"],
    description: (vals) =>
      `The brain relies on glucose as its primary fuel. Large amounts of added` +
      ` sugar can cause rapid blood-glucose swings that affect energy levels and` +
      ` concentration. This product provides ${vals.calories ?? "–"} kcal and` +
      ` ${vals.sugar ?? "–"} g sugar per 100 g.`,
  },
  {
    id: "heart",
    label: "Heart & Circulation",
    nutrients: ["saturated_fat", "trans_fat", "sodium"],
    description: (vals) =>
      `Diets high in saturated fat, trans fat, and sodium are associated with` +
      ` elevated blood cholesterol and blood pressure in population studies.` +
      ` This product provides ${vals.saturated_fat ?? "–"} g saturated fat,` +
      ` ${vals.trans_fat ?? "–"} g trans fat, and ${vals.sodium ?? "–"} mg` +
      ` sodium per 100 g.`,
  },
  {
    id: "lungs",
    label: "Lungs",
    nutrients: ["calories", "total_fat"],
    description: (vals) =>
      `Excess calorie and fat intake is linked to weight gain, which can place` +
      ` additional demand on the respiratory system over time. This product` +
      ` provides ${vals.calories ?? "–"} kcal and ${vals.total_fat ?? "–"} g` +
      ` total fat per 100 g.`,
  },
  {
    id: "liver",
    label: "Liver",
    nutrients: ["total_fat", "saturated_fat"],
    description: (vals) =>
      `The liver processes dietary fats. Consistently high fat or saturated-fat` +
      ` intake is associated with metabolic changes in population research.` +
      ` This product provides ${vals.total_fat ?? "–"} g total fat and` +
      ` ${vals.saturated_fat ?? "–"} g saturated fat per 100 g.`,
  },
  {
    id: "stomach",
    label: "Blood Sugar Regulation",
    nutrients: ["sugar", "carbohydrates"],
    description: (vals) =>
      `Sugar and refined carbohydrates are rapidly absorbed and raise` +
      ` blood-glucose levels. The pancreas responds by releasing insulin.` +
      ` This product provides ${vals.sugar ?? "–"} g sugar and` +
      ` ${vals.carbohydrates ?? "–"} g total carbohydrates per 100 g.`,
  },
  {
    id: "kidneys",
    label: "Kidneys",
    nutrients: ["sodium"],
    description: (vals) =>
      `The kidneys filter sodium from the blood. High sodium intake is` +
      ` associated with increased blood pressure and renal workload in` +
      ` population research. This product provides ${vals.sodium ?? "–"} mg` +
      ` sodium per 100 g.`,
  },
  {
    id: "intestine",
    label: "Digestive System",
    nutrients: ["fiber"],
    description: (vals) =>
      `Dietary fibre slows digestion, feeds beneficial gut bacteria, and` +
      ` supports bowel regularity. This product provides` +
      ` ${vals.fiber ?? "–"} g fibre per 100 g.`,
  },
  {
    id: "muscles",
    label: "Muscles & Recovery",
    nutrients: ["protein"],
    description: (vals) =>
      `Protein provides amino acids needed for muscle repair and synthesis.` +
      ` This product provides ${vals.protein ?? "–"} g protein per 100 g.`,
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// Severity helpers  (unchanged logic)
// ─────────────────────────────────────────────────────────────────────────────

function worstLevel(nutrients, analysis) {
  const rank = { HIGH: 2, MODERATE: 1, LOW: 0 };
  let best = -1;
  for (const key of nutrients) {
    const entry = analysis?.[key];
    if (!entry) continue;
    const lvl = (entry.level || "").toUpperCase();
    if (lvl in rank && rank[lvl] > best) best = rank[lvl];
  }
  if (best === 2) return "high";
  if (best === 1) return "moderate";
  if (best === 0) return "low";
  return null;
}

function positiveLevel(nutrients, analysis) {
  const rank = { LOW: 2, MODERATE: 1, HIGH: 0 };
  let best = -1;
  for (const key of nutrients) {
    const entry = analysis?.[key];
    if (!entry) continue;
    const lvl = (entry.level || "").toUpperCase();
    if (lvl in rank && rank[lvl] > best) best = rank[lvl];
  }
  if (best === 2) return "low";
  if (best === 1) return "moderate";
  if (best === 0) return "high";
  return null;
}

function allMissing(nutrients, analysis) {
  return nutrients.every((k) => !analysis?.[k]);
}

// ─────────────────────────────────────────────────────────────────────────────
// Highlight colours
// ─────────────────────────────────────────────────────────────────────────────

const LEVEL_COLORS = {
  high:     { fill: "rgba(180, 35, 24, 0.28)",  stroke: "#b42318", glow: "rgba(180,35,24,0.18)" },
  moderate: { fill: "rgba(148, 98,  0, 0.22)",  stroke: "#946200", glow: "rgba(148,98,0,0.14)"  },
  low:      { fill: "rgba(33, 122, 50, 0.22)",  stroke: "#217a32", glow: "rgba(33,122,50,0.14)" },
};

const LEVEL_LABEL = { high: "High", moderate: "Moderate", low: "Low" };

// ─────────────────────────────────────────────────────────────────────────────
// SVG hit regions  (clipPath-bounded paths match the internal anatomy shapes)
// ─────────────────────────────────────────────────────────────────────────────

// Each region is a <path> or <ellipse> drawn over the relevant anatomy.
// They are clickable/hoverable and receive the highlight fill+stroke.

const REGION_SHAPES = {
  brain: {
    type: "ellipse",
    cx: 200, cy: 54, rx: 26, ry: 22,
  },
  heart: {
    type: "path",
    // small teardrop centred on left chest
    d: "M196 188 C192 182 184 180 184 188 C184 196 196 206 196 206 C196 206 208 196 208 188 C208 180 200 182 196 188 Z",
  },
  lungs: {
    type: "path",
    // two rounded rectangles side by side
    d: "M178 182 Q174 178 174 194 Q174 210 180 214 Q186 218 188 210 Q190 202 188 192 Q186 182 178 182 Z " +
       "M214 182 Q218 178 218 194 Q218 210 212 214 Q206 218 204 210 Q202 202 204 192 Q206 182 214 182 Z",
  },
  liver: {
    type: "path",
    d: "M210 222 Q224 218 226 230 Q228 242 218 248 Q208 252 202 246 Q196 240 200 230 Q204 222 210 222 Z",
  },
  stomach: {
    type: "ellipse",
    cx: 193, cy: 254, rx: 18, ry: 14,
  },
  kidneys: {
    type: "path",
    d: "M174 262 Q170 258 170 270 Q170 282 176 284 Q180 285 182 278 Q184 270 180 262 Q178 258 174 262 Z " +
       "M218 262 Q222 258 222 270 Q222 282 216 284 Q212 285 210 278 Q208 270 212 262 Q214 258 218 262 Z",
  },
  intestine: {
    type: "ellipse",
    cx: 196, cy: 296, rx: 22, ry: 20,
  },
  muscles: {
    type: "path",
    // covers upper arms + thighs
    d: "M152 188 Q148 200 150 230 Q152 240 158 238 Q164 236 164 224 Q162 208 160 188 Z " +
       "M240 188 Q244 200 242 230 Q240 240 234 238 Q228 236 228 224 Q230 208 232 188 Z " +
       "M162 350 Q158 370 162 400 Q164 410 170 408 Q176 406 174 394 Q172 370 172 350 Z " +
       "M230 350 Q234 370 230 400 Q228 410 222 408 Q216 406 218 394 Q220 370 220 350 Z",
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Component
// ─────────────────────────────────────────────────────────────────────────────

export default function BodyVizMap({ analysis }) {
  const [active, setActive] = useState(null);
  const panelRef  = useRef(null);
  const figureRef = useRef(null);

  // Close on outside click
  useEffect(() => {
    function onDown(e) {
      if (
        panelRef.current  && !panelRef.current.contains(e.target) &&
        figureRef.current && !figureRef.current.contains(e.target)
      ) {
        setActive(null);
      }
    }
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, []);

  if (!analysis) return null;

  // Flat nutrient values for description interpolation
  const vals = {};
  for (const key of Object.keys(analysis)) {
    vals[key] = analysis[key]?.value ?? null;
  }

  // Compute which regions have data and at what level
  const positiveIds = new Set(["muscles", "intestine", "brain"]);
  const regions = SYSTEM_DEFS
    .map((def) => {
      if (allMissing(def.nutrients, analysis)) return null;
      const level = positiveIds.has(def.id)
        ? positiveLevel(def.nutrients, analysis)
        : worstLevel(def.nutrients, analysis);
      if (!level) return null;
      return { ...def, level, description: def.description(vals) };
    })
    .filter(Boolean);

  const activeRegion = regions.find((r) => r.id === active) || null;
  const regionMap    = Object.fromEntries(regions.map((r) => [r.id, r]));

  // Keyboard handler for SVG regions
  function handleKeyRegion(e, id) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      setActive(active === id ? null : id);
    }
  }

  return (
    <section
      className="bvm-section"
      aria-label="Body system educational visualization"
    >
      {/* ── Header ── */}
      <div className="bvm-header">
        <p className="bvm-label">BODY SYSTEMS</p>
        <h2>Nutritional associations with body systems</h2>
        <p className="bvm-intro">
          Each highlighted region shows a body system associated with one or
          more nutrients in this product, based on values per 100 g. Select a
          region on the figure or a label in the list to read more. This is an
          educational illustration — not a prediction, diagnosis, or medical
          advice.
        </p>
      </div>

      {/* ── Main layout ── */}
      <div className="bvm-layout">

        {/* ── SVG figure ── */}
        <div className="bvm-figure-wrap" ref={figureRef}>
          <svg
            className="bvm-svg"
            viewBox="0 0 392 620"
            xmlns="http://www.w3.org/2000/svg"
            role="img"
            aria-label="Detailed human body illustration with highlighted body system regions"
          >
            <defs>
              {/* Skin gradient */}
              <linearGradient id="skinGrad" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%"   stopColor="#e8d5c4" />
                <stop offset="50%"  stopColor="#f2e0d0" />
                <stop offset="100%" stopColor="#e8d5c4" />
              </linearGradient>
              <linearGradient id="skinGradV" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%"   stopColor="#edddd0" />
                <stop offset="100%" stopColor="#dfc8b8" />
              </linearGradient>
              {/* Muscle shading */}
              <linearGradient id="muscleShade" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%"   stopColor="#d4b99e" stopOpacity="0.5" />
                <stop offset="40%"  stopColor="#f2e0d0" stopOpacity="0"   />
                <stop offset="60%"  stopColor="#f2e0d0" stopOpacity="0"   />
                <stop offset="100%" stopColor="#d4b99e" stopOpacity="0.5" />
              </linearGradient>
              {/* Glow filter for active region */}
              <filter id="regionGlow" x="-30%" y="-30%" width="160%" height="160%">
                <feGaussianBlur stdDeviation="4" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
              {/* Inner anatomy clip — torso only */}
              <clipPath id="torsoClip">
                <path d="M152 150 C140 152 132 160 130 175 L128 320
                         C128 332 136 340 148 340 L244 340
                         C256 340 264 332 264 320 L262 175
                         C260 160 252 152 240 150 Z" />
              </clipPath>
              <clipPath id="headClip">
                <ellipse cx="200" cy="60" rx="44" ry="52" />
              </clipPath>
            </defs>

            {/* ═══════════════════════════════════════════════
                BODY SILHOUETTE  –  drawn back to front
            ═══════════════════════════════════════════════ */}

            {/* ── Left upper arm shadow ── */}
            <path
              d="M142 160 C128 162 118 174 116 196 L114 268
                 C114 278 118 286 126 288 L134 288
                 C142 288 146 280 146 268 L148 196 Z"
              fill="#dfc8b8" opacity="0.6"
            />
            {/* ── Right upper arm shadow ── */}
            <path
              d="M250 160 C264 162 274 174 276 196 L278 268
                 C278 278 274 286 266 288 L258 288
                 C250 288 246 280 246 268 L244 196 Z"
              fill="#dfc8b8" opacity="0.6"
            />

            {/* ── Left upper arm ── */}
            <path
              d="M142 158 C128 160 118 172 116 194 L114 266
                 C114 276 118 284 126 286 L134 286
                 C142 286 146 278 146 266 L148 194 Z"
              fill="url(#skinGrad)"
              stroke="#c9ad98" strokeWidth="1.2"
            />
            {/* ── Right upper arm ── */}
            <path
              d="M250 158 C264 160 274 172 276 194 L278 266
                 C278 276 274 284 266 286 L258 286
                 C250 286 246 278 246 266 L244 194 Z"
              fill="url(#skinGrad)"
              stroke="#c9ad98" strokeWidth="1.2"
            />

            {/* ── Left forearm ── */}
            <path
              d="M116 268 C112 278 110 296 112 316 L114 346
                 C114 354 118 360 124 360 L132 360
                 C138 360 142 354 142 346 L144 318
                 C146 296 144 278 140 268 Z"
              fill="url(#skinGrad)"
              stroke="#c9ad98" strokeWidth="1.2"
            />
            {/* ── Right forearm ── */}
            <path
              d="M276 268 C280 278 282 296 280 316 L278 346
                 C278 354 274 360 268 360 L260 360
                 C254 360 250 354 250 346 L248 318
                 C246 296 248 278 252 268 Z"
              fill="url(#skinGrad)"
              stroke="#c9ad98" strokeWidth="1.2"
            />

            {/* ── Left hand ── */}
            <ellipse cx="128" cy="370" rx="14" ry="12"
              fill="url(#skinGrad)" stroke="#c9ad98" strokeWidth="1.1" />
            {/* Fingers left */}
            <line x1="118" y1="375" x2="112" y2="388" stroke="#c9ad98" strokeWidth="2.8" strokeLinecap="round" />
            <line x1="123" y1="380" x2="119" y2="394" stroke="#c9ad98" strokeWidth="2.8" strokeLinecap="round" />
            <line x1="128" y1="382" x2="126" y2="396" stroke="#c9ad98" strokeWidth="2.8" strokeLinecap="round" />
            <line x1="133" y1="380" x2="133" y2="394" stroke="#c9ad98" strokeWidth="2.8" strokeLinecap="round" />
            <line x1="138" y1="375" x2="141" y2="387" stroke="#c9ad98" strokeWidth="2.5" strokeLinecap="round" />
            {/* knuckle dots left */}
            <circle cx="118" cy="374" r="1.5" fill="#c9ad98" />
            <circle cx="123" cy="379" r="1.5" fill="#c9ad98" />
            <circle cx="128" cy="381" r="1.5" fill="#c9ad98" />
            <circle cx="133" cy="379" r="1.5" fill="#c9ad98" />

            {/* ── Right hand ── */}
            <ellipse cx="264" cy="370" rx="14" ry="12"
              fill="url(#skinGrad)" stroke="#c9ad98" strokeWidth="1.1" />
            {/* Fingers right */}
            <line x1="274" y1="375" x2="280" y2="388" stroke="#c9ad98" strokeWidth="2.8" strokeLinecap="round" />
            <line x1="269" y1="380" x2="273" y2="394" stroke="#c9ad98" strokeWidth="2.8" strokeLinecap="round" />
            <line x1="264" y1="382" x2="266" y2="396" stroke="#c9ad98" strokeWidth="2.8" strokeLinecap="round" />
            <line x1="259" y1="380" x2="259" y2="394" stroke="#c9ad98" strokeWidth="2.8" strokeLinecap="round" />
            <line x1="254" y1="375" x2="251" y2="387" stroke="#c9ad98" strokeWidth="2.5" strokeLinecap="round" />
            {/* knuckle dots right */}
            <circle cx="274" cy="374" r="1.5" fill="#c9ad98" />
            <circle cx="269" cy="379" r="1.5" fill="#c9ad98" />
            <circle cx="264" cy="381" r="1.5" fill="#c9ad98" />
            <circle cx="259" cy="379" r="1.5" fill="#c9ad98" />

            {/* ── Torso ── */}
            <path
              d="M152 150 C140 152 132 160 130 175 L128 320
                 C128 332 136 340 148 340 L244 340
                 C256 340 264 332 264 320 L262 175
                 C260 160 252 152 240 150 Z"
              fill="url(#skinGrad)"
              stroke="#c9ad98" strokeWidth="1.4"
            />
            {/* Torso muscle shading */}
            <path
              d="M152 150 C140 152 132 160 130 175 L128 320
                 C128 332 136 340 148 340 L244 340
                 C256 340 264 332 264 320 L262 175
                 C260 160 252 152 240 150 Z"
              fill="url(#muscleShade)"
            />

            {/* ── Pectoral line ── */}
            <path d="M160 178 Q196 170 232 178" fill="none" stroke="#c2a48c" strokeWidth="1" opacity="0.7" />

            {/* ── Abs lines ── */}
            <line x1="196" y1="196" x2="196" y2="310" stroke="#c2a48c" strokeWidth="0.8" strokeDasharray="3 5" opacity="0.5" />
            <path d="M168 220 Q196 214 224 220" fill="none" stroke="#c2a48c" strokeWidth="0.7" opacity="0.5" />
            <path d="M166 248 Q196 242 226 248" fill="none" stroke="#c2a48c" strokeWidth="0.7" opacity="0.5" />
            <path d="M166 274 Q196 268 226 274" fill="none" stroke="#c2a48c" strokeWidth="0.7" opacity="0.5" />

            {/* ── Collar bones ── */}
            <path d="M162 154 Q180 148 196 150 Q212 148 230 154"
              fill="none" stroke="#bfa88e" strokeWidth="1.4" strokeLinecap="round" />

            {/* ── Internal anatomy  (clipped to torso) ── */}

            {/* Lungs */}
            <g clipPath="url(#torsoClip)" opacity="0.18">
              <path d="M178 168 Q168 164 166 184 Q164 206 170 220 Q176 230 182 226 Q188 220 188 204 Q188 186 182 168 Z"
                fill="#9fc5e8" stroke="#5b8ab5" strokeWidth="0.8" />
              <path d="M214 168 Q224 164 226 184 Q228 206 222 220 Q216 230 210 226 Q204 220 204 204 Q204 186 210 168 Z"
                fill="#9fc5e8" stroke="#5b8ab5" strokeWidth="0.8" />
            </g>

            {/* Heart */}
            <g clipPath="url(#torsoClip)" opacity="0.22">
              <path d="M196 194 C192 186 180 184 180 196 C180 208 196 220 196 220 C196 220 212 208 212 196 C212 184 200 186 196 194 Z"
                fill="#e8a0a0" stroke="#b05050" strokeWidth="0.8" />
            </g>

            {/* Liver */}
            <g clipPath="url(#torsoClip)" opacity="0.2">
              <path d="M208 224 Q228 218 232 236 Q236 252 224 258 Q212 262 206 252 Q200 242 204 232 Q206 224 208 224 Z"
                fill="#c8946e" stroke="#a06040" strokeWidth="0.8" />
            </g>

            {/* Stomach / pancreas */}
            <g clipPath="url(#torsoClip)" opacity="0.18">
              <ellipse cx="187" cy="252" rx="20" ry="14"
                fill="#c8a0b0" stroke="#986070" strokeWidth="0.8" />
            </g>

            {/* Kidneys */}
            <g clipPath="url(#torsoClip)" opacity="0.2">
              <path d="M166 268 Q160 262 160 280 Q160 294 168 296 Q174 296 176 286 Q178 274 174 266 Q172 262 166 268 Z"
                fill="#d4a0a0" stroke="#a06060" strokeWidth="0.8" />
              <path d="M226 268 Q232 262 232 280 Q232 294 224 296 Q218 296 216 286 Q214 274 218 266 Q220 262 226 268 Z"
                fill="#d4a0a0" stroke="#a06060" strokeWidth="0.8" />
            </g>

            {/* Intestine */}
            <g clipPath="url(#torsoClip)" opacity="0.16">
              <path d="M170 302 Q162 298 162 312 Q162 326 172 328 Q184 330 192 322 Q200 330 212 328 Q222 326 222 312 Q222 298 214 302 Q206 306 196 300 Q186 306 170 302 Z"
                fill="#c8b888" stroke="#9a8848" strokeWidth="0.8" />
            </g>

            {/* ── Pelvis / hip area ── */}
            <path
              d="M130 330 Q128 344 132 352 Q148 368 196 368 Q244 368 260 352 Q264 344 262 330 Z"
              fill="#dfc4b0" stroke="#c4a890" strokeWidth="1.1"
            />
            <path d="M148 340 Q172 350 196 348 Q220 350 244 340"
              fill="none" stroke="#c4a890" strokeWidth="0.8" opacity="0.6" />

            {/* ── Left thigh ── */}
            <path
              d="M134 362 C122 364 114 376 112 398 L110 454
                 C110 464 116 472 124 472 L146 472
                 C154 472 158 464 158 454 L160 398
                 C162 376 156 366 148 362 Z"
              fill="url(#skinGrad)" stroke="#c9ad98" strokeWidth="1.2"
            />
            {/* ── Right thigh ── */}
            <path
              d="M258 362 C270 364 278 376 280 398 L282 454
                 C282 464 276 472 268 472 L246 472
                 C238 472 234 464 234 454 L232 398
                 C230 376 236 366 244 362 Z"
              fill="url(#skinGrad)" stroke="#c9ad98" strokeWidth="1.2"
            />

            {/* ── Quad shading ── */}
            <path d="M134 362 C122 364 114 376 112 398 L110 454 C110 464 116 472 124 472 L146 472 C154 472 158 464 158 454 L160 398 C162 376 156 366 148 362 Z"
              fill="url(#muscleShade)" />
            <path d="M258 362 C270 364 278 376 280 398 L282 454 C282 464 276 472 268 472 L246 472 C238 472 234 464 234 454 L232 398 C230 376 236 366 244 362 Z"
              fill="url(#muscleShade)" />

            {/* ── Left knee ── */}
            <ellipse cx="135" cy="476" rx="22" ry="12"
              fill="#dfc8b8" stroke="#c4a890" strokeWidth="1" />
            {/* ── Right knee ── */}
            <ellipse cx="257" cy="476" rx="22" ry="12"
              fill="#dfc8b8" stroke="#c4a890" strokeWidth="1" />

            {/* ── Left calf ── */}
            <path
              d="M114 480 C110 490 110 508 114 530 L118 556
                 C118 562 122 566 128 566 L144 566
                 C150 566 154 562 154 556 L158 530
                 C162 508 160 490 156 480 Z"
              fill="url(#skinGrad)" stroke="#c9ad98" strokeWidth="1.2"
            />
            {/* ── Right calf ── */}
            <path
              d="M278 480 C282 490 282 508 278 530 L274 556
                 C274 562 270 566 264 566 L248 566
                 C242 566 238 562 238 556 L234 530
                 C230 508 232 490 236 480 Z"
              fill="url(#skinGrad)" stroke="#c9ad98" strokeWidth="1.2"
            />

            {/* ── Ankles ── */}
            <ellipse cx="136" cy="568" rx="16" ry="8"
              fill="#dfc8b8" stroke="#c4a890" strokeWidth="1" />
            <ellipse cx="256" cy="568" rx="16" ry="8"
              fill="#dfc8b8" stroke="#c4a890" strokeWidth="1" />

            {/* ── Left foot ── */}
            <path
              d="M120 572 Q108 574 102 580 Q98 586 104 594 Q108 598 120 598
                 L148 598 Q158 596 160 590 Q162 582 156 576 Q150 572 140 572 Z"
              fill="#dfc4b0" stroke="#c4a890" strokeWidth="1.1"
            />
            {/* Toes left */}
            <ellipse cx="104" cy="596" rx="4" ry="3.5" fill="#d4b8a4" stroke="#c4a890" strokeWidth="0.7" />
            <ellipse cx="111" cy="598" rx="4" ry="3.5" fill="#d4b8a4" stroke="#c4a890" strokeWidth="0.7" />
            <ellipse cx="119" cy="599" rx="4" ry="3.5" fill="#d4b8a4" stroke="#c4a890" strokeWidth="0.7" />
            <ellipse cx="127" cy="599" rx="4" ry="3.5" fill="#d4b8a4" stroke="#c4a890" strokeWidth="0.7" />
            <ellipse cx="135" cy="598" rx="3.5" ry="3" fill="#d4b8a4" stroke="#c4a890" strokeWidth="0.7" />

            {/* ── Right foot ── */}
            <path
              d="M272 572 Q284 574 290 580 Q294 586 288 594 Q284 598 272 598
                 L244 598 Q234 596 232 590 Q230 582 236 576 Q242 572 252 572 Z"
              fill="#dfc4b0" stroke="#c4a890" strokeWidth="1.1"
            />
            {/* Toes right */}
            <ellipse cx="288" cy="596" rx="4" ry="3.5" fill="#d4b8a4" stroke="#c4a890" strokeWidth="0.7" />
            <ellipse cx="281" cy="598" rx="4" ry="3.5" fill="#d4b8a4" stroke="#c4a890" strokeWidth="0.7" />
            <ellipse cx="273" cy="599" rx="4" ry="3.5" fill="#d4b8a4" stroke="#c4a890" strokeWidth="0.7" />
            <ellipse cx="265" cy="599" rx="4" ry="3.5" fill="#d4b8a4" stroke="#c4a890" strokeWidth="0.7" />
            <ellipse cx="257" cy="598" rx="3.5" ry="3" fill="#d4b8a4" stroke="#c4a890" strokeWidth="0.7" />

            {/* ═══════════════════════════════════════════════
                HEAD  –  drawn last so it appears on top
            ═══════════════════════════════════════════════ */}

            {/* ── Neck ── */}
            <path d="M182 108 Q178 116 180 136 L212 136 Q214 116 210 108 Z"
              fill="url(#skinGradV)" stroke="#c9ad98" strokeWidth="1.1" />
            {/* Neck shadow */}
            <path d="M182 120 Q184 128 196 130 Q208 128 210 120"
              fill="none" stroke="#c2a48c" strokeWidth="0.7" opacity="0.5" />

            {/* ── Left ear ── */}
            <path d="M156 68 Q148 62 146 74 Q144 86 148 94 Q152 100 158 96 Q162 92 160 84 Q160 74 156 68 Z"
              fill="#e0c8b4" stroke="#c9ad98" strokeWidth="1" />
            {/* Ear canal */}
            <path d="M152 74 Q150 80 152 86" fill="none" stroke="#c0a080" strokeWidth="0.8" />

            {/* ── Right ear ── */}
            <path d="M236 68 Q244 62 246 74 Q248 86 244 94 Q240 100 234 96 Q230 92 232 84 Q232 74 236 68 Z"
              fill="#e0c8b4" stroke="#c9ad98" strokeWidth="1" />
            {/* Ear canal */}
            <path d="M240 74 Q242 80 240 86" fill="none" stroke="#c0a080" strokeWidth="0.8" />

            {/* ── Head base ── */}
            <path
              d="M158 24 Q178 12 200 12 Q222 12 238 24
                 Q256 38 256 62 Q256 92 248 108
                 Q232 126 200 128 Q168 126 152 108
                 Q144 92 144 62 Q144 38 158 24 Z"
              fill="url(#skinGradV)"
              stroke="#c9ad98" strokeWidth="1.4"
            />

            {/* ── Hair ── */}
            <path
              d="M158 24 Q168 10 196 8 Q224 8 238 24
                 Q248 14 250 30 Q256 20 256 40
                 Q260 26 256 44
                 Q248 16 238 22
                 Q222 10 200 10 Q178 10 162 22
                 Q152 16 144 44 Q140 26 144 40
                 Q144 20 150 30 Z"
              fill="#3a2a1e" stroke="#2a1e14" strokeWidth="0.8"
            />
            {/* Hair body top */}
            <path
              d="M158 22 Q168 6 196 4 Q224 6 238 22
                 Q246 12 252 28 Q252 10 240 12 Q224 4 200 4 Q176 4 160 12
                 Q148 10 148 28 Q154 12 158 22 Z"
              fill="#3a2a1e"
            />

            {/* ── Forehead subtle shading ── */}
            <ellipse cx="200" cy="38" rx="36" ry="16"
              fill="#e8c8b0" opacity="0.2" />

            {/* ── Eyebrows ── */}
            <path d="M170 52 Q180 46 190 50" fill="none" stroke="#3a2a1e" strokeWidth="2.2" strokeLinecap="round" />
            <path d="M202 50 Q212 46 222 52" fill="none" stroke="#3a2a1e" strokeWidth="2.2" strokeLinecap="round" />

            {/* ── Eyes ── */}
            {/* Left eye */}
            <ellipse cx="180" cy="62" rx="10" ry="7" fill="white" stroke="#c9ad98" strokeWidth="0.8" />
            <ellipse cx="180" cy="63" rx="6"  ry="5.5" fill="#5a3e28" />
            <ellipse cx="180" cy="63" rx="4"  ry="4"   fill="#2a1a0e" />
            <ellipse cx="177" cy="61" rx="1.5" ry="1.5" fill="white" />
            {/* Left eyelid crease */}
            <path d="M170 62 Q180 55 190 62" fill="none" stroke="#c0987a" strokeWidth="0.7" opacity="0.6" />
            {/* Left lashes */}
            <path d="M170 62 Q168 57 170 54" fill="none" stroke="#2a1a0e" strokeWidth="0.9" />
            <path d="M190 62 Q192 57 190 54" fill="none" stroke="#2a1a0e" strokeWidth="0.9" />

            {/* Right eye */}
            <ellipse cx="220" cy="62" rx="10" ry="7" fill="white" stroke="#c9ad98" strokeWidth="0.8" />
            <ellipse cx="220" cy="63" rx="6"  ry="5.5" fill="#5a3e28" />
            <ellipse cx="220" cy="63" rx="4"  ry="4"   fill="#2a1a0e" />
            <ellipse cx="217" cy="61" rx="1.5" ry="1.5" fill="white" />
            {/* Right eyelid crease */}
            <path d="M210 62 Q220 55 230 62" fill="none" stroke="#c0987a" strokeWidth="0.7" opacity="0.6" />
            {/* Right lashes */}
            <path d="M210 62 Q208 57 210 54" fill="none" stroke="#2a1a0e" strokeWidth="0.9" />
            <path d="M230 62 Q232 57 230 54" fill="none" stroke="#2a1a0e" strokeWidth="0.9" />

            {/* ── Nose ── */}
            <path d="M196 66 Q193 78 188 84 Q194 88 200 88 Q206 88 212 84 Q207 78 204 66 Z"
              fill="none" stroke="#c0987a" strokeWidth="1" strokeLinejoin="round" />
            <ellipse cx="190" cy="84" rx="4" ry="3" fill="#d4a880" opacity="0.5" />
            <ellipse cx="210" cy="84" rx="4" ry="3" fill="#d4a880" opacity="0.5" />
            <ellipse cx="190" cy="84" rx="2.5" ry="2" fill="#b8906a" opacity="0.6" />
            <ellipse cx="210" cy="84" rx="2.5" ry="2" fill="#b8906a" opacity="0.6" />

            {/* ── Philtrum ── */}
            <path d="M196 88 Q197 92 200 94 Q203 92 204 88"
              fill="none" stroke="#c0987a" strokeWidth="0.8" opacity="0.5" />

            {/* ── Mouth / lips ── */}
            {/* Upper lip */}
            <path d="M186 96 Q192 92 200 94 Q208 92 214 96 Q208 98 200 97 Q192 98 186 96 Z"
              fill="#c89080" stroke="#b07060" strokeWidth="0.5" />
            {/* Lower lip */}
            <path d="M186 96 Q192 104 200 106 Q208 104 214 96 Q208 98 200 97 Q192 98 186 96 Z"
              fill="#d4a090" stroke="#b07060" strokeWidth="0.5" />
            {/* Lip line */}
            <path d="M186 96 Q200 97 214 96" fill="none" stroke="#a06050" strokeWidth="0.7" />
            {/* Smile corners */}
            <path d="M186 96 Q184 98 185 101" fill="none" stroke="#b07060" strokeWidth="0.7" />
            <path d="M214 96 Q216 98 215 101" fill="none" stroke="#b07060" strokeWidth="0.7" />

            {/* ── Chin / jaw line ── */}
            <path d="M152 92 Q152 112 162 122 Q176 132 200 134 Q224 132 238 122 Q248 112 248 92"
              fill="none" stroke="#c2a48c" strokeWidth="0.6" opacity="0.4" />

            {/* ── Cheek blush ── */}
            <ellipse cx="168" cy="80" rx="12" ry="7" fill="#e8a090" opacity="0.12" />
            <ellipse cx="232" cy="80" rx="12" ry="7" fill="#e8a090" opacity="0.12" />

            {/* ── Brain visible through head ── */}
            <g clipPath="url(#headClip)" opacity="0.1">
              <ellipse cx="200" cy="44" rx="36" ry="28" fill="#a0b8e0" stroke="#6080b0" strokeWidth="0.8" />
              <path d="M178 38 Q196 30 214 38" fill="none" stroke="#6080b0" strokeWidth="0.8" />
              <path d="M170 50 Q196 40 222 50" fill="none" stroke="#6080b0" strokeWidth="0.7" />
            </g>

            {/* ═══════════════════════════════════════════════
                HIGHLIGHT OVERLAY REGIONS  –  clickable
            ═══════════════════════════════════════════════ */}

            {regions.map((region) => {
              const shape = REGION_SHAPES[region.id];
              if (!shape) return null;
              const colors  = LEVEL_COLORS[region.level];
              const isActive = active === region.id;

              const sharedProps = {
                key: region.id,
                fill: colors.fill,
                stroke: colors.stroke,
                strokeWidth: isActive ? 2.4 : 1.6,
                strokeDasharray: isActive ? "none" : "4 3",
                filter: isActive ? "url(#regionGlow)" : "none",
                style: { cursor: "pointer", transition: "all 0.22s ease" },
                onClick: () => setActive(isActive ? null : region.id),
                onMouseEnter: () => setActive(region.id),
                tabIndex: 0,
                role: "button",
                "aria-label": `${region.label}: ${LEVEL_LABEL[region.level]} level. Press Enter to read details.`,
                "aria-pressed": isActive,
                onKeyDown: (e) => handleKeyRegion(e, region.id),
              };

              if (shape.type === "ellipse") {
                return (
                  <ellipse
                    {...sharedProps}
                    cx={shape.cx}
                    cy={shape.cy}
                    rx={shape.rx + (isActive ? 3 : 0)}
                    ry={shape.ry + (isActive ? 3 : 0)}
                  />
                );
              }
              return <path {...sharedProps} d={shape.d} />;
            })}

          </svg>

          {/* Legend key below figure */}
          <div className="bvm-fig-legend" aria-label="Colour key">
            <span className="bvm-dot" data-level="high"     aria-label="High" />  High
            <span className="bvm-dot" data-level="moderate" aria-label="Moderate" /> Moderate
            <span className="bvm-dot" data-level="low"      aria-label="Low" />    Low
          </div>
        </div>

        {/* ── Right panel: region list + detail ── */}
        <div className="bvm-right" ref={panelRef}>

          <p className="bvm-right-hint">
            Select a region on the figure or choose a system below.
          </p>

          {/* Region buttons */}
          <div className="bvm-region-list" role="list">
            {regions.map((region) => (
              <button
                key={region.id}
                role="listitem"
                className={`bvm-region-btn${active === region.id ? " active" : ""}`}
                data-level={region.level}
                onClick={() => setActive(active === region.id ? null : region.id)}
                aria-expanded={active === region.id}
                aria-controls={`bvm-panel-${region.id}`}
              >
                <span className="bvm-dot" data-level={region.level} aria-hidden="true" />
                <span className="bvm-region-label">{region.label}</span>
                <span className="bvm-level-badge" data-level={region.level}>
                  {LEVEL_LABEL[region.level]}
                </span>
              </button>
            ))}
          </div>

          {/* Detail panel */}
          {activeRegion && (
            <div
              id={`bvm-panel-${activeRegion.id}`}
              className="bvm-panel"
              role="region"
              aria-live="polite"
            >
              <div className="bvm-panel-head">
                <span className="bvm-dot" data-level={activeRegion.level} aria-hidden="true" />
                <strong>{activeRegion.label}</strong>
                <span className="bvm-level-badge" data-level={activeRegion.level}>
                  {LEVEL_LABEL[activeRegion.level]}
                </span>
                <button
                  className="bvm-close"
                  onClick={() => setActive(null)}
                  aria-label="Close detail panel"
                >
                  &#x2715;
                </button>
              </div>
              <p className="bvm-panel-desc">{activeRegion.description}</p>
              <p className="bvm-panel-basis">
                Based on: values per 100 g as recorded in the database.
              </p>
            </div>
          )}

          {/* Screen-reader summary */}
          <ul
            className="bvm-sr-only"
            aria-label="Nutrient to body system associations"
          >
            {regions.map((r) => (
              <li key={r.id}>
                {r.label} ({LEVEL_LABEL[r.level]}): {r.description}
              </li>
            ))}
          </ul>

        </div>
      </div>

      {/* ── Disclaimer ── */}
      <p className="bvm-disclaimer">
        This is an educational illustration showing possible associations
        between nutrients and body systems as described in nutritional and
        epidemiological literature. It does not predict individual health
        outcomes, is not a risk assessment, and is not medical or dietary
        advice. Nutrient levels shown are the database values per 100 g,
        classified using the project&rsquo;s own analytical categories
        (LOW / MODERATE / HIGH). Consult a qualified health professional for
        personal guidance.
      </p>
    </section>
  );
}
