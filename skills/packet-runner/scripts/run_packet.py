#!/usr/bin/env python3
"""Codex skill entrypoint wrapper.

Delegates to the canonical runner:
  python .codex/tools/run_packet.py <contract_path>
"""

from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Codex packet runner wrapper.")
    ap.add_argument("contract_path")
    ap.add_argument("--resume", action="store_true", help="Reuse existing worktree on collision.")
    args = ap.parse_args(argv[1:])
    contract_path = args.contract_path
    plant_root = pathlib.Path(__file__).resolve().parents[3]
    runner = plant_root / "tools" / "run_packet.py"
    cmd = [sys.executable, str(runner), contract_path]
    if args.resume:
        cmd.append("--resume")
    p = subprocess.run(cmd)
    return int(p.returncode)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
