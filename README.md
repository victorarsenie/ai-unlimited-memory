# Personal Memory

Local-first personal knowledge and memory system for Windows and Android. The PC is planned as the canonical source of truth; Android access, search, and offline synchronization will be added incrementally. Personal imports and derived data stay outside this Git repository.

## Current increment

Initialize the private data layout and canonical SQLite schema using Python 3.12:

```powershell
python .\src\personal_memory\initialize.py
```

By default, the initializer uses `%LOCALAPPDATA%\PersonalMemory`. To choose another location outside this checkout:

```powershell
python .\src\personal_memory\initialize.py --data-dir D:\AI\PersonalMemoryData
```

Or set `PERSONAL_MEMORY_HOME`. The initializer creates `RAW/`, `INDEX/`, `DERIVED/`, and `backups/`, then applies versioned SQL migrations to `INDEX/personal_memory.sqlite3`. It does not import conversations or create demo content.

## Architecture

- [System requirements and scope](docs/project/requirements-and-scope.md)
- [System design](docs/superpowers/specs/2026-10-01-personal-memory-system-design.md)
- [Implementation plan](tasks/plan.md)
- [ADR-0001: SQLite local data foundation](docs/decisions/0001-sqlite-local-data-foundation.md)
- [Existing-solutions comparison](docs/research/existing-solutions-comparison.md)
- [English documentation](docs/en/README.md)

The ChatGPT export has not been inspected. Its importer will be implemented only after the actual archive and included documentation are available.
