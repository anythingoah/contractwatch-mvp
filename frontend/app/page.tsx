"use client";
import { useRef, useState } from "react";
import Link from "next/link";

function ArrowIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M5 12h14" /><path d="m12 5 7 7-7 7" />
    </svg>
  );
}

const FEATURES = [
  { title: "REST & MCP, one tool", body: "Point it at an OpenAPI spec or an MCP server. Same diff engine, same alerts." },
  { title: "Real diffs, not status codes", body: "See the exact field, type, or tool signature that changed \u2014 not just \u201csomething broke.\u201d" },
  { title: "Alerts where you work", body: "Slack, email, or a webhook into your own system. No dashboard you have to remember to check." },
  { title: "Free to start", body: "2 monitors, daily checks, email alerts \u2014 no credit card required. Upgrade when you outgrow it." },
];

const CAPABILITIES = [
  { label: "Breaking, warning, or info", note: "Every change classified automatically, not just flagged." },
  { label: "Runs on your schedule", note: "Daily up to every 15 minutes, depending on plan." },
  { label: "One failure won\u2019t block another", note: "Every monitor checks independently." },
];

const PRICING = [
  { name: "Free", price: "$0", features: ["2 monitors", "Daily checks", "Email alerts"] },
  { name: "Developer", price: "$19/mo", features: ["10 monitors", "Hourly checks", "Slack + email alerts"], highlighted: true },
  { name: "Team", price: "$49/mo", features: ["Unlimited monitors", "15-min checks", "Slack + email + webhook alerts"] },
];

