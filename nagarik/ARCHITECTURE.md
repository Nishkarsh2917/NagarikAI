# Nagarik — Architecture

A nonpartisan civic intelligence platform for India. This document is the design contract that the code in `backend/` and `frontend/` implements. Read this first.

---

## 1. Folder Structure

```
nagarik/
├── ARCHITECTURE.md              ← you are here
├── README.md                    ← setup & run instructions
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── app/
│   │   ├── main.py              ← FastAPI app entry
│   │   ├── config.py            ← env-driven settings
│   │   ├── db.py                ← SQLAlchemy engine/session
│   │   ├── storage.py           ← raw-payload object store (fs / S3-ready)
│   │   ├── seed.py              ← loads /data/seed JSON into DB
│   │   ├── scheduler.py         ← APScheduler — runs pipeline at 00:00 IST
│   │   ├── models/              ← SQLAlchemy ORM (one file per aggregate)
│   │   ├── schemas/             ← Pydantic response/request models
│   │   ├── api/                 ← FastAPI routers (one file per resource)
│   │   ├── ingestion/
│   │   │   ├── pipeline.py      ← orchestrator (idempotent)
│   │   │   ├── parsers.py       ← HTML/PDF/OCR text extraction
│   │   │   ├── classifier.py    ← document type detection
│   │   │   ├── extractor.py     ← who/what/where/when/numbers
│   │   │   ├── summarizer.py    ← 1-line, 3-bullet, why/who, EN+HI
│   │   │   ├── mapper.py        ← constituency/topic mapping
│   │   │   ├── dedupe.py        ← checksum-based
│   │   │   └── adapters/        ← per-source fetchers (pluggable)
│   │   └── ai/
│   │       ├── client.py        ← LLM abstraction (Anthropic + fallback)
│   │       ├── prompts.py       ← per-step prompts (JSON-mode)
│   │       └── rule_based.py    ← deterministic no-key fallback
│   └── tests/
├── frontend/
│   ├── package.json
│   ├── app/                     ← Next.js App Router
│   │   ├── layout.tsx           ← global shell, fonts
│   │   ├── page.tsx             ← Home
│   │   ├── updates/[id]/        ← Document detail
│   │   ├── constituencies/      ← list + [id] detail
│   │   ├── candidates/[id]/
│   │   ├── feedback/
│   │   └── admin/               ← ingestion status
│   ├── components/              ← Header, UpdateCard, SourceLabel, ConfidenceBadge…
│   └── lib/api.ts               ← typed fetch wrapper
└── data/
    ├── seed/                    ← bootstrap JSON
    └── storage/                 ← raw HTML/PDF snapshots (gitignored)
```

Rule: ingestion never imports from `api/`, and `api/` never imports from `ingestion/adapters/`. They share `models/` and `db.py` only.

---

## 2. Database Schema

Relational. One row per real-world thing. Everything trust-bearing carries `confidence_score`, `fetched_at`, and a `source_id`. SQLite for the demo, Postgres-ready (no SQLite-only types used).

### Core entities

**source** — every place we fetch from
| field | type | notes |
|---|---|---|
| id | int PK | |
| name | str | "Press Information Bureau" |
| slug | str unique | "pib" |
| source_type | enum | `central_gov` / `parliament` / `eci` / `open_data` / `local_gov` / `local_news` |
| trust_label | enum | `official` / `third_party` / `tentative` |
| base_url | str | |
| adapter_key | str | matches a class in `ingestion/adapters/` |
| config_json | json | adapter-specific (feed URL, selectors…) |
| active | bool | |
| last_fetched_at | datetime | |
| last_status | str | `ok` / `error: <msg>` |

**document** — one fetched item
| field | type | notes |
|---|---|---|
| id | int PK | |
| source_id | FK → source | |
| source_url | str | original URL |
| canonical_url | str | post-redirect/cleaned |
| title | str | |
| document_type | enum | `press_release` / `policy` / `budget` / `bill` / `affidavit` / `constituency_update` / `local_update` / `feedback` / `unknown` |
| raw_storage_path | str | path in object store |
| extracted_text | text | parsed plain text |
| language | str | ISO-639-1 |
| published_at | datetime | from source |
| fetched_at | datetime | when we pulled it |
| updated_at | datetime | last reprocess |
| checksum | str unique | sha256 of normalized payload — dedup key |
| status | enum | `fetched` / `parsed` / `classified` / `summarized` / `published` / `failed` |
| confidence_score | float | 0–1, propagated from worst step |
| state_id, district_id, constituency_id | FK | nullable — set by mapper |
| canonical_url | str | |
| tags_json | json | topic tags |

