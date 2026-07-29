import Link from "next/link";

const pricingTiers = [
  { name: "Free", price: "$0", features: ["2 monitors", "Daily checks", "Email alerts"] },
  { name: "Developer", price: "$19/mo", features: ["20 monitors", "Hourly checks", "Slack alerts"], highlighted: true },
  { name: "Team", price: "$49/mo", features: ["Unlimited monitors", "15-min checks", "Webhooks"] },
];

export default function LandingPage() {
  return (
    <main>
      <nav className="flex items-center justify-between px-8 py-6 border-b border-border">
        <span className="font-semibold text-lg">ContractWatch</span>
        <div className="flex gap-4">
          <Link href="/login" className="text-sm text-muted hover:text-white">Log in</Link>
          <Link href="/signup" className="text-sm bg-white text-black px-4 py-2 rounded-md font-medium">
            Sign up free
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="px-8 py-24 text-center max-w-3xl mx-auto">
        <h1 className="text-4xl md:text-5xl font-semibold tracking-tight">
          Know when your API or MCP server breaks — before your users do.
        </h1>
        <p className="mt-6 text-lg text-muted">
          Contract monitoring for REST APIs and MCP servers. Get Slack alerts the moment
          a schema drifts.
        </p>
        <div className="mt-8 flex justify-center gap-4">
          <Link href="/signup" className="bg-white text-black px-6 py-3 rounded-md font-medium">
            Start monitoring free
          </Link>
        </div>
      </section>

      {/* Problem */}
      <section className="px-8 py-16 border-t border-border max-w-3xl mx-auto">
        <h2 className="text-2xl font-semibold mb-4">The problem</h2>
        {/* Apostrophe is intentional prose, not an HTML delimiter. */}
        {/* eslint-disable react/no-unescaped-entities */}
        <p className="text-muted">
          APIs and MCP servers silently change shape — a required parameter disappears,
          a field's type flips, a tool gets renamed — and every consumer downstream
          breaks without warning. CI tests only catch this before deploy. Nothing
          watches production, continuously, for you.
        </p>
        {/* eslint-enable react/no-unescaped-entities */}
      </section>

      {/* How it works */}
      <section className="px-8 py-16 border-t border-border max-w-3xl mx-auto">
        <h2 className="text-2xl font-semibold mb-6">How it works</h2>
        <ol className="space-y-4 text-muted">
          <li><span className="text-white font-medium">1. Connect —</span> point ContractWatch at your OpenAPI spec or MCP server.</li>
          <li><span className="text-white font-medium">2. Watch —</span> we check on your schedule and snapshot every contract.</li>
          <li><span className="text-white font-medium">3. Get alerted —</span> Slack, email, or webhook the moment something breaks.</li>
        </ol>
      </section>

      {/* Pricing */}
      <section id="pricing" className="px-8 py-16 border-t border-border max-w-4xl mx-auto">
        <h2 className="text-2xl font-semibold mb-8 text-center">Pricing</h2>
        <div className="grid md:grid-cols-3 gap-6">
          {pricingTiers.map((tier) => (
            <div
              key={tier.name}
              className={`rounded-xl border p-6 ${tier.highlighted ? "border-white" : "border-border"}`}
            >
              <h3 className="font-semibold">{tier.name}</h3>
              <p className="text-2xl font-semibold mt-2">{tier.price}</p>
              <ul className="mt-4 space-y-2 text-sm text-muted">
                {tier.features.map((f) => <li key={f}>• {f}</li>)}
              </ul>
            </div>
          ))}
        </div>
      </section>

      <footer className="px-8 py-10 border-t border-border text-center text-sm text-muted">
        ContractWatch — monitoring, not governance.
      </footer>
    </main>
  );
}
