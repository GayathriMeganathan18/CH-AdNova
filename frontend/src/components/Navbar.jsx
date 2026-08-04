import { NavLink } from "react-router-dom";
import ThemeToggle from "./ThemeToggle.jsx";

const linkClass = ({ isActive }) =>
  `px-3 py-2 rounded-md text-sm font-medium transition-colors duration-150 ${
    isActive ? "bg-accent/20 text-accent" : "text-ink3 hover:text-ink"
  }`;

export default function Navbar() {
  return (
    <header className="border-b border-line bg-panel themed-transition">
      <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-lg font-bold tracking-tight whitespace-nowrap">
            CH-AdNova
          </span>
          <span className="text-xs text-ink3 hidden sm:inline truncate">
            AI-Powered Root Cause Investigation Platform
          </span>
        </div>
        <div className="flex items-center gap-3">
          <nav className="flex gap-1">
            <NavLink to="/" end className={linkClass}>Dashboard</NavLink>
            <NavLink to="/investigate" className={linkClass}>New Investigation</NavLink>
            <NavLink to="/history" className={linkClass}>History</NavLink>
            <NavLink to="/alerts" className={linkClass}>Alerts</NavLink>
          </nav>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
