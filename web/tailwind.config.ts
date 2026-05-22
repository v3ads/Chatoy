import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#0C0B1A", // Deep Navy
          elevated: "#13112A",
          card: "#1A1738",
          border: "#27244A",
        },
        text: {
          primary: "#FBFBFD",
          secondary: "#A8A6BC",
          muted: "#6E6C88",
        },
        accent: {
          DEFAULT: "#F5B042", // Amber
          dim: "#C48A1E",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        serif: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"], // Reverting to sans for the clean look
      },
    },
  },
  plugins: [],
};

export default config;
