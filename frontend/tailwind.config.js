/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        wine: { DEFAULT: '#6b1f2a', dark: '#4a141d', light: '#8c3341' },
        gold: { DEFAULT: '#c19a5b', dark: '#a67e42' },
        cream: '#faf6f0',
        ink: '#2b2622',
      },
      fontFamily: {
        serif: ['Georgia', 'Cambria', 'Times New Roman', 'serif'],
        sans: ['ui-sans-serif', 'system-ui', 'Segoe UI', 'Helvetica', 'Arial', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
