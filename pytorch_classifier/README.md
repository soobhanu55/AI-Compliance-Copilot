# Compliance-Relevance Classifier — Model Card

## What it does

Fine-tuned `deepset/gbert-base` sentence-pair classifier. Given `(regulation clause,
company profile description)`, predicts one of:

- `applicable`
- `not_applicable`
- `needs_human_review`

Wired into the gap-report pipeline at [`backend/app/agents/classifier.py`](../backend/app/agents/classifier.py)
and [`backend/app/agents/report_agent.py`](../backend/app/agents/report_agent.py). Predictions
below a 0.6 confidence threshold are downgraded to `needs_human_review` regardless of the raw
argmax — see "Metrics" below for why that threshold matters in practice.

## Status

**Trained, proof-of-concept quality — improved after a first dataset expansion.** Macro F1
went from 0.50 (140 rows / 35 articles) to **0.69** (188 rows / 47 articles) after adding 12
more real articles to categories that were already being reasoned about. Still small enough
that every prediction should be treated as a first-pass triage aid, not a determination — but
the direction and size of the improvement is a genuine, measured result, not a guess.

## Training data

- **Source**: [`data/labeled_pairs.csv`](data/labeled_pairs.csv), built by
  [`scripts/build_labeled_dataset.py`](scripts/build_labeled_dataset.py) — 188 rows crossing
  **47 curated articles** (24 AI Act, 13 NIS2, 10 CSRD, read from the real EUR-Lex text in
  `data_pipeline/regulations/*_articles.json`) against the 4 synthetic SME profiles in
  `data_pipeline/synthetic_profiles/profiles.json`.
- **Labeling methodology — read this before trusting the data**: labels are **not**
  crowd-sourced or independently verified ground truth. Each curated article was read in full
  and assigned to one of 22 "obligation categories" (e.g. `ai_high_risk_provider_obligation`,
  `nis2_risk_mgmt`, `csrd_reporting_large`). For each synthetic profile, every category then
  got one applicability verdict + written rationale, reasoned from that profile's stated facts.
  Every article sharing a category gets the same verdict from a given profile — this is
  rule-based weak supervision applied at the (profile × category) level, not per-row human
  annotation. It is disclosed as such, not presented as ground truth.
- **The first expansion (35 → 47 articles) added no new categories or profile-reasoning** — all
  12 new articles (e.g. AI Act Art. 21/25/43/49, NIS2 Art. 22/25/26/30, CSRD Art. 40b/40c/27a/28a)
  were mapped onto the 22 categories already reasoned through in the first pass, on the
  judgment that they raise the same underlying applicability question as an existing article in
  that category (e.g. NIS2 Art. 30's voluntary notification raises the same question as Art. 29's
  voluntary information-sharing). This is real new regulatory text, not label noise — but it
  means the *coverage* of distinct applicability questions didn't grow, only the amount of text
  per question.
- **Label distribution**: 30 `applicable` / 88 `needs_human_review` / 70 `not_applicable` (was
  22/67/51 before the expansion) — the imbalance reflects the profiles themselves (e.g. the
  smallest, no-AI profile is mostly `not_applicable`; the largest, AI-heavy profile is mostly
  `applicable`/`needs_human_review`), not an artificial balancing choice.
- **Known bias risk**: profiles and labels were written by the project author (AI-assisted),
  not sourced from real companies or a legal professional. The classifier will not generalize
  to profile phrasing, sectors, or edge cases outside this set without further labeling.

## Train/eval methodology

- **Split**: grouped by `article`, not by row (`scripts/dataset.py::train_val_split`,
  `sklearn.model_selection.GroupShuffleSplit`, 80/20, `random_state=42`) — 152 train rows / 36
  val rows (was 108/32). Each article appears once per profile (4x) with identical
  `clause_text`; a plain row-level split would let the model see the same clause text in both
  train and val, just paired with a different profile, which would overstate generalization.
  The group split means val-set articles are genuinely unseen during training.
