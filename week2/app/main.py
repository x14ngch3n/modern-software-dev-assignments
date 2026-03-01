"""FastAPI app: lifecycle, routes, and global error handling."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .db import init_db
from .routers import action_items, notes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup (e.g. init DB) and optionally cleanup on shutdown."""
    init_db()
    yield
    # Shutdown: nothing to close for SQLite per-connection model


app = FastAPI(title="Action Item Extractor", lifespan=lifespan)


@app.exception_handler(RuntimeError)
def handle_runtime_error(request: Request, exc: RuntimeError) -> JSONResponse:
    """Map database (and other) runtime errors to 500 without leaking details."""
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."},
    )


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    """Serve the frontend HTML."""
    html_path = config.BASE_DIR / "frontend" / "index.html"
    return html_path.read_text(encoding="utf-8")


app.include_router(notes.router)
app.include_router(action_items.router)

static_dir = config.BASE_DIR / "frontend"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
