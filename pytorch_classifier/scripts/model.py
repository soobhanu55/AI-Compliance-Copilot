from transformers import AutoModelForSequenceClassification, AutoTokenizer

from dataset import ID_TO_LABEL, LABEL_TO_ID

BASE_MODEL = "deepset/gbert-base"  # German BERT; swap for distilbert-base-german-cased for speed


def load_model_and_tokenizer(checkpoint: str = BASE_MODEL):
    tokenizer = AutoTokenizer.from_pretrained(checkpoint)
    model = AutoModelForSequenceClassification.from_pretrained(
        checkpoint,
        num_labels=len(LABEL_TO_ID),
        id2label=ID_TO_LABEL,
        label2id=LABEL_TO_ID,
    )
    return model, tokenizer
