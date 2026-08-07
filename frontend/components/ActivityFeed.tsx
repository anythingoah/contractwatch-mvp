import Link from "next/link";
import type { Monitor, RecentChange } from "@/lib/api";

interface ActivityItem {
  id: string;
  monitor_id: number;
  monitor_name: string;
  kind: "change" | "baseline";
  title: string;
  description: string;
  created_at: string;
  isBreaking: boolean;
}

function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

// Builds the merged, time-sorted feed. Baseline rows are a frontend
// approximation — see note in chat: the backend doesn't persist a distinct
// baseline event, so this infers one from change_count === 0 + last_checked.
export function buildActivityFeed(monitors: Monitor[], changes: RecentChange[]): ActivityItem[] {
  const changeItems: ActivityItem[] = changes.map((c) => ({
    id: `change-${c.id}`,
    monitor_id: c.monitor_id,
    monitor_name: c.monitor_name,
    kind: "change",
    title: `${c.monitor_name} — ${c.severity === "critical" ? "breaking change" : c.change_type.replace(/_/g, " ")}`,
    description: c.summary,
    created_at: c.created_at,
    isBreaking: c.severity === "critical",
  }));

  // snapshot_count === 1 means "checked exactly once, nothing to compare
  // yet" — true right after the first check, and false forever after
  // (the second check pushes it to 2 whether or not it found drift). That's
  // what makes this stay accurate instead of re-labeling every routine
  // no-op recheck as a fresh "baseline created" event.
  const baselineItems: ActivityItem[] = monitors
    .filter((m) => m.snapshot_count === 1 && m.change_count === 0 && m.last_checked)
    .map((m) => ({
      id: `baseline-${m.id}`,
      monitor_id: m.id,
      monitor_name: m.name,
      kind: "baseline",
      title: `${m.name} — baseline created`,
      description: "First check, no prior snapshot to compare",
      created_at: m.last_checked as string,
      isBreaking: false,
    }));

  return [...changeItems, ...baselineItems].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );
}

export default function ActivityFeed({ items }: { items: ActivityItem[] }) {
  if (items.length === 0) {
    return (
      <div className="text-center py-10 border border-dashed border-border rounded-2xl bg-white/[0.02]">
        <p className="text-muted text-sm">No activity yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {items.map((item) => (
        <Link
          key={item.id}
          href={`/monitors/${item.monitor_id}`}
          className={`block border-l-2 pl-3 ${item.isBreaking ? "border-danger" : "border-border"}`}
        >
          <div className="flex items-center justify-between">
            <span className={`text-sm font-medium ${item.isBreaking ? "text-danger" : ""}`}>
              {item.title}
            </span>
            <span className="text-xs text-muted whitespace-nowrap ml-4">{timeAgo(item.created_at)}</span>
          </div>
          <p className="text-sm text-muted mt-1">{item.description}</p>
        </Link>
      ))}
    </div>
  );
}
