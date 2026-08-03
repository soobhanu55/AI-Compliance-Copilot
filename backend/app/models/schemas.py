from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


class ChatRequest(BaseModel):
    user_id: str
    message: str
    language: Literal["de", "en"] = "en"


class Citation(BaseModel):
    regulation: str  # e.g. "AI Act"
    article: str  # e.g. "Article 6(2)"
    chunk_id: str
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]


class CompanyProfile(BaseModel):
    name: str
    sector: str
    employee_count: int
    uses_ai_systems: bool
    ai_system_descriptions: list[str] = []
    third_party_vendors: list[str] = []
    notes: str = ""


class ClauseAssessment(BaseModel):
    regulation: str
    article: str
    article_title: str = ""
    verdict: Literal["applicable", "not_applicable", "needs_human_review"]
    confidence: float
    rationale: str
    # Evidence matching against the user's own uploaded documents — only computed for
    # verdict == "applicable" (see report_agent.py). None means "not checked", not "no evidence".
    evidence_status: Literal["evidence_found", "partial_match", "gap"] | None = None
    evidence_excerpt: str | None = None
    evidence_source: str | None = None


class GapReportRequest(BaseModel):
    user_id: str
    company_profile: CompanyProfile


class GapReport(BaseModel):
    id: str
    company_profile: CompanyProfile
    assessments: list[ClauseAssessment]
    created_at: datetime


class DocumentChunk(BaseModel):
    id: str
    document_id: str
    content: str
    metadata: dict[str, Any] = {}
    score: float | None = None  # cosine similarity to the query, when the backend provides one
