/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: {
          50: '#fdfcf9',
          100: '#fbf9f5', // Main warm paper background
          200: '#f4efe6',
          300: '#e8e2d5', // Subtle warm border
        },
        forest: {
          DEFAULT: '#1e3a2f',
          dark: '#142820',
          muted: '#3b554b',
        },
        sage: {
          50: '#f2f6f4',
          100: '#e4ede7',
          200: '#cdddd3',
          300: '#a3c2b0',
          500: '#3f7259',
          600: '#2d5a47', // Primary calm action state
          700: '#234737',
          800: '#1b372b',
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        serif: ['Newsreader', 'Georgia', 'serif'],
      }
    },
  },
  plugins: [],
}
