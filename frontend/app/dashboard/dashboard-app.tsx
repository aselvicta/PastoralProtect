"use client";

import { useCallback, useEffect, useState } from "react";
import { PoolChart } from "@/components/pool-chart";
import { apiGet, apiPost, API_BASE, getStoredToken, parseApiErrorBody, setStoredToken } from "@/lib/api";

type Pool = {
  total_policies: number;
  active_policies: number;
  total_premiums_mock_tzs: number;
  total_payouts_mock_tzs: number;
  total_payouts_completed: number;
  latest_trigger: Record<string, unknown> | null;
  contract_address: string | null;
  latest_tx_hash: string | null;
};

type Zone = {
  id: number;
  zone_id: string;
  name: string;
  ndvi_threshold: number;
  is_active: boolean;
};

type Recent = { type: string; at: string; summary: string };

type Impact = {
  total_farmers_enrolled: number;
  total_livestock_protected: number;
  total_payouts_executed: number;
  drought_events_detected: number;
  ndvi_snapshots_archived: number;
};

type CyclePhase = {
  id: string;
  label: string;
  status: "complete" | "pending" | "failed" | "skipped";
  detail: string;
};

type CycleStatus = {
  phases: CyclePhase[];
  storage_backend: "mock" | "storacha" | "legacy_http";
  chain_configured: boolean;
  cycle_complete: boolean;
};

function phaseStyles(status: CyclePhase["status"]) {
  switch (status) {
    case "complete":
      return "border-emerald-200 bg-emerald-50/80 text-emerald-950";
    case "failed":
      return "border-red-200 bg-red-50 text-red-950";
    case "skipped":
      return "border-savanna-200 bg-savanna-50/80 text-savanna-700";
    default:
      return "border-amber-200 bg-amber-50/90 text-amber-950";
  }
}

