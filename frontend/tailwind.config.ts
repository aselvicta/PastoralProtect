import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        savanna: {
          50: "#f6f7f4",
          100: "#e3e7dd",
          200: "#c8cfbc",
          300: "#a3af93",
          400: "#7f8c6c",
          500: "#637356",
          600: "#4e5b44",
          700: "#404839",
          800: "#363c31",
          900: "#2f332b",
        },
        dry: { DEFAULT: "#c45c3e", dark: "#8f3d28" },
        skyj: { DEFAULT: "#3a7ca5", light: "#81b1ce" },
      },
      fontFamily: {
        sans: ["var(--font-dm-sans)", "system-ui", "sans-serif"],
        display: ["var(--font-fraunces)", "Georgia", "serif"],
      },
    },
  },
  plugins: [],
};
export default config;
