"""Builds pytorch_classifier/data/labeled_pairs.csv.

Methodology (documented here and in the model card — read before trusting this data):
this is NOT crowd-sourced or independently-verified ground truth. Each of the 35 curated
articles below was read in full (from data_pipeline/regulations/*_articles.json, the real
EUR-Lex text) and assigned to one of 22 "obligation categories" (e.g. "ai_high_risk_provider
_obligation", "nis2_risk_mgmt", "csrd_reporting_large"). For each of the 4 synthetic SME
profiles, every category was then given one applicability verdict + a written rationale,
reasoned from that profile's stated facts (sector, employee count, AI systems, vendors).

That is: labels are applied at the (profile x category) level, not the (profile x article)
level — every article sharing a category gets the same verdict from a given profile, because
the underlying applicability question (e.g. "is this AI system high-risk?") doesn't change
between Article 9 and Article 15. This is closer to rule-based weak supervision than to
per-row human annotation, and is disclosed as such — see pytorch_classifier/README.md.

Run:
    python build_labeled_dataset.py
"""

import csv
import json
from pathlib import Path

REGULATIONS_DIR = Path(__file__).parent.parent.parent / "data_pipeline" / "regulations"
PROFILES_PATH = Path(__file__).parent.parent.parent / "data_pipeline" / "synthetic_profiles" / "profiles.json"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "labeled_pairs.csv"

# (regulation file stem, article heading as it appears in the source JSON, category)
CURATED_ARTICLES = [
    ("ai_act", "Article\xa04", "ai_general_obligation_if_ai_user"),
    ("ai_act", "Article\xa05", "ai_prohibited_practices"),
    ("ai_act", "Article\xa06", "ai_high_risk_classification"),
    ("ai_act", "Article\xa08", "ai_high_risk_provider_obligation"),
    ("ai_act", "Article\xa09", "ai_high_risk_provider_obligation"),
    ("ai_act", "Article\xa010", "ai_high_risk_provider_obligation"),
    ("ai_act", "Article\xa011", "ai_high_risk_provider_obligation"),
    ("ai_act", "Article\xa012", "ai_high_risk_provider_obligation"),
    ("ai_act", "Article\xa013", "ai_high_risk_provider_obligation"),
    ("ai_act", "Article\xa014", "ai_high_risk_provider_obligation"),
    ("ai_act", "Article\xa015", "ai_high_risk_provider_obligation"),
    ("ai_act", "Article\xa016", "ai_high_risk_provider_obligation"),
    ("ai_act", "Article\xa017", "ai_high_risk_provider_obligation"),
    ("ai_act", "Article\xa072", "ai_high_risk_provider_obligation"),
    ("ai_act", "Article\xa073", "ai_high_risk_provider_obligation"),
    ("ai_act", "Article\xa021", "ai_high_risk_provider_obligation"),
    ("ai_act", "Article\xa025", "ai_high_risk_provider_obligation"),
    ("ai_act", "Article\xa043", "ai_high_risk_provider_obligation"),
    ("ai_act", "Article\xa049", "ai_high_risk_provider_obligation"),
    ("ai_act", "Article\xa026", "ai_high_risk_deployer_obligation"),
    ("ai_act", "Article\xa027", "ai_high_risk_deployer_obligation"),
    ("ai_act", "Article\xa050", "ai_transparency_limited_risk"),
    ("ai_act", "Article\xa053", "ai_gpai_provider"),
    ("ai_act", "Article\xa062", "ai_sme_support"),
    ("nis2", "Article\xa03", "nis2_scope"),
    ("nis2", "Article\xa026", "nis2_scope"),
    ("nis2", "Article\xa020", "nis2_governance"),
    ("nis2", "Article\xa021", "nis2_risk_mgmt"),
    ("nis2", "Article\xa022", "nis2_risk_mgmt"),
    ("nis2", "Article\xa023", "nis2_reporting"),
    ("nis2", "Article\xa024", "nis2_certification"),
    ("nis2", "Article\xa025", "nis2_certification"),
    ("nis2", "Article\xa027", "nis2_registration"),
    ("nis2", "Article\xa029", "nis2_info_sharing_voluntary"),
    ("nis2", "Article\xa030", "nis2_info_sharing_voluntary"),
    ("nis2", "Article\xa032", "nis2_enforcement_essential"),
    ("nis2", "Article\xa033", "nis2_enforcement_important"),
    ("csrd", "‘Article\xa019a", "csrd_reporting_large"),
    ("csrd", "‘Article\xa029a", "csrd_reporting_group"),
    ("csrd", "Article\xa029b", "csrd_reporting_standards"),
    ("csrd", "Article\xa029c", "csrd_reporting_sme_voluntary"),
    ("csrd", "Article\xa040a", "csrd_third_country"),
    ("csrd", "Article\xa040b", "csrd_third_country"),
    ("csrd", "Article\xa040c", "csrd_third_country"),
    ("csrd", "‘Article\xa026a", "csrd_assurance"),
    ("csrd", "‘Article\xa027a", "csrd_assurance"),
    ("csrd", "‘Article\xa028a", "csrd_assurance"),
]

