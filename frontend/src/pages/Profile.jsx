import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import "./Profile.css";

function toForm(profile) {
  return {
    age: profile.age ?? "",
    gender: profile.gender ?? "",
    height_cm: profile.height_cm ?? "",
    weight_kg: profile.weight_kg ?? "",
    diet_preference: profile.diet_preference ?? "",
    allergies: profile.allergies || [],
    health_goal: profile.health_goal ?? "",
  };
}

const toNumber = (value) => (value === "" ? null : Number(value));

function toPayload(form) {
  return {
    age: form.age === "" ? null : Math.round(Number(form.age)),
    gender: form.gender || null,
    height_cm: toNumber(form.height_cm),
    weight_kg: toNumber(form.weight_kg),
    diet_preference: form.diet_preference || null,
    allergies: form.allergies,
    health_goal: form.health_goal || null,
  };
}

// Same limits as the server (the server checks them again)
function validate(form) {
  const check = (value, low, high, label) => {
    if (value === "") {
      return "";
    }

    const number = Number(value);

    if (Number.isNaN(number) || number < low || number > high) {
      return `${label} must be between ${low} and ${high}.`;
    }

    return "";
  };

  return (
    check(form.age, 5, 120, "Age") ||
    check(form.height_cm, 50, 250, "Height (cm)") ||
    check(form.weight_kg, 10, 300, "Weight (kg)")
  );
}

// Live preview only; the saved value comes from the server
function previewBmi(form) {
  const height = Number(form.height_cm);
  const weight = Number(form.weight_kg);

  if (!height || !weight || height < 50 || weight < 10) {
    return null;
  }

  const value = Math.round((weight / (height / 100) ** 2) * 10) / 10;
  const age = form.age === "" ? null : Number(form.age);

  let category = null;

  if (age === null || age >= 18) {
    if (value < 18.5) {
      category = "Underweight";
    } else if (value < 23) {
      category = "Healthy weight";
    } else if (value < 25) {
      category = "Overweight";
    } else {
      category = "Obese";
    }
  }

  return { value, category };
}

function errorText(body, fallback) {
  const detail = body?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item) => String(item.msg || "").replace(/^Value error,\s*/i, ""))
      .filter(Boolean)
      .join(" ");
  }

  return fallback;
}

