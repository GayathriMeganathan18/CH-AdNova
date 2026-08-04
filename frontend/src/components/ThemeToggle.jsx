import { Sun, Moon, Monitor } from "lucide-react";
import { useTheme } from "../theme/ThemeContext.jsx";

const OPTIONS = [
  { value: "light", icon: Sun, label: "Light theme" },
  { value: "dark", icon: Moon, label: "Dark theme" },
  { value: "system", icon: Monitor, label: "Match system theme" },
];

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <div role="radiogroup" aria-label="Theme" className="flex items-center gap-0.5 bg-surface border border-line rounded-lg p-0.5 themed-transition">
      {OPTIONS.map(({ value, icon: Icon, label }) => {
        const active = theme === value;
        return (
          <button
            key={value}
            type="button"
            role="radio"
            aria-checked={active}
            title={label}
            aria-label={label}
            onClick={() => setTheme(value)}
            className={`p-1.5 rounded-md transition-colors duration-150 ${
              active ? "bg-accent/20 text-accent" : "text-ink3 hover:text-ink hover:bg-ink/10"
            }`}
          >
            <Icon size={14} />
          </button>
        );
      })}
    </div>
  );
}
