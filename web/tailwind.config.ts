import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#0C0B1A", // --bg
          elevated: "#13112A", // --bg2
          card: "#1A1738", // --card
          border: "#27244A", // --border
        },
        text: {
          primary: "#FBFBFD", // --ink
          secondary: "#A8A6BC", // --body
          muted: "#6E6C88", // --muted
        },
        accent: {
          DEFAULT: "#F5B042", // --amber
          dim: "#C48A1E", // --amber-dim
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        serif: ["Georgia", "Times New Roman", "serif"],
      },
    },
  },
  plugins: [],
};

export default config;
