import type { ReactNode } from "react";
import AppNav from "@/components/AppNav";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <AppNav />
      {children}
    </>
  );
}