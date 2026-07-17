/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#059669',
        success: '#16a34a',
        warning: '#ea580c',
        danger: '#dc2626',
      },
    },
  },
  plugins: [],
}
