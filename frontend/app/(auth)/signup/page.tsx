"use client";
import { useState } from "react";
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
    <main className="flex items-center justify-center min-h-screen px-4">
      <form onSubmit={handleSubmit} className="w-full max-w-sm bg-surface border border-border rounded-xl p-8">
        <h1 className="text-xl font-semibold mb-6">Create your account</h1>
        {error && <p className="text-red-400 text-sm mb-4">{error}</p>}
        <input
          type="email" placeholder="Email" value={email} required
          onChange={(e) => setEmail(e.target.value)}
          className="w-full bg-bg border border-border rounded-md px-3 py-2 mb-3 text-sm"
        />
        <input
          type="password" placeholder="Password (min 8 chars)" value={password} required minLength={8}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full bg-bg border border-border rounded-md px-3 py-2 mb-4 text-sm"
        />
        <button type="submit" disabled={submitting}
          className="w-full bg-white text-black rounded-md py-2 font-medium text-sm disabled:opacity-50">
          {submitting ? "Creating account..." : "Sign up"}
        </button>
        <p className="text-sm text-muted mt-4 text-center">
          Already have an account? <a href="/login" className="text-white">Log in</a>
        </p>
      </form>
    </main>
  );
}
