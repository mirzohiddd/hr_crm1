/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#EFF6FF',
          100: '#DBEAFE',
          200: '#BFDBFE',
          300: '#93C5FD',
          400: '#60A5FA',
          500: '#3B82F6',
          600: '#2563EB',
          700: '#1D4ED8',
          800: '#1E40AF',
          900: '#1E3A8A',
        },
        canvas: '#F8FAFC',
        ink: '#0F172A',
        muted: '#64748B',
        line: '#E2E8F0',
        navy: '#0F172A',
      },
      fontFamily: {
        sans: ['Onest', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'Arial', 'sans-serif'],
      },
      boxShadow: {
        pop: '0 12px 32px -12px rgba(15, 23, 42, 0.18), 0 2px 6px -2px rgba(15, 23, 42, 0.06)',
      },
    },
  },
  plugins: [],
}
