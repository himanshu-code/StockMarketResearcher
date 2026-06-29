/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        obsidian: '#0B0E14',
        surface: '#151921',
        'surface-high': '#272A31',
        'surface-mid': '#1D2026',
        border: '#2D343F',
        'text-primary': '#E1E2EB',
        'text-muted': '#BBCBB2',
        'accent-green': '#00C805',
        'accent-blue': '#3D8BFF',
        'accent-red': '#FF3B30',
      },
      fontFamily: {
        sans: ['Geist', 'Inter', 'ui-sans-serif', 'system-ui'],
        mono: ['Geist Mono', 'JetBrains Mono', 'ui-monospace'],
      },
      backgroundImage: {
        'glow-green': 'radial-gradient(ellipse at center, rgba(0,200,5,0.12) 0%, transparent 70%)',
      },
      boxShadow: {
        'glow-green': '0 0 20px rgba(0,200,5,0.2)',
        'glow-blue': '0 0 20px rgba(61,139,255,0.2)',
        card: '0 1px 3px rgba(0,0,0,0.4), 0 0 0 1px #2D343F',
      },
      keyframes: {
        pulse_dot: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.3' },
        },
      },
      animation: {
        'pulse-dot': 'pulse_dot 1.5s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
