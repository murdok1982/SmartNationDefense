import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SESIS-FEDERATION C4ISR",
  description: "Common Operating Picture — Plataforma Unificada de Gobierno Digital Militar",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className="dark">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-military-bg-primary text-military-text-primary antialiased">
        {children}
      </body>
    </html>
  );
}
