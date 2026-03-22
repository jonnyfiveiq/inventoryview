/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#0a0a0f",
        surface: { DEFAULT: "#111118", hover: "#1a1a24" },
        border: { DEFAULT: "#2a2a3a", light: "#3a3a4a" },
        text: { DEFAULT: "#e4e4ef", muted: "#8888a0", dim: "#55556a" },
        accent: { DEFAULT: "#6366f1", hover: "#818cf8" },
        vendor: {
          vmware: "#60a5fa",
          aws: "#f59e0b",
          azure: "#06b6d4",
          openshift: "#ef4444",
        },
        state: {
          on: "#22c55e",
          off: "#6b7280",
          maintenance: "#f59e0b",
          error: "#ef4444",
          connected: "#22c55e",
          disconnected: "#6b7280",
        },
      },
    },
  },
  plugins: [],
};
