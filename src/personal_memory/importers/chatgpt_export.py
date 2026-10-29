"""Import ChatGPT account exports while keeping original bytes in RAW."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import mimetypes
import os
import re
import sqlite3
import sys
import tempfile
import uuid
import zipfile
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO

try:
    from personal_memory.initialize import connect, default_data_dir, initialize
except ModuleNotFoundError:
    # Also support direct execution from this source checkout.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from personal_memory.initialize import connect, default_data_dir, initialize


ADAPTER_NAME = "chatgpt-account-export"
ADAPTER_VERSION = "1.0.0"
NAMESPACE = uuid.UUID("45d26baa-4486-4bf6-9a20-1fd391f55eea")
MAX_ARCHIVE_BYTES = 2 * 1024 * 1024 * 1024
MAX_MEMBER_BYTES = 1024 * 1024 * 1024
ASSET_ID = re.compile(r"(file_[A-Za-z0-9_-]+)")


class ChatGPTExportError(ValueError):
    """Raised when an export is malformed or unsafe to ingest."""


@dataclass(frozen=True)
class ExportInventory:
    archive_sha256: str
    archive_bytes: int
    archive_members: int
    conversations: int
    mapping_nodes: int
    messages: int
    role_counts: dict[str, int]
    asset_references: int
    resolvable_asset_references: int
    unresolved_asset_references: int


@dataclass(frozen=True)
class ImportReport:
    adapter: str
    adapter_version: str
    archive_sha256: str
    archive_bytes: int
    conversations: int
    mapping_nodes: int
    messages: int
    role_counts: dict[str, int]
    attachment_references: int
    attachments_preserved: int
    unresolved_asset_references: int
    raw_archive_path: str
    already_imported: bool = False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return str(uuid.uuid5(NAMESPACE, value))


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def _validate_member_name(name: str) -> str:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if not path.parts or path.is_absolute() or any(part in ("..", "") for part in path.parts):
        raise ChatGPTExportError("The archive contains an unsafe member path.")
    if ":" in path.parts[0]:
        raise ChatGPTExportError("The archive contains an unsafe member path.")
    return normalized


def _archive_members(archive: zipfile.ZipFile) -> dict[str, zipfile.ZipInfo]:
    members: dict[str, zipfile.ZipInfo] = {}
    total = 0
    for info in archive.infolist():
        if info.is_dir():
            continue
        name = _validate_member_name(info.filename)
        if name in members:
            raise ChatGPTExportError("The archive contains duplicate file names.")
        if info.flag_bits & 0x1:
            raise ChatGPTExportError("Encrypted ZIP entries are not supported.")
        if info.file_size > MAX_MEMBER_BYTES:
            raise ChatGPTExportError("An archive member exceeds the supported size limit.")
        total += info.file_size
        if total > MAX_ARCHIVE_BYTES:
            raise ChatGPTExportError("The expanded archive exceeds the supported size limit.")
        members[name] = info
    return members


def _read_json_member(archive: zipfile.ZipFile, member: zipfile.ZipInfo) -> Any:
    try:
        with archive.open(member, "r") as stream:
            return json.load(io.TextIOWrapper(stream, encoding="utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError, OSError, RuntimeError) as error:
        raise ChatGPTExportError("A required export JSON file is invalid.") from error


def _load_export(archive_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any], int]:
    if not archive_path.is_file() or archive_path.suffix.lower() != ".zip":
        raise ChatGPTExportError("Pass the original ChatGPT export ZIP file.")
    try:
        archive = zipfile.ZipFile(archive_path, "r")
    except (OSError, zipfile.BadZipFile) as error:
        raise ChatGPTExportError("The selected file is not a readable ZIP archive.") from error
    with archive:
        members = _archive_members(archive)
        conversations_member = members.get("conversations.json")
        if conversations_member is None:
            raise ChatGPTExportError("The export does not contain conversations.json.")
        conversations = _read_json_member(archive, conversations_member)
        if not isinstance(conversations, list) or any(not isinstance(item, dict) for item in conversations):
            raise ChatGPTExportError("conversations.json must contain an array of conversation records.")
        asset_names: dict[str, Any] = {}
        asset_member = members.get("conversation_asset_file_names.json")
        if asset_member is not None:
            raw_asset_names = _read_json_member(archive, asset_member)
            if isinstance(raw_asset_names, dict):
                asset_names = raw_asset_names
        return conversations, {"members": members, "asset_names": asset_names}, len(members)


def _mapping(conversation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = conversation.get("mapping")
    if not isinstance(raw, dict):
        raise ChatGPTExportError("A conversation record has no mapping object.")
    result: dict[str, dict[str, Any]] = {}
    for node_id, node in raw.items():
        if not isinstance(node_id, str) or not isinstance(node, dict):
            raise ChatGPTExportError("A conversation mapping contains an invalid node.")
        result[node_id] = node
    return result


def _children(mapping: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {node_id: [] for node_id in mapping}
    for node_id, node in mapping.items():
        supplied = node.get("children")
        if isinstance(supplied, list):
            for child in supplied:
                if isinstance(child, str) and child in mapping and child not in result[node_id]:
                    result[node_id].append(child)
    for node_id, node in mapping.items():
        parent = node.get("parent")
        if isinstance(parent, str) and parent in mapping and node_id not in result[parent]:
            result[parent].append(node_id)
    return result


def _walk_order(mapping: dict[str, dict[str, Any]], children: dict[str, list[str]]) -> tuple[list[str], set[str]]:
    roots = [node_id for node_id, node in mapping.items() if node.get("parent") not in mapping]
    ordered: list[str] = []
    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in visiting:
            raise ChatGPTExportError("A conversation mapping contains a cycle.")
        if node_id in visited:
            return
        visiting.add(node_id)
        ordered.append(node_id)
        for child in children[node_id]:
            visit(child)
        visiting.remove(node_id)
        visited.add(node_id)

    for root in roots:
        visit(root)
    reachable = set(visited)
    for node_id in mapping:
        visit(node_id)
    return ordered, reachable


def _selected_path(conversation: dict[str, Any], mapping: dict[str, dict[str, Any]]) -> set[str]:
    selected: set[str] = set()
    current = conversation.get("current_node")
    while isinstance(current, str) and current in mapping and current not in selected:
        selected.add(current)
        parent = mapping[current].get("parent")
        current = parent if isinstance(parent, str) else None
    return selected


def _asset_identifier(pointer: Any) -> str | None:
    if not isinstance(pointer, str):
        return None
    match = ASSET_ID.search(pointer)
    return match.group(1) if match else None


def _asset_member_name(asset_id: str, members: dict[str, zipfile.ZipInfo]) -> str | None:
    prefix = asset_id.lower() + "."
    for name in members:
        if PurePosixPath(name).name.lower().startswith(prefix):
            return name
    return None


def _parts(message: dict[str, Any]) -> list[Any]:
    content = message.get("content")
    if isinstance(content, dict) and isinstance(content.get("parts"), list):
        return content["parts"]
    return []


def _text_from_part(part: Any) -> str:
    if isinstance(part, str):
        return part
    if isinstance(part, dict):
        text = part.get("text")
        if isinstance(text, str):
            return text
        if isinstance(text, list):
            return "".join(piece for piece in text if isinstance(piece, str))
    return ""


def _part_kind(part: Any) -> str:
    if isinstance(part, str):
        return "text"
    if not isinstance(part, dict):
        return "unknown"
    content_type = str(part.get("content_type", "")).lower()
    mime_type = str(part.get("mime_type", "")).lower()
    if "audio" in content_type or mime_type.startswith("audio/"):
        return "audio"
    if "video" in content_type or mime_type.startswith("video/"):
        return "video"
    if part.get("asset_pointer"):
        return "image" if "image" in content_type or mime_type.startswith("image/") else "file"
    if "text" in content_type or isinstance(part.get("text"), str):
        return "text"
    if content_type:
        return "structured"
    return "unknown"


def inspect_archive(archive_path: Path) -> ExportInventory:
    """Return aggregate format and coverage information; never expose message text."""
    path = archive_path.expanduser().resolve()
    conversations, archive_data, member_count = _load_export(path)
    digest, size = _sha256_file(path)
    roles: Counter[str] = Counter()
    mapping_nodes = messages = asset_references = resolvable = 0
    members = archive_data["members"]
    for conversation in conversations:
        mapping = _mapping(conversation)
        mapping_nodes += len(mapping)
        for node in mapping.values():
            message = node.get("message")
            if not isinstance(message, dict):
                continue
            messages += 1
            author = message.get("author")
            role = author.get("role") if isinstance(author, dict) else None
            roles[str(role or "unknown")] += 1
            for part in _parts(message):
                if isinstance(part, dict) and part.get("asset_pointer"):
                    asset_references += 1
                    asset_id = _asset_identifier(part.get("asset_pointer"))
                    if asset_id and _asset_member_name(asset_id, members):
                        resolvable += 1
    return ExportInventory(
        archive_sha256=digest,
        archive_bytes=size,
        archive_members=member_count,
        conversations=len(conversations),
        mapping_nodes=mapping_nodes,
        messages=messages,
        role_counts=dict(sorted(roles.items())),
        asset_references=asset_references,
        resolvable_asset_references=resolvable,
        unresolved_asset_references=asset_references - resolvable,
    )


def _store_stream(stream: BinaryIO, raw_root: Path) -> tuple[str, str, int]:
    temporary: Path | None = None
    digest = hashlib.sha256()
    size = 0
    try:
        with tempfile.NamedTemporaryFile(prefix="raw-", suffix=".tmp", dir=raw_root, delete=False) as output:
            temporary = Path(output.name)
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
                size += len(chunk)
                output.write(chunk)
            output.flush()
            os.fsync(output.fileno())
        sha = digest.hexdigest()
        relative = Path("objects") / sha[:2] / sha
        target = raw_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            existing_sha, existing_size = _sha256_file(target)
            if existing_sha != sha or existing_size != size:
                raise ChatGPTExportError("A content-addressed RAW object failed its integrity check.")
            temporary.unlink(missing_ok=True)
        else:
            os.replace(temporary, target)
        return sha, relative.as_posix(), size
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _store_file(path: Path, raw_root: Path) -> tuple[str, str, int]:
    with path.open("rb") as stream:
        return _store_stream(stream, raw_root)


def _timestamp(value: Any) -> str | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return datetime.fromtimestamp(value, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        return value
    return None


def _conversation_metadata(conversation: dict[str, Any]) -> dict[str, Any]:
    modeled = {"id", "conversation_id", "title", "create_time", "update_time", "mapping", "current_node", "_export_index"}
    return {key: value for key, value in conversation.items() if key not in modeled}


def _process_conversation(
    connection: sqlite3.Connection,
    archive: zipfile.ZipFile,
    members: dict[str, zipfile.ZipInfo],
    asset_names: dict[str, Any],
    conversation: dict[str, Any],
    source_id: str,
    import_run_id: str,
    source_file_id: str,
    archive_sha: str,
    raw_root: Path,
    now: str,
) -> tuple[int, int, int, Counter[str], int]:
    external_conversation_id = str(conversation.get("conversation_id") or conversation.get("id") or "")
    if not external_conversation_id:
        raise ChatGPTExportError("A conversation record has no external identifier.")
    conversation_id = _stable_id(f"conversation:{archive_sha}:{external_conversation_id}")
    mapping = _mapping(conversation)
    children = _children(mapping)
    order, reachable = _walk_order(mapping, children)
    selected = _selected_path(conversation, mapping)
    message_id_by_node = {
        node_id: _stable_id(f"message:{archive_sha}:{external_conversation_id}:{node_id}")
        for node_id in mapping
        if isinstance(mapping[node_id].get("message"), dict)
    }
    sequence_for_node = {node_id: index for index, node_id in enumerate(node_id for node_id in order if node_id in message_id_by_node)}

    connection.execute(
        """INSERT OR IGNORE INTO conversations
           (conversation_id, source_id, external_id, title, created_at, updated_at, metadata_json, source_locator_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            conversation_id,
            source_id,
            external_conversation_id,
            conversation.get("title") if isinstance(conversation.get("title"), str) else None,
            _timestamp(conversation.get("create_time")),
            _timestamp(conversation.get("update_time")),
            _json(_conversation_metadata(conversation)),
            _json({"member": "conversations.json", "conversation_index": conversation.get("_export_index"), "external_id": external_conversation_id}),
        ),
    )

    unresolved = 0
    attachment_count = 0
    role_counts: Counter[str] = Counter()
    branch_for_node: dict[str, str | None] = {}
    visited: set[str] = set()

    def mark_branches(node_id: str, inherited: str | None = None) -> None:
        if node_id in visited:
            return
        visited.add(node_id)
        branch_for_node[node_id] = inherited
        message_children = [child for child in children[node_id] if isinstance(mapping[child].get("message"), dict)]
        for child in children[node_id]:
            child_branch = child if len(message_children) > 1 and child in message_children else inherited
            mark_branches(child, child_branch)

    roots = [node_id for node_id, node in mapping.items() if node.get("parent") not in mapping]
    for root in roots:
        mark_branches(root)
    for node_id in order:
        mark_branches(node_id)

    for node_id in order:
        node = mapping[node_id]
        message = node.get("message")
        if not isinstance(message, dict):
            continue
        source_parent_node = node.get("parent")
        parent = source_parent_node
        seen_parents: set[str] = set()
        while isinstance(parent, str) and parent in mapping and parent not in seen_parents and parent not in message_id_by_node:
            seen_parents.add(parent)
            next_parent = mapping[parent].get("parent")
            parent = next_parent if isinstance(next_parent, str) else None
        parent_message_id = message_id_by_node.get(parent) if isinstance(parent, str) else None
        author = message.get("author") if isinstance(message.get("author"), dict) else {}
        role = str(author.get("role") or "unknown")
        role_counts[role] += 1
        content = message.get("content") if isinstance(message.get("content"), dict) else {}
        content_text = "".join(_text_from_part(part) for part in _parts(message))
        message_id = message_id_by_node[node_id]
        siblings = [child for child in children.get(source_parent_node, []) if isinstance(mapping[child].get("message"), dict)] if isinstance(source_parent_node, str) else []
        variant_group_id = _stable_id(f"variant:{archive_sha}:{external_conversation_id}:{parent}") if len(siblings) > 1 else None
        branch_id = branch_for_node.get(node_id)
        source_locator = {
            "member": "conversations.json",
            "conversation_external_id": external_conversation_id,
            "mapping_node_id": node_id,
            "mapping_node_reachable_from_root": node_id in reachable,
        }
        connection.execute(
            """INSERT OR IGNORE INTO messages
               (message_id, conversation_id, external_id, sequence_number, role, author, created_at,
                content_text, metadata_json, parent_message_id, branch_id, variant_group_id,
                is_selected_variant, source_locator_json, source_payload_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                message_id,
                conversation_id,
                node_id,
                sequence_for_node[node_id],
                role,
                author.get("name") if isinstance(author.get("name"), str) else None,
                _timestamp(message.get("create_time")),
                content_text,
                _json({"content_type": content.get("content_type"), "status": message.get("status"), "recipient": message.get("recipient")}),
                parent_message_id,
                branch_id,
                variant_group_id,
                1 if node_id in selected else 0,
                _json(source_locator),
                _json(node),
            ),
        )
        for part_index, part in enumerate(_parts(message)):
            kind = _part_kind(part)
            attachment_id = None
            if isinstance(part, dict) and part.get("asset_pointer"):
                asset_id = _asset_identifier(part.get("asset_pointer"))
                member_name = _asset_member_name(asset_id, members) if asset_id else None
                if not asset_id or member_name is None:
                    unresolved += 1
                else:
                    attachment_id = _stable_id(f"attachment:{archive_sha}:{external_conversation_id}:{node_id}:{asset_id}")
                    info = members[member_name]
                    with archive.open(info, "r") as asset_stream:
                        asset_sha, asset_relative, asset_size = _store_stream(asset_stream, raw_root)
                    raw_path = raw_root / Path(asset_relative)
                    extension_name = asset_names.get(PurePosixPath(member_name).name)
                    if not isinstance(extension_name, str):
                        extension_name = asset_names.get(asset_id + ".dat")
                    mime_type = part.get("mime_type") if isinstance(part.get("mime_type"), str) else None
                    if not mime_type and isinstance(extension_name, str):
                        mime_type = mimetypes.guess_type(extension_name)[0]
                    connection.execute(
                        "INSERT OR IGNORE INTO raw_objects(sha256, relative_path, byte_size, observed_mime_type, first_seen_at) VALUES (?, ?, ?, ?, ?)",
                        (asset_sha, asset_relative, asset_size, mime_type, now),
                    )
                    connection.execute(
                        """INSERT OR IGNORE INTO source_files
                           (source_file_id, source_id, raw_sha256, file_role, original_filename, added_at, metadata_json)
                           VALUES (?, ?, ?, 'attachment', ?, ?, ?)""",
                        (_stable_id(f"source-file:{source_id}:{asset_sha}"), source_id, asset_sha, extension_name if isinstance(extension_name, str) else None, now, _json({"archive_member": member_name})),
                    )
                    connection.execute(
                        """INSERT OR IGNORE INTO attachments
                           (attachment_id, source_id, message_id, raw_sha256, original_filename, observed_mime_type, attached_at, metadata_json)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (attachment_id, source_id, message_id, asset_sha, extension_name if isinstance(extension_name, str) else PurePosixPath(member_name).name, mime_type, _timestamp(message.get("create_time")), _json({"archive_member": member_name, "asset_pointer": part.get("asset_pointer")})),
                    )
                    attachment_count += 1
            part_text = _text_from_part(part)
            part_payload = part if isinstance(part, dict) else {"source_value_type": type(part).__name__}
            connection.execute(
                """INSERT OR IGNORE INTO message_parts
                   (message_part_id, message_id, part_index, part_kind, text_content, attachment_id, payload_json, source_locator_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (_stable_id(f"part:{archive_sha}:{external_conversation_id}:{node_id}:{part_index}"), message_id, part_index, kind, part_text or None, attachment_id, _json(part_payload), _json({**source_locator, "part_index": part_index})),
            )

    capture_id = _stable_id(f"capture:{import_run_id}:{conversation_id}")
    connection.execute(
        """INSERT OR IGNORE INTO conversation_captures
           (capture_id, conversation_id, source_id, import_run_id, capture_method, completeness,
            captured_at, source_file_id, source_locator_json, report_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (capture_id, conversation_id, source_id, import_run_id, "chatgpt_account_export", "partial" if unresolved else "complete", now, source_file_id, _json({"member": "conversations.json", "external_id": external_conversation_id}), _json({"messages": len(message_id_by_node), "mapping_nodes": len(mapping), "unresolved_asset_references": unresolved})),
    )
    return len(mapping), len(message_id_by_node), attachment_count, role_counts, unresolved


def import_archive(archive_path: Path, data_dir: Path) -> ImportReport:
    """Import every conversation/message represented in the ZIP; repeated runs are idempotent."""
    archive_path = archive_path.expanduser().resolve()
    if archive_path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ChatGPTExportError("The compressed archive exceeds the supported size limit.")
    conversations, archive_data, member_count = _load_export(archive_path)
    raw_root = initialize(data_dir).parent.parent / "RAW"
    archive_sha, archive_relative, archive_size = _store_file(archive_path, raw_root)
    if archive_size > MAX_ARCHIVE_BYTES:
        raise ChatGPTExportError("The compressed archive exceeds the supported size limit.")
    source_id = _stable_id(f"source:{archive_sha}")
    import_run_id = _stable_id(f"import:{archive_sha}:{ADAPTER_NAME}:{ADAPTER_VERSION}")
    source_file_id = _stable_id(f"source-file:{source_id}:{archive_sha}")
    now = _now()
    archive_names = archive_data["members"]
    asset_names = archive_data["asset_names"]
    roles: Counter[str] = Counter()
    node_count = message_count = attachments = unresolved = 0

    try:
        with connect(raw_root.parent / "INDEX" / "personal_memory.sqlite3") as connection:
            connection.execute("BEGIN IMMEDIATE")
            prior = connection.execute("SELECT status, report_json FROM import_runs WHERE import_run_id = ?", (import_run_id,)).fetchone()
            if prior and prior["status"] == "succeeded":
                report_data = json.loads(prior["report_json"])
                report_data["already_imported"] = True
                return ImportReport(**report_data)
            connection.execute(
                "INSERT OR IGNORE INTO sources(source_id, source_type, display_name, origin_uri, created_at, metadata_json) VALUES (?, ?, ?, NULL, ?, ?)",
                (source_id, "chatgpt_export", "ChatGPT account export", now, _json({"archive_sha256": archive_sha, "adapter_version": ADAPTER_VERSION})),
            )
            connection.execute(
                "INSERT OR IGNORE INTO raw_objects(sha256, relative_path, byte_size, observed_mime_type, first_seen_at) VALUES (?, ?, ?, 'application/zip', ?)",
                (archive_sha, archive_relative, archive_size, now),
            )
            connection.execute(
                """INSERT OR IGNORE INTO source_files
                   (source_file_id, source_id, raw_sha256, file_role, original_filename, added_at, metadata_json)
                   VALUES (?, ?, ?, 'archive', ?, ?, ?)""",
                (source_file_id, source_id, archive_sha, archive_path.name, now, _json({"archive_members": member_count})),
            )
            connection.execute(
                """INSERT OR IGNORE INTO import_runs
                   (import_run_id, source_id, adapter_name, adapter_version, started_at, status, report_json)
                   VALUES (?, ?, ?, ?, ?, 'running', '{}')""",
                (import_run_id, source_id, ADAPTER_NAME, ADAPTER_VERSION, now),
            )
            with zipfile.ZipFile(archive_path, "r") as archive:
                for index, original in enumerate(conversations):
                    conversation = dict(original)
                    conversation["_export_index"] = index
                    nodes, messages, added_attachments, conversation_roles, missing = _process_conversation(
                        connection, archive, archive_names, asset_names, conversation, source_id,
                        import_run_id, source_file_id, archive_sha, raw_root, now,
                    )
                    node_count += nodes
                    message_count += messages
                    attachments += added_attachments
                    unresolved += missing
                    roles.update(conversation_roles)
            report = ImportReport(
                adapter=ADAPTER_NAME,
                adapter_version=ADAPTER_VERSION,
                archive_sha256=archive_sha,
                archive_bytes=archive_size,
                conversations=len(conversations),
                mapping_nodes=node_count,
                messages=message_count,
                role_counts=dict(sorted(roles.items())),
                attachment_references=attachments + unresolved,
                attachments_preserved=attachments,
                unresolved_asset_references=unresolved,
                raw_archive_path=archive_relative,
            )
            connection.execute(
                "UPDATE import_runs SET finished_at = ?, status = ?, report_json = ? WHERE import_run_id = ?",
                (_now(), "partial" if unresolved else "succeeded", _json(asdict(report)), import_run_id),
            )
            connection.commit()
            return report
    except Exception:
        # The source objects are append-only; a failed DB transaction leaves no partial index rows.
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect or import a ChatGPT account export ZIP locally.")
    parser.add_argument("--archive", type=Path, required=True, help="Path to the original ChatGPT export ZIP.")
    parser.add_argument("--data-dir", type=Path, help="Private PersonalMemory data directory; defaults to the OS user data path.")
    parser.add_argument("--inspect-only", action="store_true", help="Print aggregate counts without copying or importing content.")
    args = parser.parse_args()
    try:
        if args.inspect_only:
            report = inspect_archive(args.archive)
        else:
            if args.data_dir is None:
                data_dir = default_data_dir()
            else:
                data_dir = args.data_dir
            report = import_archive(args.archive, data_dir)
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
        return 0
    except (OSError, sqlite3.Error, ChatGPTExportError, zipfile.BadZipFile, ValueError) as error:
        print(f"ChatGPT export import failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
