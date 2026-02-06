/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        surface: "#0a0b0f",
        card: "#1a1b23",
        "card-hover": "#22232d",
        accent: {
          green: "#00d4aa",
          red: "#ff4757",
          blue: "#3b82f6",
          yellow: "#fbbf24",
        },
      },
    },
  },
  plugins: [],
};
