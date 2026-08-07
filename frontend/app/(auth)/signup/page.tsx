"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await api.signup(email, password); // sets httpOnly cookie server-side
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="relative flex items-center justify-center min-h-screen px-4 overflow-hidden">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 60% 50% at 30% 20%, rgba(124,156,255,0.10), transparent 60%), radial-gradient(ellipse 50% 40% at 80% 80%, rgba(245,183,89,0.06), transparent 65%)",
        }}
      />
      <form
        onSubmit={handleSubmit}
        className="relative w-full max-w-sm bg-white/5 backdrop-blur-xl border border-border rounded-2xl p-8"
      >
        <Link href="/" className="font-display text-sm font-medium tracking-tight text-muted hover:text-ink transition-colors">
          ContractWatch
        </Link>
        <h1 className="font-display text-xl font-medium mt-4 mb-6">Create your account</h1>
        {error && <p className="text-danger text-sm mb-4">{error}</p>}
        <input
          type="email" placeholder="Email" value={email} required
          onChange={(e) => setEmail(e.target.value)}
          className="w-full bg-white/5 border border-border rounded-xl px-3 py-2 mb-3 text-sm focus:border-signal-blue transition-colors"
        />
        <input
          type="password" placeholder="Password (min 8 chars)" value={password} required minLength={8}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full bg-white/5 border border-border rounded-xl px-3 py-2 mb-4 text-sm focus:border-signal-blue transition-colors"
        />
        <button
          type="submit" disabled={submitting}
          className="w-full bg-ink text-bg rounded-full py-2 font-medium text-sm disabled:opacity-50 hover:scale-[1.01] transition-transform"
        >
          {submitting ? "Creating account…" : "Sign up"}
        </button>
        <p className="text-sm text-muted mt-4 text-center">
          Already have an account? <Link href="/login" className="text-signal-blue hover:text-signal-blue-hover">Log in</Link>
        </p>
      </form>
    </main>
  );
}