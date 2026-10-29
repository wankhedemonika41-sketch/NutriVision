import { useState } from "react";
import { useAuth } from "../auth/AuthContext";
import "./Auth.css";

const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

function validate(mode, form) {
  if (mode === "signup" && form.name.trim().length < 2) {
    return "Please enter your name.";
  }

  if (!EMAIL_PATTERN.test(form.email.trim())) {
    return "Enter a valid email address.";
  }

  if (mode === "signup") {
    if (form.password.length < 8) {
      return "Password must be at least 8 characters.";
    }

    if (!/[A-Za-z]/.test(form.password) || !/\d/.test(form.password)) {
      return "Password must contain at least one letter and one number.";
    }

    if (form.password !== form.confirm) {
      return "The two passwords do not match.";
    }
  } else if (!form.password) {
    return "Enter your password.";
  }

  return "";
}

function Login({ initialMode = "login", onBack }) {
  const { login, register } = useAuth();

  const [mode, setMode] = useState(initialMode);
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirm: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const isSignup = mode === "signup";

  const update = (key) => (event) => {
    setForm((current) => ({ ...current, [key]: event.target.value }));
  };

  const switchMode = (next) => {
    setMode(next);
    setError("");
    setForm((current) => ({ ...current, password: "", confirm: "" }));
  };

  const submit = async (event) => {
    event.preventDefault();

    const problem = validate(mode, form);

    if (problem) {
      setError(problem);
      return;
    }

    setLoading(true);
    setError("");

    try {
      if (isSignup) {
        await register(form.name.trim(), form.email.trim(), form.password);
      } else {
        await login(form.email.trim(), form.password);
      }
      // on success the app switches to the dashboard by itself
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <div className="nv-auth">

      <aside className="nv-auth-side">

        <div className="nv-brand">
          <div className="nv-brand-icon">N</div>
          NutriVision
        </div>

        <h2>Know what is really inside your food.</h2>

        <p>
          Scan a barcode or a label and get a clear health score, simple
          ingredient explanations, and healthier alternatives.
        </p>

        <ul className="nv-auth-points">
          <li>Health score from 0 to 100 with reasons</li>
          <li>Detects additives, palm oil and allergens</li>
          <li>Compare two products side by side</li>
        </ul>

      </aside>

      <main className="nv-auth-main">

        <div className="nv-auth-topbar">
          <button className="nv-linkbtn" type="button" onClick={onBack}>
            &larr; Back to home
          </button>
        </div>

        <div className="nv-auth-card">

          <h1>{isSignup ? "Create your account" : "Welcome back"}</h1>

          <p className="nv-auth-sub">
            {isSignup
              ? "It takes less than a minute."
              : "Log in to continue to your dashboard."}
          </p>

          <div className="nv-tabs" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={!isSignup}
              className={`nv-tab ${!isSignup ? "active" : ""}`}
              onClick={() => switchMode("login")}
            >
              Log in
            </button>

            <button
              type="button"
              role="tab"
              aria-selected={isSignup}
              className={`nv-tab ${isSignup ? "active" : ""}`}
              onClick={() => switchMode("signup")}
            >
              Sign up
            </button>
          </div>

          <form onSubmit={submit} noValidate>

            {isSignup && (
              <label className="nv-field">
                <span>Full name</span>
                <input
                  type="text"
                  autoComplete="name"
                  value={form.name}
                  onChange={update("name")}
                  placeholder="Your name"
                />
              </label>
            )}

            <label className="nv-field">
              <span>Email</span>
              <input
                type="email"
                autoComplete="email"
                value={form.email}
                onChange={update("email")}
                placeholder="you@example.com"
              />
            </label>

            <label className="nv-field">
              <span>Password</span>

              <div className="nv-input-wrap">
                <input
                  type={showPassword ? "text" : "password"}
                  autoComplete={isSignup ? "new-password" : "current-password"}
                  value={form.password}
                  onChange={update("password")}
                  placeholder={isSignup ? "Create a password" : "Your password"}
                />

                <button
                  type="button"
                  className="nv-toggle"
                  onClick={() => setShowPassword((shown) => !shown)}
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>

              {isSignup && (
                <small className="nv-hint">
                  At least 8 characters, with a letter and a number.
                </small>
              )}
            </label>

            {isSignup && (
              <label className="nv-field">
                <span>Confirm password</span>
                <input
                  type={showPassword ? "text" : "password"}
                  autoComplete="new-password"
                  value={form.confirm}
                  onChange={update("confirm")}
                  placeholder="Type the password again"
                />
              </label>
            )}

            {error && (
              <div className="nv-error" role="alert">
                {error}
              </div>
            )}

            <button className="nv-submit" type="submit" disabled={loading}>
              {loading
                ? "Please wait..."
                : isSignup
                  ? "Create account"
                  : "Log in"}
            </button>

          </form>

          <p className="nv-switch">
            {isSignup ? "Already have an account? " : "New to NutriVision? "}

            <button
              type="button"
              className="nv-linkbtn"
              onClick={() => switchMode(isSignup ? "login" : "signup")}
            >
              {isSignup ? "Log in" : "Create an account"}
            </button>
          </p>

        </div>

      </main>

    </div>
  );
}

export default Login;