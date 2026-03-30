"use client";

import Image, { type StaticImageData } from "next/image";
import Link from "next/link";
import { useState } from "react";
import { API_BASE } from "@/lib/api";

import auditTrails from "@/images/auditTrails.webp";
import cows from "@/images/cows.jpg";
import developers from "@/images/developers.jpg";
import mobilephones from "@/images/mobilephones.jpg";
import satelliteOracle from "@/images/sattelite.png";

const API_DOCS_URL = `${API_BASE}/docs`;

const techPills = ["FastAPI", "Solidity", "Filecoin / IPFS", "Oracle"];

/** Local assets under `frontend/images/` — `object-cover` in FeatureColumn keeps aspect ratio in cards. */
const IMG: Record<string, StaticImageData | string> = {
  satellite: satelliteOracle,
  paymentRail: mobilephones,
  code: auditTrails,
  orgDesk: developers,
  pastoral: cows,
};

const featureColumns = [
  {
    topTitle: "NDVI & zone rules",
    topBody:
      "Each zone has a vegetation threshold. Readings are compared automatically—no one-off field loss assessments.",
    image: IMG.satellite,
    imageLabel: "Satellite & oracle data",
    bottomTitle: "Trigger when it matters",
    bottomBody: "When stress crosses the rule, the oracle path runs verification before any payout.",
  },
  {
    topTitle: "Payout rail",
    topBody:
      "Structured for mobile money: the demo uses a mock ledger you can swap for a live M-Pesa or similar provider.",
    image: IMG.paymentRail,
    imageLabel: "Mobile-ready payouts",
    bottomTitle: "Fast, traceable transfers",
    bottomBody: "Payouts are logged with amounts and policy links so operators can reconcile quickly.",
  },
  {
    topTitle: "Pool, hash, optional chain",
    topBody:
      "REST APIs for enrollment and simulation. Optional Solidity pool on Base; trigger bundles can be pinned on IPFS.",
    image: IMG.code,
    imageLabel: "APIs & audit trail",
    bottomTitle: "Integrity before funds move",
    bottomBody: "SHA-256 checks align stored bundles with what the payout engine executed.",
  },
];

const capabilities = [
  {
    title: "Enrollment & zones",
    body: "Farmers join by zone with livestock counts and premiums—validated before policies are stored.",
  },
  {
    title: "NDVI & drought rules",
    body: "Vegetation stress is compared to per-zone thresholds so triggers are automatic, not subjective.",
  },
  {
    title: "Verifiable storage",
    body: "Trigger bundles can be anchored on IPFS (Filecoin ecosystem) with integrity checks before payouts.",
  },
  {
    title: "Payout rail",
    body: "Mock mobile-money flow today; structured so a real provider can plug in without rewriting core logic.",
  },
  {
    title: "Operator dashboard",
    body: "Pool health, impact metrics, and recent events in one place for demos and audits.",
  },
  {
    title: "REST APIs",
    body: "Enrollment, oracle simulation, and admin metrics—build your own UI on top.",
  },
];

const audiences = [
  {
    title: "Insurers & programs",
    body: "Launch parametric-style livestock protection without building claims ops from scratch.",
  },
  {
    title: "Cooperatives",
    body: "Pool risk across members with transparent rules and faster relief when drought hits.",
  },
  {
    title: "NGOs & government",
    body: "Run climate resilience programs with logged triggers and payout trails stakeholders can review.",
  },
  {
    title: "Agri-finance",
    body: "De-risk pastoral portfolios with automated triggers aligned to real climate stress.",
  },
];

