/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./app.js",
    "./src/**/*.{js,ts,jsx,tsx,html}",
    "../ai-task-management-ui/**/*.{js,ts,jsx,tsx,html}"
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          200: '#bae0fd',
          300: '#7cc7fb',
          400: '#36abf6',
          500: '#0c8fe6',
          600: '#0270c4',
          700: '#03599f',
          800: '#074c83',
          900: '#0c406e',
          950: '#082849',
        },
        surface: {
          dark: '#0f172a',
          card: '#1e293b',
          border: '#334155'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'glow': '0 0 25px -5px rgba(12, 143, 230, 0.3)',
      }
    },
  },
  plugins: [],
}
