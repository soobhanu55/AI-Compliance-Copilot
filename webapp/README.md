# Statuta — AI Compliance Copilot frontend

Static HTML/CSS/vanilla JS frontend calling the FastAPI backend directly via `fetch()`. No
build step, no framework — styled to match the referenced Statuta design (dark sidebar, serif
headings, monospace citation chips).

## Run locally

Backend must be running first (see [`../README.md`](../README.md)):

```bash
uvicorn app.main:app --reload --port 8000
```

Then serve this directory as static files — any static server works:

```bash
cd webapp
python -m http.server 5500
```

Open http://localhost:5500. The frontend defaults to `http://localhost:8000` for the API — to
point at a deployed backend instead, edit the one line in [`js/config.js`](js/config.js).

## Structure

```
index.html       Shell — loads config.js, styles.css, and app.js
css/styles.css    Design tokens (colors, fonts) + all component styles
js/config.js      One line: window.STATUTA_API_BASE — edit this to point at a deployed backend
js/api.js         Thin fetch() wrapper around every backend endpoint used
js/render.js      Pure HTML-string templates per view, given the current state
js/app.js         State, event delegation (click/submit/change/drag), API calls, re-render
```

Single-page app: `app.js` owns one `state` object and calls `render(state)` into `#app` on
every change — no router, no framework, no build tool. Views: Dashboard, Gap Report,
Documents, Assistant, Drafted Docs (matches `docs/BUILD_PLAN.md`'s Week 3 scope).

## Known gaps

- The company profile is editable via the sidebar card, but there's no persistence — refreshing
  the page resets to the default RouteWise profile and clears the in-session document list
  (uploads themselves persist server-side; only the client-side upload list resets).
- No "list existing documents" endpoint yet — the Documents page only shows what was uploaded
  in the current browser session, not documents uploaded in a previous session or via curl.
- Chat answers are extractive (quotes the top retrieved clause), not LLM-generated — no LLM API
  key is configured in this environment. See `backend/app/api/chat.py`.
- Drafted-doc section review state (the "Mark reviewed" toggles) is client-side only and resets
  on reload — not persisted to the backend.
