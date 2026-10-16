/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        soc: {
          bg: "#0B1120",        // Deep Navy background
          card: "#131C31",      // Slate card surface
          cardHover: "#1A2642", // Hover card surface
          border: "#1E293B",    // Subtle border
          borderLight: "#334155",
          primary: "#3B82F6",   // Blue accent
          primaryHover: "#2563EB",
          cyan: "#06B6D4",      // Cyan cyber accent
          cyanHover: "#0891B2",
          emerald: "#10B981",   // Success / Normal
          amber: "#F59E0B",     // Warning / Caution
          rose: "#F43F5E",      // Danger / Anomaly
          text: "#F8FAFC",      // High contrast text
          muted: "#94A3B8",     // Subdued text
          subtle: "#64748B",    // Extra subdued
        }
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Menlo", "Monaco", "Consolas", "monospace"],
      }
    },
  },
  plugins: [],
}
