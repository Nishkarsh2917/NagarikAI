import Link from "next/link";
import { notFound } from "next/navigation";
import { api } from "@/lib/api";
import { UpdateCard } from "@/components/UpdateCard";

export const dynamic = "force-dynamic";

interface PageProps {
  params: { id: string };
}

export default async function ConstituencyDetailPage({ params }: PageProps) {
  const id = Number(params.id);
  if (!Number.isFinite(id)) notFound();

  let c;
  try {
    c = await api.constituency(id);
  } catch {
    notFound();
  }

  // Also pull feedback clusters for this constituency.
  let clusters: Awaited<ReturnType<typeof api.feedbackClusters>> = [];
  try {
    clusters = await api.feedbackClusters({ constituency_id: id });
  } catch {
    // non-fatal
  }

  return (
    <div>
      {/* Editorial header */}
      <header className="ruled pt-3 mb-10">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <p className="ident">
            <Link href="/constituencies" className="hover:text-ashoka">← All constituencies</Link>
          </p>
          <p className="ident">
            {c.type === "lok_sabha" ? "Lok Sabha" : "Vidhan Sabha"}
            {c.number ? ` · PC ${c.number}` : ""}
          </p>
        </div>
        <h1 className="font-display font-semibold text-5xl md:text-6xl mt-3 tracking-tightish">
          {c.name}
        </h1>
        <p className="mt-3 text-ink-soft">
          {[c.district?.name, c.state?.name].filter(Boolean).join(" · ")}
        </p>
      </header>

      <div className="grid md:grid-cols-3 gap-x-12 gap-y-12">
        {/* Recent updates — main column */}
        <section className="md:col-span-2">
          <div className="flex items-end justify-between mb-6 border-b border-paper-line pb-3">
            <h2 className="font-display text-2xl font-semibold">Recent updates</h2>
            <span className="text-xs text-ink-muted">{c.recent_updates.length} mapped here</span>
          </div>

          {c.recent_updates.length === 0 ? (
            <p className="text-ink-muted py-12">
              No updates have been automatically mapped to this constituency yet.
            </p>
          ) : (
            <div className="space-y-8">
              {c.recent_updates.map((u) => (
                <UpdateCard key={u.id} item={u} />
              ))}
            </div>
          )}
        </section>

        {/* Sidebar */}
        <aside className="md:col-span-1 md:border-l md:border-paper-line md:pl-8 space-y-10">
          {/* Candidates */}
          <div>
            <p className="label-caps mb-4">Candidates</p>
            {c.candidates.length === 0 ? (
              <p className="text-sm text-ink-muted">None on record.</p>
            ) : (
              <ul className="space-y-4">
                {c.candidates.map((cand) => (
                  <li key={cand.id} className="border-b border-paper-line/70 pb-3 last:border-0">
                    <Link href={`/candidates/${cand.politician.id}`} className="group block">
                      <p className="font-display text-lg font-semibold group-hover:text-ashoka transition-colors">
                        {cand.politician.name}
                      </p>
                      <p className="text-xs text-ink-muted">
                        {cand.politician.party} · contesting {cand.election_year}
                      </p>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Top issues */}
          <div className="border-t border-paper-line pt-6">
            <p className="label-caps mb-4">Top issues</p>
            {c.top_topics.length === 0 ? (
              <p className="text-sm text-ink-muted">
                No clustered citizen feedback yet for this constituency.
              </p>
            ) : (
              <ul className="space-y-2">
                {c.top_topics.map((t) => (
                  <li key={t.id} className="flex items-center justify-between text-sm">
                    <span>{t.name}</span>
                    <span className="font-mono text-xs text-ink-muted">{t.count}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Feedback clusters */}
          {clusters.length > 0 && (
            <div className="border-t border-paper-line pt-6">
              <p className="label-caps mb-4">Recurring feedback</p>
              <ul className="space-y-4">
                {clusters.slice(0, 4).map((fc) => (
                  <li key={fc.id} className="text-sm leading-relaxed text-ink-soft">
                    {fc.summary}
                    <span className="block text-[11px] text-ink-muted mt-1 font-mono">
                      {fc.count} submissions
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="border-t border-paper-line pt-6">
            <Link
              href={`/feedback?constituency_id=${c.id}`}
              className="inline-block text-sm text-ashoka hover:text-ashoka-deep underline underline-offset-4"
            >
              Submit feedback for this constituency →
            </Link>
          </div>
        </aside>
      </div>
    </div>
  );
}
