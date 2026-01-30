#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run(cmd: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True)
    return p.returncode, p.stdout, p.stderr


def git_root() -> Optional[Path]:
    rc, out, err = run(["git", "rev-parse", "--show-toplevel"])
    if rc != 0:
        return None
    return Path(out.strip())


def git_dir(repo: Path) -> Optional[Path]:
    rc, out, err = run(["git", "rev-parse", "--git-dir"], cwd=repo)
    if rc != 0:
        return None
    d = out.strip()
    return (repo / d).resolve()


def git_rev_parse(repo: Path, ref: str) -> Optional[str]:
    rc, out, err = run(["git", "rev-parse", "--verify", ref], cwd=repo)
    if rc != 0:
        return None
    return out.strip()


def git_op_in_progress(gitdir: Path) -> bool:
    markers = [
        "rebase-apply",
        "rebase-merge",
        "MERGE_HEAD",
        "CHERRY_PICK_HEAD",
        "REVERT_HEAD",
        "BISECT_LOG",
        "BISECT_NAMES",
    ]
    for name in markers:
        if (gitdir / name).exists():
            return True
    return False


def safe_read_json(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not path.exists():
        return None, f"contract not found: {path}"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as e:
        return None, f"failed to parse contract json: {e}"


def parse_worktree_list(repo: Path) -> Dict[str, Dict[str, str]]:
    rc, out, err = run(["git", "worktree", "list", "--porcelain"], cwd=repo)
    if rc != 0:
        return {}
    entries: Dict[str, Dict[str, str]] = {}
    current: Dict[str, str] = {}
    for line in out.splitlines():
        if line.startswith("worktree "):
            if current.get("path"):
                entries[current["path"]] = current
            current = {"path": line.split(" ", 1)[1].strip()}
        else:
            if not line.strip():
                continue
            key, _, val = line.partition(" ")
            current[key] = val.strip()
    if current.get("path"):
        entries[current["path"]] = current
    return entries


def worktree_branch(entry: Dict[str, str]) -> Optional[str]:
    branch = entry.get("branch")
    if not branch:
        return None
    if branch.startswith("refs/heads/"):
        return branch[len("refs/heads/") :]
    return branch


@dataclass
class Decision:
    allow: bool = True
    deny_code: Optional[str] = None
    message: Optional[str] = None

    def deny(self, code: str, message: str) -> None:
        if self.allow:
            self.allow = False
            self.deny_code = code
            self.message = message


def default_evidence_path(contract: Optional[Dict[str, Any]]) -> Path:
    out_dir = ".codex/out"
    packet_id = "unknown"
    if contract:
        packet_id = str(contract.get("packet_id") or packet_id)
        evidence = contract.get("evidence") or {}
        out_dir = str(evidence.get("out_dir") or out_dir)
    return Path(out_dir) / packet_id / "g0_enter_work.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Enter WORK (G0) gate.")
    parser.add_argument("--contract", required=True, help="Path to packet contract JSON.")
    parser.add_argument("--evidence-out", help="Override evidence output path.")
    args = parser.parse_args()

    repo_root = git_root()
    decision = Decision()

    contract_path = Path(args.contract)
    contract, contract_err = safe_read_json(contract_path)
    evidence_path = Path(args.evidence_out) if args.evidence_out else default_evidence_path(contract)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)

    packet_id = ""
    branch = ""
    base_ref = ""
    github_ops_required = False
    worktree_root = ".codex/.worktrees"
    deny_if_exists = True

    if contract is None:
        decision.deny("WORKTREE_MISMATCH", contract_err or "contract parse failed")
    else:
        packet_id = str(contract.get("packet_id") or "")
        branch = str(contract.get("branch") or "")
        base_ref = str(contract.get("base_ref") or "")
        github_ops_required = bool(contract.get("github_ops_required", False))
        policy = contract.get("worktree_policy") or {}
        worktree_root = str(policy.get("worktree_root") or ".codex/.worktrees")
        deny_if_exists = bool(policy.get("deny_if_worktree_exists", True))
        if not packet_id or not branch or not base_ref:
            decision.deny("WORKTREE_MISMATCH", "contract missing packet_id/branch/base_ref")

    if repo_root is None:
        decision.deny("WORKTREE_MISMATCH", "not a git repository")

    wt_root = repo_root / worktree_root if repo_root else None
    wt_path = (wt_root / packet_id) if wt_root and packet_id else None

    worktree_created = False
    worktree_reused = False
    mismatch_detail = ""
    collision = False

    wt_list: Dict[str, Dict[str, str]] = {}
    if decision.allow and repo_root:
        wt_list = parse_worktree_list(repo_root)

    if decision.allow and wt_path and wt_path.exists() and deny_if_exists:
        decision.deny("WORKTREE_COLLISION", "worktree exists and deny_if_worktree_exists=true")

    if decision.allow and wt_path and wt_path.exists():
        registered_paths = {Path(p).resolve() for p in wt_list.keys()}
        if wt_path.resolve() not in registered_paths:
            collision = True
            decision.deny("WORKTREE_COLLISION", "worktree path exists but is not registered")

    if decision.allow and wt_path and wt_path.exists():
        entry = wt_list.get(str(wt_path)) or wt_list.get(str(wt_path.resolve()))
        wt_branch = worktree_branch(entry or {})
        if not wt_branch or wt_branch != branch:
            mismatch_detail = f"branch mismatch: expected {branch}, found {wt_branch}"
            decision.deny("WORKTREE_MISMATCH", mismatch_detail)
        else:
            worktree_reused = True

    if decision.allow and wt_path and not wt_path.exists():
        wt_root.mkdir(parents=True, exist_ok=True)
        rc_branch, out_branch, err_branch = run(
            ["git", "show-ref", "--verify", f"refs/heads/{branch}"], cwd=repo_root
        )
        if rc_branch == 0:
            cmd = ["git", "worktree", "add", str(wt_path), branch]
        else:
            cmd = ["git", "worktree", "add", "-b", branch, str(wt_path), base_ref]
        rc, out, err = run(cmd, cwd=repo_root)
        if rc != 0:
            decision.deny("WORKTREE_MISMATCH", f"git worktree add failed: {err.strip() or out.strip()}")
        else:
            worktree_created = True

    if decision.allow and wt_path:
        gdir = git_dir(wt_path)
        if gdir and git_op_in_progress(gdir):
            decision.deny("GIT_OP_IN_PROGRESS", "git operation in progress in worktree")

    head_ref = ""
    head_sha = ""
    base_sha = ""
    base_is_ancestor = None
    if decision.allow and wt_path and repo_root and base_ref:
        base_sha = git_rev_parse(repo_root, base_ref) or ""
        rc, out, err = run(["git", "rev-parse", "HEAD"], cwd=wt_path)
        if rc == 0:
            head_sha = out.strip()
        rc, out, err = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=wt_path)
        head_ref = out.strip() if rc == 0 else ""
        if base_sha:
            rc, out, err = run(["git", "merge-base", "HEAD", base_sha], cwd=wt_path)
            if rc == 0:
                base_is_ancestor = out.strip() == base_sha
            else:
                base_is_ancestor = False
            if base_is_ancestor is False:
                decision.deny("WORKTREE_MISMATCH", "base_ref is not an ancestor of worktree HEAD")

    push_probe: Dict[str, Any] = {}
    if decision.allow and wt_path:
        cmd = ["git", "push", "--dry-run", "-u", "origin", f"HEAD:{branch}"]
        rc, out, err = run(cmd, cwd=wt_path)
        push_probe = {"rc": rc, "stdout": out, "stderr": err}
        if github_ops_required and rc != 0:
            decision.deny("GH_PUSH_DENIED", "git push --dry-run failed")

    evidence = {
        "stage": "G0",
        "timestamp_utc": utc_now(),
        "repo_root": str(repo_root) if repo_root else None,
        "packet_id": packet_id,
        "branch": branch,
        "base_ref": base_ref,
        "base_sha": base_sha or None,
        "head_ref": head_ref,
        "head_sha": head_sha or None,
        "github_ops_required": github_ops_required,
        "worktree_root": worktree_root,
        "deny_if_worktree_exists": deny_if_exists,
        "worktree_path": str(wt_path) if wt_path else None,
        "worktree_created": worktree_created,
        "worktree_reused": worktree_reused,
        "collision": collision,
        "mismatch_detail": mismatch_detail or None,
        "base_ref_is_ancestor": base_is_ancestor,
        "push_probe": push_probe,
        "decision": "ALLOW" if decision.allow else "DENY",
        "deny_code": decision.deny_code,
        "message": decision.message,
    }
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return 0 if decision.allow else 2


if __name__ == "__main__":
    raise SystemExit(main())
