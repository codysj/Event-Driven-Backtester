import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        lab: {
          bg: "#070A12",
          surface: "#0E1422",
          panel: "#111827",
          card: "#151B2D",
          border: "#253044",
          text: "#E6EDF7",
          secondary: "#98A2B3",
          muted: "#667085",
          blue: "#3B82F6",
          cyan: "#38BDF8",
          green: "#22C55E",
          red: "#EF4444",
          amber: "#F59E0B",
          grid: "#1F2937"
        },
        panel: "#111827",
        surface: "#0f172a",
        muted: "#94a3b8"
      }
    }
  },
  plugins: []
};

export default config;
