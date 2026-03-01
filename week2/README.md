# Week 2 – Action Item Extractor

A small FastAPI application that turns free-form notes into structured action items. You can paste notes in the UI, extract tasks using either **rule-based heuristics** or an **LLM (Ollama)**, save notes and items to SQLite, list notes, and mark action items as done.

## Overview

- **Backend:** FastAPI with SQLite for notes and action items. Extraction is implemented two ways: a heuristic in `app/services/extract.py` (`extract_action_items`) and an LLM-based version (`extract_action_items_llm`) using Ollama with structured JSON output.
- **Frontend:** Single HTML page (in `frontend/index.html`) with “Extract”, “Extract LLM”, and “List Notes” buttons. Action items are shown as checkboxes that can be toggled done via the API.
- **API:** Pydantic request/response schemas in `app/schemas.py`; config and DB paths in `app/config.py` and `app/db.py`; routes under `/notes` and `/action-items`.

## Setup and run

**Requirements:** Python 3.10+, and [Ollama](https://ollama.com) installed and running if you use the “Extract LLM” feature.

1. From the **repository root** (parent of `week2/`), install dependencies and run the app:

   ```bash
   # With uv (recommended)
   uv run uvicorn week2.app.main:app --reload --host 127.0.0.1 --port 8000
   ```

   Or with Poetry:

   ```bash
   poetry run uvicorn week2.app.main:app --reload
   ```

2. Open a browser at **http://127.0.0.1:8000/**.

3. **Optional – LLM extraction:** Install and run Ollama, then pull a model (e.g. small one):

   ```bash
   ollama run llama3.2:3b
   ```

   Override the model with the `OLLAMA_MODEL` env var (default: `llama3.2:3b`). Override the DB/data directory with `WEEK2_DATA_DIR` if needed.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Serves the frontend HTML. |
| **Notes** | | |
| `POST` | `/notes` | Create a note. Body: `{"content": "..."}`. Returns `{id, content, created_at}`. |
| `GET` | `/notes` | List all notes (newest first). Returns array of `{id, content, created_at}`. |
| `GET` | `/notes/{note_id}` | Get one note by id. 404 if not found. |
| **Action items** | | |
| `POST` | `/action-items/extract` | Extract action items from text using **heuristics**. Body: `{"text": "...", "save_note": bool}`. Returns `{note_id?, items: [{id, text}, ...]}`. |
| `POST` | `/action-items/extract-llm` | Same as above but uses **Ollama LLM** for extraction. Requires Ollama and the configured model. |
| `GET` | `/action-items` | List action items. Query: optional `note_id` to filter by note. Returns array of `{id, note_id, text, done, created_at}`. |
| `POST` | `/action-items/{id}/done` | Mark item done/not done. Body: `{"done": true\|false}`. Returns `{id, done}`. |

All request/response shapes are defined by Pydantic schemas in `app/schemas.py`. Invalid or missing required fields yield 422; DB/runtime errors are mapped to 500 with a generic message.

## Running the test suite

From the **repository root**:

```bash
uv run pytest week2/tests/ -v
```

Or:

```bash
poetry run pytest week2/tests/ -v
```

Tests in `week2/tests/test_extract.py` cover the heuristic `extract_action_items()` and the LLM-based `extract_action_items_llm()` (with Ollama mocked so no server is required). Ensure the project’s virtualenv has the dependencies installed so imports resolve correctly.