const faqs = [
  {
    q: "What is PastoralProtect's purpose and target audience?",
    a: "PastoralProtect is a B2B-style stack for insurers, cooperatives, NGOs, government programs, and agri-finance teams that want parametric livestock protection when drought shows up in vegetation—not weeks later in paperwork. You bring farmers, channels, and risk appetite; the demo shows zone rules, NDVI-style triggers, payout rails shaped for mobile money, and optional on-chain pool wiring. It is built for partners to embed in their own programs, not as a standalone consumer app every pastoralist installs separately.",
  },
  {
    q: "Which data streams drive the automated evaluation process?",
    a: "The reference build centers on NDVI-like greenness by climate zone: each zone carries a minimum vegetation threshold, and when readings stay below that line the system can treat it as pasture stress. In the demo you can simulate those readings; in production the same logic maps cleanly to satellite-derived NDVI (for example Sentinel-2 pipelines), partner indices, or other feeds you certify. Rainfall or temperature triggers can sit beside NDVI as you harden the product. When a rule fires, the oracle path runs checks (including integrity around stored bundles) before payouts—no manual claim forms for every shock. Filecoin / IPFS-style pinning is optional: it gives a stable copy of what was hashed at payout time, for appeals and audits.",
  },
  {
    q: "What are the steps for starting a partnership or pilot program?",
    a: "You start with zones and thresholds that match your geography, then enroll pastoralists with livestock counts, premiums, and payout contact details. The demo includes seed zones and flows so you can enroll a farmer and simulate a drought in one sitting. Staff access uses roles (for example admin vs oracle): configuration versus running assessments. A real rollout adds your KYC, languages, and production data feeds—but the same enrollment → monitor → trigger → payout sequence stays intact.",
  },
  {
    q: "How is the service priced?",
    a: "In the demo, premiums are mock amounts (for example in TZS) so you can follow premiums and payouts in the dashboard. In a live program you set premium levels and pool rules; totals stay reflected in pool and payout logs instead of hidden spreadsheets. Commercial platform fees would be agreed with your organization—the important part we demonstrate is transparent math: what was collected, what triggered, and what was paid.",
  },
  {
    q: "Is it possible to sync PastoralProtect with our current infrastructure?",
    a: "Yes. The stack is API-first: REST endpoints cover enrollment, zones, oracle simulation, storage pointers, and admin impact metrics. You can drive the same flows from USSD, a core banking system, or your own agent UI, and use the included web dashboard only where needed. Optional Solidity pools on Base can mirror pool health for partners who want on-chain transparency alongside off-chain operations.",
  },
  {
    q: "What is the process for launching the demo?",
    a: "Clone the repo, start the FastAPI backend and this Next.js app using the README environment examples, then open the Dashboard and sign in with the demo users. Use Demo enrollment to add a policy, Simulate drought to breach a zone’s NDVI threshold, and watch triggers, storage CIDs (when enabled), and payouts appear in the UI. Many teams run the one-click demo from the dashboard first, then explore the API.",
  },
];

function FeatureColumn({
  topTitle,
  topBody,
  image,
  imageLabel,
  bottomTitle,
  bottomBody,
}: {
  topTitle: string;
  topBody: string;
  image: StaticImageData | string;
  imageLabel: string;
  bottomTitle: string;
  bottomBody: string;
}) {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h3 className="font-display text-lg font-semibold text-savanna-900">{topTitle}</h3>
        <p className="mt-2 text-sm leading-relaxed text-savanna-600">{topBody}</p>
      </div>
      <div className="relative aspect-[4/3] overflow-hidden rounded-2xl border border-savanna-200 shadow-sm">
        <Image src={image} alt={imageLabel} fill className="object-cover" sizes="(max-width: 1024px) 100vw, 33vw" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/20 to-transparent" />
        <p className="absolute bottom-4 left-4 right-4 font-display text-lg font-semibold text-white">{imageLabel}</p>
      </div>
      <div>
        <h4 className="font-display text-base font-semibold text-savanna-900">{bottomTitle}</h4>
        <p className="mt-2 text-sm leading-relaxed text-savanna-600">{bottomBody}</p>
      </div>
    </div>
  );
}

