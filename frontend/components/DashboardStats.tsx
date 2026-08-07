import type { Monitor } from "@/lib/api";

export default function DashboardStats({ monitors }: { monitors: Monitor[] }) {
  const healthy = monitors.filter((m) => m.status === "healthy").length;
  const breaking = monitors.filter((m) => m.status === "breaking_change").length;
  const total = monitors.length;

  return (
    <div className="grid grid-cols-3 gap-4 mb-10">
      <div className="bg-white/5 backdrop-blur-md border border-border rounded-2xl p-6">
        <p className="text-sm text-muted mb-2">Healthy</p>
        <p className="text-3xl font-display font-medium text-success">{healthy}</p>
      </div>
      <div className="bg-white/5 backdrop-blur-md border border-border rounded-2xl p-6">
        <p className="text-sm text-muted mb-2">Breaking</p>
        <p className="text-3xl font-display font-medium text-danger">{breaking}</p>
      </div>
      <div className="bg-white/5 backdrop-blur-md border border-border rounded-2xl p-6">
        <p className="text-sm text-muted mb-2">Total monitors</p>
        <p className="text-3xl font-display font-medium">{total}</p>
      </div>
    </div>
  );
}