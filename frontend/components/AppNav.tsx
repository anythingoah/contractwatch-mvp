"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";

const LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/billing", label: "Billing" },
];

export default function AppNav() {
  const pathname = usePathname();
  const router = useRouter();

  async function handleLogout() {
    try {
      await api.logout();
    } catch {
      // logout errors are non-blocking — still send them to /login
    }
    router.push("/login");
  }

  return (
    <header className="sticky top-0 z-40 bg-bg/80 backdrop-blur-xl border-b border-white/10">
      <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link href="/dashboard" className="font-display text-sm font-medium tracking-tight">
          ContractWatch
        </Link>
        <nav className="flex items-center gap-6 text-sm text-muted">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              aria-current={pathname === l.href ? "page" : undefined}
              className={pathname === l.href ? "text-ink" : "hover:text-ink transition-colors"}
            >
              {l.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          <Link
            href="/monitors/new"
            className="rounded-full bg-ink text-bg px-4 py-1.5 text-xs font-medium hover:scale-[1.03] transition-transform"
          >
            + New monitor
          </Link>
          <button onClick={handleLogout} className="text-sm text-muted hover:text-ink transition-colors">
            Log out
          </button>
        </div>
      </div>
    </header>
  );
}