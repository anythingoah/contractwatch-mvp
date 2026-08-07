"use client";
import { useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api, ApiError, SubscriptionInfo } from "@/lib/api";
import { buttonVariants } from "@/components/ui/Button";
import { CheckCircleIcon } from "@/components/ui/Icons";

type PlanId = "developer" | "team";

const PLANS: { id: PlanId; name: string; price: string; features: string[] }[] = [
  {
    id: "developer",
    name: "Developer",
    price: "$19/mo",
    features: ["Up to 10 monitors", "Hourly checks", "Slack + email alerts"],
  },
  {
    id: "team",
    name: "Team",
    price: "$49/mo",
    features: ["Unlimited monitors", "15-minute checks", "Slack + email + webhook alerts", "Priority support"],
  },
];

const STATUS_LABEL: Record<string, string> = {
  active: "Active",
  past_due: "Past due",
  canceled: "Canceled",
  failed: "Failed",
};

export default function BillingPage() {
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [pendingPlan, setPendingPlan] = useState<PlanId | null>(null);
  const [portalLoading, setPortalLoading] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  const checkoutSuccess = searchParams.get("checkout") === "success";

  const fetchSubscription = useCallback(() => {
    let cancelled = false;
    api
      .getSubscription()
      .then((data) => {
        if (!cancelled) setSubscription(data);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 401) {
          router.push("/login");
          return;
        }
        setError(err instanceof ApiError ? err.message : "Failed to load billing info");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [router]);

  useEffect(() => fetchSubscription(), [fetchSubscription]);

  async function handleUpgrade(plan: PlanId) {
    setError("");
    setPendingPlan(plan);
    try {
      const { checkout_url } = await api.createCheckout(plan);
      window.location.assign(checkout_url);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to start checkout");
      setPendingPlan(null);
    }
  }

  async function handleManageBilling() {
    setError("");
    setPortalLoading(true);
    try {
      const { portal_url } = await api.getBillingPortal();
      window.location.assign(portal_url);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to open billing portal");
      setPortalLoading(false);
    }
  }

  function retry() {
    setLoading(true);
    setError("");
    fetchSubscription();
  }

  const currentPlan = subscription?.plan ?? "free";
  const hasBillingAccount = subscription?.subscription_status != null;

  return (
    <main className="max-w-5xl mx-auto px-4 sm:px-6 py-10">
      <h1 className="text-2xl font-semibold mb-8">Billing</h1>

      {checkoutSuccess && (
        <div className="rounded-xl border border-success-border bg-success-bg p-4 mb-8 flex items-center gap-2 text-sm text-success">
          <CheckCircleIcon className="h-4 w-4 shrink-0" />
          Checkout complete — your plan will update shortly.
        </div>
      )}

      {loading && (
        <div aria-hidden="true" aria-busy="true" className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
          <div className="rounded-xl border border-border bg-surface p-6 h-40 animate-skeleton" />
          <div className="rounded-xl border border-border bg-surface p-6 h-40 animate-skeleton" />
        </div>
      )}

      {!loading && error && (
        <div role="alert" className="rounded-xl border border-danger-border bg-danger-bg p-6 text-center mb-8">
          <p className="text-danger text-sm mb-4">{error}</p>
          <button onClick={retry} className={buttonVariants({ variant: "outline", size: "sm" })}>
            Retry
          </button>
        </div>
      )}

      {!loading && !error && (
        <>
          <div className="rounded-xl border border-border bg-surface p-6 mb-8 flex items-center justify-between flex-wrap gap-4">
            <div>
              <p className="text-sm text-muted mb-1">Current plan</p>
              <p className="text-lg font-medium capitalize">{currentPlan}</p>
              {subscription?.subscription_status && (
                <span className="inline-flex items-center rounded-full border border-border bg-white/5 text-muted text-[11px] px-2 py-0.5 mt-2">
                  {STATUS_LABEL[subscription.subscription_status] ?? subscription.subscription_status}
                </span>
              )}
            </div>
            {hasBillingAccount && (
              <button
                onClick={handleManageBilling}
                disabled={portalLoading}
                className={buttonVariants({ variant: "outline", size: "sm" })}
              >
                {portalLoading ? "Opening…" : "Manage billing"}
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {PLANS.map((plan) => {
              const isCurrent = currentPlan === plan.id;
              return (
                <div key={plan.id} className="rounded-xl border border-border bg-surface p-6 flex flex-col">
                  <div className="flex items-baseline justify-between mb-1">
                    <h2 className="text-base font-medium">{plan.name}</h2>
                    <span className="text-sm text-muted">{plan.price}</span>
                  </div>
                  <ul className="text-sm text-muted space-y-1.5 my-4 flex-1">
                    {plan.features.map((feature) => (
                      <li key={feature} className="flex items-center gap-2">
                        <CheckCircleIcon className="h-3.5 w-3.5 text-success shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                  <button
                    onClick={() => handleUpgrade(plan.id)}
                    disabled={isCurrent || pendingPlan !== null}
                    className={buttonVariants({
                      variant: isCurrent ? "outline" : "primary",
                      size: "md",
                      className: "w-full",
                    })}
                  >
                    {isCurrent ? "Current plan" : pendingPlan === plan.id ? "Redirecting…" : "Upgrade"}
                  </button>
                </div>
              );
            })}
          </div>
        </>
      )}
    </main>
  );
}