export default function LandingPage() {
  const stackRef = useRef<HTMLDivElement>(null);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });

  function handleMouseMove(e: React.MouseEvent<HTMLDivElement>) {
    const el = stackRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width - 0.5;
    const py = (e.clientY - rect.top) / rect.height - 0.5;
    setTilt({ x: py * -8, y: px * 10 });
  }
  function resetTilt() {
    setTilt({ x: 0, y: 0 });
  }

  return (
    <div className="cw-root">
      <style>{`
        .cw-root {
          --bg-deep: #090C10; --bg-mesh: #101826;
          --ink: #F5F7FA; --muted: #8892A6;
          --signal-blue: #7C9CFF; --signal-blue-hover: #9DB4FF; --signal-amber: #F5B759;
          --success: #4ADE80; --danger: #F87171;
          --glass-fill: rgba(255,255,255,0.05); --glass-border: rgba(255,255,255,0.12);
          background: var(--bg-deep); color: var(--ink); font-family: var(--font-body);
          min-height: 100vh;
        }
        .cw-root * { box-sizing: border-box; }
        .cw-root a { text-decoration: none; color: inherit; }
        .cw-root :focus { outline: none; }
        .cw-root :focus-visible { box-shadow: 0 0 0 2px var(--bg-deep), 0 0 0 4px var(--signal-blue); border-radius: 6px; }

        .cw-header { position: sticky; top: 0; z-index: 40; background: rgba(9,12,16,0.78); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255,255,255,0.08); }
        .cw-header-inner { max-width: 72rem; margin: 0 auto; padding: 1rem 1.5rem; display: flex; align-items: center; justify-content: space-between; }
        .cw-logo { font-family: var(--font-display); font-size: 15px; font-weight: 500; letter-spacing: -0.01em; }
        .cw-nav { display: none; align-items: center; gap: 2rem; font-size: 14px; color: var(--muted); }
        .cw-nav a:hover { color: var(--ink); }
        @media (min-width: 640px) { .cw-nav { display: flex; } }
        .cw-nav-right { display: flex; align-items: center; gap: 1rem; }
        .cw-login-link { font-size: 14px; color: var(--muted); }
        .cw-login-link:hover { color: var(--ink); }
        .cw-btn-primary { border-radius: 999px; background: var(--ink); color: var(--bg-deep); padding: 6px 16px; font-size: 12px; font-weight: 500; transition: transform 0.15s; display: inline-block; }
        .cw-btn-primary:hover { transform: scale(1.03); }
        .cw-btn-primary.lg { padding: 12px 24px; font-size: 14px; }

        .cw-hero { position: relative; overflow: hidden; padding: 5rem 1.5rem 7rem; }
        .cw-hero-bg { position: absolute; inset: 0; pointer-events: none;
          background: radial-gradient(ellipse 70% 55% at 20% 10%, rgba(124,156,255,0.10), transparent 60%),
                      radial-gradient(ellipse 60% 45% at 85% 25%, rgba(245,183,89,0.08), transparent 65%), var(--bg-deep); }
        .cw-hero-inner { position: relative; max-width: 72rem; margin: 0 auto; display: grid; grid-template-columns: 1fr; align-items: center; gap: 4rem; }
        @media (min-width: 1024px) { .cw-hero-inner { grid-template-columns: 1fr 0.95fr; } }

        .cw-badge { display: inline-flex; align-items: center; gap: 8px; border-radius: 999px; border: 1px solid var(--glass-border); background: var(--glass-fill); padding: 6px 14px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.16em; color: var(--muted); font-family: var(--font-mono); }
        .cw-h1 { margin-top: 1.5rem; font-family: var(--font-display); font-size: 2.6rem; font-weight: 500; line-height: 1.08; letter-spacing: -0.02em; }
        @media (min-width: 640px) { .cw-h1 { font-size: 3.75rem; } }
        .cw-h1 .muted { color: var(--muted); }
        .cw-p { margin-top: 1.5rem; max-width: 28rem; font-size: 15px; line-height: 1.7; color: var(--muted); }

        .cw-cta-row { margin-top: 2rem; display: flex; flex-wrap: wrap; align-items: center; gap: 16px; }
        .cw-login-cta { display: inline-flex; align-items: center; gap: 6px; font-size: 14px; color: var(--signal-blue); }
        .cw-login-cta:hover { color: var(--signal-blue-hover); }

        .cw-stack { position: relative; margin: 0 auto; height: 380px; width: 100%; max-width: 28rem; perspective: 1400px; }
        .cw-card { position: absolute; border-radius: 16px; padding: 20px; transition: transform 0.3s ease-out; }
        .cw-card-back { inset-inline: 24px; top: 16px; border: 1px solid rgba(255,255,255,0.08); background: rgba(124,156,255,0.05); backdrop-filter: blur(10px); box-shadow: 0 20px 40px -20px rgba(0,0,0,0.6); }
        .cw-card-mid { inset-inline: 12px; top: 36px; border: 1px solid rgba(255,255,255,0.10); background: rgba(124,156,255,0.06); backdrop-filter: blur(16px); box-shadow: 0 24px 48px -20px rgba(0,0,0,0.65); }
        .cw-card-front { inset-inline: 0; top: 64px; padding: 24px; border: 1px solid rgba(248,113,113,0.35); background: rgba(248,113,113,0.08); backdrop-filter: blur(20px); box-shadow: 0 30px 60px -16px rgba(0,0,0,0.75), 0 0 0 1px rgba(248,113,113,0.12); }
        .cw-snap-header { display: flex; align-items: center; justify-content: space-between; }
        .cw-snap-date { font-size: 12px; color: var(--muted); font-family: var(--font-mono); }
        .cw-snap-ok { border-radius: 999px; background: rgba(74,222,128,0.14); color: var(--success); padding: 2px 8px; font-size: 10px; font-weight: 500; }
        .cw-snap-bad { border-radius: 999px; background: rgba(248,113,113,0.16); color: var(--danger); padding: 2px 10px; font-size: 11px; font-weight: 500; }
        .cw-diff-row { margin-top: 6px; border-radius: 6px; padding: 4px 8px; font-family: var(--font-mono); font-size: 13px; }
        .cw-diff-remove { background: rgba(248,113,113,0.14); color: var(--danger); }
        .cw-diff-add { background: rgba(74,222,128,0.10); color: var(--success); margin-top: 6px; }
        .cw-card-note { margin-top: 12px; font-size: 12px; line-height: 1.6; color: var(--muted); }

        .cw-caps { padding: 3rem 1.5rem; border-top: 1px solid rgba(255,255,255,0.08); border-bottom: 1px solid rgba(255,255,255,0.08); }
        .cw-caps-inner { max-width: 72rem; margin: 0 auto; display: grid; grid-template-columns: 1fr; gap: 2rem; }
        @media (min-width: 768px) { .cw-caps-inner { grid-template-columns: repeat(3, 1fr); } }
        .cw-cap-label { font-family: var(--font-display); font-size: 17px; font-weight: 500; }
        .cw-cap-note { margin-top: 6px; font-size: 13px; color: var(--muted); line-height: 1.6; }

        .cw-h2 { font-family: var(--font-display); font-size: 2rem; font-weight: 500; letter-spacing: -0.01em; text-align: center; }

        .cw-features { max-width: 72rem; margin: 0 auto; padding: 6rem 1.5rem; }
        .cw-feature-grid { margin-top: 3rem; display: grid; grid-template-columns: 1fr; gap: 1rem; }
        @media (min-width: 768px) { .cw-feature-grid { grid-template-columns: repeat(2, 1fr); } }
        .cw-feature-card { border-radius: 16px; border: 1px solid var(--glass-border); background: var(--glass-fill); backdrop-filter: blur(10px); padding: 1.75rem; }
        .cw-feature-card h3 { font-family: var(--font-display); font-size: 16px; font-weight: 500; }
        .cw-feature-card p { margin-top: 8px; font-size: 14px; line-height: 1.6; color: var(--muted); }

        .cw-pricing { max-width: 72rem; margin: 0 auto; padding: 0 1.5rem 6rem; }
        .cw-pricing-grid { margin-top: 3rem; display: grid; grid-template-columns: 1fr; gap: 1rem; }
        @media (min-width: 768px) { .cw-pricing-grid { grid-template-columns: repeat(3, 1fr); } }
        .cw-price-card { border-radius: 16px; border: 1px solid var(--glass-border); background: var(--glass-fill); backdrop-filter: blur(10px); padding: 1.75rem; display: flex; flex-direction: column; }
        .cw-price-card.highlighted { border-color: rgba(124,156,255,0.45); background: rgba(124,156,255,0.06); }
        .cw-price-card h3 { font-family: var(--font-display); font-size: 15px; font-weight: 500; color: var(--muted); }
        .cw-price-value { margin-top: 8px; font-family: var(--font-display); font-size: 28px; font-weight: 500; }
        .cw-price-list { margin-top: 16px; font-size: 13px; color: var(--muted); line-height: 2; flex: 1; }
        .cw-price-cta { margin-top: 20px; text-align: center; border-radius: 999px; border: 1px solid var(--glass-border); padding: 10px; font-size: 13px; transition: background 0.15s; }
        .cw-price-cta:hover { background: rgba(255,255,255,0.06); }
        .cw-price-card.highlighted .cw-price-cta { background: var(--ink); color: var(--bg-deep); border: none; }

        .cw-footer { max-width: 40rem; margin: 0 auto; padding: 3rem 1.5rem 7rem; text-align: center; }
        .cw-footer-row { margin-top: 2rem; display: flex; flex-wrap: wrap; justify-content: center; align-items: center; gap: 12px; }
        .cw-footer-note { margin-top: 2.5rem; font-size: 12px; color: var(--muted); }

        @media (prefers-reduced-motion: reduce) {
          .cw-card { transition: none !important; }
        }
      `}</style>

      {/* ================= NAV ================= */}
      <header className="cw-header">
        <div className="cw-header-inner">
          <span className="cw-logo">ContractWatch</span>
          <nav className="cw-nav">
            <a href="#features">Features</a>
            <a href="#pricing">Pricing</a>
          </nav>
          <div className="cw-nav-right">
            <Link href="/login" className="cw-login-link">Log in</Link>
            <Link href="/signup" className="cw-btn-primary">Start free</Link>
          </div>
        </div>
      </header>

      {/* ================= HERO ================= */}
      <section className="cw-hero">
        <div className="cw-hero-bg" aria-hidden="true" />
        <div className="cw-hero-inner">
          <div>
            <span className="cw-badge">REST &amp; MCP · contract monitoring</span>

            <h1 className="cw-h1">
              Your API changed.
              <br />
              <span className="muted">Nobody told you.</span>
            </h1>

            <p className="cw-p">
              ContractWatch snapshots your REST or MCP contracts on a schedule
              and diffs them against yesterday. When something breaking
              slips in, you hear about it in Slack — before your users file
              the ticket.
            </p>

            <div className="cw-cta-row">
              <Link href="/signup" className="cw-btn-primary lg">Start monitoring free</Link>
              <Link href="/login" className="cw-login-cta">Log in <ArrowIcon /></Link>
            </div>
          </div>

          {/* ---- Right: 3D glass snapshot stack (signature element) ---- */}
          <div
            ref={stackRef}
            onMouseMove={handleMouseMove}
            onMouseLeave={resetTilt}
            className="cw-stack"
          >
            <div
              className="cw-card cw-card-back"
              style={{ transform: `translateZ(-90px) translateY(10px) scale(0.92) rotateX(${8 + tilt.x * 0.4}deg) rotateY(${tilt.y * 0.4}deg)` }}
            >
              <div className="cw-snap-header">
                <span className="cw-snap-date">Aug 4</span>
                <span className="cw-snap-ok">No changes</span>
              </div>
            </div>

            <div
              className="cw-card cw-card-mid"
              style={{ transform: `translateZ(-30px) translateY(6px) scale(0.965) rotateX(${5 + tilt.x * 0.7}deg) rotateY(${tilt.y * 0.7}deg)` }}
            >
              <div className="cw-snap-header">
                <span className="cw-snap-date">Aug 5</span>
                <span className="cw-snap-ok">No changes</span>
              </div>
            </div>

            <div
              className="cw-card cw-card-front"
              style={{ transform: `translateZ(40px) rotateX(${2 + tilt.x}deg) rotateY(${tilt.y}deg)` }}
            >
              <div className="cw-snap-header">
                <span className="cw-snap-date">Aug 6 · POST /v1/charges</span>
                <span className="cw-snap-bad">Breaking change</span>
              </div>
              <div className="cw-diff-row cw-diff-remove">− &quot;customer_id&quot;: string (required)</div>
              <div className="cw-diff-row cw-diff-add">+ &quot;payment_method&quot;: string (required)</div>
              <p className="cw-card-note">
                Any client still sending <code>customer_id</code> alone will start receiving 400s.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ================= CAPABILITIES STRIP ================= */}
      <section className="cw-caps">
        <div className="cw-caps-inner">
          {CAPABILITIES.map((c) => (
            <div key={c.label}>
              <div className="cw-cap-label">{c.label}</div>
              <div className="cw-cap-note">{c.note}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ================= FEATURES (bento) ================= */}
      <section id="features" className="cw-features">
        <h2 className="cw-h2">Built for the moment things drift</h2>
        <div className="cw-feature-grid">
          {FEATURES.map((f) => (
            <div key={f.title} className="cw-feature-card">
              <h3>{f.title}</h3>
              <p>{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ================= PRICING ================= */}
      <section id="pricing" className="cw-pricing">
        <h2 className="cw-h2">Pricing</h2>
        <div className="cw-pricing-grid">
          {PRICING.map((tier) => (
            <div key={tier.name} className={`cw-price-card ${tier.highlighted ? "highlighted" : ""}`}>
              <h3>{tier.name}</h3>
              <div className="cw-price-value">{tier.price}</div>
              <ul className="cw-price-list">
                {tier.features.map((f) => <li key={f}>{f}</li>)}
              </ul>
              <Link href="/signup" className="cw-price-cta">Get started</Link>
            </div>
          ))}
        </div>
      </section>

      {/* ================= FOOTER CTA ================= */}
      <section className="cw-footer">
        <h2 className="cw-h2">Stop finding out from your users.</h2>
        <div className="cw-footer-row">
          <Link href="/signup" className="cw-btn-primary lg">Get started free</Link>
        </div>
        <p className="cw-footer-note">No credit card required for the free tier.</p>
      </section>
    </div>
  );
}
