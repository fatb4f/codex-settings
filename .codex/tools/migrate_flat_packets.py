#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import List


def find_flat_packets(root: Path) -> List[Path]:
    return sorted((root / "packets" / "examples").glob("*.json"))


def migrate_packet(contract_path: Path, area: str, apply: bool) -> str:
    packet_id = contract_path.stem
    prompt_path = contract_path.with_name(f"{packet_id}.EXEC_PROMPT.md")
    if not prompt_path.exists():
        return f"skip {packet_id}: missing prompt {prompt_path.name}"

    dest_dir = contract_path.parents[2] / "packets" / area / packet_id
    dest_contract = dest_dir / "contract.json"
    dest_prompt = dest_dir / "EXEC_PROMPT.md"

    if dest_contract.exists() or dest_prompt.exists():
        return f"skip {packet_id}: destination exists"

    if not apply:
        return f"plan {packet_id}: {contract_path} -> {dest_contract}; {prompt_path} -> {dest_prompt}"

    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(contract_path), str(dest_contract))
    shutil.move(str(prompt_path), str(dest_prompt))
    return f"moved {packet_id}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate flat packets into directory layout.")
    parser.add_argument("--area", required=True, help="target area for new packet directories")
    parser.add_argument("--apply", action="store_true", help="apply changes (default is dry-run)")
    parser.add_argument("--root", default=".", help="repo root")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    flat = find_flat_packets(root)
    if not flat:
        print("no flat packets found")
        return 0

    for contract in flat:
        print(migrate_packet(contract, args.area, args.apply))

    if not args.apply:
        print("dry-run only; rerun with --apply to move files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
