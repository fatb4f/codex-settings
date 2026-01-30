# Packet Contract (SSOT)

This document describes the packet contract. The single source of truth for generation is
`.codex/packets/packet_contract.template.json`.

> Copy to `packets/examples/<packet_id>.json` and fill in.

## Identity
- packet_id: "packet-001-worktree-collab"
- area: "pipeline-sre" | "engineering" | "content-gen"
- repo: "<org>/<repo>" (or local path)

## Git
- base_ref: "main" (or tag/sha)
- branch: "packet/<packet_id>"
- github_ops_required: false

## Path controls
- allowed_paths: [".codex/"]
- forbidden_outputs: []
  - Use this list only for outputs that must not appear in git diffs or tracked files.
  - Runtime directories like `.codex/out/` and `.codex/.worktrees/` are allowed to exist and should be ignored via `.gitignore`.

## Worktree policy (required)
- worktree_policy:
    mode: "strict" | "allow_dirty_allowlist"
    worktree_root: ".codex/.worktrees"
    deny_if_worktree_exists: true
    allow_dirty_globs: []          # used only when mode=allow_dirty_allowlist
    allow_untracked_globs: []      # used only when mode=allow_dirty_allowlist

## Network policy (required)
- network_policy:
    internet_access: "off" | "on"
    domain_allowlist_preset: "none" | "corp" | "public"
    additional_domains: []
    allowed_http_methods: []

## Execution
- run:
    regen_cmd: ""                 # optional
    test_cmd: ""                  # optional
    commands: []                   # optional list of additional commands (strings)

## Budgets (optional)
- budgets:
    max_changed_files: 200
    max_changed_lines: 20000

## Evidence (required)
- evidence:
    out_dir: ".codex/out"         # evidence is written under .codex/out/<packet_id>/
    include_git_diff_patch: false
