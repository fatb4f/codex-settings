#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def read_json(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not path.exists():
        return None, f"manifest not found: {path}"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:
        return None, f"failed to parse manifest json: {exc}"


def ensure_string(name: str, value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return f"{name} must be string"
    return None


def ensure_list_of_strings(name: str, value: Any) -> Optional[str]:
    if not isinstance(value, list):
        return f"{name} must be array"
    for item in value:
        if not isinstance(item, str):
            return f"{name} must contain only strings"
    return None


def find_manifest(repo_root: Path) -> Tuple[Optional[Path], Optional[Path]]:
    downstream = repo_root / ".codex" / "plant.manifest.json"
    if downstream.exists():
        return downstream.parent, downstream
    upstream = repo_root / "plant.manifest.json"
    if upstream.exists():
        return upstream.parent, upstream
    return None, None


def validate_manifest(manifest: Dict[str, Any], plant_root: Path) -> Optional[str]:
    required_keys = [
        "plant_id",
        "schema_version",
        "required_files",
        "required_dirs",
        "contract_schema",
        "plant_schema",
    ]
    missing = [k for k in required_keys if k not in manifest]
    if missing:
        return f"manifest missing required keys: {missing}"

    for key in ("plant_id", "schema_version", "contract_schema", "plant_schema"):
        err = ensure_string(key, manifest.get(key))
        if err:
            return err

    err = ensure_list_of_strings("required_files", manifest.get("required_files"))
    if err:
        return err
    err = ensure_list_of_strings("required_dirs", manifest.get("required_dirs"))
    if err:
        return err

    contract_schema = plant_root / str(manifest.get("contract_schema"))
    plant_schema = plant_root / str(manifest.get("plant_schema"))
    if not contract_schema.exists():
        return f"contract schema missing: {contract_schema}"
    if not plant_schema.exists():
        return f"plant schema missing: {plant_schema}"

    for rel_path in manifest.get("required_files", []):
        path = plant_root / rel_path
        if not path.exists() or not path.is_file():
            return f"required file missing: {path}"

    for rel_path in manifest.get("required_dirs", []):
        path = plant_root / rel_path
        if not path.exists() or not path.is_dir():
            return f"required directory missing: {path}"

    return None


def validate_repo(repo_root: Path) -> Optional[str]:
    plant_root, manifest_path = find_manifest(repo_root)
    if plant_root is None or manifest_path is None:
        return "plant.manifest.json not found in repo root or .codex/"
    manifest, err = read_json(manifest_path)
    if err:
        return err
    return validate_manifest(manifest, plant_root)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Plant A manifest and structure.")
    parser.add_argument("--repo-root", default=".", help="Repo root to validate from.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    err = validate_repo(repo_root)
    if err:
        print(err)
        return 2
    print("plant manifest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
