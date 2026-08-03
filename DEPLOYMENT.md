# Deployment guide

Goal: a live, clickable demo — backend + frontend both publicly reachable — for a portfolio
link.

**Status as actually tested in this project:** Hugging Face Spaces' free tier turned out not to
work for this backend — see the "What we tried on Hugging Face" section below for the full
story (kept for context/future reference, not because it's the recommended path). **Google Cloud
Run** is the primary path now: it has a genuine always-free tier with real CPU/RAM, no
GPU-decorator gating, and we can reuse the existing root [`Dockerfile`](Dockerfile) unchanged.
The frontend is static HTML/CSS/JS with no build step, so **GitHub Pages** is the simplest place
for it.

## 0. Accounts you'll need

1. [github.com](https://github.com) — free, if you don't already have one
2. [console.cloud.google.com](https://console.cloud.google.com) — Google account + a GCP
   project with billing enabled. **Billing enabled ≠ getting charged** — Cloud Run's always-free
   tier (2 million requests/month, 360,000 GB-seconds memory, 180,000 vCPU-seconds/month) covers
   a demo like this comfortably; billing just has to exist as a safety net GCP requires even for
   free-tier usage. Google may ask for a card for identity verification when creating the billing
   account — that's Google's requirement, not something specific to this project.

## 1. Push the source code to GitHub

*(Already done for this project — see the note in the repo if you're following this guide fresh.)*

```bash
git init
git add .
git commit -m "Initial commit"
```

Create an empty repo on GitHub (github.com → New repository, don't initialize with a README),
then:

```bash
git remote add origin https://github.com/<your-username>/<repo-name>.git
git branch -M main
git push -u origin main
```

## 2. Deploy the backend to Google Cloud Run

1. Install the `gcloud` CLI: https://cloud.google.com/sdk/docs/install (this is a local install
   on your machine — not something that can be done from within this chat).
2. Authenticate and set your project:
   ```bash
   gcloud auth login
   gcloud config set project <your-gcp-project-id>
   ```
3. From this repo's root (where the [`Dockerfile`](Dockerfile) lives):
   ```bash
   gcloud run deploy ai-compliance-copilot \
     --source . \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 4Gi \
     --timeout 300
   ```
   `--source .` builds the container via Cloud Build **remotely** — no local Docker daemon
   needed. `--memory 4Gi` gives enough headroom for `torch` + `transformers` +
   `sentence-transformers` loaded together; adjust down if you trim the embedding model (see
   note below). First build takes 10-20 minutes (same reason as the Dockerfile's own comments —
   it downloads the embedding + classifier models and rebuilds the regulation corpus / retrains
   the classifier as part of the build).
4. `gcloud run deploy` prints a service URL when done (something like
   `https://ai-compliance-copilot-xxxxx-uc.a.run.app`). Confirm with:
   ```bash
   curl https://<your-service-url>/health
   ```
   should return `{"status":"ok"}`.

**If you want to shrink the memory footprint** (e.g. to stay further inside the free tier's
GB-seconds budget, or if 4Gi ever isn't enough): swap `intfloat/multilingual-e5-large` for
`intfloat/multilingual-e5-small` in `backend/app/core/config.py`'s `embedding_model` default —
untested in this project (the large model is what was actually verified working throughout),
but it's the same embedding family at a fraction of the size, and would need
`data_pipeline/chunk_and_embed.py` re-run once against the new model before redeploying, since
embeddings from different models aren't interchangeable.

## 3. Deploy the frontend to GitHub Pages

1. Edit [`webapp/js/config.js`](webapp/js/config.js) — change the URL to your Cloud Run service
   URL from step 2:
   ```js
   window.STATUTA_API_BASE = "https://<your-service-url>";
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

## What we tried on Hugging Face Spaces (kept for reference)

This project's free HF account only offers **Gradio**, **Static**, and **ZeroGPU** as Space
options — no Docker, and switching an existing Space to **CPU basic** hardware is blocked
outright without a PRO subscription (`"Without a PRO subscription, you can't downgrade this
Space to cpu-basic"`). That leaves ZeroGPU as the only free hardware tier, which requires at
least one `@spaces.GPU`-decorated function to exist and be detected at startup — a real
requirement even for an app that has no actual GPU workload.

We got as far as:
- [`app.py`](app.py) mounting the existing FastAPI app under a Gradio page, verified working
  locally (real `/api/chat` responses, `/docs`, `/ui/` all returned 200)
- Found and fixed a real `gradio 4.44.1` / `starlette 1.x` incompatibility along the way
  (`TypeError: unhashable type: 'dict'` rendering the Gradio UI page — fixed by pinning
  `starlette<1.0` in `requirements.txt`)
- Two different attempts at satisfying ZeroGPU's `@spaces.GPU` detection (a bare decorated
  function, then wiring it into a `demo.load` event) both failed with the identical error
  `"No @spaces.GPU function detected during startup"`, and the Space's own runtime status showed
  `"hardware":{"current":null}` — hardware was never actually allocated to the container

That last point suggests the blocker sits below the application code, in how this specific free
account's ZeroGPU allocation behaves — not something fixable by changing `app.py` further. If
Hugging Face's free-tier offering changes later (or a PRO subscription is added), `app.py` and
the root `Dockerfile` are both already written and tested locally; only the actual push +
account-side hardware selection would need retrying.

## What's NOT handled by this guide

- **Auth** — there is none. Anyone with the URL can upload documents and generate reports under
  the shared `demo-user` ID the frontend currently hardcodes. Fine for a portfolio demo, not for
  real use.
- **Persistence across redeploys** — the local JSON store (uploaded documents, generated
  reports) lives inside the Cloud Run container's filesystem, which is ephemeral per instance.
  Documents uploaded via the live demo may disappear when Cloud Run scales an instance down. The
  regulation corpus and classifier don't, since they're rebuilt from source on every deploy.
- **A real Supabase project** — if you want persistent, multi-user storage instead of the demo
  local store, follow `supabase/schema.sql` and set `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY`
  as Cloud Run environment variables/secrets (`gcloud run services update ... --set-secrets`)
  instead of committing them to `.env`.
