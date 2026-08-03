"""Evaluate a trained checkpoint on its held-out validation split: F1 (macro), per-class
report, confusion matrix plot.

Usage:
    python evaluate.py --checkpoint ../checkpoints/gbert-compliance-classifier --data ../data/labeled_pairs.csv

Uses the same article-grouped train/val split as train.py (same random_state) so this reports
genuine held-out performance, not train-set performance.
"""

import argparse

import matplotlib.pyplot as plt
import torch
from dataset import ID_TO_LABEL, ClausePairDataset, train_val_split
from sklearn.metrics import ConfusionMatrixDisplay, classification_report
from torch.utils.data import DataLoader, Subset
from transformers import AutoModelForSequenceClassification, AutoTokenizer


def evaluate(checkpoint: str, data_path: str, output_plot: str):
    tokenizer = AutoTokenizer.from_pretrained(checkpoint)
    model = AutoModelForSequenceClassification.from_pretrained(checkpoint)
    model.eval()

    dataset = ClausePairDataset(data_path, tokenizer)
    _, val_idx = train_val_split(dataset)
    loader = DataLoader(Subset(dataset, val_idx), batch_size=8)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    all_preds, all_labels = [], []
    with torch.no_grad():
        for batch in loader:
            labels = batch.pop("labels")
            batch = {k: v.to(device) for k, v in batch.items()}
            logits = model(**batch).logits
            preds = torch.argmax(logits, dim=-1).cpu()
            all_preds.extend(preds.tolist())
            all_labels.extend(labels.tolist())

    label_names = [ID_TO_LABEL[i] for i in sorted(ID_TO_LABEL)]
    print(classification_report(all_labels, all_preds, target_names=label_names))

    fig, ax = plt.subplots(figsize=(6, 5))
    ConfusionMatrixDisplay.from_predictions(
        all_labels, all_preds, display_labels=label_names, ax=ax, xticks_rotation=30
    )
    fig.tight_layout()
    fig.savefig(output_plot)
    print(f"Saved confusion matrix to {output_plot}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default="../checkpoints/gbert-compliance-classifier")
    parser.add_argument("--data", default="../data/labeled_pairs.csv")
    parser.add_argument("--output-plot", default="../checkpoints/confusion_matrix.png")
    args = parser.parse_args()

    evaluate(args.checkpoint, args.data, args.output_plot)
