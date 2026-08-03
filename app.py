"""Entry point for deploying the backend on a Hugging Face Space using the Gradio SDK.

Gradio/Static Spaces (the free tiers available without Docker) run `python app.py` with no
custom build step — they can't run the embed/train pipeline the Dockerfile does at build time.
This file mounts the existing FastAPI app (backend/app/main.py, completely unmodified) under a
minimal Gradio Blocks page, then serves the combined app with uvicorn. All the real REST
endpoints (/api/chat, /api/documents/upload, /api/reports/...) work exactly as they do locally;
the Gradio page is just a landing page + a way to satisfy the SDK's expectations.

Because there's no build step here, the regulation embeddings
(data_pipeline/local_index/chunks.json) and the trained classifier checkpoint
(pytorch_classifier/checkpoints/gbert-compliance-classifier/) must already exist on disk when
this runs — see DEPLOYMENT.md for how those get committed into the Space's git repo.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

import gradio as gr
import spaces

from app.main import app as fastapi_app  # noqa: E402  (path insert must happen first)


@spaces.GPU
def _zerogpu_placeholder():
    """Satisfies the ZeroGPU Space runtime's requirement that at least one @spaces.GPU
    function exists at startup. This project's workload (embeddings + a small BERT
    classifier) is CPU-only by design — this function is never called."""
    return None

with gr.Blocks(title="AI Compliance Copilot") as demo:
    gr.Markdown(
        """
        # Statuta — AI Compliance Copilot (API)

        This Space hosts the backend API only. The full UI is the static frontend in
        `webapp/`, deployed separately (see `DEPLOYMENT.md`) and pointed at this Space's URL.

        - API docs: [`/docs`](/docs)
        - Health check: [`/health`](/health)
        """
    )

app = gr.mount_gradio_app(fastapi_app, demo, path="/ui")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7860)
