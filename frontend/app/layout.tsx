import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "ContractWatch — API & MCP contract drift monitoring",
  description: "Know when your API or MCP server breaks before your users do.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-bg text-white antialiased">{children}</body>
    </html>
  );
}
