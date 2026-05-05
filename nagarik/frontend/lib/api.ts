// Typed thin wrapper around the Nagarik backend.
// Server components fetch via these helpers; types mirror app/schemas/__init__.py.

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

// ---- Types ----
export type TrustLabel = "official" | "third_party" | "tentative";

export interface UpdateOut {
  id: number;
  title: string | null;
  document_type: string;
  source_id: number;
  source_name: string | null;
  source_trust_label: TrustLabel | null;
  source_url: string;
  published_at: string | null;
  fetched_at: string;
  confidence_score: number;
  constituency_id: number | null;
  summary_one_line_en: string | null;
  summary_one_line_hi: string | null;
  tags_json: string[] | null;
}

export interface FactOut {
  key: string;
  value: string | null;
  confidence: number;
}

export interface SummaryOut {
  language: string;
  one_line: string | null;
  three_bullets_json: string[] | null;
  why_it_matters: string | null;
  who_is_affected: string | null;
  source_citation: string | null;
  model_used: string;
  generated_at: string;
  confidence_score: number;
}

export interface UpdateDetail extends UpdateOut {
  canonical_url: string | null;
  extracted_text_preview: string | null;
  facts: FactOut[];
  summaries: SummaryOut[];
}

export interface UpdateList {
  items: UpdateOut[];
  total: number;
  page: number;
  page_size: number;
}

export interface ConstituencyOut {
  id: number;
  name: string;
  type: string;
  number: number | null;
  state_id: number;
  district_id: number | null;
}

export interface PoliticianOut {
  id: number;
  name: string;
  party: string | null;
  photo_url: string | null;
  bio: string | null;
  official_links_json: Record<string, unknown> | null;
}

export interface CandidacyOut {
  id: number;
  politician: PoliticianOut;
  constituency_id: number;
  election_year: number;
  status: string;
  affidavit_document_id: number | null;
}

export interface ConstituencyDetail extends ConstituencyOut {
  state: { id: number; name: string; code: string } | null;
  district: { id: number; name: string; state_id: number } | null;
  recent_updates: UpdateOut[];
  candidates: CandidacyOut[];
  top_topics: { id: number; name: string; slug: string; count: number }[];
}

export interface ManifestoItemOut {
  id: number;
  politician_id: number | null;
  party: string | null;
  title: string;
  description: string | null;
  category: string | null;
  target_year: number | null;
  status: string;
  confidence: number;
}

export interface ManifestoProgressOut {
  id: number;
  manifesto_item_id: number;
  document_id: number | null;
  note: string | null;
  status: string;
  recorded_at: string;
}

export interface CandidateDetail {
  politician: PoliticianOut;
  candidacies: CandidacyOut[];
  affidavit: UpdateOut | null;
  manifesto: ManifestoItemOut[];
  progress: ManifestoProgressOut[];
}

export interface FeedbackClusterOut {
  id: number;
  topic_id: number | null;
  constituency_id: number | null;
  summary: string;
  count: number;
  avg_sentiment: number;
  last_updated: string;
}

export interface SourceOut {
  id: number;
  name: string;
  slug: string;
  source_type: string;
  trust_label: TrustLabel;
  base_url: string | null;
  active: boolean;
  last_fetched_at: string | null;
  last_status: string | null;
}

export interface IngestionRunOut {
  id: number;
  source_id: number;
  started_at: string;
  finished_at: string | null;
  status: string;
  fetched_count: number;
  new_count: number;
  error_count: number;
}

export interface IngestionStatusOut {
  runs: IngestionRunOut[];
  sources: SourceOut[];
}

// ---- Fetcher ----
async function get<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    // Force fresh data — civic info should reflect the latest pipeline run.
    cache: "no-store",
    ...init,
  });
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`);
  return res.json() as Promise<T>;
}

// ---- API ----
export const api = {
  updates: (params: Record<string, string | number> = {}) => {
    const q = new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)])
    );
    return get<UpdateList>(`/api/v1/updates?${q.toString()}`);
  },
  update: (id: number) => get<UpdateDetail>(`/api/v1/updates/${id}`),
  constituencies: () => get<ConstituencyOut[]>(`/api/v1/constituencies`),
  constituency: (id: number) => get<ConstituencyDetail>(`/api/v1/constituencies/${id}`),
  candidate: (id: number) => get<CandidateDetail>(`/api/v1/candidates/${id}`),
  search: (q: string) => get<UpdateOut[]>(`/api/v1/search?q=${encodeURIComponent(q)}`),
  sources: () => get<SourceOut[]>(`/api/v1/sources`),
  feedbackClusters: (params: Record<string, string | number> = {}) => {
    const q = new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)])
    );
    return get<FeedbackClusterOut[]>(`/api/v1/feedback?${q.toString()}`);
  },
  submitFeedback: (body: {
    text: string;
    language?: string;
    constituency_id?: number;
    document_id?: number;
    topic_id?: number;
  }) =>
    fetch(`${BASE}/api/v1/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then((r) => {
      if (!r.ok) throw new Error(`POST /feedback failed: ${r.status}`);
      return r.json();
    }),
  ingestionStatus: (token: string) =>
    get<IngestionStatusOut>(`/api/v1/admin/ingestion-status`, {
      headers: { "X-Admin-Token": token },
    }),
};

// ---- Formatters ----
export function timeAgo(iso: string | null | undefined): string {
  if (!iso) return "—";
  const ms = Date.now() - new Date(iso).getTime();
  const s = Math.round(ms / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.round(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.round(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.round(h / 24);
  return `${d}d ago`;
}

export function formatDocType(t: string): string {
  return t.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
