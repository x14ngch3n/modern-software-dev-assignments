import json
import os
import pytest
from unittest.mock import patch, MagicMock

from ..app.services.extract import extract_action_items, extract_action_items_llm


def test_extract_bullets_and_checkboxes():
    text = """
    Notes from meeting:
    - [ ] Set up database
    * implement API extract endpoint
    1. Write tests
    Some narrative sentence.
    """.strip()

    items = extract_action_items(text)
    assert "Set up database" in items
    assert "implement API extract endpoint" in items
    assert "Write tests" in items


# ---- Unit tests for extract_action_items_llm (mock Ollama so no server required) ----


def test_extract_action_items_llm_empty_input():
    """Empty string returns [] and does not call the LLM."""
    with patch("week2.app.services.extract.chat") as mock_chat:
        result = extract_action_items_llm("")
        assert result == []
        mock_chat.assert_not_called()


def test_extract_action_items_llm_whitespace_only():
    """Whitespace-only input returns [] and does not call the LLM."""
    with patch("week2.app.services.extract.chat") as mock_chat:
        result = extract_action_items_llm("   \n\t  ")
        assert result == []
        mock_chat.assert_not_called()


def _make_ollama_response(action_items: list[str]) -> MagicMock:
    """Build a mock Ollama chat response with the given action_items."""
    body = json.dumps({"action_items": action_items})
    response = MagicMock()
    response.message.content = body
    return response


def test_extract_action_items_llm_bullet_list():
    """Bullet-list notes: LLM response is parsed and returned as list of strings."""
    text = """
    - [ ] Set up database
    * implement API extract endpoint
    1. Write tests
    """
    expected = ["Set up database", "implement API extract endpoint", "Write tests"]
    with patch("week2.app.services.extract.chat") as mock_chat:
        mock_chat.return_value = _make_ollama_response(expected)
        result = extract_action_items_llm(text)
        assert result == expected
        mock_chat.assert_called_once()
        # Check that the user message contains the input text
        call_kw = mock_chat.call_args[1]
        assert "Set up database" in call_kw["messages"][0]["content"]
        assert call_kw.get("format") is not None
        assert call_kw.get("options") == {"temperature": 0}


def test_extract_action_items_llm_keyword_prefixed():
    """Notes with todo:/action:/next: style lines; LLM returns extracted items."""
    text = "todo: Review PR\naction: Deploy to staging\nnext: Update docs"
    expected = ["Review PR", "Deploy to staging", "Update docs"]
    with patch("week2.app.services.extract.chat") as mock_chat:
        mock_chat.return_value = _make_ollama_response(expected)
        result = extract_action_items_llm(text)
        assert result == expected
        mock_chat.assert_called_once()
        call_kw = mock_chat.call_args[1]
        assert "todo:" in call_kw["messages"][0]["content"]


def test_extract_action_items_llm_empty_response():
    """When the LLM returns no action items, we get an empty list."""
    text = "Some notes with no clear tasks."
    with patch("week2.app.services.extract.chat") as mock_chat:
        mock_chat.return_value = _make_ollama_response([])
        result = extract_action_items_llm(text)
        assert result == []
        mock_chat.assert_called_once()
