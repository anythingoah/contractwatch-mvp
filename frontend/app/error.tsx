"use client";

export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-bg text-ink grid place-items-center p-6">
        <main className="max-w-md text-center space-y-4">
          <h1 className="text-2xl font-semibold">Something went wrong</h1>
          <p className="text-muted">Please try again. If the problem persists, return to the dashboard.</p>
          <button onClick={reset} className="rounded-full bg-ink text-bg px-4 py-2 text-sm font-medium">
            Try again
          </button>
        </main>
      </body>
    </html>
  );
}
