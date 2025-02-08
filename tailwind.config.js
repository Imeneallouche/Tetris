/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        "gilroy-bold": ["Gilroy-Bold", "sans-serif"],
        "gilroy-medium": ["Gilroy-Medium", "sans-serif"],
        "gilroy-light": ["Gilroy-Light", "sans-serif"],
      },
    },
  },
  plugins: [],
};
