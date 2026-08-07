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

  return (
    <main className="max-w-5xl mx-auto px-6 py-10">
      <h1 className="text-2xl font-display font-medium mb-8">Dashboard</h1>

      {loading && <p className="text-muted">Loading…</p>}
      {error && <p className="text-danger text-sm mb-4">{error}</p>}

      {!loading && !error && monitors.length === 0 && (
        <div className="text-center py-20 border border-dashed border-border rounded-2xl bg-white/[0.02]">
          <p className="text-muted mb-4">No monitors yet.</p>
          <Link href="/monitors/new" className="text-signal-blue hover:text-signal-blue-hover underline">
            Add your first monitor
          </Link>
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