**document_snapshot** — version history. We never mutate raw; we add a new snapshot when the source changes.
| id, document_id FK, fetched_at, raw_storage_path, checksum |

**extracted_fact** — structured key-value. One row per (doc, key).
| id, document_id, key, value, confidence, source_span (offset+len in extracted_text) |

**summary** — one row per (doc, language, variant)
| id, document_id, language (`en`/`hi`), one_line, three_bullets_json, why_it_matters, who_is_affected, source_citation, model_used, generated_at, confidence_score |

### Geography
**state**, **district**, **constituency** — standard hierarchy. `constituency.type` ∈ `{lok_sabha, vidhan_sabha}`. `pc_number` / `ac_number` ints.

### Politics
**politician** — id, name, party, photo_url, bio_json, official_links_json
**candidacy** — politician_id, constituency_id, election_year, status, affidavit_document_id (FK → document)
**manifesto_item** — politician_id (or party_id), title, description, category, target_year, status (`promised`/`in_progress`/`achieved`/`broken`/`unknown`), confidence
**manifesto_progress_update** — manifesto_item_id, document_id, note, status, recorded_at

### Citizen voice
**topic** — id, name, slug, parent_id (self-FK for hierarchy)
**citizen_feedback** — id, constituency_id (nullable), document_id (nullable), topic_id (nullable), text, language, sentiment (`-1..1`), submitted_at, ip_hash, status (`pending`/`approved`/`rejected`)
**feedback_cluster** — id, topic_id, constituency_id, summary, count, last_updated, sample_feedback_ids_json

### Operations
**audit_log** — id, actor (`pipeline`/`api`/`admin`), action, entity_type, entity_id, payload_json, at
**ingestion_run** — id, source_id, started_at, finished_at, status, fetched_count, new_count, error_count, log_text

Indexes worth calling out: `document(checksum)` unique, `document(fetched_at desc)`, `document(constituency_id, fetched_at desc)`, `citizen_feedback(constituency_id, topic_id)`, `extracted_fact(document_id, key)`. Full-text on `document.extracted_text` and `summary.one_line` (Postgres tsvector; SQLite uses LIKE in MVP).

---

## 3. API Routes

All under `/api/v1`. JSON only. Read endpoints are public; `POST /feedback` is rate-limited; `/admin/*` is token-gated.

| Method | Path | Purpose |
|---|---|---|
| GET | `/updates` | paginated, filters: `constituency_id, source_id, document_type, from, to, q` |
| GET | `/updates/{id}` | full detail incl. extracted facts, summary, source link |
| GET | `/constituencies` | list with current counts |
| GET | `/constituencies/{id}` | profile + recent updates + candidates + top issues |
| GET | `/candidates/{id}` | profile + affidavits + manifesto + progress |
| GET | `/manifestos` | filters: `politician_id, party, status` |
| GET | `/feedback` | aggregated clusters, filters: `constituency_id, topic_id` |
| POST | `/feedback` | submit citizen feedback (validated, queued for moderation) |
| GET | `/search?q=` | full-text across docs + summaries |
| GET | `/sources` | list with last-fetch status |
| GET | `/admin/ingestion-status` | runs, failures, retry button (requires `X-Admin-Token`) |
| POST | `/admin/run-ingestion` | manual trigger (requires token) |

Response envelope is flat: lists return `{items, total, page, page_size}`; details return the entity. Every public summary response includes `source_url`, `source_label`, `fetched_at`, `confidence_score`.

---

## 4. Background Job Flow

Single daily cron at **00:00 IST** via APScheduler. Idempotent — safe to re-run.

```
                         ┌──────────────────┐
                         │  Scheduler Tick  │  (00:00 IST or manual)
                         └────────┬─────────┘
                                  │
                                  ▼
                  ┌──────────────────────────────┐
                  │ for each active Source       │
                  │  → IngestionRun row created  │
                  └──────────────┬───────────────┘
                                 │  (per-source, isolated try/except)
                                 ▼
        ┌────────────┐    ┌──────────────┐    ┌──────────────┐
        │ 1. Fetch   │ →  │ 2. Parse     │ →  │ 3. Dedupe    │
        │ adapter()  │    │ html/pdf/OCR │    │ checksum     │
        └────────────┘    └──────────────┘    └──────┬───────┘
                                                     │ new
                                                     ▼
        ┌────────────┐    ┌──────────────┐    ┌──────────────┐
        │ 6. Map     │ ←  │ 5. Summarize │ ←  │ 4. Classify  │
        │ geo/topic  │    │ EN + HI      │    │ + extract    │
        └─────┬──────┘    └──────────────┘    └──────────────┘
              │
              ▼
        ┌────────────────────────────┐
        │ 7. Persist + status=publish│
        │ + AuditLog                 │
        └────────────────────────────┘
```

