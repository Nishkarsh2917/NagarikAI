"""Pydantic schemas for API I/O. Kept in one file for an MVP — split later by resource."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


# ---- Source ----
class SourceOut(ORMModel):
    id: int
    name: str
    slug: str
    source_type: str
    trust_label: str
    base_url: str | None
    active: bool
    last_fetched_at: datetime | None
    last_status: str | None


# ---- Geography ----
class StateOut(ORMModel):
    id: int
    name: str
    code: str


class DistrictOut(ORMModel):
    id: int
    name: str
    state_id: int


class ConstituencyOut(ORMModel):
    id: int
    name: str
    type: str
    number: int | None
    state_id: int
    district_id: int | None


class ConstituencyDetail(ConstituencyOut):
    state: StateOut | None = None
    district: DistrictOut | None = None
    recent_updates: list["UpdateOut"] = []
    candidates: list["CandidacyOut"] = []
    top_topics: list[dict[str, Any]] = []


# ---- Document / Updates ----
class FactOut(ORMModel):
    key: str
    value: str | None
    confidence: float


class SummaryOut(ORMModel):
    language: str
    one_line: str | None
    three_bullets_json: list[str] | None
    why_it_matters: str | None
    who_is_affected: str | None
    source_citation: str | None
    model_used: str
    generated_at: datetime
    confidence_score: float


class UpdateOut(ORMModel):
    """Lightweight card-shape for list views."""
    id: int
    title: str | None
    document_type: str
    source_id: int
    source_name: str | None = None
    source_trust_label: str | None = None
    source_url: str
    published_at: datetime | None
    fetched_at: datetime
    confidence_score: float
    constituency_id: int | None
    summary_one_line_en: str | None = None
    summary_one_line_hi: str | None = None
    tags_json: list[str] | None = None


class UpdateDetail(UpdateOut):
    extracted_text_preview: str | None = None
    facts: list[FactOut] = []
    summaries: list[SummaryOut] = []
    canonical_url: str | None = None


class UpdateList(BaseModel):
    items: list[UpdateOut]
    total: int
    page: int
    page_size: int


# ---- Politicians / Manifestos ----
class PoliticianOut(ORMModel):
    id: int
    name: str
    party: str | None
    photo_url: str | None
    bio: str | None
    official_links_json: dict | None


class CandidacyOut(ORMModel):
    id: int
    politician: PoliticianOut
    constituency_id: int
    election_year: int
    status: str
    affidavit_document_id: int | None


class ManifestoItemOut(ORMModel):
    id: int
    politician_id: int | None
    party: str | None
    title: str
    description: str | None
    category: str | None
    target_year: int | None
    status: str
    confidence: float


class ManifestoProgressOut(ORMModel):
    id: int
    manifesto_item_id: int
    document_id: int | None
    note: str | None
    status: str
    recorded_at: datetime


class CandidateDetail(BaseModel):
    politician: PoliticianOut
    candidacies: list[CandidacyOut]
    affidavit: UpdateOut | None = None
    manifesto: list[ManifestoItemOut]
    progress: list[ManifestoProgressOut]


# ---- Feedback ----
class FeedbackIn(BaseModel):
    text: str = Field(..., min_length=4, max_length=2000)
    language: str = "en"
    constituency_id: int | None = None
    document_id: int | None = None
    topic_id: int | None = None


class FeedbackOut(ORMModel):
    id: int
    text: str
    language: str
    sentiment: float
    constituency_id: int | None
    document_id: int | None
    topic_id: int | None
    submitted_at: datetime
    status: str


class FeedbackClusterOut(ORMModel):
    id: int
    topic_id: int | None
    constituency_id: int | None
    summary: str
    count: int
    avg_sentiment: float
    last_updated: datetime


# ---- Admin ----
class IngestionRunOut(ORMModel):
    id: int
    source_id: int
    started_at: datetime
    finished_at: datetime | None
    status: str
    fetched_count: int
    new_count: int
    error_count: int


class IngestionStatusOut(BaseModel):
    runs: list[IngestionRunOut]
    sources: list[SourceOut]


# Resolve forward refs
ConstituencyDetail.model_rebuild()
