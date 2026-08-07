"use client";

import Link from "next/link";

export default function DashboardError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="max-w-3xl mx-auto px-6 py-16 text-center space-y-4">
      <h1 className="text-2xl font-semibold">This page could not be loaded</h1>
      <p className="text-muted">Your data is safe. Please try again.</p>
      <div className="flex justify-center gap-3">
        <button onClick={reset} className="rounded-full bg-ink text-bg px-4 py-2 text-sm font-medium">Try again</button>
        <Link href="/dashboard" className="rounded-full border border-border px-4 py-2 text-sm">Dashboard</Link>
      </div>
    </main>
  );
}