- **Training**: 8 epochs, batch size 8, lr 2e-5, AdamW, CPU. Full loss curve in
  `checkpoints/gbert-compliance-classifier/history.json`.

  | epoch | train_loss (188-row) | val_loss (188-row) | train_loss (140-row, prior run) | val_loss (140-row, prior run) |
  |---|---|---|---|---|
  | 1 | 1.041 | 1.024 | 1.004 | 1.054 |
  | 2 | 0.914 | 0.968 | 0.789 | 1.411 |
  | 3 | 0.726 | 0.951 | 0.706 | 1.494 |
  | 4 | 0.556 | 0.948 | 0.669 | 1.494 |
  | 5 | 0.491 | 1.004 | 0.670 | 1.334 |
  | 6 | 0.381 | 0.977 | 0.634 | 1.365 |
  | 7 | 0.292 | 0.896 | 0.515 | 1.280 |
  | 8 | 0.257 | 0.912 | 0.389 | 1.333 |

  Val loss is both lower and far more stable this run (0.90–1.02 vs. 1.28–1.49 before) — the
  extra data measurably reduced overfitting, it didn't just add more of the same noise.

## Metrics (held-out val split, 36 examples, unseen articles)

```
                    precision    recall  f1-score   support

    not_applicable       0.90      0.60      0.72        15
        applicable       0.57      0.57      0.57         7
needs_human_review       0.68      0.93      0.79        14

          accuracy                           0.72        36
         macro avg       0.72      0.70      0.69        36
      weighted avg       0.75      0.72      0.72        36
```

**Before vs. after the 140 → 188 row expansion:**

| | 140 rows (35 articles) | 188 rows (47 articles) |
|---|---|---|
| Accuracy | 0.53 | **0.72** |
| Macro F1 | 0.50 | **0.69** |
| `applicable` F1 | 0.33 | **0.57** |
| `not_applicable` F1 | 0.58 | **0.72** |
| `needs_human_review` F1 | 0.57 | **0.79** |

Every class improved, `applicable` (previously the weakest, with only 4 val examples) the most
in relative terms. Confusion matrix: [`checkpoints/confusion_matrix.png`](checkpoints/confusion_matrix.png).
The remaining error mode is still `not_applicable` articles occasionally getting predicted as
`needs_human_review` (4 of 15) — mistakes still lean toward the conservative side, which is the
direction you want them to lean if they're going to be wrong.

**Macro F1 of 0.69 is a real improvement, not yet a reliable classifier.** 47 articles and 4
profiles is still a small, narrow dataset. The jump from a small, targeted expansion suggests
more labeling is the highest-leverage next step if this needs to go beyond a demo — but that's
an inference from one data point, not a guaranteed trend.

## Intended use

Pre-screening step inside the gap-report pipeline — narrows the set of regulation clauses a
human (or the LLM drafting agent) needs to look at closely. **Not** a substitute for legal
advice, and not a certified compliance determination. `report_agent.py` forces any prediction
under 60% confidence to `needs_human_review`.

## Limitations

- 152 training rows for a 110M-parameter model is still too little for reliable
  generalization to real-world companies outside the 4 synthetic profiles.
- Training data covers only 47 of the ~191 substantive articles across the three regulations,
  and only 4 company profiles — real SMEs will present facts and phrasing this dataset never
  saw.
- The 35→47 article expansion added text volume within existing applicability *questions*, not
  new questions — it doesn't test whether the classifier generalizes to genuinely novel
  obligation types. That's a fair next test before claiming broader coverage.
- No adversarial or edge-case testing.
- Regulation texts change (e.g. AI Act delegated acts, national NIS2 transposition) — the
  classifier does not know about amendments after `data_pipeline/regulations/*_articles.json`
  was fetched.
- `applicable` remains the smallest class (7 val examples) — treat a confident `applicable`
  prediction with the same scrutiny as `needs_human_review`, i.e. always check the cited
  article yourself.

## Reproducing

```bash
cd pytorch_classifier/scripts
python build_labeled_dataset.py       # writes ../data/labeled_pairs.csv
python train.py --epochs 8            # writes ../checkpoints/gbert-compliance-classifier/
python evaluate.py                    # prints the classification report, writes confusion_matrix.png
```
