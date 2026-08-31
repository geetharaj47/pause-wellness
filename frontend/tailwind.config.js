/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        wellness: {
          50: '#f4f7f6',
          100: '#e3eae5',
          200: '#cbdad0',
          300: '#a4c0b0',
          400: '#79a28c',
          500: '#58846c',
          600: '#436954',
          700: '#365343',
          800: '#2b4337',
          900: '#24372e',
        }
      }
    },
  },
  plugins: [],
}
