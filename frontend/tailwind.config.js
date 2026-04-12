/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        wukong: {
          50: '#fef7ff',
          100: '#fde8ff',
          200: '#fad1ff',
          300: '#f5aaff',
          400: '#e075ff',
          500: '#c84dff',
          600: '#a628ea',
          700: '#8b1cd6',
          800: '#7019bc',
          900: '#5b14a0',
          950: '#3d0d6b',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace']
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-slow': 'bounce 2s infinite',
        'typing': 'typing 1.5s steps(3, end), blink .75s step-end infinite'
      }
    },
  },
  plugins: [
    require('tailwind-merge'),
  ],
}
