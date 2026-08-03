"""Fine-tune the compliance-relevance classifier.

Usage:
    python train.py --data ../data/labeled_pairs.csv --epochs 5

Splits by *article*, not by row: each article appears 4 times in the dataset (once per
synthetic company profile) with identical clause_text. A random row-level split would let the
model see the same clause_text in both train and val, just paired with a different profile —
an easy way to overstate how well it generalizes. GroupShuffleSplit keeps every occurrence of
a given article on one side of the split.
"""

import argparse
import json
from pathlib import Path

import torch
from dataset import ClausePairDataset, train_val_split
from model import load_model_and_tokenizer
from torch.utils.data import DataLoader, Subset
from torch.optim import AdamW


def train(data_path: str, epochs: int, batch_size: int, lr: float, output_dir: str):
    model, tokenizer = load_model_and_tokenizer()
    dataset = ClausePairDataset(data_path, tokenizer)

    train_idx, val_idx = train_val_split(dataset)
    train_loader = DataLoader(Subset(dataset, train_idx), batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(Subset(dataset, val_idx), batch_size=batch_size)
    print(f"train rows: {len(train_idx)}, val rows: {len(val_idx)} (split by article, not row)")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    optimizer = AdamW(model.parameters(), lr=lr)

    history = {"train_loss": [], "val_loss": []}

    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        for batch in train_loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            optimizer.zero_grad()
            outputs = model(**batch)
            outputs.loss.backward()
            optimizer.step()
            total_loss += outputs.loss.item()
        train_loss = total_loss / max(len(train_loader), 1)

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch in val_loader:
                batch = {k: v.to(device) for k, v in batch.items()}
                outputs = model(**batch)
                val_loss += outputs.loss.item()
        val_loss = val_loss / max(len(val_loader), 1)

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        print(f"epoch {epoch + 1}/{epochs}  train_loss={train_loss:.4f}  val_loss={val_loss:.4f}")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_path)
    tokenizer.save_pretrained(output_path)
    (output_path / "history.json").write_text(json.dumps(history, indent=2))
    print(f"Saved checkpoint + training history to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="../data/labeled_pairs.csv")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--output-dir", default="../checkpoints/gbert-compliance-classifier")
    args = parser.parse_args()

    train(args.data, args.epochs, args.batch_size, args.lr, args.output_dir)
