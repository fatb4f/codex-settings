#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from root_preflight import (
    extract_exec_prompt_metadata,
    resolve_exec_prompt_path,
    safe_read_json,
    validate_exec_prompt_metadata,
)


def validate_prompt(prompt_path: Path) -> Optional[str]:
    try:
        text = prompt_path.read_text(encoding="utf-8")
    except Exception as exc:
        return f"exec_prompt unreadable: {exc}"
    meta, meta_err = extract_exec_prompt_metadata(text)
    if meta_err:
        return meta_err
    err = validate_exec_prompt_metadata(meta or {})
    if err:
        return err
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate EXEC_PROMPT metadata block.")
    parser.add_argument("--contract", required=True, help="Path to packet contract JSON.")
    parser.add_argument("--prompt", help="Override EXEC_PROMPT path.")
    args = parser.parse_args()

    contract_path = Path(args.contract)
    contract, err = safe_read_json(contract_path)
    if err:
        print(err)
        return 2

    prompt_path = Path(args.prompt) if args.prompt else resolve_exec_prompt_path(contract_path)
    if not prompt_path.exists():
        print(f"exec_prompt missing: {prompt_path}")
        return 2

    prompt_err = validate_prompt(prompt_path)
    if prompt_err:
        print(prompt_err)
        return 2

    print("exec_prompt ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
