"""Initialize a private Personal Memory data directory and its SQLite schema."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sqlite3
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = Path(__file__).with_name("migrations")
MIGRATION_NAME = re.compile(r"^(\d{3,})_[a-z0-9_]+\.sql$")
DATA_DIRS = ("RAW", "INDEX", "DERIVED", "backups")


def default_data_dir() -> Path:
    """Return a per-user data location outside the source checkout."""
    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "PersonalMemory"
    return Path.home() / ".local" / "share" / "personal-memory"


def ensure_outside_repository(data_dir: Path) -> Path:
    resolved = data_dir.expanduser().resolve()
    if resolved == PROJECT_ROOT or PROJECT_ROOT in resolved.parents:
        raise ValueError(
            f"Personal data must stay outside the Git checkout ({PROJECT_ROOT})."
        )
    return resolved


def connect(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 30000")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def apply_migrations(connection: sqlite3.Connection) -> None:
    connection.execute(
        """CREATE TABLE IF NOT EXISTS schema_migrations (
               version INTEGER PRIMARY KEY,
               name TEXT NOT NULL,
               sha256 TEXT NOT NULL,
               applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
           )"""
    )
    connection.commit()

    for migration_path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        match = MIGRATION_NAME.fullmatch(migration_path.name)
        if not match:
            raise ValueError(f"Invalid migration filename: {migration_path.name}")

        version = int(match.group(1))
        sql = migration_path.read_text(encoding="utf-8")
        checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
        previous = connection.execute(
            "SELECT name, sha256 FROM schema_migrations WHERE version = ?",
            (version,),
        ).fetchone()

        if previous:
            if previous["name"] != migration_path.name or previous["sha256"] != checksum:
                raise RuntimeError(
                    f"Applied migration {version} was changed; add a new migration instead."
                )
            continue

        try:
            connection.executescript("BEGIN IMMEDIATE;\n" + sql)
            connection.execute(
                "INSERT INTO schema_migrations(version, name, sha256) VALUES (?, ?, ?)",
                (version, migration_path.name, checksum),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise


def initialize(data_dir: Path) -> Path:
    root = ensure_outside_repository(data_dir)
    for directory in DATA_DIRS:
        (root / directory).mkdir(parents=True, exist_ok=True)

    database_path = root / "INDEX" / "personal_memory.sqlite3"
    with connect(database_path) as connection:
        apply_migrations(connection)
    return database_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create the private RAW/INDEX/DERIVED data layout and initial schema."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(os.environ["PERSONAL_MEMORY_HOME"])
        if os.environ.get("PERSONAL_MEMORY_HOME")
        else default_data_dir(),
        help="Private data directory (defaults to %LOCALAPPDATA%/PersonalMemory on Windows).",
    )
    args = parser.parse_args()

    try:
        database_path = initialize(args.data_dir)
    except (OSError, ValueError, RuntimeError, sqlite3.Error) as error:
        print(f"Initialization failed: {error}", file=sys.stderr)
        return 1

    print(f"Personal Memory initialized: {database_path.parent.parent}")
    print(f"Database: {database_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
