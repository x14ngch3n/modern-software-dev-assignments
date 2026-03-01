"""Pydantic schemas for API request/response contracts."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


# ---- Notes ----
class NoteCreateRequest(BaseModel):
    """Request body for creating a note."""

    content: str = Field(..., min_length=1, description="Note text content")


class NoteResponse(BaseModel):
    """Single note in API responses."""

    id: int
    content: str
    created_at: str


# ---- Action items: extract ----
class ExtractRequest(BaseModel):
    """Request body for action-item extraction (heuristic or LLM)."""

    text: str = Field(..., min_length=1, description="Raw notes text to extract action items from")
    save_note: bool = Field(default=False, description="If true, persist the note and link items to it")


class ActionItemRef(BaseModel):
    """Single action item as returned from extract or list."""

    id: int
    text: str


class ExtractResponse(BaseModel):
    """Response from extract endpoint."""

    note_id: Optional[int] = None
    items: List[ActionItemRef]


# ---- Action items: list ----
class ActionItemResponse(BaseModel):
    """Full action item as returned by list endpoint."""

    id: int
    note_id: Optional[int] = None
    text: str
    done: bool
    created_at: str


# ---- Action items: mark done ----
class MarkDoneRequest(BaseModel):
    """Request body for marking an action item done/not done."""

    done: bool = True


class MarkDoneResponse(BaseModel):
    """Response after updating done status."""

    id: int
    done: bool
