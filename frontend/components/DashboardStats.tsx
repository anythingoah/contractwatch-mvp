import type { Monitor } from "@/lib/api";

export default function DashboardStats({ monitors }: { monitors: Monitor[] }) {
  const healthy = monitors.filter((m) => m.status === "healthy").length;
  const breaking = monitors.filter((m) => m.status === "breaking_change").length;
  const total = monitors.length;

  return (
    <div className="grid grid-cols-3 gap-4 mb-10">
      <div className="bg-surface border border-border rounded-xl p-6">
        <p className="text-sm text-muted mb-2">Healthy</p>
        <p className="text-3xl font-semibold text-green-400">{healthy}</p>
      </div>
      <div className="bg-surface border border-border rounded-xl p-6">
        <p className="text-sm text-muted mb-2">Breaking</p>
        <p className="text-3xl font-semibold text-red-400">{breaking}</p>
      </div>
      <div className="bg-surface border border-border rounded-xl p-6">
        <p className="text-sm text-muted mb-2">Total monitors</p>
        <p className="text-3xl font-semibold">{total}</p>
      </div>
    </div>
  );
}
