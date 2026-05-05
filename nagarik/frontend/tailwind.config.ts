import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Editorial ink-on-paper palette.
        ink: { DEFAULT: "#181715", soft: "#3a3530", muted: "#6a6258" },
        paper: { DEFAULT: "#f6f1e6", deep: "#ece4d3", line: "#d8cfb8" },
        ashoka: { DEFAULT: "#1f3d80", deep: "#142a5c", soft: "#e6ecf6" },
        saffron: { DEFAULT: "#c2691a", soft: "#f6e9d6" },
        green: { DEFAULT: "#2d6a4f", soft: "#dcefe4" },
        amber: { DEFAULT: "#a07b1b", soft: "#f3ead0" },
      },
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        body: ["var(--font-body)", "system-ui", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "monospace"],
      },
      letterSpacing: {
        tightish: "-0.012em",
        wideish: "0.04em",
      },
      maxWidth: {
        column: "68ch",
      },
    },
  },
  plugins: [],
};

export default config;