**Failure semantics:**
- Each source runs in its own try/except; one bad source cannot fail the run.
- Each step is its own try/except; partial documents land at the latest successful `status` and stay reprocessable.
- Network calls have backoff (3 tries, exp).
- Raw payload is saved *before* any parsing so we can reprocess later with better prompts.

**Idempotency guarantees:**
- `document.checksum` is unique → re-fetching the same payload is a no-op insert.
- Snapshots are append-only → a changed payload creates a new snapshot, the canonical document row points to the latest.
- Summary regeneration is keyed on `(document_id, language, model_version)` — bumping the version invalidates and re-runs.

---

## 5. Source Adapters

Plug-in pattern. Every adapter implements the same `BaseAdapter` interface so adding a source is a config + class change, not a pipeline change.

```python
class BaseAdapter:
    key: str                                           # matches source.adapter_key
    def fetch(self, source: Source) -> list[FetchedItem]: ...

class FetchedItem(TypedDict):
    source_url: str
    title: str | None
    raw_bytes: bytes
    content_type: str        # text/html, application/pdf, …
    published_at: datetime | None
```

**MVP adapters (3 official + 1 local + mock):**

| Key | Source | Type | Method |
|---|---|---|---|
| `pib` | Press Information Bureau | central_gov | RSS feed + per-release HTML scrape |
| `prsindia` | PRS India (Bills/Acts) | parliament (third-party but high-trust) | RSS + PDF download |
| `eci_affidavits` | ECI MyNeta affidavits (mirror) | eci | JSON / CSV |
| `delhi_gov_local` | Delhi government press releases | local_gov | HTML list page |
| `mock` | seed JSON | demo | reads `data/seed/sample_documents.json` |

The MVP ships with `mock` enabled by default so the pipeline runs offline. Real adapters are scaffolded with the correct shape; flipping `active=true` in the DB plus implementing the `fetch()` body activates them.

---

## 6. UI Page Map

Next.js App Router. Server components for read pages; client components only where interactivity needs it (filters, search, feedback form).

```
/                                    Home
  ├── hero with search
  ├── "Today on Nagarik" — recent updates (from /api/updates)
  ├── Featured constituency strip
  └── Latest manifesto/affidavit briefs

/updates/[id]                        Document detail
  ├── source badge + trust label + fetched_at + confidence
  ├── 1-line summary (EN | HI toggle)
  ├── 3-bullet explanation
  ├── why this matters / who is affected
  ├── extracted facts table
  ├── original source link (always)
  └── extracted text preview (collapsed)

/constituencies                      Constituency index (filterable)
/constituencies/[id]                 Constituency profile
  ├── top issues (from feedback clusters)
  ├── recent gov updates mapped here
  ├── candidates list
  └── feedback widget (links to /feedback)

/candidates/[id]                     Candidate profile
  ├── basic info + party
  ├── linked ECI affidavit document
  ├── manifesto promises with status pills
  └── progress timeline

/feedback                            Aggregated citizen feedback
  ├── filter: constituency, topic
  ├── clusters with cluster summary + sentiment + count
  ├── recurring complaints panel
  └── submit form

/admin                               Token-gated
  ├── recent ingestion runs (status, counts)
  ├── failed sources highlighted
  ├── per-source last-success timestamp
  └── manual "Run now" button
```

Trust UI elements present on every public summary card:
- **Source label** chip — "Official" / "Third-party" / "Tentative"
- **Fetched** timestamp — "fetched 6h ago"
- **Confidence** dot — green/amber/grey with tooltip
- **Source link** — outbound icon, always

---

## 7. AI Pipeline Rules (codified)

The prompt insists, and the code enforces:

1. **No mega-prompt.** Five separate, narrow LLM calls — `classify`, `extract`, `summarize_en`, `summarize_hi`, `map_topic`. Each lives in `ai/prompts.py`.
2. **JSON-mode for extraction.** All extract/classify prompts demand `{...}` output and are parsed strictly; on parse failure the field is `null` and `confidence` drops, but the doc still publishes.
3. **No invention.** Prompts say "if not present in the source, return null". Summaries are constrained to "use only facts from the provided text".
4. **Confidence propagation.** Each step returns its own confidence; the document's final score is `min` of all steps. Below threshold → `tentative` label in UI.
5. **Reprocessable.** Raw is preserved → bumping a model/prompt version triggers re-summarization without re-fetching.
6. **Offline default.** If `ANTHROPIC_API_KEY` is unset, `ai/rule_based.py` provides deterministic fallbacks (first-sentence summary, regex extraction) so the demo always runs.
