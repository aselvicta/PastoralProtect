"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost, getStoredToken } from "@/lib/api";

type Zone = { zone_id: string; name: string; ndvi_threshold: number };

type SimResult = {
  breached: boolean;
  zone_id: string;
  week: number;
  ndvi_value: number;
  threshold: number;
  trigger_tx_hash?: string | null;
  payouts_created: Array<Record<string, unknown>>;
  chain_error?: string | null;
  message: string;
  verification_passed?: boolean | null;
  verification_detail?: string | null;
  storage_cid?: string | null;
};

type StepState = "done" | "warn" | "skip";

function StepRow({
  label,
  state,
  hint,
}: {
  label: string;
  state: StepState;
  hint?: string;
}) {
  const icon =
    state === "done" ? (
      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-600 text-sm font-bold text-white">
        ✓
      </span>
    ) : state === "warn" ? (
      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-500 text-sm font-bold text-white">
        !
      </span>
    ) : (
      <span className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-savanna-300 text-sm text-savanna-400">
        —
      </span>
    );

  return (
    <li className="flex gap-3 rounded-xl border border-savanna-100 bg-white/90 px-3 py-3 shadow-sm">
      {icon}
      <div className="min-w-0 flex-1">
        <p className="font-medium text-savanna-900">{label}</p>
        {hint ? <p className="mt-0.5 text-xs text-savanna-600">{hint}</p> : null}
      </div>
    </li>
  );
}

export default function SimulatePage() {
  const [zones, setZones] = useState<Zone[]>([]);
  const [zoneId, setZoneId] = useState("Z1");
  const [week, setWeek] = useState(12);
  const [ndvi, setNdvi] = useState(0.18);
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState<SimResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [needsLogin, setNeedsLogin] = useState(false);

  useEffect(() => {
    apiGet<Zone[]>("/api/zones")
      .then((z) => {
        setZones(z);
        if (z[0]) setZoneId(z[0].zone_id);
      })
      .catch(() => {});
    setNeedsLogin(!getStoredToken());
  }, []);

  const steps = useMemo(() => {
    if (!res) return null;

    const hasPayouts = res.payouts_created.length > 0;
    const refsOk =
      hasPayouts &&
      res.payouts_created.every((p) => typeof p.mock_reference === "string" && (p.mock_reference as string).length > 0);

    const s1: StepState = res.breached ? "done" : "skip";
    const s2: StepState =
      !res.breached ? "skip" : res.verification_passed === false ? "warn" : "done";

    let s3: StepState = "skip";
    let s3Hint: string | undefined;
    if (res.breached) {
      if (res.trigger_tx_hash) {
        s3 = "done";
      } else if (res.chain_error) {
        s3 = "warn";
        s3Hint = "On-chain step skipped or failed; demo payouts may still run.";
      } else {
        s3 = "done";
        s3Hint = "Optional in this demo—configure the contract for a live tx hash.";
      }
    }

    const s4: StepState = !res.breached ? "skip" : hasPayouts ? "done" : "warn";
    const s4Hint = res.breached && !hasPayouts ? "No policies in this zone yet—enroll first on Demo Enrollment." : undefined;

    const s5: StepState = !res.breached ? "skip" : !hasPayouts ? "skip" : refsOk ? "done" : "warn";

    return {
      rows: [
        {
          label: "Step 1: NDVI below threshold",
          state: s1,
          hint: res.breached ? `Reading ${res.ndvi_value} is below ${res.threshold} for ${res.zone_id}.` : "Stress rule not fired.",
        },
        {
          label: "Step 2: Oracle validated",
          state: s2,
          hint: res.verification_detail || undefined,
        },
        { label: "Step 3: Smart contract triggered", state: s3, hint: s3Hint },
        { label: "Step 4: Payout executed", state: s4, hint: s4Hint },
        {
          label: "Step 5: Mock M-Pesa sent",
          state: s5,
          hint: refsOk ? "Mock references issued for each payout." : undefined,
        },
      ],
    };
  }, [res]);

  async function run(e: React.FormEvent) {
    e.preventDefault();
    if (!getStoredToken()) {
      setNeedsLogin(true);
      setErr("Sign in on the dashboard first (admin or oracle).");
      return;
    }
    setBusy(true);
    setErr(null);
    setRes(null);
    try {
      const out = await apiPost<SimResult>("/api/oracle/simulate", {
        zone_id: zoneId,
        ndvi_value: ndvi,
        week,
      });
      setRes(out);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Simulation failed";
      setErr(msg);
      if (msg.includes("401") || msg.toLowerCase().includes("oracle")) {
        setNeedsLogin(true);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <div className="mx-auto max-w-lg space-y-8">
        <div>
          <h1 className="font-display text-3xl font-semibold text-savanna-900">Simulate drought</h1>
          <p className="mt-2 text-sm leading-relaxed text-savanna-700">
            Pick a zone, lower the vegetation reading, and run one button to see triggers and payouts end to end.
          </p>
          {needsLogin && (
            <p className="mt-3 rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-950">
              You need a session token: open{" "}
              <Link href="/dashboard" className="font-semibold underline">
                Dashboard
              </Link>{" "}
              and sign in as <strong>admin</strong> or <strong>oracle</strong>, then come back here.
            </p>
          )}
        </div>

        <form onSubmit={run} className="space-y-4 rounded-2xl border border-savanna-200 bg-white/90 p-6 shadow-sm">
          <label className="block text-sm">
            <span className="font-medium text-savanna-800">Zone</span>
            <select
              className="mt-1 w-full rounded-lg border border-savanna-200 px-3 py-2.5"
              value={zoneId}
              onChange={(e) => setZoneId(e.target.value)}
            >
              {zones.map((z) => (
                <option key={z.zone_id} value={z.zone_id}>
                  {z.zone_id} — {z.name}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="font-medium text-savanna-800">Week</span>
            <input
              type="number"
              min={1}
              max={53}
              className="mt-1 w-full rounded-lg border border-savanna-200 px-3 py-2.5"
              value={week}
              onChange={(e) => setWeek(Number(e.target.value))}
            />
          </label>
          <label className="block text-sm">
            <span className="font-medium text-savanna-800">Vegetation index (NDVI)</span>
            <input
              step="0.01"
              type="number"
              className="mt-1 w-full rounded-lg border border-savanna-200 px-3 py-2.5"
              value={ndvi}
              onChange={(e) => setNdvi(Number(e.target.value))}
            />
            <span className="mt-1 block text-xs text-savanna-500">Use a value below the zone threshold to trigger drought.</span>
          </label>
          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-xl bg-dry py-3 text-sm font-semibold text-white shadow-sm hover:bg-dry-dark disabled:opacity-60"
          >
            {busy ? "Running…" : "Simulate drought"}
          </button>
        </form>

        {err && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900">{err}</div>
        )}

        {res && steps && (
          <div className="space-y-4">
            <h2 className="font-display text-lg font-semibold text-savanna-900">What just happened</h2>
            <ul className="space-y-2">
              {steps.rows.map((row) => (
                <StepRow key={row.label} label={row.label} state={row.state} hint={row.hint} />
              ))}
            </ul>
            <p className="text-sm text-savanna-700">{res.message}</p>
            {res.storage_cid && (
              <p className="break-all font-mono text-xs text-savanna-600">
                Stored bundle: <span className="text-savanna-900">{res.storage_cid}</span>
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