# profile_name -> {category: (label, rationale)}
PROFILE_LABELS: dict[str, dict[str, tuple[str, str]]] = {
    "RouteWise Logistics Software GmbH": {
        "ai_general_obligation_if_ai_user": ("applicable", "Uses AI systems in a business context; the AI-literacy obligation applies to providers and deployers regardless of risk classification."),
        "ai_prohibited_practices": ("not_applicable", "No use of subliminal manipulation, biometric categorisation, social scoring, or other prohibited practices; route optimization and demand forecasting are not compliance-relevant here."),
        "ai_high_risk_classification": ("needs_human_review", "Whether route optimization for a company's own delivery fleet counts as a safety component in the management and operation of critical infrastructure under Annex III is genuinely unsettled; requires a documented classification decision."),
        "ai_high_risk_provider_obligation": ("needs_human_review", "High-risk provider obligations only attach if the Article 6/Annex III classification resolves to high-risk; that classification is undetermined for this system."),
        "ai_high_risk_deployer_obligation": ("needs_human_review", "Same classification uncertainty applies on the deployer side."),
        "ai_transparency_limited_risk": ("not_applicable", "Neither system generates synthetic content, deep fakes, or interacts conversationally with end users; the relevant transparency triggers do not appear to apply."),
        "ai_gpai_provider": ("not_applicable", "RouteWise builds narrow, task-specific models; it is not a provider of general-purpose AI models."),
        "ai_sme_support": ("applicable", "RouteWise is an SME (45 employees); SME support measures apply."),
        "nis2_scope": ("needs_human_review", "RouteWise is a logistics software vendor, not itself a courier/postal operator; whether it qualifies as an important entity under the postal-and-courier or digital-infrastructure categories depends on facts not stated in the profile."),
        "nis2_governance": ("needs_human_review", "Depends on the unresolved entity-scope question above."),
        "nis2_risk_mgmt": ("needs_human_review", "Depends on the unresolved entity-scope question above."),
        "nis2_reporting": ("needs_human_review", "Depends on the unresolved entity-scope question above."),
        "nis2_certification": ("needs_human_review", "Depends on the unresolved entity-scope question above."),
        "nis2_registration": ("needs_human_review", "Depends on the unresolved entity-scope question above."),
        "nis2_info_sharing_voluntary": ("applicable", "Voluntary information-sharing is open to any entity regardless of essential/important status."),
        "nis2_enforcement_essential": ("not_applicable", "Even if in scope, RouteWise's profile does not match the scale/criticality typical of essential-entity designation."),
        "nis2_enforcement_important": ("needs_human_review", "Depends on the unresolved entity-scope question above."),
        "csrd_reporting_large": ("not_applicable", "45 employees is well below the CSRD size thresholds, and there is no indication of a group-reporting obligation."),
        "csrd_reporting_group": ("not_applicable", "No indication RouteWise is a parent undertaking of a large group."),
        "csrd_reporting_standards": ("not_applicable", "No direct reporting obligation, so the reporting-standards provision does not attach."),
        "csrd_reporting_sme_voluntary": ("applicable", "This is exactly the voluntary simplified standard intended for an SME like RouteWise, relevant if it chooses (or is asked by a customer) to report."),
        "csrd_third_country": ("not_applicable", "RouteWise is a German/EU undertaking, not a third-country entity."),
        "csrd_assurance": ("not_applicable", "No reporting obligation exists yet, so no assurance obligation follows."),
    },
    "Nordkette Präzisionsteile GmbH": {
        "ai_general_obligation_if_ai_user": ("applicable", "Uses an AI system (defect detection) in production; the AI-literacy obligation applies regardless of risk tier."),
        "ai_prohibited_practices": ("not_applicable", "Computer-vision defect detection is not a prohibited practice under any Article 5 category."),
        "ai_high_risk_classification": ("needs_human_review", "Whether production-line defect detection is a safety component subject to third-party conformity assessment under sectoral product-safety law (the Annex I trigger for high-risk status) depends on the specific system's function and needs legal review."),
        "ai_high_risk_provider_obligation": ("needs_human_review", "Contingent on the unresolved high-risk classification above."),
        "ai_high_risk_deployer_obligation": ("needs_human_review", "Contingent on the unresolved high-risk classification above."),
        "ai_transparency_limited_risk": ("not_applicable", "The defect-detection system does not generate synthetic content or interact with end users."),
        "ai_gpai_provider": ("not_applicable", "Nordkette is not a provider of general-purpose AI models."),
        "ai_sme_support": ("applicable", "180 employees still qualifies as an SME under the EU definition (<250 employees)."),
        "nis2_scope": ("applicable", "Precision manufacturing of machinery/parts falls within the NIS2 manufacturing sector, and 180 employees exceeds the medium-enterprise size threshold used to determine NIS2 scope."),
        "nis2_governance": ("applicable", "Follows directly from in-scope status as an important entity."),
        "nis2_risk_mgmt": ("applicable", "Directly relevant given the recently onboarded third-party IoT vendor with no formal security review — supply-chain security is an explicit requirement."),
        "nis2_reporting": ("applicable", "Follows directly from in-scope status as an important entity."),
        "nis2_certification": ("needs_human_review", "Depends on whether the specific IoT/SCADA components need to meet a European cybersecurity certification scheme; not clear from the profile."),
        "nis2_registration": ("applicable", "Follows directly from in-scope status as an important entity."),
        "nis2_info_sharing_voluntary": ("applicable", "Voluntary information-sharing is open to any entity."),
        "nis2_enforcement_essential": ("not_applicable", "Manufacturing is designated an important-entity sector under NIS2, not an essential-entity one; the essential-entity enforcement regime does not apply."),
        "nis2_enforcement_important": ("applicable", "Matches Nordkette's likely classification as an important entity."),
        "csrd_reporting_large": ("needs_human_review", "180 employees alone does not confirm large-undertaking status; turnover and balance-sheet figures are needed to assess the other two CSRD size criteria."),
        "csrd_reporting_group": ("needs_human_review", "Same missing financial data applies if Nordkette is part of a group."),
        "csrd_reporting_standards": ("needs_human_review", "Contingent on the unresolved size-threshold question above."),
        "csrd_reporting_sme_voluntary": ("needs_human_review", "Could go either way depending on whether Nordkette falls under the large-undertaking threshold or the SME voluntary standard."),
        "csrd_third_country": ("not_applicable", "Nordkette is a German/EU undertaking, not a third-country entity."),
        "csrd_assurance": ("needs_human_review", "Contingent on whether a reporting obligation ultimately applies."),
    },
    "Feldgrün Agrar-Consulting UG": {
        "ai_general_obligation_if_ai_user": ("needs_human_review", "Feldgrün has no AI systems today, but the AI-literacy obligation would attach as soon as the crop-yield SaaS tool is adopted — a forward-looking question rather than a clean yes/no."),
        "ai_prohibited_practices": ("not_applicable", "No AI systems in use, and none of the prohibited-practice categories are relevant to agricultural consulting."),
        "ai_high_risk_classification": ("not_applicable", "A commodity crop-yield prediction tool used for internal agronomic advice is not on the Annex III high-risk list."),
        "ai_high_risk_provider_obligation": ("not_applicable", "Feldgrün would only ever be a deployer of this third-party tool, never a provider, and the tool is not high-risk in any case."),
        "ai_high_risk_deployer_obligation": ("not_applicable", "The tool under evaluation is not high-risk, so deployer obligations for high-risk systems do not attach."),
        "ai_transparency_limited_risk": ("not_applicable", "The crop-yield tool does not generate synthetic content or interact conversationally with end users."),
        "ai_gpai_provider": ("not_applicable", "Feldgrün is not a provider of any AI model."),
        "ai_sme_support": ("applicable", "Feldgrün is a micro-enterprise; SME support measures apply if it engages with AI Act processes."),
        "nis2_scope": ("not_applicable", "Agricultural consulting is not among the NIS2 covered sectors, and at 12 employees Feldgrün falls below any relevant size threshold in any case."),
        "nis2_governance": ("not_applicable", "Out of scope — see nis2_scope."),
        "nis2_risk_mgmt": ("not_applicable", "Out of scope — see nis2_scope."),
        "nis2_reporting": ("not_applicable", "Out of scope — see nis2_scope."),
        "nis2_certification": ("not_applicable", "Out of scope — see nis2_scope."),
        "nis2_registration": ("not_applicable", "Out of scope — see nis2_scope."),
        "nis2_info_sharing_voluntary": ("applicable", "Voluntary information-sharing is open to any entity regardless of sector or size."),
        "nis2_enforcement_essential": ("not_applicable", "Out of scope — see nis2_scope."),
        "nis2_enforcement_important": ("not_applicable", "Out of scope — see nis2_scope."),
        "csrd_reporting_large": ("not_applicable", "12 employees is far below the CSRD size thresholds; no direct reporting obligation."),
        "csrd_reporting_group": ("not_applicable", "No indication Feldgrün is part of a corporate group."),
        "csrd_reporting_standards": ("not_applicable", "No direct reporting obligation, so the reporting-standards provision does not attach."),
        "csrd_reporting_sme_voluntary": ("applicable", "This voluntary SME standard is the relevant provision if Feldgrün chooses to respond to its large customer's value-chain sustainability-data request."),
        "csrd_third_country": ("not_applicable", "Feldgrün is a German/EU undertaking, not a third-country entity."),
        "csrd_assurance": ("not_applicable", "No reporting obligation exists, so no assurance obligation follows."),
    },
    "Baumann Energie- und Gebäudetechnik AG": {
        "ai_general_obligation_if_ai_user": ("applicable", "Uses multiple AI systems in client-facing operations; the AI-literacy obligation applies regardless of risk tier."),
        "ai_prohibited_practices": ("not_applicable", "Predictive maintenance and anomaly detection are not prohibited practices under Article 5."),
        "ai_high_risk_classification": ("needs_human_review", "Predictive maintenance and anomaly detection for client building energy/heating systems sits close to the Annex III critical-infrastructure category (heating/electricity supply); requires a documented classification decision."),
        "ai_high_risk_provider_obligation": ("needs_human_review", "Contingent on the unresolved high-risk classification above."),
        "ai_high_risk_deployer_obligation": ("needs_human_review", "Contingent on the unresolved high-risk classification above."),
        "ai_transparency_limited_risk": ("not_applicable", "Neither system generates synthetic content or interacts conversationally with end users."),
        "ai_gpai_provider": ("not_applicable", "Baumann is not a provider of general-purpose AI models."),
        "ai_sme_support": ("not_applicable", "310 employees exceeds the EU SME threshold (250 employees); SME-targeted measures do not apply."),
        "nis2_scope": ("needs_human_review", "Baumann is a technology vendor to buildings' energy systems, not itself an energy undertaking; whether it is captured directly (e.g. as a district-heating infrastructure operator) or only indirectly (as a supply-chain vendor to essential entities) needs a sector-specific legal read."),
        "nis2_governance": ("needs_human_review", "Depends on the unresolved entity-scope question above."),
        "nis2_risk_mgmt": ("needs_human_review", "Depends on the unresolved entity-scope question above."),
        "nis2_reporting": ("needs_human_review", "Depends on the unresolved entity-scope question above."),
        "nis2_certification": ("needs_human_review", "Depends on the unresolved entity-scope question above."),
        "nis2_registration": ("needs_human_review", "Depends on the unresolved entity-scope question above."),
        "nis2_info_sharing_voluntary": ("applicable", "Voluntary information-sharing is open to any entity regardless of scope status."),
        "nis2_enforcement_essential": ("needs_human_review", "If in scope at all, Baumann's role in energy-adjacent infrastructure makes the essential-vs-important distinction genuinely unclear."),
        "nis2_enforcement_important": ("needs_human_review", "Same unresolved essential-vs-important distinction."),
        "csrd_reporting_large": ("applicable", "310 employees exceeds the >250-employee CSRD size criterion; combined with its scale, full sustainability reporting very likely applies pending confirmation of the turnover/balance-sheet criteria."),
        "csrd_reporting_group": ("applicable", "Same size-driven reasoning applies if group reporting is relevant."),
        "csrd_reporting_standards": ("applicable", "Follows directly from the likely large-undertaking reporting obligation."),
        "csrd_reporting_sme_voluntary": ("not_applicable", "Baumann is well above the SME threshold; the voluntary SME standard is not the relevant provision."),
        "csrd_third_country": ("not_applicable", "Baumann is a German/EU undertaking, not a third-country entity."),
        "csrd_assurance": ("applicable", "If the underlying reporting obligation applies, the assurance requirement for that reporting follows directly."),
    },
}


