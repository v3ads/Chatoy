import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#0e1116",
          elevated: "#171b22",
          border: "#262c36",
        },
        text: {
          primary: "#e8edf2",
          secondary: "#aab4c0",
          muted: "#6b7685",
        },
        accent: {
          DEFAULT: "#2ecc9b",
          soft: "#1c3a33",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
