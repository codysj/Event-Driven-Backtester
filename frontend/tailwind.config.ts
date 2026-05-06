import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        panel: "#111827",
        surface: "#0f172a",
        muted: "#94a3b8"
      }
    }
  },
  plugins: []
};

export default config;

