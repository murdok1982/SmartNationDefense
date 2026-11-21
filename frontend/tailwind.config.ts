import type { Config } from "tailwindcss";

/**
 * Design System — SESIS Command Center
 *
 * Paleta: navy profundo + grafito, acento cian, señales semánticas.
 * La escala `gray` se remapea a la paleta navy para que los componentes
 * heredados (paneles operativos) mantengan contraste y coherencia visual.
 */
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#060a12",
        foreground: "#e8eefc",
        ink: {
          DEFAULT: "#e8eefc",
          muted: "#93a4c2",
          // 5.4:1 sobre `surface` y 4.7:1 sobre `overlay` (WCAG AA para texto normal).
          faint: "#778bab",
        },
        surface: {
          DEFAULT: "#0b1220",
          raised: "#101a2c",
          overlay: "#152136",
          sunken: "#070d18",
        },
        stroke: {
          DEFAULT: "#1c2942",
          strong: "#263854",
        },
        accent: {
          DEFAULT: "#22d3ee",
          soft: "#0e7490",
          deep: "#0891b2",
        },
        signal: {
          success: "#34d399",
          warning: "#fbbf24",
          danger: "#f87171",
          info: "#60a5fa",
        },
        gray: {
          50: "#f4f7fd",
          100: "#e6ecf8",
          200: "#cbd7ea",
          300: "#a3b4d0",
          400: "#7f93b4",
          500: "#5f7496",
          600: "#465a79",
          700: "#263854",
          800: "#16223a",
          900: "#0d1526",
          950: "#070c16",
        },
        military: {
          bg: {
            primary: "#060a12",
            secondary: "#0b1220",
            tertiary: "#152136",
          },
          border: "#1c2942",
          text: {
            primary: "#e8eefc",
            secondary: "#93a4c2",
          },
          green: "#34d399",
          yellow: "#fbbf24",
          red: "#f87171",
          blue: "#60a5fa",
          magenta: "#a78bfa",
          cyan: "#22d3ee",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "SFMono-Regular", "monospace"],
        sans: ["Inter", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
      },
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "0.875rem", letterSpacing: "0.04em" }],
        "3xs": ["0.5625rem", { lineHeight: "0.75rem", letterSpacing: "0.06em" }],
      },
      borderRadius: {
        xl: "0.875rem",
        "2xl": "1.125rem",
      },
      boxShadow: {
        panel:
          "inset 0 1px 0 rgba(255,255,255,0.035), 0 20px 44px -28px rgba(0,0,0,0.95)",
        glow: "0 0 0 1px rgba(34,211,238,0.22), 0 0 34px -10px rgba(34,211,238,0.5)",
        "glow-soft": "0 0 26px -12px rgba(34,211,238,0.55)",
      },
      backgroundImage: {
        "app-radial":
          "radial-gradient(1100px 620px at 78% -12%, rgba(34,211,238,0.10), transparent 62%), radial-gradient(900px 520px at 8% 108%, rgba(59,130,246,0.10), transparent 60%)",
        "app-grid":
          "linear-gradient(rgba(148,180,220,0.055) 1px, transparent 1px), linear-gradient(90deg, rgba(148,180,220,0.055) 1px, transparent 1px)",
        "accent-line":
          "linear-gradient(90deg, transparent, rgba(34,211,238,0.65), transparent)",
      },
      backgroundSize: {
        grid: "44px 44px",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideIn: {
          "0%": { transform: "translateY(-6px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-400px 0" },
          "100%": { backgroundPosition: "400px 0" },
        },
        sweep: {
          "0%": { transform: "translateX(-120%)" },
          "100%": { transform: "translateX(320%)" },
        },
        "pulse-ring": {
          "0%": { boxShadow: "0 0 0 0 rgba(34,211,238,0.45)" },
          "70%": { boxShadow: "0 0 0 8px rgba(34,211,238,0)" },
          "100%": { boxShadow: "0 0 0 0 rgba(34,211,238,0)" },
        },
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-in": "slideIn 0.22s ease-out",
        shimmer: "shimmer 1.8s linear infinite",
        sweep: "sweep 2.6s ease-in-out infinite",
        "pulse-ring": "pulse-ring 2.4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [],
};

export default config;
