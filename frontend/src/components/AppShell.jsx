import { useState } from "react";
import "./AppShell.css";

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard" },
  { id: "search", label: "Search Product" },
  { id: "scan", label: "Scan Barcode" },
  { id: "label", label: "Scan Label" },
  { id: "compare", label: "Compare" },
  { id: "history", label: "My Report" },
  { id: "profile", label: "My Profile" },
];

function AppShell({ user, active, onNavigate, onLogout, children }) {
  const [menuOpen, setMenuOpen] = useState(false);

  const go = (id) => {
    setMenuOpen(false);
    onNavigate(id);
  };

  return (
    <div className="nv-shell">

      <header className="nv-topbar">
        <button
          className="nv-menu"
          aria-label="Open menu"
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((open) => !open)}
        >
          &#9776;
        </button>

        <span>NutriVision</span>
      </header>

      {menuOpen && (
        <div className="nv-backdrop" onClick={() => setMenuOpen(false)} />
      )}

      <aside className={`nv-sidebar ${menuOpen ? "open" : ""}`}>

        <div className="nv-side-brand">
          <div className="nv-brand-icon">N</div>
          NutriVision
        </div>

        <nav className="nv-nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={active === item.id ? "active" : ""}
              onClick={() => go(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="nv-side-user">

          <div>
            <strong>{user.name}</strong>
            <small>{user.email}</small>
          </div>

          <button className="nv-logout" onClick={onLogout}>
            Log out
          </button>

        </div>

      </aside>

      <main className="nv-content">{children}</main>

    </div>
  );
}

export default AppShell;