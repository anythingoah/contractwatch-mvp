import Link from "next/link";
import type { Monitor } from "@/lib/api";

const BADGE_STYLES: Record<string, { label: string; className: string }> = {
  healthy: { label: "healthy", className: "bg-green-500/15 text-green-400" },
  breaking_change: { label: "breaking", className: "bg-red-500/15 text-red-400" },
  unreachable: { label: "unreachable", className: "bg-yellow-500/15 text-yellow-400" },
  pending: { label: "pending", className: "bg-white/10 text-muted" },
};

function timeAgo(iso: string | null): string {
  if (!iso) return "never checked";
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function MonitorsPanel({ monitors }: { monitors: Monitor[] }) {
  if (monitors.length === 0) {
    return <p className="text-sm text-muted">No monitors yet.</p>;
  }

  return (
    <div className="space-y-3">
      {monitors.map((m) => {
        const badge = BADGE_STYLES[m.status] || BADGE_STYLES.pending;
        const isBreaking = m.status === "breaking_change";
        return (
          <Link
            key={m.id}
            href={`/monitors/${m.id}`}
            className={`block bg-surface border rounded-xl p-4 hover:border-white/40 transition-colors ${
              isBreaking ? "border-red-400/60" : "border-border"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-medium">{m.name}</span>
              <span className={`text-xs rounded-full px-2 py-0.5 ${badge.className}`}>{badge.label}</span>
            </div>
            <p className="text-xs text-muted mt-1">{timeAgo(m.last_checked)}</p>
          </Link>
        );
      })}
    </div>
  );
}
