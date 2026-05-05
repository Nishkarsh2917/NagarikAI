"use client";

import { useState } from "react";
import { api, type IngestionStatusOut, type IngestionRunOut, type SourceOut, timeAgo } from "@/lib/api";

const STATUS_COLOR: Record<string, string> = {
  success: "text-green",
  partial: "text-amber",
  failed: "text-saffron",
  running: "text-ashoka",
};

export function AdminPanel() {
  const [token, setToken] = useState("");
  const [data, setData] = useState<IngestionStatusOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [triggering, setTriggering] = useState(false);
  const [triggerMsg, setTriggerMsg] = useState<string | null>(null);

  async function load(t: string) {
    setLoading(true);
    setError(null);
    try {
      const result = await api.ingestionStatus(t);
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load.");
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  async function onUnlock(e: React.FormEvent) {
    e.preventDefault();
    if (!token.trim()) return;
    await load(token.trim());
  }

  async function onRunNow() {
    if (!token) return;
    setTriggering(true);
    setTriggerMsg(null);
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
      const res = await fetch(`${base}/api/v1/admin/run-ingestion`, {
        method: "POST",
        headers: { "X-Admin-Token": token },
      });
      if (!res.ok) throw new Error(`Trigger failed: ${res.status}`);
      setTriggerMsg("Ingestion queued. Refreshing in a few seconds…");
      setTimeout(() => load(token).then(() => setTriggerMsg(null)), 4000);
    } catch (e) {
      setTriggerMsg(e instanceof Error ? e.message : "Failed.");
    } finally {
      setTriggering(false);
    }
  }

  // ---- Locked state ----
  if (!data) {
    return (
      <form onSubmit={onUnlock} className="max-w-md space-y-4">
        <div>
          <label htmlFor="token" className="label-caps block mb-1.5">
            Admin token
          </label>
          <input
            id="token"
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            className="w-full bg-paper-deep border border-paper-line text-sm py-2 px-3 outline-none focus:border-ashoka rounded-sm font-mono"
            placeholder="X-Admin-Token"
          />
        </div>
        {error && <p className="text-sm text-saffron">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="bg-ink text-paper px-5 py-2.5 text-sm uppercase tracking-wideish font-medium hover:bg-ashoka transition-colors disabled:opacity-50"
        >
          {loading ? "Verifying…" : "Unlock"}
        </button>
        <p className="text-xs text-ink-muted leading-relaxed">
          The default dev token is <code className="font-mono px-1 py-0.5 bg-paper-deep rounded-sm">dev-admin-token-change-me</code>.
          Override via <code className="font-mono px-1">ADMIN_TOKEN</code> in the backend&apos;s <code className="font-mono px-1">.env</code>.
        </p>
      </form>
    );
  }

  // ---- Authenticated state ----
  const failedSources = data.sources.filter(
    (s) => s.last_status && s.last_status !== "ok" && !s.last_status.startsWith("partial")
  );

  return (
    <div className="space-y-12">
      {/* Top bar with manual trigger */}
      <div className="flex items-center justify-between flex-wrap gap-4 border-b border-paper-line pb-4">
        <div>
          <p className="text-sm text-ink-soft">
            {data.runs.length} runs on record · {data.sources.length} configured sources
          </p>
          {triggerMsg && (
            <p className="text-xs text-ashoka mt-1">{triggerMsg}</p>
          )}
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => load(token)}
            className="text-xs uppercase tracking-wideish text-ink-soft hover:text-ink"
          >
            ↻ Refresh
          </button>
          <button
            onClick={onRunNow}
            disabled={triggering}
            className="bg-ashoka text-paper px-4 py-2 text-xs uppercase tracking-wideish font-medium hover:bg-ashoka-deep transition-colors disabled:opacity-50"
          >
            {triggering ? "Queueing…" : "Run ingestion now"}
          </button>
        </div>
      </div>

      {/* Failed sources callout */}
      {failedSources.length > 0 && (
        <div className="border-l-4 border-saffron bg-saffron-soft px-5 py-4 rounded-sm">
          <p className="font-display font-semibold text-saffron mb-2">
            {failedSources.length} source{failedSources.length > 1 ? "s" : ""} failing
          </p>
          <ul className="text-sm space-y-1">
            {failedSources.map((s) => (
              <li key={s.id} className="font-mono text-xs">
                <span className="text-ink">{s.slug}</span>: <span className="text-ink-soft">{s.last_status}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Sources table */}
      <section>
        <h2 className="font-display text-2xl font-semibold mb-4 border-b border-paper-line pb-3">
          Sources
        </h2>
        <div className="overflow-x-auto">
          <SourcesTable sources={data.sources} />
        </div>
      </section>

      {/* Recent runs */}
      <section>
        <h2 className="font-display text-2xl font-semibold mb-4 border-b border-paper-line pb-3">
          Recent runs
        </h2>
        <div className="overflow-x-auto">
          <RunsTable runs={data.runs} sources={data.sources} />
        </div>
      </section>
    </div>
  );
}

function SourcesTable({ sources }: { sources: SourceOut[] }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-left text-[11px] uppercase tracking-wideish text-ink-muted border-b border-paper-line">
          <th className="py-2 pr-4">Source</th>
          <th className="py-2 pr-4">Type</th>
          <th className="py-2 pr-4">Trust</th>
          <th className="py-2 pr-4">Active</th>
          <th className="py-2 pr-4">Last fetched</th>
          <th className="py-2 pr-4">Last status</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-paper-line/70">
        {sources.map((s) => (
          <tr key={s.id}>
            <td className="py-3 pr-4">
              <p className="font-medium">{s.name}</p>
              <p className="text-xs text-ink-muted font-mono">{s.slug}</p>
            </td>
            <td className="py-3 pr-4 font-mono text-xs">{s.source_type}</td>
            <td className="py-3 pr-4 text-xs">{s.trust_label.replace("_", " ")}</td>
            <td className="py-3 pr-4">
              <span className={`text-xs ${s.active ? "text-green" : "text-ink-muted"}`}>
                {s.active ? "● active" : "○ inactive"}
              </span>
            </td>
            <td className="py-3 pr-4 font-mono text-xs text-ink-muted">{timeAgo(s.last_fetched_at)}</td>
            <td className="py-3 pr-4 font-mono text-xs text-ink-muted">{s.last_status ?? "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function RunsTable({ runs, sources }: { runs: IngestionRunOut[]; sources: SourceOut[] }) {
  const sourceById = Object.fromEntries(sources.map((s) => [s.id, s]));
  if (runs.length === 0) {
    return <p className="text-ink-muted py-6">No runs recorded yet.</p>;
  }
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-left text-[11px] uppercase tracking-wideish text-ink-muted border-b border-paper-line">
          <th className="py-2 pr-4">Source</th>
          <th className="py-2 pr-4">Started</th>
          <th className="py-2 pr-4">Status</th>
          <th className="py-2 pr-4 text-right">Fetched</th>
          <th className="py-2 pr-4 text-right">New</th>
          <th className="py-2 pr-4 text-right">Errors</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-paper-line/70">
        {runs.map((r) => (
          <tr key={r.id}>
            <td className="py-2 pr-4 font-mono text-xs">{sourceById[r.source_id]?.slug ?? `#${r.source_id}`}</td>
            <td className="py-2 pr-4 font-mono text-xs text-ink-muted">{timeAgo(r.started_at)}</td>
            <td className={`py-2 pr-4 text-xs uppercase tracking-wideish font-medium ${STATUS_COLOR[r.status] ?? "text-ink-muted"}`}>
              {r.status}
            </td>
            <td className="py-2 pr-4 text-right font-mono">{r.fetched_count}</td>
            <td className="py-2 pr-4 text-right font-mono">{r.new_count}</td>
            <td className="py-2 pr-4 text-right font-mono">
              {r.error_count > 0 ? <span className="text-saffron">{r.error_count}</span> : "0"}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
