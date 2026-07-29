import Link from "next/link";
import type { Monitor } from "@/lib/api";

const STATUS_STYLES: Record<string, { label: string; color: string }> = {
  healthy: { label: "Healthy", color: "text-green-400" },
  breaking_change: { label: "Breaking Change Found", color: "text-red-400" },
  unreachable: { label: "Unreachable", color: "text-yellow-400" },
  pending: { label: "Pending first check", color: "text-muted" },
};

function timeAgo(iso: string | null): string {
  if (!iso) return "never";
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} minute${mins === 1 ? "" : "s"} ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  return `${Math.floor(hours / 24)} day(s) ago`;
}

export default function MonitorCard({ monitor }: { monitor: Monitor }) {
  const status = STATUS_STYLES[monitor.status] || STATUS_STYLES.pending;

  return (
    <Link
      href={`/monitors/${monitor.id}`}
      className="block bg-surface border border-border rounded-xl p-5 hover:border-white/40 transition-colors"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-medium">{monitor.name}</span>
          <span className="text-xs uppercase tracking-wide text-muted border border-border rounded px-2 py-0.5">
            {monitor.type}
          </span>
        </div>
        <span className={`text-sm font-medium ${status.color}`}>{status.label}</span>
      </div>
      <div className="mt-3 flex items-center justify-between text-sm text-muted">
        <span>Last checked: {timeAgo(monitor.last_checked)}</span>
        <span>Changes detected: {monitor.change_count}</span>
      </div>
    </Link>
  );
}