def _profile_text(profile: dict) -> str:
    ai_systems = "; ".join(profile["ai_system_descriptions"]) or "none"
    vendors = "; ".join(profile["third_party_vendors"]) or "none"
    return (
        f"{profile['name']}: {profile['sector']} company, {profile['employee_count']} employees. "
        f"Uses AI systems: {profile['uses_ai_systems']}. AI systems: {ai_systems}. "
        f"Third-party vendors: {vendors}. Notes: {profile['notes'] or 'none'}."
    )


def build():
    profiles = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
    profile_texts = {p["name"]: _profile_text(p) for p in profiles}

    regulation_data = {
        stem: json.loads((REGULATIONS_DIR / f"{stem}_articles.json").read_text(encoding="utf-8"))
        for stem in {stem for stem, _, _ in CURATED_ARTICLES}
    }
    regulation_names = {stem: data["regulation"] for stem, data in regulation_data.items()}

    rows = []
    missing = []
    for stem, heading, category in CURATED_ARTICLES:
        articles = regulation_data[stem]["articles"]
        match = next((a for a in articles if a["heading"] == heading), None)
        if match is None:
            missing.append((stem, heading))
            continue

        # Strip EUR-Lex's amending-legislation "inserted article" marker (U+2018) — legally
        # meaningful in the directive text, just noise for a citation label.
        clean_heading = match["heading"].replace("\xa0", " ").lstrip("‘").strip()
        title = match["title"].rstrip("`").strip()
        clause_text = f"{clean_heading} — {title}\n{match['body']}" if title else f"{clean_heading}\n{match['body']}"

        for profile_name, profile_text in profile_texts.items():
            label, rationale = PROFILE_LABELS[profile_name][category]
            rows.append(
                {
                    "regulation": regulation_names[stem],
                    "article": clean_heading,
                    "clause_text": clause_text,
                    "company_profile_text": profile_text,
                    "label": label,
                    "rationale": rationale,
                }
            )

    if missing:
        raise SystemExit(f"Could not find these curated article headings in the source JSON: {missing}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["regulation", "article", "clause_text", "company_profile_text", "label", "rationale"])
        writer.writeheader()
        writer.writerows(rows)

    label_counts = {}
    for row in rows:
        label_counts[row["label"]] = label_counts.get(row["label"], 0) + 1

    print(f"Wrote {len(rows)} labeled pairs to {OUTPUT_PATH}")
    print(f"Label distribution: {label_counts}")


if __name__ == "__main__":
    build()