export function LandingPage() {
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  return (
    <div>
      {/* Hero */}
      <section className="mx-auto max-w-6xl px-4 pb-12 pt-6 md:pt-10">
        <div className="relative overflow-hidden rounded-3xl border border-savanna-200/90 bg-gradient-to-b from-white via-white to-savanna-50/40 px-6 py-14 shadow-sm md:px-12 md:py-20">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="font-display text-4xl font-semibold leading-[1.1] tracking-tight text-savanna-900 md:text-5xl lg:text-[3.25rem]">
              Parametric livestock protection
              <span className="block text-savanna-800">for drought-prone regions</span>
            </h1>
            <p className="mt-6 text-lg leading-relaxed text-savanna-700 md:text-xl">
              PastoralProtect helps organizations offer automated, rules-based payouts when vegetation stress crosses
              defined thresholds—without manual claims or field-by-field reviews.
            </p>
            <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row sm:flex-wrap">
              <Link
                href="/dashboard"
                className="inline-flex min-w-[200px] justify-center rounded-xl bg-savanna-900 px-8 py-3.5 text-sm font-semibold text-white shadow-md transition hover:brightness-95"
              >
                Open dashboard
              </Link>
              <Link
                href="/simulate"
                className="inline-flex min-w-[200px] justify-center rounded-xl bg-dry px-8 py-3.5 text-sm font-semibold text-white shadow-md transition hover:bg-dry-dark"
              >
                Simulate drought
              </Link>
              <Link
                href="/enroll"
                className="inline-flex min-w-[200px] justify-center rounded-xl border-2 border-savanna-300 bg-white px-8 py-3.5 text-sm font-semibold text-savanna-900 transition hover:bg-savanna-50"
              >
                Demo enrollment
              </Link>
            </div>
          </div>
          <div className="mx-auto mt-14 max-w-4xl border-t border-savanna-200/80 pt-10">
            <div className="flex flex-wrap items-center justify-center gap-2 md:gap-3">
              {techPills.map((t) => (
                <span
                  key={t}
                  className="rounded-full border border-savanna-200 bg-white px-4 py-2 text-xs font-medium text-savanna-800 shadow-sm md:text-sm"
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Problem */}
      <section className="mx-auto max-w-3xl px-4 pb-16 text-center">
        <h2 className="font-display text-2xl font-semibold text-savanna-900">The problem</h2>
        <p className="mt-4 text-lg text-savanna-700">
          Manual insurance fails pastoralists: slow verification, paperwork, and poor connectivity leave communities
          exposed when drought strikes.
        </p>
      </section>

      {/* How it works */}
      <section className="mx-auto max-w-6xl px-4 pb-20">
        <h2 className="text-center font-display text-2xl font-semibold text-savanna-900 md:text-3xl">
          How PastoralProtect works
        </h2>
        <ol className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { n: "01", t: "Enroll", d: "Farmers join a protection pool for a climate zone." },
            { n: "02", t: "Monitor", d: "Vegetation signals are tracked against zone thresholds." },
            { n: "03", t: "Trigger", d: "When rules say drought, the oracle path runs—no claim forms." },
            { n: "04", t: "Payout", d: "Eligible policies pay out on a mobile-money-ready rail." },
          ].map((s) => (
            <li
              key={s.n}
              className="relative rounded-2xl border border-savanna-200 bg-white p-6 shadow-sm transition hover:border-savanna-300 hover:shadow-md"
            >
              <span className="font-display text-3xl font-bold text-savanna-200">{s.n}</span>
              <p className="mt-3 font-display text-lg font-semibold text-savanna-900">{s.t}</p>
              <p className="mt-2 text-sm leading-relaxed text-savanna-600">{s.d}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* Three-column features (MicroCrop-style) */}
      <section className="border-y border-savanna-200/80 bg-white py-20">
        <div className="mx-auto max-w-6xl px-4">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="font-display text-2xl font-semibold text-savanna-900 md:text-3xl">
              Enrollment, risk, and rails in one flow
            </h2>
            <p className="mt-4 text-savanna-600">
              NDVI-style inputs, a payout rail shaped for mobile money, and optional on-chain pool plus IPFS-backed
              records—aligned with how this demo is wired.
            </p>
          </div>
          <div className="mt-14 grid gap-12 lg:grid-cols-3 lg:gap-8">
            {featureColumns.map((col) => (
              <FeatureColumn key={col.topTitle} {...col} />
            ))}
          </div>
        </div>
      </section>

      {/* Capabilities grid */}
      <section className="bg-savanna-100/40 py-20">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="text-center font-display text-2xl font-semibold text-savanna-900 md:text-3xl">
            What PastoralProtect provides
          </h2>
          <ul className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {capabilities.map((c) => (
              <li key={c.title} className="rounded-2xl border border-savanna-200/80 bg-white p-6 shadow-sm">
                <h3 className="font-display text-lg font-semibold text-savanna-900">{c.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-savanna-600">{c.body}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* For organizations — copy + imagery */}
      <section className="mx-auto max-w-6xl px-4 py-20">
        <h2 className="text-center font-display text-2xl font-semibold text-savanna-900 md:text-3xl">
          Built for teams serving pastoral communities
        </h2>
        <p className="mx-auto mt-4 max-w-3xl text-center text-lg text-savanna-600">
          Whether you are an insurer, cooperative, NGO, or public program—PastoralProtect ties clear rules, telemetry,
          and payout logs together so relief can move when vegetation stress crosses the line.
        </p>
        <div className="mt-12 grid gap-6 md:grid-cols-2">
          <div className="relative aspect-[16/11] overflow-hidden rounded-2xl border border-savanna-200 shadow-sm">
            <Image
              src={IMG.orgDesk}
              alt="People collaborating at a desk with laptops"
              fill
              className="object-cover"
              sizes="(max-width: 768px) 100vw, 50vw"
            />
          </div>
          <div className="relative aspect-[16/11] overflow-hidden rounded-2xl border border-savanna-200 shadow-sm">
            <Image
              src={IMG.pastoral}
              alt="Cattle grazing in open rangeland"
              fill
              className="object-cover"
              sizes="(max-width: 768px) 100vw, 50vw"
            />
          </div>
        </div>
      </section>

      {/* Audiences */}
      <section className="mx-auto max-w-6xl px-4 pb-20">
        <h2 className="text-center font-display text-2xl font-semibold text-savanna-900 md:text-3xl">
          Who it&apos;s for
        </h2>
        <ul className="mt-10 grid gap-6 sm:grid-cols-2">
          {audiences.map((a) => (
            <li
              key={a.title}
              className="rounded-2xl border border-savanna-200 bg-gradient-to-br from-white to-savanna-50/50 p-6 shadow-sm"
            >
              <h3 className="font-display text-lg font-semibold text-savanna-900">{a.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-savanna-600">{a.body}</p>
            </li>
          ))}
        </ul>
      </section>

      {/* Developers — API docs + USSD once (not repeated in footer) */}
      <section className="border-y border-savanna-200 bg-savanna-50/80 py-14">
        <div className="mx-auto max-w-3xl px-4 text-center">
          <h2 className="font-display text-2xl font-semibold text-savanna-900 md:text-3xl">Developers</h2>
          <p className="mt-3 text-sm leading-relaxed text-savanna-600 md:text-base">
            Open the docs to try the API in your browser. You will see login, enroll, oracle, storage, admin, and a simple
            USSD test (
            <code className="rounded bg-white px-1.5 py-0.5 font-mono text-xs text-savanna-800">POST /api/ussd</code>
            ).
          </p>
          <a
            href={API_DOCS_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-6 inline-flex min-w-[220px] justify-center rounded-xl border-2 border-skyj bg-skyj px-8 py-3.5 text-sm font-semibold text-white shadow-sm transition hover:bg-sky-800"
          >
            Open API documentation
          </a>
        </div>
      </section>

      {/* FAQ — savanna band (matches platform neutrals) */}
      <section className="bg-gradient-to-b from-savanna-800 to-savanna-900 py-16 text-white md:py-24">
        <div className="mx-auto max-w-3xl px-4">
          <h2 className="text-center font-display text-3xl font-semibold tracking-tight md:text-4xl">
            Frequently asked questions
          </h2>
          <div className="mt-10 divide-y divide-white/15">
            {faqs.map((f, i) => (
              <div key={f.q} className="py-5 first:pt-0">
                <button
                  type="button"
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="flex w-full items-start justify-between gap-4 text-left text-base font-medium text-white md:text-lg"
                >
                  <span>{f.q}</span>
                  <span className="shrink-0 text-xl leading-none text-white/80" aria-hidden>
                    {openFaq === i ? "−" : "+"}
                  </span>
                </button>
                {openFaq === i && (
                  <p className="mt-4 text-sm leading-relaxed text-white/85 md:text-base">{f.a}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA — full-bleed image + overlay */}
      <section className="relative min-h-[420px] w-full overflow-hidden">
        <Image
          src={IMG.pastoral}
          alt=""
          fill
          className="object-cover object-center"
          sizes="100vw"
          priority={false}
          aria-hidden
        />
        <div className="absolute inset-0 bg-savanna-900/65" />
        <div className="relative z-10 mx-auto flex min-h-[420px] max-w-4xl flex-col items-center justify-center px-4 py-16 text-center">
          <h2 className="font-display text-3xl font-semibold text-white md:text-4xl">
            Ready to run the full demo?
          </h2>
          <p className="mt-4 max-w-xl text-lg text-white/90">
            Open the dashboard, enroll a farmer, then simulate a drought to see triggers, storage, and payouts in one
            flow.
          </p>
          <div className="mt-10 flex flex-wrap justify-center gap-4">
            <Link
              href="/dashboard"
              className="inline-flex min-w-[180px] justify-center rounded-xl bg-white px-8 py-3.5 text-sm font-semibold text-savanna-900 shadow-lg transition hover:bg-savanna-50"
            >
              Go to dashboard
            </Link>
            <Link
              href="/simulate"
              className="inline-flex min-w-[180px] justify-center rounded-xl border-2 border-white/90 bg-transparent px-8 py-3.5 text-sm font-semibold text-white transition hover:bg-white/10"
            >
              Simulate drought
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
