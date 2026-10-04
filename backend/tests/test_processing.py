import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import calculate_reduction, preprocess_text, split_into_chunks


def test_preprocess_text_removes_headers_and_extra_whitespace():
    raw_text = """
    From: alice@example.com

    To: bob@example.com
    Subject: Weekly update
    Date: 2026-08-11


    Hello   world!


    This is a test.

    > Previous email text
    On August 10, Alice wrote:
    Thanks for the update.

    Best,
    Alice
    """

    cleaned = preprocess_text(raw_text)

    assert "From:" not in cleaned
    assert "Subject:" not in cleaned
    assert "Best," not in cleaned
    assert "Alice" not in cleaned
    assert "Hello world!" in cleaned
    assert "This is a test." in cleaned
    assert "\n\n\n" not in cleaned


def test_split_into_chunks_respects_max_words():
    long_text = " ".join([f"Sentence {i} about the summarizer and chunking logic." for i in range(20)])

    chunks = split_into_chunks(long_text, max_words=8)

    assert len(chunks) > 1
    assert all(len(chunk.split()) <= 8 for chunk in chunks)


def test_calculate_reduction_handles_zero_original_words():
    assert calculate_reduction(0, 5) == 0.0
    assert calculate_reduction(100, 50) == 50.0
