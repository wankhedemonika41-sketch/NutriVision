import { useState } from "react";
import "./App.css";

import { useAuth } from "./auth/AuthContext";
import AppShell from "./components/AppShell";

import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";
import ScanProduct from "./pages/ScanProduct";
import ScanLabel from "./pages/ScanLabel";
import ProductCompare from "./pages/ProductCompare";
import ProductSearch from "./pages/ProductSearch";
import ProductDetails from "./pages/ProductDetails";
import Profile from "./pages/Profile";
import NutritionAnalysis from "./pages/NutritionAnalysis";

// Pages that belong under a sidebar item
const SIDEBAR_FOR = {
  details: "search",
  analysis: "search",
};

function App() {
  const { user, loading, logout } = useAuth();

  // Before login: null = landing page, "login" / "signup" = login page
  const [authMode, setAuthMode] = useState(null);

  // After login
  const [view, setView] = useState("dashboard");
  const [productId, setProductId] = useState(null);

  const go = (nextView) => {
    setView(nextView);
    setProductId(null);
  };

  const handleLogout = () => {
    logout();
    setAuthMode(null);
    go("dashboard");
  };

  if (loading) {
    return <div className="nv-splash">Loading...</div>;
  }


  /* ---------------- NOT LOGGED IN ---------------- */

  if (!user) {
    if (authMode) {
      return (
        <Login
          initialMode={authMode}
          onBack={() => setAuthMode(null)}
        />
      );
    }

    return (
      <Landing
        onLogin={() => setAuthMode("login")}
        onSignup={() => setAuthMode("signup")}
      />
    );
  }


  /* ---------------- LOGGED IN ---------------- */

  const backToDashboard = () => go("dashboard");

  let page;

  if (view === "search") {
    page = (
      <ProductSearch
        onBack={backToDashboard}
        onProductSelect={(id) => {
          setProductId(id);
          setView("details");
        }}
      />
    );
  } else if (view === "details") {
    page = (
      <ProductDetails
        productId={productId}
        onBack={() => setView("search")}
        onAnalyze={() => setView("analysis")}
        onOpenProduct={(id) => setProductId(id)}
        onOpenProfile={() => go("profile")}
      />
    );
  } else if (view === "analysis") {
    page = (
      <NutritionAnalysis
        productId={productId}
        onBack={() => setView("details")}
      />
    );
  } else if (view === "scan") {
    page = <ScanProduct onBack={backToDashboard} />;
  } else if (view === "label") {
    page = <ScanLabel onBack={backToDashboard} />;
  } else if (view === "compare") {
    page = <ProductCompare onBack={backToDashboard} />;
  } else if (view === "history") {
    page = <History onNavigate={go} />;
  } else if (view === "profile") {
    page = <Profile />;
  } else {
    page = <Dashboard user={user} onNavigate={go} />;
  }

  return (
    <AppShell
      user={user}
      active={SIDEBAR_FOR[view] || view}
      onNavigate={go}
      onLogout={handleLogout}
    >
      {page}
    </AppShell>
  );
}

export default App;