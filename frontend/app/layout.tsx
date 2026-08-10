import "./globals.css";
import type { ReactNode } from "react";
import { Space_Grotesk, IBM_Plex_Sans, IBM_Plex_Mono } from "next/font/google";

const display = Space_Grotesk({ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--font-display" });
const body = IBM_Plex_Sans({ subsets: ["latin"], weight: ["400", "500"], variable: "--font-body" });
const mono = IBM_Plex_Mono({ subsets: ["latin"], weight: ["400", "500"], variable: "--font-mono" });

export const metadata = {
  title: "ContractWatch — API & MCP contract drift monitoring",
  description: "Know when your API or MCP server breaks before your users do.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`dark ${display.variable} ${body.variable} ${mono.variable}`}>
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