export function DashboardApp() {
  const [user, setUser] = useState("admin");
  const [pass, setPass] = useState("");
  const [loadErr, setLoadErr] = useState<string | null>(null);
  const [data, setData] = useState<{
    pool: Pool;
    zones: Zone[];
    events: Recent[];
    impact: Impact;
    cycle: CycleStatus;
  } | null>(null);
  const [demoLog, setDemoLog] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [initializing, setInitializing] = useState(true);

  const refresh = useCallback(async (t?: string | null) => {
    const tok = t ?? getStoredToken();
    if (!tok) {
      setData(null);
      return;
    }
    setLoadErr(null);
    try {
      const [pool, zones, events, impact, cycle] = await Promise.all([
        apiGet<Pool>("/api/admin/pool-status", tok),
        apiGet<Zone[]>("/api/zones", tok),
        apiGet<Recent[]>("/api/admin/recent-events", tok),
        apiGet<Impact>("/api/admin/impact", tok),
        apiGet<CycleStatus>("/api/cycle/status", tok),
      ]);
      setData({ pool, zones, events, impact, cycle });
    } catch (e) {
      setData(null);
      setLoadErr(e instanceof Error ? e.message : "Failed to load dashboard");
    }
  }, []);

  useEffect(() => {
    const tok = getStoredToken();
    if (!tok) {
      setInitializing(false);
      return;
    }
    void refresh(tok).finally(() => setInitializing(false));
  }, [refresh]);

  useEffect(() => {
    const onAuthChange = () => {
      const t = getStoredToken();
      if (!t) {
        setData(null);
        setLoadErr(null);
        setDemoLog(null);
        setPass("");
        setInitializing(false);
      } else {
        void refresh(t).finally(() => setInitializing(false));
      }
    };
    window.addEventListener("pastoral-auth-change", onAuthChange);
    return () => window.removeEventListener("pastoral-auth-change", onAuthChange);
  }, [refresh]);

  const signOut = () => {
    setStoredToken(null);
    setData(null);
    setLoadErr(null);
    setDemoLog(null);
    setPass("");
  };

  const login = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setLoadErr(null);
    try {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: user.trim(), password: pass }),
      });
      if (!res.ok) throw new Error(parseApiErrorBody(await res.text()));
      const body = (await res.json()) as { access_token: string };
      setStoredToken(body.access_token);
      await refresh(body.access_token);
    } catch (err) {
      setLoadErr(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  };

  const runDemo = async () => {
    setBusy(true);
    setDemoLog(null);
    try {
      const res = await apiPost<Record<string, unknown>>("/api/demo/run", {});
      setDemoLog(JSON.stringify(res, null, 2));
      await refresh();
    } catch (err) {
      setDemoLog(err instanceof Error ? err.message : "Demo failed");
    } finally {
      setBusy(false);
    }
  };

  const tok = typeof window !== "undefined" ? getStoredToken() : null;
  const isLoaded = data !== null;
  const showLoginGate = !initializing && !isLoaded && !tok;
  const showLoginError = !initializing && !isLoaded && tok && loadErr;

  const chartData =
    data != null
      ? [
          { name: "Premiums", v: data.pool.total_premiums_mock_tzs },
          { name: "Payouts", v: data.pool.total_payouts_mock_tzs },
        ]
      : [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl font-semibold text-savanna-900">Dashboard</h1>
        {isLoaded ? (
          <p className="mt-1 text-sm text-savanna-600">Live pool health and activity.</p>
        ) : (
          <p className="mt-1 text-sm text-savanna-600">Sign in to view operator metrics.</p>
        )}
      </div>

      {initializing && tok && (
        <p className="text-sm text-savanna-600" aria-live="polite">
          Loading dashboard…
        </p>
      )}

      {/* Login: only when there is no session */}
      {showLoginGate && (
        <form
          onSubmit={login}
          className="max-w-md space-y-4 rounded-2xl border border-savanna-200 bg-white/90 p-6 shadow-sm"
        >
          <div className="space-y-3">
            <label className="block text-sm">
              <span className="font-medium text-savanna-800">Username</span>
              <input
                className="mt-1 w-full rounded-lg border border-savanna-200 px-3 py-2"
                value={user}
                onChange={(e) => setUser(e.target.value)}
                autoComplete="username"
              />
            </label>
            <label className="block text-sm">
              <span className="font-medium text-savanna-800">Password</span>
              <input
                type="password"
                className="mt-1 w-full rounded-lg border border-savanna-200 px-3 py-2"
                value={pass}
                onChange={(e) => setPass(e.target.value)}
                autoComplete="current-password"
              />
            </label>
          </div>
          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-xl bg-savanna-800 py-2.5 text-sm font-semibold text-white hover:bg-savanna-900 disabled:opacity-60"
          >
            {busy ? "Signing in…" : "Sign in"}
          </button>
          <p className="text-center text-xs text-savanna-500">
            Demo credentials are in the project README.
          </p>
        </form>
      )}

      {showLoginError && (
        <div className="max-w-md space-y-3 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-950">
          <p>{loadErr}</p>
          <button
            type="button"
            onClick={signOut}
            className="font-semibold text-skyj underline"
          >
            Clear session and sign in again
          </button>
        </div>
      )}

      {loadErr && showLoginGate && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900">{loadErr}</div>
      )}

      {isLoaded && data && (
        <>
          <div className="rounded-2xl border border-savanna-200 bg-white/90 p-5 shadow-sm">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 className="font-display text-lg font-semibold text-savanna-900">README pipeline</h2>
                <p className="mt-1 text-xs text-savanna-600">
                  Same flow as the architecture diagram: ingress → IPFS pin → verifiable oracle → optional pool → mock
                  payouts. Storage: <span className="font-mono">{data.cycle.storage_backend}</span>
                  {data.cycle.chain_configured ? " · chain configured" : ""}.
                </p>
              </div>
              <span
                className={
                  data.cycle.cycle_complete
                    ? "inline-flex shrink-0 items-center rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-900"
                    : "inline-flex shrink-0 items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-950"
                }
              >
                {data.cycle.cycle_complete ? "Full cycle complete" : "Run demo or simulate to finish"}
              </span>
            </div>
            <ol className="mt-4 space-y-2">
              {data.cycle.phases.map((ph, i) => (
                <li
                  key={ph.id}
                  className={`flex gap-3 rounded-xl border px-3 py-2.5 text-sm ${phaseStyles(ph.status)}`}
                >
                  <span className="font-mono text-xs font-semibold opacity-70">{i + 1}</span>
                  <div className="min-w-0 flex-1">
                    <p className="font-medium leading-snug">{ph.label}</p>
                    <p className="mt-0.5 text-xs opacity-90">{ph.detail}</p>
                    <p className="mt-1 text-[10px] font-semibold uppercase tracking-wide opacity-80">{ph.status}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>

          <div className="rounded-2xl border border-savanna-200 bg-white/90 p-5 shadow-sm">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <h2 className="font-display text-lg font-semibold text-savanna-900">Pool metrics</h2>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => refresh()}
                  className="rounded-lg border border-savanna-300 px-3 py-1.5 text-sm hover:bg-savanna-50 disabled:opacity-50"
                >
                  Refresh
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={runDemo}
                  className="rounded-lg bg-dry px-3 py-1.5 text-sm font-medium text-white hover:bg-dry-dark disabled:opacity-50"
                >
                  Run full demo
                </button>
              </div>
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-2 border-t border-savanna-100 pt-3 text-xs text-savanna-600">
              {[
                "Oracle",
                "NDVI monitoring",
                "Payout rail",
                data.pool.latest_trigger?.storage_cid ? "IPFS active" : "IPFS",
              ].map((label) => (
                <span key={label} className="inline-flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" aria-hidden />
                  {label}
                </span>
              ))}
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {[
                { k: "Farmers enrolled", v: data.impact.total_farmers_enrolled },
                { k: "Livestock protected", v: data.impact.total_livestock_protected },
                { k: "Active policies", v: data.pool.active_policies },
                { k: "Premiums (mock TZS)", v: data.pool.total_premiums_mock_tzs },
                { k: "Payouts out (mock TZS)", v: data.pool.total_payouts_mock_tzs },
                { k: "Drought events", v: data.impact.drought_events_detected },
                { k: "Payouts completed", v: data.pool.total_payouts_completed },
                { k: "NDVI snapshots", v: data.impact.ndvi_snapshots_archived },
              ].map((c) => (
                <div key={c.k} className="rounded-xl border border-savanna-100 bg-savanna-50/60 px-4 py-3">
                  <p className="text-xs font-medium text-savanna-600">{c.k}</p>
                  <p className="mt-1 font-display text-xl font-semibold text-savanna-900">{c.v}</p>
                </div>
              ))}
            </div>
            {demoLog && (
              <details className="mt-4 rounded-lg border border-savanna-200 bg-savanna-50/80 p-3 text-xs">
                <summary className="cursor-pointer font-medium text-savanna-900">Raw demo response</summary>
                <pre className="mt-2 max-h-40 overflow-auto font-mono text-[11px] text-savanna-700">{demoLog}</pre>
              </details>
            )}
          </div>

          {/* Chart — full width */}
          <div className="rounded-2xl border border-savanna-200 bg-white/90 p-5 shadow-sm">
            <h2 className="font-display text-base font-semibold text-savanna-900">Premiums vs payouts</h2>
            <div className="mt-4 h-56">
              <PoolChart data={chartData} />
            </div>
          </div>

          {/* Technical blocks collapsed by default */}
          <details className="group rounded-2xl border border-savanna-200 bg-white/80">
            <summary className="cursor-pointer list-none px-5 py-4 font-display text-base font-semibold text-savanna-900 marker:content-none [&::-webkit-details-marker]:hidden">
              <span className="flex items-center justify-between gap-2">
                Technical details
                <span className="text-sm font-normal text-skyj group-open:hidden">Show</span>
                <span className="hidden text-sm font-normal text-skyj group-open:inline">Hide</span>
              </span>
            </summary>
            <div className="border-t border-savanna-100 px-5 py-4 space-y-6">
              <dl className="grid gap-3 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-xs uppercase text-savanna-500">Contract</dt>
                  <dd className="break-all font-mono text-xs text-savanna-800">
                    {data.pool.contract_address || "Not configured"}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs uppercase text-savanna-500">Latest tx</dt>
                  <dd className="break-all font-mono text-xs text-savanna-800">{data.pool.latest_tx_hash || "—"}</dd>
                </div>
                <div className="sm:col-span-2">
                  <dt className="text-xs uppercase text-savanna-500">Latest storage CID</dt>
                  <dd className="break-all font-mono text-xs text-savanna-800">
                    {(data.pool.latest_trigger?.storage_cid as string) || "—"}
                  </dd>
                </div>
              </dl>
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wide text-savanna-500">Zones</h3>
                <table className="mt-2 w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-savanna-200 text-savanna-500">
                      <th className="py-2 pr-2">Zone</th>
                      <th className="py-2 pr-2">Name</th>
                      <th className="py-2 pr-2">NDVI min</th>
                      <th className="py-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.zones.map((z) => (
                      <tr key={z.id} className="border-b border-savanna-100">
                        <td className="py-2 pr-2 font-mono text-xs">{z.zone_id}</td>
                        <td className="py-2 pr-2">{z.name}</td>
                        <td className="py-2 pr-2">{z.ndvi_threshold}</td>
                        <td className="py-2">{z.is_active ? "Active" : "Off"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div>
                <h3 className="text-xs font-semibold uppercase tracking-wide text-savanna-500">Recent events</h3>
                <ul className="mt-2 max-h-48 space-y-2 overflow-y-auto text-sm text-savanna-700">
                  {data.events.map((e, i) => (
                    <li key={`${e.at}-${i}`} className="rounded bg-savanna-50 px-2 py-1.5">
                      <span className="text-xs font-semibold text-dry">{e.type}</span> · {e.summary}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </details>
        </>
      )}
    </div>
  );
}
