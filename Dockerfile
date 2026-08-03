# Self-contained backend image: embeds the regulation corpus and trains the classifier at
# BUILD time, so nothing large (model weights, embeddings) needs to be committed to git —
# the image is reproducible from source alone. Built for Hugging Face Spaces' Docker SDK
# (listens on $PORT / 7860, no external DB required — falls back to the local JSON store).
#
# Build is slow (~10-20 min) mostly from downloading intfloat/multilingual-e5-large (~2GB) and
# deepset/gbert-base, then embedding 274 chunks and fine-tuning for 8 epochs. That's a one-time
# cost per deploy, not a request-time cost.
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt backend/requirements.txt
COPY pytorch_classifier/requirements.txt pytorch_classifier/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt -r pytorch_classifier/requirements.txt

COPY backend/ backend/
COPY pytorch_classifier/ pytorch_classifier/
COPY data_pipeline/ data_pipeline/

# Embed the regulation corpus into the local JSON vector store (no SUPABASE_URL is set here,
# so app.rag.local_store is used automatically — see backend/app/rag/retriever.py).
WORKDIR /app/data_pipeline
RUN python chunk_and_embed.py --file regulations/ai_act_articles.json \
    && python chunk_and_embed.py --file regulations/nis2_articles.json \
    && python chunk_and_embed.py --file regulations/csrd_articles.json

# Build the labeled dataset and train the compliance classifier (see pytorch_classifier/README.md
# for what this model actually is — a proof-of-concept, not a certified legal tool).
WORKDIR /app/pytorch_classifier/scripts
RUN python build_labeled_dataset.py \
    && python train.py --epochs 8

WORKDIR /app/backend
ENV PORT=7860
EXPOSE 7860
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
