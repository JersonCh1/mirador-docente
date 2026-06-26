/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F7F8FA",
        ink: "#1B2A4A",
        inkSoft: "#41506E",
        evidence: "#E8843D",
        good: "#5C8A6B",
        warn: "#C2724B",
        line: "#E2E5EB",
        white: "#FFFFFF",
      },
      fontFamily: {
        display: ["Fraunces", "serif"],
        body: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      borderRadius: {
        card: "14px",
        chip: "8px",
      },
    },
  },
  plugins: [],
};
