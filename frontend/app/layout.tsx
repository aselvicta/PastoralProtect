import type { Metadata } from "next";
import { DM_Sans, Fraunces } from "next/font/google";
import { SiteHeader } from "@/components/site-header";
import "./globals.css";

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-dm-sans",
});

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
});

export const metadata: Metadata = {
  title: "PastoralProtect — Climate risk infrastructure",
  description: "Automated drought-triggered livestock protection for pastoralists.",
};

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${dmSans.variable} ${fraunces.variable}`}>
      <body className="font-sans antialiased">
        <SiteHeader />
        <main className="min-h-screen">{children}</main>
        <footer className="border-t border-savanna-200 bg-white">
          <div className="mx-auto max-w-6xl px-4 py-10 text-center space-y-2">
            <p className="text-xs text-savanna-500">
              © {new Date().getFullYear()} PastoralProtect. Climate risk demo for pastoral communities.
            </p>
            <p className="text-xs text-savanna-500">
              <a href={`${apiBase}/docs`} className="font-medium text-skyj underline hover:text-savanna-800">
                API docs
              </a>
              <span className="text-savanna-400"> · </span>
              <span>
                USSD mock: <code className="rounded bg-savanna-100 px-1 py-0.5 font-mono text-[11px]">POST /api/ussd</code>
              </span>
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
