/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Backed by CSS custom properties (index.css) so every existing
        // bg-panel2 / text-good / border-line usage automatically follows
        // the active theme with zero per-component changes. The
        // rgb(var(...) / <alpha-value>) form is what makes Tailwind's own
        // opacity modifiers (bg-accent/20 etc) keep working on top of a
        // CSS-variable color.
        bg: "rgb(var(--c-bg) / <alpha-value>)",
        panel: "rgb(var(--c-panel) / <alpha-value>)",
        panel2: "rgb(var(--c-panel2) / <alpha-value>)",
        surface: "rgb(var(--c-surface) / <alpha-value>)",
        line: "rgb(var(--c-line) / <alpha-value>)",
        ink: "rgb(var(--c-ink) / <alpha-value>)",
        ink2: "rgb(var(--c-ink2) / <alpha-value>)",
        ink3: "rgb(var(--c-ink3) / <alpha-value>)",
        accent: "rgb(var(--c-accent) / <alpha-value>)",
        good: "rgb(var(--c-good) / <alpha-value>)",
        bad: "rgb(var(--c-bad) / <alpha-value>)",
        warn: "rgb(var(--c-warn) / <alpha-value>)",
      },
      transitionDuration: {
        DEFAULT: "200ms",
      },
    },
  },
  plugins: [],
};
