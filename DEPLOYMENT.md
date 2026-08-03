# Deployment guide

Goal: a live, clickable demo — backend + frontend both publicly reachable — for a portfolio
link. Everything below uses free tiers. Total cost: $0.

**Why this stack:** the backend needs enough RAM to hold `torch` + `transformers` +
`sentence-transformers` in memory (the embedding model alone is ~2GB). **Hugging Face Spaces'**
free CPU tier is built for exactly this kind of workload and is a platform ML recruiters
recognize on sight — a better signal for this project than a generic host. The frontend is
static HTML/CSS/JS with no build step, so **GitHub Pages** is the simplest place for it — free,
and it's the same account you'll want for the source code anyway.

**Note on Space SDK:** if your Hugging Face account's free tier only offers **Gradio**,
**Static**, and **ZeroGPU** as Space SDK options (no Docker), use §2 below — it wraps the
existing FastAPI app under a minimal Gradio page (`app.py` at the repo root), verified working
locally in this project (real API responses, `/docs`, and the Gradio landing page all confirmed
through the mounted app). If Docker *is* available on your account, the root [`Dockerfile`](Dockerfile)
is the cleaner path (rebuilds everything from source at build time); §2a covers that instead.

## 0. Accounts you'll need (both free)

1. [github.com](https://github.com) — if you don't already have one
2. [huggingface.co](https://huggingface.co) — sign up, no payment info required for the free tier

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

This repo's `.gitignore` deliberately excludes the trained classifier checkpoint and the
regulation embeddings (`pytorch_classifier/checkpoints/*/`, `data_pipeline/local_index/`) —
keeps GitHub lean. §2 below explains why the Hugging Face Space needs those committed
separately.

## 2. Deploy the backend to Hugging Face Spaces (Gradio SDK — no Docker needed)

Gradio and Static Spaces run `pip install -r requirements.txt` then `python app.py` — there's
no build-time shell step like Docker's `RUN`, so the regulation embeddings and trained
classifier can't be regenerated at build time here. Instead, commit the already-built files
directly into the Space's own git repo (kept separate from your GitHub repo, which stays lean).

1. On huggingface.co, click **New Space**. Name it (e.g. `ai-compliance-copilot`), SDK:
   **Gradio**, hardware: the free CPU tier, visibility your choice.
2. HF Spaces auto-creates that Space's own git repo with a starter `README.md` (with required
   YAML frontmatter — don't overwrite it and lose the `sdk: gradio` / `app_file: app.py`
   declaration) and a placeholder `app.py`. Clone it **separately** from your GitHub working
   directory — trying to push this same folder to two remotes with different `.gitignore` needs
   gets confusing fast:
   ```bash
   git clone https://huggingface.co/spaces/<your-username>/ai-compliance-copilot statuta-space
   ```
3. Copy the following from this project into `statuta-space/`, **overwriting** the placeholder
   `app.py` but **keeping** the Space's auto-generated `README.md` as-is (just append your own
   description below its frontmatter block if you want):
   ```
   app.py                                        → overwrite the placeholder
   requirements.txt                                → the root one (not backend/'s)
   backend/                                        → whole directory
   pytorch_classifier/                             → whole directory, INCLUDING checkpoints/
                                                      and data/labeled_pairs.csv (both gitignored
                                                      in the main repo — include them here)
   data_pipeline/                                  → whole directory, INCLUDING local_index/
                                                      (also gitignored in the main repo)
   ```
4. From inside `statuta-space/`:
   ```bash
   git add .
   git commit -m "Deploy Statuta backend"
   git push
   ```
   The classifier checkpoint (`model.safetensors`, ~440MB) will trigger Hugging Face's
   automatic Git LFS handling for large files — this is normal and expected on HF (unlike
   GitHub's stricter free-tier LFS limits, HF's is generous and built for exactly this).
5. The Space rebuilds (no training/embedding step this time — just installing dependencies and
   starting `python app.py`, so this should take a few minutes, not 10-20). Once live:
   ```bash
   curl https://<your-username>-ai-compliance-copilot.hf.space/health
   ```
   should return `{"status":"ok"}`.

## 2a. Alternative: Docker SDK (if available on your account)

1. New Space → SDK: **Docker** → free CPU tier.
2. Push this whole repo (the one with `.gitignore` as-is — no separate clone needed) to the
   Space's git remote:
   ```bash
   git remote add space https://huggingface.co/spaces/<your-username>/ai-compliance-copilot
   git push space main
   ```
3. HF reads the root [`Dockerfile`](Dockerfile) and builds automatically. **First build takes
   10-20 minutes** — it downloads the embedding + classifier models and rebuilds the regulation
   embeddings / retrains the classifier as part of the build, so nothing large needs to be
   committed to git at all.
4. This Dockerfile has not been build-tested in this environment (Docker Desktop wasn't running
   here) — if the build fails, check the HF build log; likely failure points are dependency
   installs (large downloads occasionally time out — retry) or the embed/train steps (confirmed
   working when run directly, see `docs/BUILD_PLAN.md`).

## 3. Deploy the frontend to GitHub Pages

1. Edit [`webapp/js/config.js`](webapp/js/config.js) in your **GitHub** repo (not the Space
   clone) — change the URL to your Space's URL from step 2:
   ```js
   window.STATUTA_API_BASE = "https://<your-username>-ai-compliance-copilot.hf.space";
   ```
2. Commit and push that change to GitHub.
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
- **Persistence across redeploys** — the local JSON store (uploaded documents, generated
  reports) lives inside the Space's container filesystem. Free-tier Spaces don't guarantee
  that survives a sleep/restart cycle, so documents uploaded via the live demo may disappear
  after inactivity. The regulation corpus and classifier don't, since they're committed/rebuilt
  as part of the deploy either way.
- **A real Supabase project** — if you want persistent, multi-user storage instead of the demo
  local store, follow `supabase/schema.sql` and set `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY`
  as secrets in the HF Space's settings (Settings → Variables and secrets) instead of committing
  them to `.env`.
