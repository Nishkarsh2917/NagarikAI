import Link from "next/link";
import { notFound } from "next/navigation";
import { api } from "@/lib/api";
import { SourceLabel } from "@/components/Trust";

export const dynamic = "force-dynamic";

const STATUS_STYLES: Record<string, string> = {
  promised: "bg-paper-deep text-ink-soft",
  in_progress: "bg-ashoka-soft text-ashoka",
  achieved: "bg-green-soft text-green",
  broken: "bg-saffron-soft text-saffron",
  unknown: "bg-paper-deep text-ink-muted",
};

const STATUS_LABEL: Record<string, string> = {
  promised: "Promised",
  in_progress: "In progress",
  achieved: "Achieved",
  broken: "Broken",
  unknown: "Unknown",
};

interface PageProps {
  params: { id: string };
}

export default async function CandidatePage({ params }: PageProps) {
  const id = Number(params.id);
  if (!Number.isFinite(id)) notFound();

  let c;
  try {
    c = await api.candidate(id);
  } catch {
    notFound();
  }

  return (
    <div>
      <header className="ruled pt-3 mb-10">
        <p className="ident">
          <Link href="/" className="hover:text-ashoka">← Today</Link>
          <span className="text-paper-line mx-2">/</span>
          <span>Candidate</span>
        </p>
        <div className="mt-3 flex items-end gap-6 flex-wrap">
          <h1 className="font-display font-semibold text-5xl md:text-6xl tracking-tightish">
            {c.politician.name}
          </h1>
        </div>
        <p className="mt-3 text-sm uppercase tracking-wideish text-ink-muted">
          {c.politician.party ?? "Independent"}
        </p>
        {c.politician.bio && (
          <p className="mt-5 text-ink-soft leading-relaxed max-w-column">
            {c.politician.bio}
          </p>
        )}
      </header>

      <div className="grid md:grid-cols-3 gap-x-12 gap-y-12">
        {/* Manifesto + progress */}
        <section className="md:col-span-2 space-y-12">
          <div>
            <h2 className="font-display text-2xl font-semibold mb-6 border-b border-paper-line pb-3">
              Manifesto promises
            </h2>
            {c.manifesto.length === 0 ? (
              <p className="text-ink-muted">No manifesto items recorded.</p>
            ) : (
              <ul className="divide-y divide-paper-line">
                {c.manifesto.map((m) => (
                  <li key={m.id} className="py-5">
                    <div className="flex items-start gap-3 flex-wrap">
                      <span className={`text-[11px] uppercase tracking-wideish px-2 py-0.5 rounded-sm font-medium ${STATUS_STYLES[m.status] ?? STATUS_STYLES.unknown}`}>
                        {STATUS_LABEL[m.status] ?? m.status}
                      </span>
                      {m.category && (
                        <span className="text-[11px] uppercase tracking-wideish text-ink-muted">
                          {m.category}
                        </span>
                      )}
                      {m.target_year && (
                        <span className="text-[11px] uppercase tracking-wideish text-ink-muted">
                          target {m.target_year}
                        </span>
                      )}
                    </div>
                    <h3 className="font-display text-lg font-semibold mt-2 leading-snug">
                      {m.title}
                    </h3>
                    {m.description && (
                      <p className="mt-2 text-sm text-ink-soft leading-relaxed max-w-column">
                        {m.description}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>

          {c.progress.length > 0 && (
            <div>
              <h2 className="font-display text-2xl font-semibold mb-6 border-b border-paper-line pb-3">
                Progress timeline
              </h2>
              <ol className="space-y-4 border-l-2 border-paper-line pl-6">
                {c.progress.map((p) => (
                  <li key={p.id}>
                    <p className="text-[11px] uppercase tracking-wideish text-ink-muted">
                      {new Date(p.recorded_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
                      <span className="ml-2">{p.status}</span>
                    </p>
                    {p.note && <p className="text-sm text-ink-soft mt-1">{p.note}</p>}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </section>

        {/* Sidebar — candidacies & affidavit */}
        <aside className="md:col-span-1 md:border-l md:border-paper-line md:pl-8 space-y-10">
          <div>
            <p className="label-caps mb-3">Contested elections</p>
            <ul className="space-y-3">
              {c.candidacies.map((cand) => (
                <li key={cand.id} className="border-b border-paper-line/70 pb-3 last:border-0">
                  <p className="text-sm font-medium">
                    {cand.election_year} · {cand.status}
                  </p>
                  <Link
                    href={`/constituencies/${cand.constituency_id}`}
                    className="text-xs text-ashoka hover:underline"
                  >
                    See constituency →
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div className="border-t border-paper-line pt-6">
            <p className="label-caps mb-3">Affidavit on record</p>
            {c.affidavit ? (
              <Link href={`/updates/${c.affidavit.id}`} className="block group">
                <p className="font-display text-base leading-snug group-hover:text-ashoka">
                  {c.affidavit.title}
                </p>
                <div className="mt-2 flex items-center gap-3 flex-wrap">
                  <SourceLabel label={c.affidavit.source_trust_label} />
                </div>
              </Link>
            ) : (
              <p className="text-sm text-ink-muted">
                No affidavit document linked yet. Activate the <code className="font-mono text-xs">eci_affidavits</code> source
                in admin to ingest live ECI data.
              </p>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
