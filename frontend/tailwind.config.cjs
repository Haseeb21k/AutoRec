/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'primary': {
          '50': '#eef2f6',
          '100': '#b3daff',
          '200': '#80c2ff',
          '300': '#4da9ff',
          '400': '#1a91ff',
          '500': '#0077e6',
          '600': '#005db3',
          '700': '#004280',
          '800': '#00284d',
          '900': '#000d19',
        },
      },
    },
  },
  plugins: [],
}