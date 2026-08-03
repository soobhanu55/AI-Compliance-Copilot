# Build Plan

## Week 1 — Data pipeline + RAG foundation
- [x] Download consolidated AI Act, NIS2, CSRD texts from EUR-Lex — done via a real browser
      session (EUR-Lex's CloudFront WAF blocks scripted HTTP fetches); parsed into structured
      per-article JSON using the site's `.oj-ti-art` / `.oj-sti-art` markup, not regex splitting
- [ ] NIS2UmsuCG (German national implementation) — not yet available/found; revisit
- [x] Chunk + embed regulation corpus (`data_pipeline/chunk_and_embed.py`) — 274 chunks indexed
      (AI Act 154, NIS2 64, CSRD 56) using `intfloat/multilingual-e5-large`
- [ ] Supabase project: apply `supabase/schema.sql`, enable `pgvector`, enable RLS — waiting on
      a live Supabase project; local JSON store (`app/rag/local_store.py`) used as a stand-in
      so the rest of the pipeline could be built and tested now
- [x] FastAPI RAG endpoint: `POST /api/chat` retrieves from the regulation corpus, returns
      cited answers — verified via curl against the local store with real embeddings.
      Example: "Does the AI Act require a risk management system for high-risk AI systems?"
      correctly surfaces Article 9 (Risk management system) as the top citation; a NIS2
      question correctly surfaces Article 21; a CSRD question correctly surfaces Article 19a/29a-c

## Week 2 — Classifier + drafting agent
- [x] Labeled dataset: 188 (regulation clause, company profile) pairs →
      `pytorch_classifier/data/labeled_pairs.csv`, built by
      `pytorch_classifier/scripts/build_labeled_dataset.py`. Rule-based weak supervision, not
      human-annotated ground truth — see the model card for the full methodology disclosure.
      Started at 140 rows/35 articles, expanded once to 188 rows/47 articles (12 more real
      articles mapped onto the existing 22 categories)
- [x] Trained `deepset/gbert-base` classifier — 8 epochs, article-grouped 80/20 split (152
      train / 36 val on the expanded set), real loss curve and metrics recorded
- [x] Recorded loss curves, F1, confusion matrix in the model card
      (`pytorch_classifier/README.md`) — macro F1 improved 0.50 → 0.69 after the dataset
      expansion, honestly reported as a real but still small-scale result, not oversold
- [x] Wired the trained classifier into the report pipeline
      (`backend/app/agents/classifier.py`, `report_agent.py`) — verified end-to-end against
      real AI Act retrieval; confidence < 60% is forced to `needs_human_review`
- [x] Drafting agent: structured output → `.docx` export (Annex IV skeleton) — verified,
      produces a real downloadable .docx with retrieved findings inlined

## Week 3 — Frontend polish + deploy
- [x] Frontend rebuilt as a static HTML/CSS/vanilla-JS app (`webapp/`) matching a reference
      design ("Statuta") the user provided — Streamlit dropped in favor of this, since matching
      the design's custom card/chip/typography system isn't realistic in Streamlit's component
      model. Five pages: Dashboard, Gap Report, Documents, Assistant, Drafted Docs
- [x] Gap Report page's evidence-matching feature (from the reference design, not in the
      original spec): for each `applicable` clause, retrieves the closest-matching chunk from
      the user's own uploaded documents and classifies `evidence_found` / `partial_match` / `gap`
      by cosine-similarity threshold (`backend/app/agents/report_agent.py::_match_evidence`)
- [x] Drafted Docs page: new `GET /api/reports/gap-report/{id}/draft-annex-iv/sections` JSON
      endpoint (`backend/app/agents/drafting_agent.py::build_annex_iv_sections`) so the frontend
      can render per-section citations + a client-side "mark reviewed" toggle, not just offer a
      `.docx` download — the docx export uses the same section-building function so both stay
      in sync
- [x] Fixed `backend/app/api/documents.py` to support the local store (was hardcoded to
      Supabase) — needed to test evidence matching without a live Supabase project
- [x] `/api/chat` now returns an extractive answer (quotes the top retrieved clause) instead of
      a placeholder string — still not LLM-generated, no API key configured, but no longer fake
- [x] Verified all 5 pages end-to-end in a real browser against the live backend: gap report
      generation, evidence matching against an uploaded doc, chat, and the review-toggle all
      confirmed working with real data (see `webapp/README.md` for how to run it)
- [ ] Supabase Auth — not applicable to the static frontend as built; would need a real login
      flow if this moves off `local_store`
- [ ] Actual deployment (hosting the backend + static frontend somewhere reachable) — not
      started, needs the user's hosting choice/credentials, see note below
- [ ] Record 2-minute demo video
- [ ] Finish README: problem framing, architecture diagram, model card, limitations

## Component status

| Component | Status |
|---|---|
| Repo scaffold | done |
| Backend boots (`/health` verified locally) | done |
| Backend unit tests (chunking, `/api/chat` contract) | done — `backend/tests/`, 6 passing |
| Regulation download/chunk/embed | done — 274 chunks across AI Act/NIS2/CSRD, real embeddings |
| Local vector store (JSON + cosine similarity) | done — `backend/app/rag/local_store.py`, used automatically when `SUPABASE_URL` is unset |
| Supabase schema | drafted, not yet applied to a live project |
| FastAPI RAG endpoint (`/api/chat`) | done — verified against real data, all 3 regulations |
| Labeled dataset (188 pairs) | done — `pytorch_classifier/data/labeled_pairs.csv`, expanded once from 140 |
| PyTorch classifier | trained — macro F1 0.69 on held-out val (36 examples), up from 0.50 after expansion, see model card |
| Gap-report endpoint (`/api/reports/gap-report`) | done — verified end-to-end with the real trained classifier, not a placeholder |
| Evidence matching against uploaded docs | done — `report_agent.py::_match_evidence`, verified with a real uploaded document |
| Annex IV `.docx` drafting export | done — verified, produces a real file |
| Annex IV structured JSON (`.../draft-annex-iv/sections`) | done — verified, backs the Drafted Docs page |
| Frontend (`webapp/`, static HTML/CSS/JS) | done — 5 pages, verified end-to-end in-browser against the live backend |
| Synthetic SME profiles | done — 4 profiles in `data_pipeline/synthetic_profiles/` |
| Deployment (live hosting) | not started — needs the user's hosting choice/credentials |

## Known limitations / cleanup items

- CSRD article headings for *inserted* articles carried a leading U+2018 marker
  (`'Article 19a`) from EUR-Lex's amending-legislation typography — now stripped in both
  `chunk_and_embed.py` and `build_labeled_dataset.py`.
- `backend/app/api/documents.py` (company-doc upload) still hardcodes Supabase — no local-store
  fallback yet. Only the regulation corpus and gap-report persistence have one.
- Local store has no auth/RLS and loads the whole index into memory per query — fine for one
  developer's local testing, not for the real multi-user deployment.
- Classifier training data covers only 35 of ~191 substantive articles and 4 synthetic
  profiles — expanding both is the highest-leverage next step before trusting the classifier
  on anything beyond a demo. `transformers` is pinned `<5` — v5.14.1 fails to fetch a usable
  tokenizer for `deepset/gbert-base`; revisit the pin once that's fixed upstream.
