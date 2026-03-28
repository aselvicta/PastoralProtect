"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";

type Zone = { zone_id: string; name: string; ndvi_threshold: number };

export default function EnrollPage() {
  const [zones, setZones] = useState<Zone[]>([]);
  const [farmerId, setFarmerId] = useState("F-DEMO-001");
  const [phone, setPhone] = useState("+255700000000");
  const [zoneId, setZoneId] = useState("Z1");
  const [livestock, setLivestock] = useState(20);
  const [premium, setPremium] = useState(5000);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    apiGet<Zone[]>("/api/zones")
      .then(setZones)
      .catch(() => setZones([]));
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    setResult(null);
    try {
      const body = {
        farmer_id: farmerId,
        phone_number: phone,
        zone_id: zoneId,
        livestock_count: livestock,
        premium_amount: premium,
        preferred_language: "sw",
      };
      const res = await apiPost<{ enrollment_message: string; contract_tx_hash?: string | null }>(
        "/api/policies/enroll",
        body,
      );
      setResult(`${res.enrollment_message}${res.contract_tx_hash ? `\nTx: ${res.contract_tx_hash}` : ""}`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Enrollment failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <div className="mx-auto max-w-lg space-y-6">
        <div>
          <h1 className="font-display text-3xl font-semibold text-savanna-900">Demo enrollment</h1>
          <p className="mt-2 text-sm leading-relaxed text-savanna-700">
            Add a livestock keeper to the pool—takes a few seconds. Then open{" "}
            <Link href="/simulate" className="font-semibold text-skyj underline">
              Simulate drought
            </Link>{" "}
            for the same zone to see payouts.
          </p>
        </div>

        <form onSubmit={submit} className="space-y-4 rounded-2xl border border-savanna-200 bg-white/80 p-6 shadow-sm">
          <label className="block text-sm">
            <span className="text-savanna-700">Farmer ID</span>
            <input
              className="mt-1 w-full rounded-lg border border-savanna-200 px-3 py-2"
              value={farmerId}
              onChange={(e) => setFarmerId(e.target.value)}
            />
          </label>
          <label className="block text-sm">
            <span className="text-savanna-700">Phone</span>
            <input
              className="mt-1 w-full rounded-lg border border-savanna-200 px-3 py-2"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
          </label>
          <label className="block text-sm">
            <span className="text-savanna-700">Zone</span>
            <select
              className="mt-1 w-full rounded-lg border border-savanna-200 px-3 py-2"
              value={zoneId}
              onChange={(e) => setZoneId(e.target.value)}
            >
              {zones.length === 0 ? (
                <option value="Z1">Z1 (seed)</option>
              ) : (
                zones.map((z) => (
                  <option key={z.zone_id} value={z.zone_id}>
                    {z.zone_id} — {z.name} (NDVI min {z.ndvi_threshold})
                  </option>
                ))
              )}
            </select>
          </label>
          <label className="block text-sm">
            <span className="text-savanna-700">Livestock count</span>
            <input
              type="number"
              min={1}
              className="mt-1 w-full rounded-lg border border-savanna-200 px-3 py-2"
              value={livestock}
              onChange={(e) => setLivestock(Number(e.target.value))}
            />
          </label>
          <label className="block text-sm">
            <span className="text-savanna-700">Premium (mock TZS)</span>
            <input
              type="number"
              min={1}
              className="mt-1 w-full rounded-lg border border-savanna-200 px-3 py-2"
              value={premium}
              onChange={(e) => setPremium(Number(e.target.value))}
            />
          </label>

          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-xl bg-savanna-800 py-2.5 text-sm font-medium text-white hover:bg-savanna-900 disabled:opacity-60"
          >
            {busy ? "Submitting…" : "Submit enrollment"}
          </button>
        </form>

        {err && (
        <div role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm leading-relaxed text-red-950">
          {err}
        </div>
      )}
        {result && <pre className="whitespace-pre-wrap rounded-xl bg-savanna-50 p-4 text-sm text-savanna-900">{result}</pre>}
      </div>
    </div>
  );
}
