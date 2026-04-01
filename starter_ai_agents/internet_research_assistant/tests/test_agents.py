"""
Tests for agent utilities and helper functions (no OpenAI calls).
"""
import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.helpers import (
    make_cache_key,
    truncate_text,
    sanitize_query,
    format_sources,
    extract_json,
    score_confidence,
    generate_session_id,
)
from utils.database import Database


# ──────────────────────────────────────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────────────────────────────────────

def test_make_cache_key_deterministic():
    k1 = make_cache_key("Hello World")
    k2 = make_cache_key("hello world")
    assert k1 == k2  # case-insensitive, normalised


def test_make_cache_key_different_inputs():
    assert make_cache_key("query A") != make_cache_key("query B")


def test_truncate_short_text():
    assert truncate_text("hello", 100) == "hello"


def test_truncate_long_text():
    text = " ".join(["word"] * 200)
    result = truncate_text(text, 50)
    assert len(result) <= 52  # small buffer for ellipsis
    assert result.endswith("…")


def test_sanitize_query_removes_special_chars():
    dirty = "SELECT * FROM users; DROP TABLE--"
    clean = sanitize_query(dirty)
    assert ";" not in clean
    assert "--" not in clean


def test_sanitize_query_collapses_whitespace():
    assert sanitize_query("  too   many   spaces  ") == "too many spaces"


def test_format_sources_empty():
    result = format_sources([])
    assert "No sources" in result


def test_format_sources_with_items():
    sources = [{"title": "Test", "url": "http://example.com", "snippet": "A test snippet."}]
    result = format_sources(sources)
    assert "Test" in result
    # Check that the URL appears as a complete markdown link, not just a substring
    assert "](http://example.com)" in result


def test_extract_json_object():
    text = 'some text {"key": "value"} more text'
    result = extract_json(text)
    assert result == {"key": "value"}


def test_extract_json_array():
    text = 'here ["a", "b", "c"] end'
    result = extract_json(text)
    assert result == ["a", "b", "c"]


def test_extract_json_none_when_missing():
    assert extract_json("no json here") is None


def test_score_confidence_empty():
    assert score_confidence([], "") == 0.0


def test_score_confidence_with_data():
    sources = [
        {"source": "bbc.com", "url": "http://bbc.com/a"},
        {"source": "reuters.com", "url": "http://reuters.com/b"},
        {"source": "cnn.com", "url": "http://cnn.com/c"},
    ]
    score = score_confidence(sources, "A" * 600)
    assert 0.0 < score <= 1.0


def test_generate_session_id_unique():
    ids = {generate_session_id() for _ in range(100)}
    assert len(ids) == 100


# ──────────────────────────────────────────────────────────────────────────────
# Database
# ──────────────────────────────────────────────────────────────────────────────

def _make_db():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    return Database(tmp.name), tmp.name


def test_db_save_and_retrieve_message():
    db, path = _make_db()
    try:
        db.save_message("sess-1", "user", "Hello")
        db.save_message("sess-1", "assistant", "Hi there!")
        msgs = db.get_conversation("sess-1")
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[1]["content"] == "Hi there!"
    finally:
        db.close()
        os.unlink(path)


def test_db_list_sessions():
    db, path = _make_db()
    try:
        db.save_message("sess-A", "user", "msg1")
        db.save_message("sess-B", "user", "msg2")
        sessions = db.list_sessions()
        session_ids = [s["session_id"] for s in sessions]
        assert "sess-A" in session_ids
        assert "sess-B" in session_ids
    finally:
        db.close()
        os.unlink(path)


def test_db_delete_session():
    db, path = _make_db()
    try:
        db.save_message("sess-X", "user", "to delete")
        db.delete_session("sess-X")
        msgs = db.get_conversation("sess-X")
        assert len(msgs) == 0
    finally:
        db.close()
        os.unlink(path)


def test_db_cache_set_and_get():
    db, path = _make_db()
    try:
        db.cache_set("my_key", "my_value", ttl_seconds=3600)
        result = db.cache_get("my_key")
        assert result == "my_value"
    finally:
        db.close()
        os.unlink(path)


def test_db_cache_returns_none_for_missing():
    db, path = _make_db()
    try:
        assert db.cache_get("does_not_exist") is None
    finally:
        db.close()
        os.unlink(path)


def test_db_log_and_get_analytics():
    db, path = _make_db()
    try:
        db.log_search("sess-1", "test query", sources=3, cached=False, duration_ms=250)
        analytics = db.get_analytics()
        assert len(analytics) >= 1
        assert analytics[0]["query"] == "test query"
    finally:
        db.close()
        os.unlink(path)


if __name__ == "__main__":
    test_make_cache_key_deterministic()
    test_make_cache_key_different_inputs()
    test_truncate_short_text()
    test_truncate_long_text()
    test_sanitize_query_removes_special_chars()
    test_sanitize_query_collapses_whitespace()
    test_format_sources_empty()
    test_format_sources_with_items()
    test_extract_json_object()
    test_extract_json_array()
    test_extract_json_none_when_missing()
    test_score_confidence_empty()
    test_score_confidence_with_data()
    test_generate_session_id_unique()
    test_db_save_and_retrieve_message()
    test_db_list_sessions()
    test_db_delete_session()
    test_db_cache_set_and_get()
    test_db_cache_returns_none_for_missing()
    test_db_log_and_get_analytics()
    print("All agent/helper tests passed ✅")
