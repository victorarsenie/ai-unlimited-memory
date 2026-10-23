# Personal Memory

Local-first personal knowledge and memory system for Windows and Android. Each device is intended to keep a complete local copy; the two apps will synchronize changes when connected to the same local network or when the user starts sync. Personal imports and derived data stay outside this Git repository.

## Core purpose

The historical ChatGPT archive is imported in full as backfill. For current and future conversations, the primary goal is to preserve useful context through detailed, structured periodic checkpoints; these may compress repetition while retaining decisions/rationale, facts, preferences/corrections, actions/status/deadlines, open questions, changes, and source links. A checkpoint is derived, not a verbatim transcript. Preserve accessible raw transcripts intact in RAW. Capture method and coverage must be shown and validated.

## Current increment

Initialize the private data layout and canonical SQLite schema using Python 3.12:

```powershell
python .\src\personal_memory\initialize.py
```

By default, the initializer uses `%LOCALAPPDATA%\PersonalMemory`. To choose another location outside this checkout:

```powershell
python .\src\personal_memory\initialize.py --data-dir D:\AI\ai-unlimited-memory-data
```

Or set `PERSONAL_MEMORY_HOME`. The initializer creates `RAW/`, `INDEX/`, `DERIVED/`, and `backups/`, then applies versioned SQL migrations to `INDEX/personal_memory.sqlite3`. It does not import conversations or create demo content.

To inspect or import an export from PowerShell:

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m personal_memory.importers.chatgpt_export --archive "D:\AI\chatgpt_conversation_history.zip" --inspect-only
python -m personal_memory.importers.chatgpt_export --archive "D:\AI\chatgpt_conversation_history.zip" --data-dir "D:\AI\ai-unlimited-memory-data"
```

The first command reports aggregate counts only. The second preserves the archive in RAW and imports its conversations and referenced attachments into the private local database. Neither command writes conversation content to Git.

## Architecture

- [System requirements and scope](docs/project/requirements-and-scope.md)
- [System design](docs/superpowers/specs/2026-10-01-personal-memory-system-design.md)
- [Implementation plan](tasks/plan.md)
- [ADR-0001: SQLite local data foundation](docs/decisions/0001-sqlite-local-data-foundation.md)
- [Existing-solutions comparison](docs/research/existing-solutions-comparison.md)
- [English documentation](docs/en/README.md)

The ChatGPT export format has now been inspected locally. The modular importer targets the observed graph-shaped `conversations.json` format and retains unknown message payloads and branch structure. Run it explicitly; it stores the original ZIP and referenced attachment bytes in the private RAW directory. The real export and extracted folder are outside this repository.

A small [synthetic export fixture](examples/synthetic/chatgpt-export.zip) is included for public demonstrations. It was authored from scratch and contains only fictional data.
