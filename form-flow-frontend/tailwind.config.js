/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        card: 'var(--card)',
        ring: 'var(--ring)',
        input: 'var(--input)',
        muted: 'var(--muted)',
        accent: 'var(--accent)',
        border: 'var(--border)',
        popover: 'var(--popover)',
        primary: 'var(--primary)',
        secondary: 'var(--secondary)',
        background: 'var(--background)',
        foreground: 'var(--foreground)',
        destructive: 'var(--destructive)',
        'card-foreground': 'var(--card-foreground)',
        'muted-foreground': 'var(--muted-foreground)',
        'accent-foreground': 'var(--accent-foreground)',
        'popover-foreground': 'var(--popover-foreground)',
        'primary-foreground': 'var(--primary-foreground)',
        'secondary-foreground': 'var(--secondary-foreground)',
        'destructive-foreground': 'var(--destructive-foreground)',
      },
      borderRadius: {
        DEFAULT: 'var(--radius)',
      },
      fontFamily: {
        sans: 'var(--font-sans)',
        serif: 'var(--font-serif)',
        mono: 'var(--font-mono)',
      },
    },
  },
  plugins: [],
}

