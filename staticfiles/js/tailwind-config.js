/**
 * Tailwind CSS theme config (used with CDN).
 * Must load after tailwindcss.com script.
 */
if (typeof tailwind !== 'undefined') {
  tailwind.config = {
    theme: {
      extend: {
        fontFamily: {
          sans: ['Roboto', 'sans-serif']
        },
        colors: {
          primary: { 50: '#eef2ff', 100: '#e0e7ff', 200: '#c7d2fe', 300: '#a5b4fc', 400: '#818cf8', 500: '#6366f1', 600: '#4f46e5', 700: '#4338ca', 800: '#3730a3', 900: '#312e81' },
          accent: { emerald: '#059669', amber: '#d97706', indigo: '#4f46e5' }
        }
      }
    },
    darkMode: 'class'
  };
}
