from datetime import datetime
from pathlib import Path
from tempfile import gettempdir

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.agents.drafting_agent import build_annex_iv_sections, draft_annex_iv
from app.agents.report_agent import generate_gap_report
from app.core.config import get_settings
from app.models.schemas import ClauseAssessment, CompanyProfile, GapReport, GapReportRequest

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/gap-report", response_model=GapReport)
def create_gap_report(request: GapReportRequest) -> GapReport:
    assessments = generate_gap_report(request.company_profile, request.user_id)
    report_content = {"assessments": [a.model_dump() for a in assessments]}
    settings = get_settings()

    if not settings.supabase_url:
        from app.rag.local_store import save_report

        row = save_report(request.user_id, request.company_profile.model_dump(), report_content)
        return GapReport(
            id=row["id"],
            company_profile=request.company_profile,
            assessments=assessments,
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    from app.core.supabase_client import get_supabase

    supabase = get_supabase()
    row = (
        supabase.table("compliance_reports")
        .insert(
            {
                "user_id": request.user_id,
                "company_profile": request.company_profile.model_dump(),
                "report_content": report_content,
            }
        )
        .execute()
    )

    return GapReport(
        id=row.data[0]["id"],
        company_profile=request.company_profile,
        assessments=assessments,
        created_at=datetime.fromisoformat(row.data[0]["created_at"]),
    )


def _load_report(report_id: str) -> GapReport:
    settings = get_settings()

    if not settings.supabase_url:
        from app.rag.local_store import get_report

        data = get_report(report_id)
    else:
        from app.core.supabase_client import get_supabase

        supabase = get_supabase()
        row = supabase.table("compliance_reports").select("*").eq("id", report_id).single().execute()
        data = row.data

    if not data:
        raise HTTPException(404, f"Report {report_id} not found")

    return GapReport(
        id=data["id"],
        company_profile=CompanyProfile(**data["company_profile"]),
        assessments=[ClauseAssessment(**a) for a in data["report_content"]["assessments"]],
        created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data["created_at"], str) else data["created_at"],
    )


@router.get("/gap-report/{report_id}/draft-annex-iv/sections")
def draft_annex_iv_sections_endpoint(report_id: str):
    report = _load_report(report_id)
    sections = build_annex_iv_sections(report.company_profile, report)
    return {"title": f"EU AI Act — Annex IV Technical Documentation (draft)", "sections": sections}


@router.post("/gap-report/{report_id}/draft-annex-iv")
def draft_annex_iv_endpoint(report_id: str):
    report = _load_report(report_id)
    output_path = Path(gettempdir()) / f"annex_iv_{report_id}.docx"
    draft_annex_iv(report.company_profile, report, output_path)
    return FileResponse(
        output_path,
        filename=output_path.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
