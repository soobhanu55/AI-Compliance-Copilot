"""Gap-report agent: retrieves relevant regulation clauses for a company profile, scores each
with the compliance-relevance classifier, and — for clauses classified as applicable — checks
the user's own uploaded company documents for supporting evidence.
"""

from app.agents import classifier as compliance_classifier
from app.models.schemas import ClauseAssessment, CompanyProfile
from app.rag.retriever import retrieve

# Heuristic cosine-similarity cutoffs for the e5 embeddings used by app.rag.embeddings.
# Not validated against a labeled evidence-matching set — same "disclosed, not proven" spirit
# as the classifier's confidence threshold. Tune once real usage data exists.
EVIDENCE_FOUND_THRESHOLD = 0.85
PARTIAL_MATCH_THRESHOLD = 0.65
EVIDENCE_EXCERPT_CHARS = 220


def _profile_to_text(profile: CompanyProfile) -> str:
    # Must match pytorch_classifier/scripts/build_labeled_dataset.py's _profile_text() —
    # the classifier was trained on this exact format, including the name/notes fields.
    ai_systems = ", ".join(profile.ai_system_descriptions) or "none"
    vendors = ", ".join(profile.third_party_vendors) or "none"
    return (
        f"{profile.name}: {profile.sector} company, {profile.employee_count} employees. "
        f"Uses AI systems: {profile.uses_ai_systems}. AI systems: {ai_systems}. "
        f"Third-party vendors: {vendors}. Notes: {profile.notes or 'none'}."
    )


def _match_evidence(clause_text: str, user_id: str) -> tuple[str, str | None, str | None]:
    """Checks the user's own uploaded company_policy documents for evidence supporting an
    applicable clause. Returns (evidence_status, excerpt, source_filename) — excerpt/source
    are only populated when status isn't "gap", matching the reference UI (a gap shows no
    quoted text, just the absence).
    """
    hits = retrieve(clause_text, user_id=user_id, doc_type="company_policy", top_k=1)
    if not hits:
        return "gap", None, None

    hit = hits[0]
    score = hit.score if hit.score is not None else 0.0
    source = hit.metadata.get("filename")

    if score >= EVIDENCE_FOUND_THRESHOLD:
        return "evidence_found", hit.content[:EVIDENCE_EXCERPT_CHARS], source
    if score >= PARTIAL_MATCH_THRESHOLD:
        return "partial_match", hit.content[:EVIDENCE_EXCERPT_CHARS], source
    return "gap", None, None


def generate_gap_report(profile: CompanyProfile, user_id: str) -> list[ClauseAssessment]:
    profile_text = _profile_to_text(profile)
    clauses = retrieve(profile_text, user_id="regulation-corpus", doc_type="regulation", top_k=20)

    if not compliance_classifier.is_available():
        return [
            ClauseAssessment(
                regulation=chunk.metadata.get("regulation", "unknown"),
                article=chunk.metadata.get("article", "unknown"),
                article_title=chunk.metadata.get("article_title", ""),
                verdict="needs_human_review",
                confidence=0.0,
                rationale="Classifier checkpoint not found — run pytorch_classifier/scripts/train.py first.",
            )
            for chunk in clauses
        ]

    assessments = []
    for chunk in clauses:
        verdict, confidence = compliance_classifier.classify(chunk.content, profile_text)

        evidence_status = evidence_excerpt = evidence_source = None
        if verdict == "applicable":
            evidence_status, evidence_excerpt, evidence_source = _match_evidence(chunk.content, user_id)

        assessments.append(
            ClauseAssessment(
                regulation=chunk.metadata.get("regulation", "unknown"),
                article=chunk.metadata.get("article", "unknown"),
                article_title=chunk.metadata.get("article_title", ""),
                verdict=verdict,
                confidence=confidence,
                rationale=(
                    f"Proof-of-concept classifier prediction (confidence {confidence:.0%}). "
                    "Not a substitute for legal review — see pytorch_classifier/README.md."
                ),
                evidence_status=evidence_status,
                evidence_excerpt=evidence_excerpt,
                evidence_source=evidence_source,
            )
        )
    return assessments
