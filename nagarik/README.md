# Nagarik

A nonpartisan civic intelligence platform for India. Ingests official Indian
government and election-related sources, decodes dense documents into plain-language
summaries, maps them to constituencies and issues, and presents them in a citizen-first
portal with full source traceability.

> **One-line pitch:** Government decisions, decoded for the people they affect — every claim links back to its source.

The complete design is documented in [`ARCHITECTURE.md`](./ARCHITECTURE.md). Read that first.

---

## What's in the box

```
nagarik/
├── ARCHITECTURE.md          design contract (folder structure, schema, API, job flow, UI map)
├── README.md                you are here
├── backend/                 FastAPI + SQLAlchemy + APScheduler
│   ├── app/
│   │   ├── main.py          FastAPI entrypoint
│   │   ├── models/          ORM (one file per aggregate)
│   │   ├── api/             REST routers (one file per resource)
│   │   ├── ingestion/       pipeline + adapters (pluggable)
│   │   └── ai/              LLM abstraction with no-key fallback
│   └── tests/
├── frontend/                Next.js 14 (App Router, server components)
└── data/
    ├── seed/                JSON bootstrap data
    └── storage/             raw HTML/PDF snapshots (gitignored)
```

---

## Quick start (zero-config local dev)

The MVP runs **without** a database server, message broker, or LLM API key.
SQLite + APScheduler + a deterministic fallback summarizer keep first-time setup small.

### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

On first boot the app:
- creates `nagarik.db` (SQLite),
- seeds reference data (states, constituencies, sources, fictional politicians/manifestos),
- starts the daily scheduler at 00:00 IST.

The first request to the home page won't have content until you trigger ingestion. You can:

```bash
# inside backend/, with the venv active
python -c "from app.ingestion.pipeline import run_all; print(run_all())"
```

…or use the admin UI ([Admin section](#admin)).

Verify it works:

```bash
curl http://localhost:8000/api/v1/updates | python -m json.tool
curl http://localhost:8000/healthz
```

OpenAPI docs are at `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open <http://localhost:3000>.

---

## Adding the LLM (optional but recommended)

Without an API key the system uses a rule-based fallback for classification, extraction,
summarization, and topic mapping. Quality is intentionally modest and confidence stays
low so the UI flags it as `tentative`.

To switch on Claude:

```bash
# backend/.env
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-haiku-4-5-20251001
```

Restart the backend. New documents will be processed by the LLM. Old ones can be
reprocessed by clearing the DB and re-running ingestion (raw payloads are preserved
in `data/storage/` so re-fetching isn't necessary).

---

## Admin

The admin page (`/admin`) is gated by a token sent as `X-Admin-Token`.
Default dev token: `dev-admin-token-change-me` — **change it** in production via the
`ADMIN_TOKEN` env var.

From the admin panel you can:
- view recent ingestion runs (status, fetched/new/error counts),
- spot failing sources,
- manually trigger an ingestion run.

---

## Adding a new source

The pipeline is plugin-shaped. Adding a source is two changes:

1. **Implement an adapter** in `backend/app/ingestion/adapters/`:
   ```python
   from app.ingestion.adapters.base import BaseAdapter, FetchedItem

   class MySourceAdapter(BaseAdapter):
       key = "my_source"
       def fetch(self, source) -> list[FetchedItem]:
           # return a list of FetchedItem dicts
           ...
   ```
   Register it in `adapters/__init__.py`.

2. **Add a row to `data/seed/sources.json`** with `adapter_key="my_source"`, the URL,
   and any per-source config in `config_json` (e.g. RSS feed URL, CSS selectors).
   Set `"active": true`.

That's it. The next ingestion tick will fetch, parse, classify, summarize, map, and
publish documents from your new source.

---

## How the pipeline works

End-to-end flow per document (see `ARCHITECTURE.md` §4 for the diagram):

1. **Fetch** — adapter returns raw bytes.
2. **Persist raw** — saved to object store before any processing, so future re-runs with better prompts don't need to re-fetch.
3. **Parse** — HTML/PDF → plain text. Language detected (en/hi).
4. **Dedupe** — by SHA-256 of raw payload. Re-running the cron is safe.
5. **Classify** — document type via narrow JSON-output prompt.
6. **Extract** — structured facts (who/what/where/when/numbers/deadlines).
7. **Summarize** — 1-line, 3-bullet, why-it-matters, who-is-affected. EN + HI.
8. **Map** — constituency, district, state, topic tags.
9. **Publish** — status = `published`, audit-logged.

Each step is wrapped in its own try/except. Partial failures land at the latest
successful status and stay reprocessable. The minimum confidence across steps is the
document's overall confidence — which drives the UI's "tentative" labelling.

**AI rules baked in:**
- No mega-prompt — five separate, narrow calls.
- All extraction prompts demand strict JSON.
- "If not present in the source, return null." No invention.
- Confidence is self-reported per step.
- Without an API key, deterministic fallbacks run instead.

---

## Production notes (what to swap)

The MVP uses zero-config building blocks. For production, the abstractions are in place
to swap each piece without touching domain code:

| MVP | Production swap | Where |
|---|---|---|
| SQLite | Postgres | Set `DATABASE_URL=postgresql+psycopg://…` in `.env` |
| Local filesystem object store | S3 | Implement `ObjectStore` Protocol in `app/storage.py` |
| APScheduler in-process | Celery + Redis, or managed cron + worker | Replace `app/scheduler.py` |
| LIKE-based search | Postgres tsvector / pgvector | Add a GIN index, replace `api/search.py` query |
| In-process rate limiting | Redis-backed slowapi | Set `SLOWAPI_STORAGE_URI` |
| Token auth on admin | Real auth (JWT, SSO) | Replace `require_admin` in `api/admin.py` |

**Do not deploy with the dev admin token.**

---

## Trust & safety

The architecture treats trust as a UI-visible property, not an afterthought:

- Every public summary card shows: source name, trust label
  (`Official` / `Third-party` / `Tentative`), fetched-at timestamp, and confidence
  indicator (high/moderate/low).
- The original source URL is always reachable from a document detail page.
- Raw payloads are versioned via `document_snapshot` — when a source page changes
  we add a new snapshot rather than mutate.
- All summaries are constrained to facts present in the extracted text. Where the
  extractor returns null, the UI omits the field rather than guesses.
- Audit logs (`audit_logs` table) record every pipeline action for inspection.
- Citizen feedback is rate-limited per IP (hashed, never stored raw) and held in a
  pending status until moderation.

---

## Tests

```bash
cd backend
pip install pytest
pytest -q
```

The included end-to-end test seeds the DB, runs the pipeline against the mock adapter,
and verifies that documents land at `status=published` with at least one summary —
plus that re-running the pipeline is idempotent.

---

## A note on seed data

The seed JSON files in `data/seed/` are **fictional demonstration data**:

- The "Demo Candidate" politicians are placeholders. Real ECI affidavit data plugs in
  via the `eci_affidavits` adapter — provide a manifest URL in its `config_json`.
- The mock-demo source produces synthetic press releases written for this demo. Real
  sources (`pib`, `prsindia`, `delhi_gov_local`) are scaffolded but inactive by default.
  Activate them by setting `active: true` in the DB or seed file.

This keeps the demo runnable offline and avoids any appearance of partisanship or
misattribution.

---

## License & nonpartisan commitment

Nagarik is a citizen-first tool. The architecture, prompts, and UI copy are written
to be neutral. Summaries are constrained to source facts. Confidence is shown openly.
This repository ships with no editorial position on any political party, candidate,
or policy.