function Profile() {
  const { authFetch } = useAuth();

  const [options, setOptions] = useState(null);
  const [form, setForm] = useState(null);
  const [bmi, setBmi] = useState(null);
  const [loadError, setLoadError] = useState("");

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const [profileResponse, optionsResponse] = await Promise.all([
          authFetch("/profile"),
          authFetch("/profile/options"),
        ]);

        if (!profileResponse.ok || !optionsResponse.ok) {
          throw new Error("Unable to load your profile.");
        }

        const profileBody = await profileResponse.json();
        const optionsBody = await optionsResponse.json();

        if (!cancelled) {
          setOptions(optionsBody);
          setForm(toForm(profileBody.profile));
          setBmi(profileBody.bmi);
        }
      } catch (err) {
        if (!cancelled) {
          setLoadError(
            err.message === "Failed to fetch"
              ? "Unable to reach the server. Please make sure the backend is running."
              : err.message
          );
        }
      }
    };

    load();

    return () => {
      cancelled = true;
    };
  }, [authFetch]);

  const change = (key) => (event) => {
    setForm((current) => ({ ...current, [key]: event.target.value }));
    setSaved(false);
  };

  const toggleAllergy = (name) => {
    setForm((current) => ({
      ...current,
      allergies: current.allergies.includes(name)
        ? current.allergies.filter((item) => item !== name)
        : [...current.allergies, name],
    }));
    setSaved(false);
  };

  const save = async () => {
    const problem = validate(form);

    if (problem) {
      setError(problem);
      setSaved(false);
      return;
    }

    setSaving(true);
    setError("");
    setSaved(false);

    try {
      const response = await authFetch("/profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(toPayload(form)),
      });

      const body = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(errorText(body, "Unable to save your profile."));
      }

      setForm(toForm(body.profile));
      setBmi(body.bmi);
      setSaved(true);
    } catch (err) {
      setError(
        err.message === "Failed to fetch"
          ? "Unable to reach the server. Please make sure the backend is running."
          : err.message
      );
    } finally {
      setSaving(false);
    }
  };

  if (loadError) {
    return (
      <div className="nv-pf">
        <div className="nv-pf-error" role="alert">{loadError}</div>
      </div>
    );
  }

  if (!form || !options) {
    return <div className="nv-pf"><p className="nv-pf-sub">Loading your profile...</p></div>;
  }

  const live = previewBmi(form) || (bmi?.value ? bmi : null);

  return (
    <div className="nv-pf">

      <p className="nv-pf-label">MY PROFILE</p>

      <h1>Your profile</h1>

      <p className="nv-pf-sub">
        This is used to personalise healthier-food suggestions. Only you
        can see it, and everything is optional.
      </p>

      {error && (
        <div className="nv-pf-error" role="alert">{error}</div>
      )}

      <div className="nv-pf-card">

        <h3>About you</h3>

        <div className="nv-pf-grid">

          <label className="nv-pf-field">
            <span>Age</span>
            <input
              type="number"
              min="5"
              max="120"
              value={form.age}
              onChange={change("age")}
            />
          </label>

          <label className="nv-pf-field">
            <span>Gender</span>
            <select value={form.gender} onChange={change("gender")}>
              <option value="">Not specified</option>
              {options.genders.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          <label className="nv-pf-field">
            <span>Height (cm)</span>
            <input
              type="number"
              min="50"
              max="250"
              step="any"
              value={form.height_cm}
              onChange={change("height_cm")}
            />
          </label>

          <label className="nv-pf-field">
            <span>Weight (kg)</span>
            <input
              type="number"
              min="10"
              max="300"
              step="any"
              value={form.weight_kg}
              onChange={change("weight_kg")}
            />
          </label>

        </div>

        <div className="nv-pf-bmi" data-testid="bmi">
          {live ? (
            <>
              <strong>BMI {live.value}</strong>
              {live.category ? ` • ${live.category}` : ""}
              <small>
                {live.category
                  ? "Uses Asian-Indian cut-offs (overweight from 23, obese from 25). BMI is a screening number, not a diagnosis."
                  : "BMI categories for children and teenagers need age-specific growth charts, so none is shown."}
              </small>
            </>
          ) : (
            <span>Add your height and weight to see your BMI.</span>
          )}
        </div>

      </div>

      <div className="nv-pf-card">

        <h3>Food preferences</h3>

        <div className="nv-pf-grid">

          <label className="nv-pf-field">
            <span>Diet</span>
            <select value={form.diet_preference} onChange={change("diet_preference")}>
              <option value="">Not specified</option>
              {options.diets.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          <label className="nv-pf-field">
            <span>Health goal</span>
            <select value={form.health_goal} onChange={change("health_goal")}>
              <option value="">Not specified</option>
              {options.goals.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

        </div>

        <p className="nv-pf-note">
          The dataset has no vegetarian marker, so diet matching is
          estimated from the ingredient list.
        </p>

      </div>

      <div className="nv-pf-card">

        <h3>Allergies</h3>

        <div className="nv-pf-checks">
          {options.allergens.map((name) => {
            const on = form.allergies.includes(name);

            return (
              <label key={name} className={`nv-pf-check ${on ? "on" : ""}`}>
                <input
                  type="checkbox"
                  checked={on}
                  onChange={() => toggleAllergy(name)}
                />
                {name}
              </label>
            );
          })}
        </div>

        <p className="nv-pf-note">
          Products that seem to contain these are left out of suggestions.
          Allergen detection is based on ingredient keywords, so always
          check the pack.
        </p>

      </div>

      <div className="nv-pf-actions">

        <button className="nv-pf-save" onClick={save} disabled={saving}>
          {saving ? "Saving..." : "Save profile"}
        </button>

        {saved && <span className="nv-pf-ok" role="status">Profile saved.</span>}

      </div>

    </div>
  );
}

export default Profile;