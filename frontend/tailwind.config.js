/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#090C10",
        surface: "#101826",
        border: "rgba(255,255,255,0.12)",
        muted: "#8892A6",
        ink: "#F5F7FA",
        "signal-blue": "#7C9CFF",
        "signal-blue-hover": "#9DB4FF",
        "signal-amber": "#F5B759",
        success: "#4ADE80",
        danger: "#F87171",
      },
      fontFamily: {
        display: ["var(--font-display)", "ui-sans-serif", "sans-serif"],
        sans: ["var(--font-body)", "ui-sans-serif", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};