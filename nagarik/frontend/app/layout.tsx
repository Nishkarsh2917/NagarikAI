import type { Metadata } from "next";
import { Header } from "@/components/Header";
import "./globals.css";

export const metadata: Metadata = {
  title: "Nagarik — Civic Intelligence for India",
  description: "Government updates, decoded for the people they affect. Every claim links back to its source.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Header />
        <main className="max-w-6xl mx-auto px-6 py-10">{children}</main>
        <footer className="border-t border-paper-line mt-20">
          <div className="max-w-6xl mx-auto px-6 py-8 flex flex-wrap items-start justify-between gap-6 text-xs text-ink-muted">
            <div className="max-w-md leading-relaxed">
              <p className="font-display font-semibold text-ink text-sm mb-2">Nagarik</p>
              <p>
                A nonpartisan, source-grounded civic platform. Summaries are generated
                from official documents and may be imperfect — every update links to its
                original source. Confidence indicators reflect extraction quality, not editorial trust.
              </p>
            </div>
            <div className="flex gap-10">
              <div>
                <p className="label-caps mb-2">Sections</p>
                <ul className="space-y-1">
                  <li><a href="/">Today</a></li>
                  <li><a href="/constituencies">Constituencies</a></li>
                  <li><a href="/feedback">Citizen Voice</a></li>
                </ul>
              </div>
              <div>
                <p className="label-caps mb-2">About</p>
                <ul className="space-y-1">
                  <li>Source-grounded</li>
                  <li>Reprocessable</li>
                  <li>Open architecture</li>
                </ul>
              </div>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
