"""Versioned, read-only HTTP API for local Personal Memory search."""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from personal_memory.initialize import default_data_dir
from personal_memory.search import SearchQueryError, search_messages


def _database_path() -> Path:
    configured = os.environ.get("PERSONAL_MEMORY_HOME")
    data_dir = Path(configured).expanduser() if configured else default_data_dir()
    return data_dir / "INDEX" / "personal_memory.sqlite3"


def _connect_read_only(database_path: Path) -> sqlite3.Connection:
    if not database_path.is_file():
        raise HTTPException(
            status_code=503,
            detail={"code": "DATABASE_UNAVAILABLE", "message": "Initialize the local data directory first."},
        )
    connection = sqlite3.connect(database_path.resolve().as_uri() + "?mode=ro", uri=True, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def create_app(database_path: Path | None = None) -> FastAPI:
    app = FastAPI(
        title="Personal Memory API",
        version="1",
        description="Read-only local search with source provenance.",
    )
    resolved_database = database_path.resolve() if database_path else None

    def open_connection() -> sqlite3.Connection:
        return _connect_read_only(resolved_database or _database_path())

    @app.exception_handler(SearchQueryError)
    async def invalid_search_query(_request: Request, error: SearchQueryError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "INVALID_SEARCH_QUERY", "message": str(error)}},
        )

    @app.exception_handler(RequestValidationError)
    async def invalid_parameters(_request: Request, _error: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "VALIDATION_ERROR", "message": "Invalid query parameters."}},
        )

    @app.exception_handler(HTTPException)
    async def api_http_error(_request: Request, error: HTTPException) -> JSONResponse:
        detail = error.detail if isinstance(error.detail, dict) else {}
        return JSONResponse(
            status_code=error.status_code,
            content={
                "error": {
                    "code": detail.get("code", "HTTP_ERROR"),
                    "message": detail.get("message", "The request could not be completed."),
                }
            },
        )

    @app.get("/api/v1/health")
    def health() -> dict[str, Any]:
        with closing(open_connection()) as connection:
            version = connection.execute(
                "SELECT max(version) FROM schema_migrations"
            ).fetchone()[0]
        return {"status": "ok", "apiVersion": "1", "schemaVersion": version}

    @app.get("/api/v1/search")
    def search(
        q: str = Query(min_length=1, max_length=256),
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0, le=10000),
    ) -> dict[str, Any]:
        with closing(open_connection()) as connection:
            return search_messages(connection, q, limit=limit, offset=offset)

    return app


app = create_app()
