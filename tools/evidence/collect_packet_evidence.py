#!/usr/bin/env python3
"""Packet-002: Structured Post-Run Evidence Harness.

Writes a uniform bundle to:
  .codex/out/<packet_id>/
    evidence.json
    evidence.md
    manifest.json
    manifest.sha256
    raw/

Design:
- stdlib only
- deterministic ordering
- best-effort: always attempts to write evidence

Inputs:
- --contract <path> (required)
- --meta <path> (optional; runner-written meta.json)

The harness prefers pre-captured raw files in .codex/out/<packet_id>/raw/
(head_before.txt, status_before.txt) if present, otherwise it captures
current values.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run(cmd: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True)
    return p.returncode, p.stdout, p.stderr


def git_root() -> Path:
    rc, out, err = run(["git", "rev-parse", "--show-toplevel"])
    if rc != 0:
        raise RuntimeError(err.strip() or "not a git repo")
    return Path(out.strip())


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def write_text(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def write_json(p: Path, obj: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def list_files(root: Path) -> List[Path]:
    out: List[Path] = []
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        if ".git" in p.parts:
            continue
        out.append(p)
    return out


def normalize_path(s: str) -> str:
    return s.replace("\\", "/").lstrip("./")


def matches_allowed(path: str, allowed: List[str]) -> bool:
    p = normalize_path(path)
    for a in allowed:
        a_norm = normalize_path(a)
        if any(ch in a_norm for ch in ["*", "?", "["]):
            if fnmatch.fnmatch(p, a_norm):
                return True
        else:
            a_dir = a_norm.rstrip("/")
            if p == a_dir or p.startswith(a_dir + "/"):
                return True
    return False


def matches_any(path: str, patterns: List[str]) -> bool:
    p = normalize_path(path)
    for pat in patterns:
        pat_norm = normalize_path(pat)
        if any(ch in pat_norm for ch in ["*", "?", "["]):
            if fnmatch.fnmatch(p, pat_norm):
                return True
        else:
            pat_dir = pat_norm.rstrip("/")
            if p == pat_dir or p.startswith(pat_dir + "/"):
                return True
    return False


def paths_from_porcelain(lines: List[str]) -> List[str]:
    """Extract best-effort paths from `git status --porcelain` lines."""
    out: List[str] = []
    for ln in lines:
        ln = ln.rstrip("\n")
        if not ln.strip():
            continue
        if len(ln) < 4:
            continue
        path = ln[3:].strip()
        # Handle rename/copy lines like: "R  old -> new"
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        if path:
            out.append(path)
    return out


def git_capture(wt: Path, args: List[str]) -> str:
    rc, out, err = run(["git"] + args, cwd=wt)
    if rc != 0:
        return "" if not err else f"!! {err.strip()}"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract", required=True)
    ap.add_argument("--meta")
    args = ap.parse_args()

    generated_at = utc_now()

    # Be resilient: if not in git, write minimal evidence to ./out/unknown
    try:
        root = git_root()
    except Exception as e:
        out_dir = Path(".codex/out") / "unknown"
        (out_dir / "raw").mkdir(parents=True, exist_ok=True)
        write_json(out_dir / "evidence.json", {"generated_at_utc": utc_now(), "error": str(e)})
        return 2

    contract_path = Path(args.contract)
    if not contract_path.is_absolute():
        contract_path = (root / contract_path).resolve()

    try:
        contract = json.loads(read_text(contract_path))
    except Exception as e:
        out_dir = root / ".codex/out" / "unknown"
        (out_dir / "raw").mkdir(parents=True, exist_ok=True)
        write_json(out_dir / "evidence.json", {"generated_at_utc": utc_now(), "error": str(e)})
        return 2

    packet_id = str(contract.get("packet_id") or "unknown")
    base_ref = str(contract.get("base_ref") or "")
    branch = str(contract.get("branch") or "")
    allowed_paths = list(contract.get("allowed_paths") or [])
    forbidden_outputs = list(contract.get("forbidden_outputs") or [])
    budgets = dict(contract.get("budgets") or {})
    run_cfg = dict(contract.get("run") or {})
    evidence_cfg = dict(contract.get("evidence") or {})

    out_root = str(evidence_cfg.get("out_dir") or ".codex/out")
    include_patch = bool(evidence_cfg.get("include_git_diff_patch", False))

    out_dir = (root / out_root / packet_id).resolve()
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Load meta if present (provides worktree path, test exit code, runner version)
    meta: Dict[str, Any] = {}
    if args.meta:
        meta_path = Path(args.meta)
        if not meta_path.is_absolute():
            meta_path = (root / meta_path).resolve()
        if meta_path.exists():
            try:
                meta = json.loads(read_text(meta_path))
            except Exception:
                meta = {}

    wt_path = meta.get("worktree_path")
    if not wt_path:
        wt_candidate = root / ".codex/.worktrees" / packet_id
        wt_path = str(wt_candidate) if wt_candidate.exists() else str(root)
    wt = Path(wt_path)

    # Capture BEFORE from raw if present
    head_before_path = raw_dir / "head_before.txt"
    status_before_path = raw_dir / "status_before.txt"

    if head_before_path.exists():
        head_before = read_text(head_before_path).strip()
    else:
        head_before = git_capture(wt, ["rev-parse", "HEAD"]).strip()
        write_text(head_before_path, head_before + ("\n" if head_before else ""))

    if status_before_path.exists():
        status_before = [ln for ln in read_text(status_before_path).splitlines() if ln.strip()]
    else:
        status_before = [ln for ln in git_capture(wt, ["status", "--porcelain"]).splitlines() if ln.strip()]
        write_text(status_before_path, "\n".join(status_before) + ("\n" if status_before else ""))

    # AFTER snapshot
    head_after_path = raw_dir / "head_after.txt"
    if head_after_path.exists():
        head_after = read_text(head_after_path).strip()
    else:
        head_after = git_capture(wt, ["rev-parse", "HEAD"]).strip()
        write_text(head_after_path, head_after + ("\n" if head_after else ""))

    status_after_path = raw_dir / "status_after.txt"
    if status_after_path.exists():
        status_after = [ln for ln in read_text(status_after_path).splitlines() if ln.strip()]
    else:
        status_after = [ln for ln in git_capture(wt, ["status", "--porcelain"]).splitlines() if ln.strip()]
        write_text(status_after_path, "\n".join(status_after) + ("\n" if status_after else ""))

    # Diffs (relative to head_before; captures committed + uncommitted changes)
    diff_name_only = [
        ln.strip()
        for ln in git_capture(wt, ["diff", "--name-only", head_before]).splitlines()
        if ln.strip()
    ]
    write_text(raw_dir / "diff_name_only.txt", "\n".join(diff_name_only) + ("\n" if diff_name_only else ""))

    diff_stat = git_capture(wt, ["diff", "--stat", head_before]).rstrip("\n")
    write_text(raw_dir / "diffstat.txt", diff_stat + ("\n" if diff_stat else ""))

    show_name_only_after = [
        ln.strip()
        for ln in git_capture(wt, ["show", "--name-only", "--pretty=format:", head_after or "HEAD"]).splitlines()
        if ln.strip()
    ]
    write_text(
        raw_dir / "show_name_only_after.txt",
        "\n".join(show_name_only_after) + ("\n" if show_name_only_after else ""),
    )

    if include_patch:
        diff_patch = git_capture(wt, ["diff", head_before])  # may be large
        write_text(raw_dir / "diff_patch.txt", diff_patch)

    # Paths for constraint evaluation (diff + status, includes untracked)
    status_paths_after = paths_from_porcelain(status_after)
    changed_paths = sorted(set(diff_name_only + status_paths_after))
    write_text(raw_dir / "changed_paths.txt", "\n".join(changed_paths) + ("\n" if changed_paths else ""))

    # Budgets via numstat (tracked deltas relative to head_before)
    tracked_files_changed = 0
    added = 0
    deleted = 0
    for ln in git_capture(wt, ["diff", "--numstat", head_before]).splitlines():
        ln = ln.strip()
        if not ln:
            continue
        parts = ln.split("\t", 2)
        if len(parts) < 2:
            continue
        a, d = parts[0], parts[1]
        if a.isdigit():
            added += int(a)
        if d.isdigit():
            deleted += int(d)
        tracked_files_changed += 1
    total_lines = added + deleted

    changed_files = len(changed_paths)

    # Constraint violations
    violations: List[Dict[str, Any]] = []

    if allowed_paths:
        bad = [p for p in changed_paths if not matches_allowed(p, allowed_paths)]
        if bad:
            violations.append({"code": "DIFF_OUTSIDE_ALLOWED_PATHS", "details": {"bad_paths": bad}})

    forbidden_hit: List[str] = []
    if forbidden_outputs:
        for p in status_paths_after:
            pn = normalize_path(p)
            if matches_any(pn, forbidden_outputs):
                forbidden_hit.append(pn)
        forbidden_hit = sorted(set(forbidden_hit))
        if forbidden_hit:
            violations.append({"code": "FORBIDDEN_OUTPUT_PRESENT", "details": {"paths": forbidden_hit}})

    max_files = budgets.get("max_changed_files")
    max_lines = budgets.get("max_changed_lines")
    budget_viol = []
    if isinstance(max_files, int) and changed_files > max_files:
        budget_viol.append(["max_changed_files", changed_files, max_files])
    if isinstance(max_lines, int) and total_lines > max_lines:
        budget_viol.append(["max_changed_lines", total_lines, max_lines])
    if budget_viol:
        violations.append({"code": "DIFF_BUDGET_EXCEEDED", "details": {"violations": budget_viol}})

    # Tests: meta.test_rc + raw/tests.txt if runner wrote it
    test_cmd = str(run_cfg.get("test_cmd") or "")
    test_rc = meta.get("test_rc")
    tests_path = raw_dir / "tests.txt"
    test_result = "SKIP" if not test_cmd else "UNKNOWN"
    if test_cmd and isinstance(test_rc, int):
        test_result = "PASS" if test_rc == 0 else "FAIL"

    # Decision (meta decision cannot override harness violations)
    decision_from_meta = meta.get("decision")
    decision = decision_from_meta if decision_from_meta in ("ALLOW", "DENY") else ("DENY" if violations else "ALLOW")
    if violations:
        decision = "DENY"

    reasons = meta.get("reasons") or []
    if not isinstance(reasons, list):
        reasons = [str(reasons)]
    if violations and meta.get("decision") == "ALLOW":
        reasons = list(reasons) + ["constraint_violations"]

    evidence: Dict[str, Any] = {
        "packet_id": packet_id,
        "generated_at_utc": utc_now(),
        "repo": {"root": str(root), "base_ref": base_ref, "heads": {"before": head_before, "after": head_after}},
        "worktree": {"path": str(wt), "branch": branch},
        "status": {"before": {"porcelain": status_before}, "after": {"porcelain": status_after}},
        "diff": {
            "name_only": diff_name_only,
            "stat": diff_stat,
            "changed_files": changed_files,
            "tracked_files_changed": tracked_files_changed,
            "lines_added": added,
            "lines_deleted": deleted,
        },
        "constraints": {"allowed_paths": allowed_paths, "forbidden_outputs": forbidden_outputs, "violations": violations},
        "tests": {
            "command": test_cmd,
            "exit_code": test_rc,
            "result": test_result,
            "raw_path": "raw/tests.txt" if tests_path.exists() else None,
        },
        "runner": {
            "version": meta.get("runner_version"),
            "python": meta.get("python"),
            "meta": meta,
        },
        "decision": decision,
        "reasons": reasons,
        "artifacts": {},
    }

    # Render evidence.md
    md: List[str] = []
    md.append(f"# Evidence — {packet_id}")
    md.append("")
    md.append(f"- Generated (UTC): `{evidence['generated_at_utc']}`")
    md.append(f"- Decision: **{decision}**")
    md.append(f"- Base ref: `{base_ref}`")
    md.append(f"- Worktree: `{evidence['worktree']['path']}`")
    md.append("")
    md.append("## Heads")
    md.append(f"- Before: `{head_before}`")
    md.append(f"- After: `{head_after}`")
    md.append("")
    md.append("## Diff")
    md.append(f"- Changed files: {changed_files}")
    md.append(f"- Lines added/deleted: {added}/{deleted}")
    md.append("")
    md.append("## Tests")
    md.append(f"- Command: `{test_cmd}`" if test_cmd else "- Command: *(none)*")
    md.append(f"- Result: **{test_result}**")
    if isinstance(test_rc, int):
        md.append(f"- Exit code: `{test_rc}`")
    md.append("")
    md.append("## Constraint violations")
    if violations:
        md.append("```json")
        md.append(json.dumps(violations, indent=2, sort_keys=True))
        md.append("```")
    else:
        md.append("- None")
    md.append("")

    write_json(out_dir / "evidence.json", evidence)
    write_text(out_dir / "evidence.md", "\n".join(md) + "\n")

    # Manifest (exclude manifest.* itself)
    entries = []
    for f in list_files(out_dir):
        rel = f.relative_to(out_dir).as_posix()
        if rel in ("manifest.json", "manifest.sha256"):
            continue
        entries.append({"path": rel, "sha256": sha256_file(f), "size": f.stat().st_size})
    manifest = {"generated_at_utc": generated_at, "files": sorted(entries, key=lambda x: x["path"])}
    write_json(out_dir / "manifest.json", manifest)

    m_hash = sha256_bytes((out_dir / "manifest.json").read_bytes())
    write_text(out_dir / "manifest.sha256", f"{m_hash}  manifest.json\n")

    # Fill artifacts block and rewrite evidence.json once
    raw_files = [p.relative_to(out_dir).as_posix() for p in list_files(raw_dir)] if raw_dir.exists() else []
    evidence["artifacts"] = {
        "raw": sorted(raw_files),
        "manifest": "manifest.json",
        "manifest_sha256": "manifest.sha256",
    }
    write_json(out_dir / "evidence.json", evidence)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
