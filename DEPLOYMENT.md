# Deployment guide

Goal: a live, clickable demo — backend + frontend both publicly reachable — for a portfolio
link. Everything below uses free tiers. Total cost: $0.

**Why this stack:** the backend needs enough RAM to hold `torch` + `transformers` +
`sentence-transformers` in memory (the embedding model alone is ~2GB). **Hugging Face Spaces'**
free CPU tier (2 vCPU / 16GB RAM) is built for exactly this kind of workload and is a platform
ML recruiters recognize on sight — a better signal for this project than a generic host. The
frontend is static HTML/CSS/JS with no build step, so **GitHub Pages** is the simplest place
for it — free, and it's the same account you'll want for the source code anyway.

## 0. Accounts you'll need (both free)

1. [github.com](https://github.com) — if you don't already have one
2. [huggingface.co](https://huggingface.co) — sign up, no payment info required for the free CPU tier

## 1. Push the source code to GitHub

From this directory:

```bash
git init
git add .
git commit -m "Initial commit"
```

Then create an empty repo on GitHub (github.com → New repository, don't initialize with a
README) and follow its instructions to push, roughly:

```bash
git remote add origin https://github.com/<your-username>/<repo-name>.git
git branch -M main
git push -u origin main
```

## 2. Deploy the backend to Hugging Face Spaces

1. On huggingface.co, click **New Space**.
2. Name it (e.g. `ai-compliance-copilot`), choose **Docker** as the Space SDK, choose the
   **free CPU basic** hardware tier, visibility your choice (public if you want recruiters to
   see it directly).
3. HF gives the new Space its own git remote. Push this repo to it:
   ```bash
   git remote add space https://huggingface.co/spaces/<your-username>/ai-compliance-copilot
   git push space main
   ```
4. HF Spaces will read the root [`Dockerfile`](Dockerfile) and build automatically. **The first
   build takes 10-20 minutes** — it downloads the embedding + classifier models and re-embeds
   the regulation corpus / retrains the classifier as part of the build (see the Dockerfile's
   comments for why: it keeps large model files out of git entirely).
5. Once built, your backend is live at `https://<your-username>-ai-compliance-copilot.hf.space`.
   Confirm with:
   ```bash
   curl https://<your-username>-ai-compliance-copilot.hf.space/health
   ```
   should return `{"status":"ok"}`.

**Before you push**, this Dockerfile has not been build-tested in this environment (Docker
Desktop wasn't running here) — if the build fails on HF Spaces, check the build log there first;
the most likely failure points are dependency install (large downloads can occasionally time
out — just retry the build) or the embed/train steps (check they still run locally first with
`cd data_pipeline && python chunk_and_embed.py --file regulations/ai_act_articles.json`, etc.,
per `docs/BUILD_PLAN.md`).

## 3. Deploy the frontend to GitHub Pages

1. Edit [`webapp/js/config.js`](webapp/js/config.js) — change the URL to your Space's URL from
   step 2:
   ```js
   window.STATUTA_API_BASE = "https://<your-username>-ai-compliance-copilot.hf.space";
   ```
2. Commit and push that change.
3. On GitHub: repo → **Settings → Pages** → Source: **Deploy from a branch** → Branch: `main`,
   folder: `/webapp` (if GitHub Pages doesn't offer a subfolder picker in your account, see the
   note below).
4. Your frontend will be live at `https://<your-username>.github.io/<repo-name>/` (may take a
   minute after the first Pages build).

**If GitHub Pages won't let you pick `/webapp` as the folder** (older UI only offers `/` or
`/docs`): either move `webapp/`'s contents to a `docs/` directory and point Pages there, or use
a GitHub Actions-based Pages deploy (Settings → Pages → Source: GitHub Actions, and use their
"Static HTML" starter workflow pointed at `webapp/`).

## 4. CORS

`backend/app/main.py` currently allows all origins (`allow_origins=["*"]`) — fine for this demo,
but tighten it to your actual GitHub Pages URL once both are live if you want to lock it down:

```python
allow_origins=["https://<your-username>.github.io"],
```

## What's NOT handled by this guide

- **Auth** — there is none. Anyone with the URL can upload documents and generate reports under
  the shared `demo-user` ID the frontend currently hardcodes. Fine for a portfolio demo, not for
  real use.
- **Persistence across redeploys** — the local JSON store lives inside the container's
  filesystem. Any documents uploaded via the live demo disappear on the next redeploy /
  container restart. The regulation corpus and classifier don't, since they're rebuilt from
  source every build.
- **A real Supabase project** — if you want persistent, multi-user storage instead of the demo
  local store, follow `supabase/schema.sql` and set `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY`
  as secrets in the HF Space's settings (Settings → Variables and secrets) instead of committing
  them to `.env`.
