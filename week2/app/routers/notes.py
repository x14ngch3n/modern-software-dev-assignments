"""Notes API: create, get by id, list all."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import db
from ..schemas import NoteCreateRequest, NoteResponse

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("", response_model=NoteResponse)
def create_note(payload: NoteCreateRequest) -> NoteResponse:
    """Create a note from the given content. Content must be non-empty."""
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="content is required")
    note_id = db.insert_note(content)
    note = db.get_note(note_id)
    if note is None:
        raise HTTPException(status_code=500, detail="Note was not found after insert")
    return NoteResponse(id=note["id"], content=note["content"], created_at=note["created_at"])


@router.get("/{note_id}", response_model=NoteResponse)
def get_single_note(note_id: int) -> NoteResponse:
    """Return a single note by id. 404 if not found."""
    row = db.get_note(note_id)
    if row is None:
        raise HTTPException(status_code=404, detail="note not found")
    return NoteResponse(id=row["id"], content=row["content"], created_at=row["created_at"])


@router.get("", response_model=list[NoteResponse])
def list_all_notes() -> list[NoteResponse]:
    """Return all notes (newest first)."""
    rows = db.list_notes()
    return [NoteResponse(id=r["id"], content=r["content"], created_at=r["created_at"]) for r in rows]
