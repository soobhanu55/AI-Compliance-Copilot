from app.rag.chunking import chunk_text


def test_chunk_text_empty_string_returns_no_chunks():
    assert chunk_text("") == []


def test_chunk_text_shorter_than_chunk_size_returns_single_chunk():
    text = "one two three"
    chunks = chunk_text(text, chunk_size=800, overlap=150)
    assert chunks == [text]


def test_chunk_text_splits_long_text_with_overlap():
    words = [f"w{i}" for i in range(1000)]
    text = " ".join(words)

    chunks = chunk_text(text, chunk_size=800, overlap=150)

    assert len(chunks) == 2
    first_words = chunks[0].split()
    second_words = chunks[1].split()
    assert first_words[0] == "w0"
    assert first_words[-1] == "w799"
    # overlap: second chunk should start 150 words before the first chunk ended
    assert second_words[0] == "w650"


def test_chunk_text_covers_every_word_at_least_once():
    words = [f"w{i}" for i in range(2500)]
    text = " ".join(words)

    chunks = chunk_text(text, chunk_size=800, overlap=150)
    covered = set()
    for chunk in chunks:
        covered.update(chunk.split())

    assert covered == set(words)
