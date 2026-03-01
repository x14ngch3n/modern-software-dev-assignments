from __future__ import annotations

import os
import re
from typing import List
import json
from typing import Any
from ollama import chat
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Default Ollama model for action-item extraction (small model for lower resource use).
# Override with OLLAMA_MODEL env var, e.g. OLLAMA_MODEL=llama3.2:3b
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")


class ActionItemsResponse(BaseModel):
    """Schema for LLM-structured output: a single field holding the list of action items."""

    action_items: List[str]

BULLET_PREFIX_PATTERN = re.compile(r"^\s*([-*•]|\d+\.)\s+")
KEYWORD_PREFIXES = (
    "todo:",
    "action:",
    "next:",
)


def _is_action_line(line: str) -> bool:
    stripped = line.strip().lower()
    if not stripped:
        return False
    if BULLET_PREFIX_PATTERN.match(stripped):
        return True
    if any(stripped.startswith(prefix) for prefix in KEYWORD_PREFIXES):
        return True
    if "[ ]" in stripped or "[todo]" in stripped:
        return True
    return False


def extract_action_items(text: str) -> List[str]:
    lines = text.splitlines()
    extracted: List[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if _is_action_line(line):
            cleaned = BULLET_PREFIX_PATTERN.sub("", line)
            cleaned = cleaned.strip()
            # Trim common checkbox markers
            cleaned = cleaned.removeprefix("[ ]").strip()
            cleaned = cleaned.removeprefix("[todo]").strip()
            extracted.append(cleaned)
    # Fallback: if nothing matched, heuristically split into sentences and pick imperative-like ones
    if not extracted:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        for sentence in sentences:
            s = sentence.strip()
            if not s:
                continue
            if _looks_imperative(s):
                extracted.append(s)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: List[str] = []
    for item in extracted:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(item)
    return unique


def extract_action_items_llm(text: str) -> List[str]:
    """
    Extract action items from free-form notes using an LLM (Ollama).
    Returns a list of action item strings. Uses structured output (JSON schema)
    so the model returns a JSON object with an "action_items" array of strings.

    Requires Ollama to be running locally with the configured model pulled
    (e.g. `ollama run llama3.2:3b`). Model can be overridden via OLLAMA_MODEL.
    """
    stripped = text.strip()
    if not stripped:
        return []

    response = chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "user",
                "content": (
                    "From the following notes, extract all action items, tasks, or to-dos. "
                    "Return each as a clear, concise phrase. Ignore narrative or non-action text. "
                    "Return as JSON.\n\n"
                    f"{stripped}"
                ),
            }
        ],
        format=ActionItemsResponse.model_json_schema(),
        options={"temperature": 0},
    )

    parsed = ActionItemsResponse.model_validate_json(response.message.content)
    return list(parsed.action_items) if parsed.action_items else []


def _looks_imperative(sentence: str) -> bool:
    words = re.findall(r"[A-Za-z']+", sentence)
    if not words:
        return False
    first = words[0]
    # Crude heuristic: treat these as imperative starters
    imperative_starters = {
        "add",
        "create",
        "implement",
        "fix",
        "update",
        "write",
        "check",
        "verify",
        "refactor",
        "document",
        "design",
        "investigate",
    }
    return first.lower() in imperative_starters
