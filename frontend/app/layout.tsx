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

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${dmSans.variable} ${fraunces.variable}`}>
      <body className="font-sans antialiased">
        <SiteHeader />
        <main className="min-h-screen">{children}</main>
        <footer className="border-t border-savanna-200 bg-white">
          <div className="mx-auto max-w-6xl px-4 py-8 text-center">
            <p className="text-xs text-savanna-500">
              © {new Date().getFullYear()} PastoralProtect. Climate risk infrastructure for pastoral communities.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
