"use client";
import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, type AlertChannelInput, type MonitorCreateInput, type User } from "@/lib/api";

const FREQUENCIES: Record<string, { value: MonitorCreateInput["frequency"]; label: string }[]> = {
  free: [{ value: "daily", label: "Daily" }],
  developer: [
    { value: "daily", label: "Daily" },
    { value: "hourly", label: "Hourly" },
  ],
  team: [
    { value: "daily", label: "Daily" },
    { value: "hourly", label: "Hourly" },
    { value: "every_15_min", label: "Every 15 minutes" },
  ],
};

export default function NewMonitorPage() {
  const [type, setType] = useState<"rest" | "mcp">("rest");
  const [name, setName] = useState("");
  const [apiUrl, setApiUrl] = useState("");
  const [specUrl, setSpecUrl] = useState("");
  const [mcpUrl, setMcpUrl] = useState("");
  const [transport, setTransport] = useState("http");
  const [frequency, setFrequency] = useState<MonitorCreateInput["frequency"]>("daily");
  const [slack, setSlack] = useState(false);
  const [slackWebhook, setSlackWebhook] = useState("");
  const [email, setEmail] = useState(false);
  const [emailAddr, setEmailAddr] = useState("");
  const [webhook, setWebhook] = useState(false);
  const [webhookUrl, setWebhookUrl] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();

  useEffect(() => {
    let cancelled = false;
    api.me()
      .then((data) => {
        if (!cancelled) setUser(data);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 401) router.push("/login");
        else setError(err instanceof ApiError ? err.message : "Failed to load account");
      });
    return () => {
      cancelled = true;
    };
  }, [router]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);

    const channels: AlertChannelInput[] = [];
    if (slack) channels.push({ type: "slack", configuration: { webhook_url: slackWebhook } });
    if (email) channels.push({ type: "email", configuration: { email: emailAddr } });
    if (webhook) channels.push({ type: "webhook", configuration: { url: webhookUrl } });

    const payload: MonitorCreateInput = { name, type, frequency, channels };
    if (type === "rest") {
      payload.api_url = apiUrl;
      payload.openapi_spec_url = specUrl;
    } else {
      payload.mcp_server_url = mcpUrl;
      payload.mcp_transport = transport;
    }

    try {
      const monitor = await api.createMonitor(payload);
      router.push(`/monitors/${monitor.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create monitor");
    } finally {
      setSubmitting(false);
    }
  }

  const inputClass = "w-full bg-white/5 border border-border rounded-xl px-3 py-2 mb-3 text-sm focus:border-signal-blue transition-colors";
  const frequencies = FREQUENCIES[user?.plan ?? "free"] ?? FREQUENCIES.free;

  return (
    <main className="max-w-lg mx-auto px-6 py-10">
      <h1 className="font-display text-2xl font-medium mb-6">New Monitor</h1>
      {error && <p className="text-danger text-sm mb-4">{error}</p>}

      <form onSubmit={handleSubmit} className="bg-white/5 backdrop-blur-md border border-border rounded-2xl p-6">
        <div className="flex gap-2 mb-4">
          <button type="button" onClick={() => setType("rest")}
            className={`flex-1 py-2 rounded-full text-sm border transition-colors ${type === "rest" ? "bg-ink text-bg border-transparent" : "border-border text-muted hover:text-ink"}`}>
            REST Monitor
          </button>
          <button type="button" onClick={() => setType("mcp")}
            className={`flex-1 py-2 rounded-full text-sm border transition-colors ${type === "mcp" ? "bg-ink text-bg border-transparent" : "border-border text-muted hover:text-ink"}`}>
            MCP Monitor
          </button>
        </div>

        <label className="text-sm text-muted">Name</label>
        <input className={inputClass} value={name} onChange={(e) => setName(e.target.value)} required
          placeholder="Stripe API" />

        {type === "rest" ? (
          <>
            <label className="text-sm text-muted">API URL</label>
            <input className={inputClass} value={apiUrl} onChange={(e) => setApiUrl(e.target.value)}
              placeholder="https://api.example.com" />
            <label className="text-sm text-muted">OpenAPI Spec URL</label>
            <input className={inputClass} value={specUrl} onChange={(e) => setSpecUrl(e.target.value)} required
              placeholder="https://api.example.com/openapi.json" />
          </>
        ) : (
          <>
            <label className="text-sm text-muted">MCP Server URL</label>
            <input className={inputClass} value={mcpUrl} onChange={(e) => setMcpUrl(e.target.value)} required
              placeholder="https://mcp.example.com" />
            <label className="text-sm text-muted">Transport</label>
            <select className={inputClass} value={transport} onChange={(e) => setTransport(e.target.value)}>
              <option value="http">HTTP</option>
              <option value="sse">SSE</option>
            </select>
          </>
        )}

        <label className="text-sm text-muted">Check Frequency</label>
        <select className={inputClass} value={frequency} onChange={(e) => setFrequency(e.target.value as MonitorCreateInput["frequency"])}>
          {frequencies.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>

        <p className="text-sm text-muted mt-4 mb-2">Alert channels</p>
        <label className="flex items-center gap-2 text-sm mb-1">
          <input type="checkbox" checked={slack} onChange={(e) => setSlack(e.target.checked)} /> Slack
        </label>
        {slack && (
          <input className={inputClass} placeholder="Slack webhook URL" value={slackWebhook}
            onChange={(e) => setSlackWebhook(e.target.value)} type="url" required />
        )}
        <label className="flex items-center gap-2 text-sm mb-1">
          <input type="checkbox" checked={email} onChange={(e) => setEmail(e.target.checked)} /> Email
        </label>
        {email && (
          <input className={inputClass} placeholder="you@example.com" value={emailAddr}
            onChange={(e) => setEmailAddr(e.target.value)} type="email" required />
        )}
        <label className="flex items-center gap-2 text-sm mb-1">
          <input type="checkbox" checked={webhook} onChange={(e) => setWebhook(e.target.checked)} /> Webhook
        </label>
        {webhook && (
          <input className={inputClass} placeholder="https://yourapp.com/webhook" value={webhookUrl}
            onChange={(e) => setWebhookUrl(e.target.value)} type="url" required />
        )}

        <button type="submit" disabled={submitting}
          className="w-full bg-ink text-bg rounded-full py-2 font-medium text-sm mt-4 disabled:opacity-50 hover:scale-[1.01] transition-transform">
          {submitting ? "Creating monitor…" : "Create Monitor"}
        </button>
      </form>
    </main>
  );
}