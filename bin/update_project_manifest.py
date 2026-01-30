#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HOME = Path.home()
DEFAULT_ROOT = str(HOME / "src")
DEFAULT_OUT = str(HOME / ".config" / "codex" / "memory" / "manifest.json")
DEFAULT_SCHEMA = str(HOME / ".config" / "codex" / "memory" / "project.metadata.schema.json")
DEFAULT_GLOBAL_SCHEMA = str(HOME / ".config" / "codex" / "memory" / "global.manifest.schema.json")

SKIP_DIRS = {
    ".git",
    ".codex",
    "node_modules",
    ".venv",
    "venv",
    "target",
    "dist",
    "build",
    ".tox",
    ".pytest_cache",
    ".mypy_cache",
    ".cache",
}

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-_]{1,64}$")


@dataclass
class WarningItem:
    path: str
    message: str


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def load_json(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not path.exists():
        return None, f"missing: {path}"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:
        return None, f"invalid json: {exc}"


def validate_metadata_manual(data: Dict[str, Any]) -> Optional[str]:
    required = ["id", "one_liner"]
    for key in required:
        if key not in data:
            return f"missing required field: {key}"
    if not isinstance(data.get("id"), str):
        return "id must be string"
    if not ID_RE.match(data["id"]):
        return "id must match pattern ^[a-z0-9][a-z0-9-_]{1,64}$"
    if not isinstance(data.get("one_liner"), str):
        return "one_liner must be string"
    if len(data["one_liner"]) > 120:
        return "one_liner exceeds 120 chars"

    optional_str = ["title"]
    for key in optional_str:
        if key in data and not isinstance(data[key], str):
            return f"{key} must be string"

    for key in ("tags", "stack"):
        if key in data:
            if not isinstance(data[key], list) or any(not isinstance(x, str) for x in data[key]):
                return f"{key} must be array of strings"

    if "entrypoints" in data:
        if not isinstance(data["entrypoints"], dict):
            return "entrypoints must be object"
        for k, v in data["entrypoints"].items():
            if not isinstance(k, str) or not isinstance(v, str):
                return "entrypoints keys and values must be strings"

    allowed = {"id", "title", "one_liner", "tags", "stack", "entrypoints"}
    extras = [k for k in data.keys() if k not in allowed]
    if extras:
        return f"unexpected fields: {sorted(extras)}"

    return None


def validate_metadata_schema(data: Dict[str, Any], schema_path: Path) -> Optional[str]:
    try:
        import jsonschema  # type: ignore
    except Exception:
        return validate_metadata_manual(data)

    schema, err = load_json(schema_path)
    if err:
        return f"schema load failed: {err}"
    try:
        jsonschema.validate(instance=data, schema=schema)
    except Exception as exc:
        return f"schema validation failed: {exc}"
    return None


def is_repo_root(dirnames: List[str], filenames: List[str]) -> bool:
    if ".git" in dirnames:
        return True
    if ".git" in filenames:
        return True
    return False


def scan_projects(root: Path, schema_path: Path, strict: bool) -> Tuple[List[Dict[str, Any]], List[WarningItem]]:
    entries: List[Dict[str, Any]] = []
    warnings: List[WarningItem] = []

    for current, dirnames, filenames in os.walk(root, topdown=True):
        current_path = Path(current)
        has_repo = is_repo_root(dirnames, filenames)

        # prune skip dirs early (after repo detection)
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        if has_repo:
            metadata_path = current_path / "project.metadata.json"
            if metadata_path.exists():
                data, err = load_json(metadata_path)
                if err:
                    warnings.append(WarningItem(str(metadata_path), err))
                    if strict:
                        raise SystemExit(err)
                else:
                    v_err = validate_metadata_schema(data, schema_path)
                    if v_err:
                        warnings.append(WarningItem(str(metadata_path), v_err))
                        if strict:
                            raise SystemExit(v_err)
                    else:
                        entry: Dict[str, Any] = {
                            "id": data["id"],
                            "path": str(current_path),
                            "one_liner": data["one_liner"],
                            "source_metadata": "project.metadata.json",
                            "source_mtime": int(metadata_path.stat().st_mtime),
                        }
                        for key in ("title", "tags", "stack", "entrypoints"):
                            if key in data:
                                entry[key] = data[key]
                        entries.append(entry)
            # do not descend further into repo
            dirnames[:] = []

    return entries, warnings


def resolve_conflicts(entries: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    by_id: Dict[str, List[Dict[str, Any]]] = {}
    for entry in sorted(entries, key=lambda e: e["path"]):
        by_id.setdefault(entry["id"], []).append(entry)

    kept: List[Dict[str, Any]] = []
    conflicts: List[Dict[str, Any]] = []
    for project_id, items in by_id.items():
        kept.append(items[0])
        if len(items) > 1:
            conflicts.append({
                "id": project_id,
                "paths": [item["path"] for item in items],
            })

    kept_sorted = sorted(kept, key=lambda e: (e["id"], e["path"]))
    conflicts_sorted = sorted(conflicts, key=lambda c: c["id"])
    return kept_sorted, conflicts_sorted


def write_manifest(out_path: Path, root: Path, entries: List[Dict[str, Any]], conflicts: List[Dict[str, Any]]) -> None:
    manifest: Dict[str, Any] = {
        "version": "1.0",
        "root": str(root),
        "generated_at": now_iso(),
        "projects": entries,
    }
    if conflicts:
        manifest["conflicts"] = conflicts

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Codex project memory manifest.")
    parser.add_argument("--root", default=DEFAULT_ROOT, help="Root directory to scan")
    parser.add_argument("--out", default=DEFAULT_OUT, help="Output manifest path")
    parser.add_argument("--schema", default=DEFAULT_SCHEMA, help="Project metadata schema path")
    parser.add_argument("--strict", action="store_true", help="Fail on first invalid metadata file")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    schema_path = Path(args.schema).expanduser().resolve()

    entries, warnings = scan_projects(root, schema_path, args.strict)
    kept, conflicts = resolve_conflicts(entries)
    write_manifest(out_path, root, kept, conflicts)

    for item in warnings:
        sys.stderr.write(f"warning: {item.path}: {item.message}\n")
    if conflicts:
        sys.stderr.write("warning: duplicate project ids detected; see conflicts in manifest\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
