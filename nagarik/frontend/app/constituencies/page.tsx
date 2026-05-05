import Link from "next/link";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ConstituenciesPage() {
  const constituencies = await api.constituencies();

  return (
    <div>
      <header className="ruled pt-3 mb-10">
        <p className="ident">Constituencies</p>
        <h1 className="font-display font-semibold text-4xl md:text-5xl mt-2 tracking-tightish">
          Where you live, what you&apos;re owed.
        </h1>
        <p className="mt-4 text-ink-soft max-w-column leading-relaxed">
          Each constituency has its own page with the latest government updates mapped
          to it, candidate information, and recurring citizen feedback.
        </p>
      </header>

      <ul className="grid sm:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-2">
        {constituencies.map((c) => (
          <li key={c.id} className="border-b border-paper-line py-3">
            <Link href={`/constituencies/${c.id}`} className="group flex items-baseline justify-between">
              <span>
                <span className="font-display font-semibold text-lg group-hover:text-ashoka transition-colors">
                  {c.name}
                </span>
                <span className="ml-3 text-[11px] uppercase tracking-wideish text-ink-muted">
                  {c.type === "lok_sabha" ? "Lok Sabha" : "Vidhan Sabha"}
                </span>
              </span>
              {c.number && <span className="font-mono text-xs text-ink-muted">#{c.number}</span>}
            </Link>
          </li>
        ))}
      </ul>

      {constituencies.length === 0 && (
        <p className="text-ink-muted py-12 text-center">No constituencies seeded yet.</p>
      )}
    </div>
  );
}
