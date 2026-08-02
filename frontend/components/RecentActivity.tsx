import Link from "next/link";
import type { RecentChange } from "@/lib/api";

const SEVERITY_STYLES: Record<string, { label: string; color: string }> = {
  critical: { label: "Critical", color: "text-red-400" },
  warning: { label: "Warning", color: "text-yellow-400" },
  info: { label: "Info", color: "text-muted" },
};

function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} minute${mins === 1 ? "" : "s"} ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  return `${Math.floor(hours / 24)} day(s) ago`;
}

export default function RecentActivity({ changes }: { changes: RecentChange[] }) {
  if (changes.length === 0) {
    return (
      <div className="text-center py-10 border border-dashed border-border rounded-xl">
        <p className="text-muted text-sm">No changes detected yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {changes.map((change) => {
        const severity = SEVERITY_STYLES[change.severity] || SEVERITY_STYLES.info;
        return (
          <Link
            key={change.id}
            href={`/monitors/${change.monitor_id}`}
            className="block bg-surface border border-border rounded-xl p-4 hover:border-white/40 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-medium">{change.monitor_name}</span>
                <span className="text-xs uppercase tracking-wide text-muted border border-border rounded px-2 py-0.5">
                  {change.change_type}
                </span>
              </div>
              <span className={`text-sm font-medium ${severity.color}`}>{severity.label}</span>
            </div>
            <p className="mt-2 text-sm text-muted">{change.summary}</p>
            <p className="mt-2 text-xs text-muted">{timeAgo(change.created_at)}</p>
          </Link>
        );
      })}
    </div>
  );
}
