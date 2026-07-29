"use client";
import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, ApiError, Monitor, Change } from "@/lib/api";

const SEVERITY_STYLES: Record<string, { label: string; color: string }> = {
  critical: { label: "BREAKING", color: "text-red-400 border-red-400/40" },
  warning: { label: "WARNING", color: "text-yellow-400 border-yellow-400/40" },
  info: { label: "SAFE", color: "text-green-400 border-green-400/40" },
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    month: "long", day: "numeric", hour: "numeric", minute: "2-digit",
  });
}

export default function MonitorDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);

  const [monitor, setMonitor] = useState<Monitor | null>(null);
  const [changes, setChanges] = useState<Change[]>([]);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const [m, c] = await Promise.all([api.getMonitor(id), api.getChanges(id)]);
      setMonitor(m);
      setChanges(c);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        router.push("/login");
        return;
      }
      setError(err instanceof ApiError ? err.message : "Failed to load monitor");
    }
  }, [id, router]);

  useEffect(() => {
    // The state updates occur after the external API requests resolve.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  function handleRetry() {
    setError("");
    void load();
  }

  async function handleCheckNow() {
    setError("");
    setChecking(true);
    try {
      await api.checkNow(id);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Check failed");
    } finally {
      setChecking(false);
    }
  }

  async function handleDelete() {
    if (!confirm("Delete this monitor?")) return;
    try {
      await api.deleteMonitor(id);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to delete monitor");
    }
  }

  if (!monitor) {
    return (
      <main className="max-w-3xl mx-auto px-6 py-10">
        {error ? (
          <div className="space-y-4">
            <p className="text-red-400">{error}</p>
            <button onClick={handleRetry} className="border border-border px-4 py-2 rounded-md text-sm">
              Retry
            </button>
          </div>
        ) : <p className="text-muted">Loading...</p>}
      </main>
    );
  }

  return (
    <main className="max-w-3xl mx-auto px-6 py-10">
      {error && <p role="alert" className="text-red-400 text-sm mb-4">{error}</p>}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold">{monitor.name}</h1>
          <p className="text-sm text-muted mt-1">
            {monitor.type.toUpperCase()} · {monitor.frequency} checks · status: {monitor.status}
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleCheckNow} disabled={checking}
            className="bg-white text-black px-4 py-2 rounded-md text-sm font-medium disabled:opacity-50">
            {checking ? "Checking..." : "Check now"}
          </button>
          <button onClick={handleDelete}
            className="border border-border px-4 py-2 rounded-md text-sm text-red-400">
            Delete
          </button>
        </div>
      </div>

      <h2 className="text-lg font-semibold mb-4">Change History</h2>
      {changes.length === 0 && <p className="text-muted">No changes detected yet.</p>}

      <div className="space-y-4">
        {changes.map((c) => {
          const style = SEVERITY_STYLES[c.severity] || SEVERITY_STYLES.info;
          const aiExplanation =
            typeof c.details?.ai_explanation === "string" ? c.details.ai_explanation : null;
          return (
            <div key={c.id} className={`border rounded-lg p-4 ${style.color}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold tracking-wide">{style.label}</span>
                <span className="text-xs text-muted">{formatDate(c.created_at)}</span>
              </div>
              <p className="text-white text-sm">{c.summary}</p>
              {aiExplanation && (
                <p className="text-sm text-muted mt-2 border-t border-white/10 pt-2">
                  {aiExplanation}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </main>
  );
}
