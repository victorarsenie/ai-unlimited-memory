# API v1

The first API increment is read-only and intended for the local Windows client.
It binds to loopback by default; LAN access and authentication are separate work.

## Install and run

```powershell
if (-not $env:PERSONAL_MEMORY_HOME) { $env:PERSONAL_MEMORY_HOME = Join-Path $env:LOCALAPPDATA 'PersonalMemory' }
$ApiVenv = Join-Path $env:PERSONAL_MEMORY_HOME 'api-venv'
uv venv $ApiVenv
uv pip install --python (Join-Path $ApiVenv 'Scripts\python.exe') -r requirements.txt
$env:PYTHONPATH = "$PWD\src"
python .\src\personal_memory\initialize.py
& (Join-Path $ApiVenv 'Scripts\python.exe') -m uvicorn personal_memory.api:app --host 127.0.0.1 --port 8765
```

Set `PERSONAL_MEMORY_HOME` before starting the API if the private data directory
is not `%LOCALAPPDATA%\PersonalMemory`. The API requires an initialized database
with the current migrations; it does not create or modify the data directory.

## `GET /api/v1/health`

Returns the API version and highest applied schema migration. It returns HTTP 503
with `DATABASE_UNAVAILABLE` if initialization has not been run.

## `GET /api/v1/search?q=...&limit=20&offset=0`

Searches message text, role, and conversation title with SQLite FTS5. `q` uses
FTS5 query syntax and is limited to 256 characters. `limit` is 1–100 and
`offset` is 0–10000. Results are ordered by FTS relevance and include message
identity, role, branch/variant context, excerpt, score, and provenance back to
the raw archive path and message locator. Raw message payloads are not returned
by search.

Invalid query syntax returns HTTP 422 with the common error shape:

```json
{"error":{"code":"INVALID_SEARCH_QUERY","message":"The search expression is not valid FTS5 syntax."}}
```

The database connection is opened with SQLite read-only mode. The FTS index is
regenerable and is maintained by migration-created triggers as canonical message
or conversation title records change.
