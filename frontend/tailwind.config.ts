import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#111827",
        paper: "#f8fafc",
        line: "#d9dee7",
        teal: "#0f766e",
        wine: "#9f1239",
        amber: "#b45309"
      }
    }
  },
  plugins: []
};

export default config;
