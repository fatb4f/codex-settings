#!/usr/bin/env python3
"""Create a new packet contract and EXEC_PROMPT.

Usage:
  python new_packet.py <packet_id>
  python new_packet.py --packet-id <packet_id> [--area AREA] [--repo REPO]
                       [--base-ref REF] [--branch BRANCH] [--layout dir|flat]
                       [--examples] [--template PATH] [--prompt-template PATH]
                       [--validate-prompt]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any, Dict


def die(msg: str, code: int = 2) -> None:
    sys.stderr.write(msg.rstrip() + "\n")
    raise SystemExit(code)


def plant_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[3]


def load_prompt_validator(root: pathlib.Path):
    sys.path.insert(0, str(root))
    from tools.validate_exec_prompt import validate_prompt

    return validate_prompt


def template_path(default_root: pathlib.Path, override: str | None) -> pathlib.Path:
    if override:
        return pathlib.Path(override)
    return default_root / "packets" / "packet_contract.template.json"


def prompt_template_path(default_root: pathlib.Path, override: str | None) -> pathlib.Path:
    if override:
        return pathlib.Path(override)
    return default_root / "packets" / "EXEC_PROMPT.template.md"


def load_template(path: pathlib.Path) -> Dict[str, Any]:
    if not path.exists():
        die(f"template not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        die(f"invalid template json: {path} ({exc})")


def replace_tokens(value: Any, mapping: Dict[str, str]) -> Any:
    if isinstance(value, str):
        for key, replacement in mapping.items():
            value = value.replace(f"{{{{{key}}}}}", replacement)
        return value
    if isinstance(value, list):
        return [replace_tokens(item, mapping) for item in value]
    if isinstance(value, dict):
        return {key: replace_tokens(item, mapping) for key, item in value.items()}
    return value


def build_contract(template: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
    contract = replace_tokens(template, mapping)
    contract["packet_id"] = mapping["packet_id"]
    contract["area"] = mapping["area"]
    contract["repo"] = mapping["repo"]
    contract["base_ref"] = mapping["base_ref"]
    contract["branch"] = mapping["branch"]
    return contract


def load_prompt_template(path: pathlib.Path) -> str:
    if not path.exists():
        die(f"prompt template not found: {path}")
    return path.read_text(encoding="utf-8")


def apply_text_tokens(text: str, mapping: Dict[str, str]) -> str:
    for key, replacement in mapping.items():
        text = text.replace(f"{{{{{key}}}}}", replacement)
    return text


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a new packet example contract file.")
    parser.add_argument("packet_id", nargs="?", help="packet identifier (e.g., packet-002-something)")
    parser.add_argument("--packet-id", dest="packet_id_flag", help="packet identifier")
    parser.add_argument("--area", help="area (e.g., pipeline-sre)")
    parser.add_argument("--repo", help="repo or local path")
    parser.add_argument("--base-ref", dest="base_ref", help="base ref (e.g., main)")
    parser.add_argument("--branch", help="branch name")
    parser.add_argument("--template", help="path to packet contract template json")
    parser.add_argument("--prompt-template", help="path to EXEC_PROMPT template md")
    parser.add_argument("--layout", choices=["dir", "flat"], default="dir", help="packet layout")
    parser.add_argument("--examples", action="store_true", help="write under packets/examples/")
    parser.add_argument("--validate-prompt", action="store_true", help="validate EXEC_PROMPT metadata")
    return parser.parse_args(argv[1:])


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    packet_id = (args.packet_id_flag or args.packet_id or "").strip()
    if not packet_id or "/" in packet_id or ".." in packet_id:
        die("invalid packet_id")

    defaults = {
        "area": "pipeline-sre",
        "repo": "<org>/<repo>",
        "base_ref": "main",
        "branch": f"packet/{packet_id}",
    }

    mapping = {
        "packet_id": packet_id,
        "area": args.area or defaults["area"],
        "repo": args.repo or defaults["repo"],
        "base_ref": args.base_ref or defaults["base_ref"],
        "branch": args.branch or defaults["branch"],
    }

    root = plant_root()
    template = load_template(template_path(root, args.template))
    contract = build_contract(template, mapping)
    prompt_template = load_prompt_template(prompt_template_path(root, args.prompt_template))

    if args.layout == "dir":
        base_dir = root / "packets" / ("examples" if args.examples else mapping["area"]) / packet_id
        contract_path = base_dir / "contract.json"
        prompt_path = base_dir / "EXEC_PROMPT.md"
        contract_rel = f".codex/packets/{'examples' if args.examples else mapping['area']}/{packet_id}/contract.json"
    else:
        base_dir = root / "packets" / "examples"
        contract_path = base_dir / f"{packet_id}.json"
        prompt_path = base_dir / f"{packet_id}.EXEC_PROMPT.md"
        contract_rel = f".codex/packets/examples/{packet_id}.json"

    if contract_path.exists():
        die(f"already exists: {contract_path}")
    if prompt_path.exists():
        die(f"already exists: {prompt_path}")

    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    prompt_text = apply_text_tokens(
        prompt_template,
        {
            "packet_id": packet_id,
            "area": mapping["area"],
            "contract_path": contract_rel,
            "worktree_root": f".codex/.worktrees/{packet_id}/",
        },
    )
    prompt_path.write_text(prompt_text, encoding="utf-8")
    if args.validate_prompt:
        validate_prompt = load_prompt_validator(root)
        err = validate_prompt(prompt_path)
        if err:
            die(err)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
