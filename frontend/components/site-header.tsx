"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { API_BASE, getStoredToken, setStoredToken } from "@/lib/api";

const API_DOCS_URL = `${API_BASE}/docs`;

function jwtRole(token: string): string | null {
  try {
    const part = token.split(".")[1];
    if (!part) return null;
    const b64 = part.replace(/-/g, "+").replace(/_/g, "/");
    const pad = b64 + "=".repeat((4 - (b64.length % 4)) % 4);
    const payload = JSON.parse(atob(pad)) as { role?: string };
    return payload.role ?? null;
  } catch {
    return null;
  }
}

export function SiteHeader() {
  const [, setTick] = useState(0);

  useEffect(() => {
    const sync = () => setTick((n) => n + 1);
    window.addEventListener("pastoral-auth-change", sync);
    return () => window.removeEventListener("pastoral-auth-change", sync);
  }, []);

  const tok = typeof window !== "undefined" ? getStoredToken() : null;
  const role = tok ? jwtRole(tok) : null;

  return (
    <header className="border-b border-savanna-200/80 bg-white/70 backdrop-blur-md sticky top-0 z-50">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3">
        <Link href="/" className="shrink-0 font-display text-lg font-semibold tracking-tight text-savanna-900">
          PastoralProtect
        </Link>
        <div className="flex flex-wrap items-center justify-end gap-x-1 gap-y-2 text-sm text-savanna-700 sm:gap-x-2">
          <Link className="rounded-lg px-2.5 py-1.5 hover:bg-savanna-100 sm:px-3" href="/dashboard">
            Dashboard
          </Link>
          <Link className="rounded-lg px-2.5 py-1.5 hover:bg-savanna-100 sm:px-3" href="/enroll">
            Enroll
          </Link>
          <Link
            className="rounded-lg bg-dry px-2.5 py-1.5 font-medium text-white hover:bg-dry-dark sm:px-3"
            href="/simulate"
          >
            Simulate drought
          </Link>
          <a
            href={API_DOCS_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center rounded-lg border-2 border-skyj/80 bg-skyj/10 px-2.5 py-1.5 text-sm font-semibold text-skyj hover:bg-skyj/20 sm:px-3"
          >
            API docs
          </a>
          {tok && role && (
            <span className="ml-1 rounded-md border border-savanna-200 bg-savanna-50 px-2.5 py-1 text-xs font-semibold uppercase tracking-wide text-savanna-800">
              {role}
            </span>
          )}
          {tok && (
            <button
              type="button"
              onClick={() => setStoredToken(null)}
              className="ml-0 rounded-lg border border-savanna-300 bg-white px-2.5 py-1.5 text-xs font-medium text-savanna-800 hover:bg-savanna-50 sm:px-3 sm:text-sm"
            >
              Sign out
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
