"""Loads the compliance-relevance classifier trained under pytorch_classifier/ and exposes a
classify() function for the gap-report agent.

The classifier is a proof-of-concept (macro F1 ~0.50 on 32 held-out examples grouped by
article — see pytorch_classifier/README.md for the full write-up and confusion matrix), not a
validated legal tool. Predictions below CONFIDENCE_THRESHOLD are downgraded to
needs_human_review rather than surfaced as a confident applicable/not_applicable call.
"""

from functools import lru_cache
from pathlib import Path

import torch

CHECKPOINT_PATH = (
    Path(__file__).resolve().parents[3] / "pytorch_classifier" / "checkpoints" / "gbert-compliance-classifier"
)
CONFIDENCE_THRESHOLD = 0.6


def is_available() -> bool:
    return (CHECKPOINT_PATH / "config.json").exists()


@lru_cache
def _load():
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(CHECKPOINT_PATH)
    model.eval()
    return model, tokenizer


def classify(clause_text: str, profile_text: str) -> tuple[str, float]:
    """Returns (verdict, confidence). verdict is one of applicable / not_applicable /
    needs_human_review — forced to needs_human_review whenever confidence < CONFIDENCE_THRESHOLD,
    regardless of the model's raw argmax.
    """
    model, tokenizer = _load()
    encoding = tokenizer(
        clause_text, profile_text, truncation=True, padding=True, max_length=256, return_tensors="pt"
    )
    with torch.no_grad():
        logits = model(**encoding).logits
    probs = torch.softmax(logits, dim=-1)[0]
    pred_id = int(torch.argmax(probs))
    confidence = float(probs[pred_id])
    label = model.config.id2label[pred_id]

    if confidence < CONFIDENCE_THRESHOLD:
        return "needs_human_review", confidence
    return label, confidence
