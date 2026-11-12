import pytest

from chunking import chunk_text


def test_chunk_text_with_overlap():
    result = chunk_text("abcdefghijklmnopqrstuvwxyz", 10, 3)
    assert result == ["abcdefghij", "hijklmnopq", "opqrstuvwx", "vwxyz"]

def test_chunk_shorter_than_chunk_size():
    result = chunk_text("abc", 10, 3)
    assert result == ["abc"]

def test_chunk_text_empty_text():
    assert chunk_text("", 10, 3) == []

def test_chunk_text_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_text("abc", 10, 10)