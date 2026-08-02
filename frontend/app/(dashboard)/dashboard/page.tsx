"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, ApiError, Monitor, RecentChange } from "@/lib/api";
import DashboardStats from "@/components/DashboardStats";
import ActivityFeed, { buildActivityFeed } from "@/components/ActivityFeed";
import MonitorsPanel from "@/components/MonitorsPanel";

export default function DashboardPage() {
  const [monitors, setMonitors] = useState<Monitor[]>([]);
  const [changes, setChanges] = useState<RecentChange[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const router = useRouter();

  useEffect(() => {
    let cancelled = false;
    Promise.all([api.listMonitors(), api.getRecentChanges()])
      .then(([monitorData, changeData]) => {
        if (!cancelled) {
          setMonitors(monitorData);
          setChanges(changeData);
        }
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 401) {
          router.push("/login");
          return;
        }
        setError(err instanceof ApiError ? err.message : "Failed to load dashboard");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [router]);

  async function handleLogout() {
    setError("");
    try {
      await api.logout();
      router.push("/login");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to log out");
    }
  }

  return (
    <main className="max-w-5xl mx-auto px-6 py-10">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <div className="flex gap-3">
          <Link href="/monitors/new" className="bg-white text-black px-4 py-2 rounded-md text-sm font-medium">
            + New Monitor
          </Link>
          <button onClick={handleLogout} className="text-sm text-muted hover:text-white">
            Log out
          </button>
        </div>
      </div>

      {loading && <p className="text-muted">Loading...</p>}
      {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

      {!loading && !error && monitors.length === 0 && (
        <div className="text-center py-20 border border-dashed border-border rounded-xl">
          <p className="text-muted mb-4">No monitors yet.</p>
          <Link href="/monitors/new" className="text-white underline">Add your first monitor</Link>
        </div>
      )}

      {!loading && !error && monitors.length > 0 && (
        <>
          <DashboardStats monitors={monitors} />

          <div className="grid grid-cols-3 gap-8">
            <div className="col-span-2">
              <h2 className="text-sm text-muted mb-4">Recent activity</h2>
              <ActivityFeed items={buildActivityFeed(monitors, changes)} />
            </div>
            <div>
              <h2 className="text-sm text-muted mb-4">Monitors</h2>
              <MonitorsPanel monitors={monitors} />
            </div>
          </div>
        </>
      )}
    </main>
  );
}