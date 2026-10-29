import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { API_URL } from "../config";

const TOKEN_KEY = "nutrivision_token";

const AuthContext = createContext(null);

function readableError(body, fallback) {
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

async function post(path, payload) {
  let response;

  try {
    response = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new Error(
      "Unable to reach the server. Please make sure the backend is running."
    );
  }

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(readableError(body, "Something went wrong. Please try again."));
  }

  return body;
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);   // checking a saved login

  // On page load: is the saved token still valid?
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);

    if (!token) {
      setLoading(false);
      return undefined;
    }

    let cancelled = false;

    fetch(`${API_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (response) => {
        if (response.ok) {
          const me = await response.json();

          if (!cancelled) {
            setUser(me);
          }
        } else if (response.status === 401) {
          localStorage.removeItem(TOKEN_KEY);     // expired or invalid
        }
        // any other problem (server down): keep the token, show the login page
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const startSession = (data) => {
    localStorage.setItem(TOKEN_KEY, data.token);
    setUser(data.user);
  };

  const login = async (email, password) => {
    startSession(await post("/auth/login", { email, password }));
  };

  const register = async (name, email, password) => {
    startSession(await post("/auth/register", { name, email, password }));
  };

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  }, []);

  // fetch() that sends the login token (use this for personal data later)
  const authFetch = useCallback(
    async (path, options = {}) => {
      const response = await fetch(`${API_URL}${path}`, {
        ...options,
        headers: {
          ...(options.headers || {}),
          Authorization: `Bearer ${localStorage.getItem(TOKEN_KEY) || ""}`,
        },
      });

      if (response.status === 401) {
        logout();
      }

      return response;
    },
    [logout]
  );

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, logout, authFetch }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside <AuthProvider>");
  }

  return context;
}