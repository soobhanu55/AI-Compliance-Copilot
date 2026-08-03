import pandas as pd
import torch
from sklearn.model_selection import GroupShuffleSplit
from torch.utils.data import Dataset

LABELS = ["not_applicable", "applicable", "needs_human_review"]
LABEL_TO_ID = {label: i for i, label in enumerate(LABELS)}
ID_TO_LABEL = {i: label for label, i in LABEL_TO_ID.items()}


class ClausePairDataset(Dataset):
    """(regulation clause, company profile) pairs labeled applicable / not_applicable /
    needs_human_review. Encoded as a sentence-pair classification task.
    """

    def __init__(self, csv_path: str, tokenizer, max_length: int = 256):
        self.df = pd.read_csv(csv_path)
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> dict:
        row = self.df.iloc[idx]
        encoding = self.tokenizer(
            row["clause_text"],
            row["company_profile_text"],
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )
        item = {k: v.squeeze(0) for k, v in encoding.items()}
        item["labels"] = torch.tensor(LABEL_TO_ID[row["label"]], dtype=torch.long)
        return item


def train_val_split(dataset: "ClausePairDataset", test_size: float = 0.2, random_state: int = 42):
    """Group by `article` so every occurrence of a given article (once per company profile in
    this dataset) stays on one side of the split — otherwise the model could see the exact same
    clause_text in both train and val, just paired with a different profile.
    """
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    return next(splitter.split(dataset.df, groups=dataset.df["article"]))
