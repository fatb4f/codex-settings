# Codex Project Memory: Global Manifest + Repo-local Metadata

## Overview
Maintain a **global project index** under `~/.config/codex/` that an agent can consult as “basic memory” (project ids, paths, one-line descriptions, tags, stack). Each repo under `~/src/**` owns a **repo-local metadata file** with only required fields. A scanner builds the global index by reading these repo-local files.

**Pattern**
- **Repo-local (authoritative):** `<repo_root>/project.metadata.json`
- **Global (derived):** `~/.config/codex/memory/project-memory/manifest.json`
- **Schema (validation):** `~/.config/codex/memory/project-memory/project.metadata.schema.json` and optionally `~/.config/codex/memory/project-memory/global.manifest.schema.json`
- **Agent instructions:** `~/.config/codex/AGENTS.md` points to the global index, and describes the repo-local contract.

**Split (metadata vs execution)**
- **Project memory metadata:** `~/.config/codex/memory/project-memory/`
- **Project memory execution:** `~/.config/codex/skills/project-memory/`
- **Tool-crafting metadata:** `~/.config/codex/memory/tool-crafting/`
- **Tool-crafting execution:** `~/.config/codex/skills/tool-crafting/`

---

## Goals
- Fast, deterministic “where is X?” lookup without scanning the filesystem in-agent.
- Explicit per-repo ownership of metadata (editable in the repo, reviewable in PRs).
- Global index is mechanically generated (no hand edits).
- Minimal, stable contract: **id + one_liner + optional tags/stack/entrypoints**.

## Non-goals
- Not a full dependency graph, build system inventory, or deep repository analysis.
- Not a secrets store.
- Not a source-of-truth for repo configuration beyond a lightweight index.

---

## Requirements

### Functional
1. **Repo-local metadata file**
   - File name: `project.metadata.json`
   - Location: repo root (same directory as `.git` root)
   - Contains only required fields (see contract below).

2. **Global manifest**
   - File: `~/.config/codex/memory/project-memory/manifest.json`
   - Contains:
     - `version`, `root`, `generated_at`
     - `projects[]` entries with extracted metadata + `path` and `source_mtime`

3. **Scanner**
   - Recursively walk `~/src`
   - Identify repo roots
   - If `<repo_root>/project.metadata.json` exists and validates, include it
   - Output sorted deterministically
   - Skip heavy dirs (`node_modules`, `.venv`, `target`, etc.)

4. **Validation**
   - Validate repo-local metadata against a JSON schema
   - Optionally validate the global manifest against a global schema

5. **Agent reference**
   - `~/.config/codex/AGENTS.md` instructs the agent to consult global manifest first
   - Avoid rescans unless explicitly requested or manifest missing

### Operational
- **Regeneration command** is simple and stable (single script).
- **Deterministic output** (stable ordering, stable formatting).
- **Safe failure mode**: invalid repo metadata does not crash scan; it is skipped with a log entry.

---

## Data Contracts

### Repo-local contract: `project.metadata.json`

**Minimal example**
```json
{
  "id": "cbia-builder",
  "title": "cbia-builder",
  "one_liner": "Auditable content-gen pipeline with Control Kernel + policy-gated promotion.",
  "tags": ["cbia", "control", "content-gen"],
  "stack": ["python"],
  "entrypoints": {
    "dev": "just dev",
    "tests": "pytest -q"
  }
}
```

**Required fields**
- `id` (string, unique within `~/src` scope)
- `one_liner` (string, one sentence; practical limit: 120 chars)

**Recommended fields**
- `title` (string)
- `tags` (array of strings)
- `stack` (array of strings)
- `entrypoints` (object of string->string; e.g., dev/test commands)

**Strong rule:** no secrets, tokens, internal credentials.

### Global contract: `~/.config/codex/memory/project-memory/manifest.json`

```json
{
  "version": "1.0",
  "root": "/home/src404/src",
  "generated_at": "2026-01-30T16:00:00-05:00",
  "projects": [
    {
      "id": "cbia-builder",
      "path": "/home/src404/src/cbia-builder",
      "one_liner": "Auditable content-gen pipeline with Control Kernel + policy-gated promotion.",
      "tags": ["cbia", "control", "content-gen"],
      "stack": ["python"],
      "entrypoints": {"dev": "just dev", "tests": "pytest -q"},
      "source_metadata": "project.metadata.json",
      "source_mtime": 1769790000
    }
  ]
}
```

---

## Schema

### `~/.config/codex/memory/project-memory/project.metadata.schema.json`
- Draft: 2020-12
- Enforce required fields and types
- Optional additional constraints:
  - `one_liner` max length
  - `id` pattern `[a-z0-9][a-z0-9-_]{1,64}`

### Optional: `~/.config/codex/memory/project-memory/global.manifest.schema.json`
- Ensures output shape and types are stable

---

## Scanner Design

### Repo root detection
Prefer this order:
1. `git -C <dir> rev-parse --show-toplevel` equals `<dir>`
2. fallback: `<dir>/.git` exists (dir or file)

### Directory walk
- Recursive walk from `~/src`
- When repo root found:
  - attempt to read `<repo_root>/project.metadata.json`
  - validate schema
  - include extracted fields
  - **do not descend further into repo** (prevents O(n²) in monorepos)

### Skips
Hard skip names:
- `.git`, `.codex`, `node_modules`, `.venv`, `venv`, `target`, `dist`, `build`, `.tox`, `.pytest_cache`, `.mypy_cache`, `.cache`

### Determinism
- Sort `projects` by `(id, path)`
- JSON output:
  - `sort_keys=true`
  - `indent=2`
  - newline at EOF

### Error handling
- Invalid JSON: skip project, record warning
- Missing required fields: skip
- Duplicate `id`:
  - default: keep **first** by lexical path order and record conflict
  - alternative: include `conflicts[]` section listing duplicates

### Incremental option (optional later)
- Keep `~/.config/codex/memory/project-memory/manifest.cache.json` of `{path -> source_mtime}`
- Only re-parse changed metadata files

---

## Integration with Codex CLI

### `~/.config/codex/AGENTS.md` instruction block
- Point to global manifest path
- Specify that each entry has repo-local `project.metadata.json`
- “Do not rescan `~/src` unless missing/stale or user requests”

### Access boundaries
- Reading `~/.config/codex/...` may be considered outside workspace depending on how Codex is invoked.

Mitigations (choose one):
1. **Keep as-is** and approve reads when prompted.
2. Add a **symlink** inside active repo `.codex/memory/project-memory/manifest.json -> ~/.config/codex/memory/project-memory/manifest.json`.
3. Add a **just target** in `plant-a-codex` that copies the manifest into the workspace on demand.

---

## Implementation Plan

### Phase 0 — Establish contracts (P0)
- Add `project.metadata.schema.json` under `~/.config/codex/memory/project-memory/`
- Add sample `project.metadata.json` template (copy-paste ready)
- Add `AGENTS.md` instructions block

**Deliverables**
- `~/.config/codex/memory/project-memory/project.metadata.schema.json`
- `~/.config/codex/AGENTS.md` updated
- `~/src/<one repo>/project.metadata.json` as reference example

### Phase 1 — Build scanner (P0)
- Implement `~/.config/codex/bin/update_project_manifest.py`
- Features:
  - walk `~/src`
  - repo root detect
  - parse + validate repo-local metadata
  - output global manifest

**Deliverables**
- `~/.config/codex/bin/update_project_manifest.py`
- `~/.config/codex/memory/project-memory/manifest.json` (generated)

### Phase 2 — Add local ergonomics (P1)
- Add a `just` recipe (in `plant-a-codex` or a personal justfile) to regenerate
  - `just codex-manifest-update`
- Add optional `--root` arg to scanner for alternate roots

**Deliverables**
- `justfile` target(s)
- CLI args: `--root`, `--out`, `--strict`

### Phase 3 — Repo enforcement (P1)
Per repo:
- Add `project.metadata.json`
- Add CI/pre-commit check:
  - validate JSON schema
  - enforce required fields

**Deliverables**
- `tools/validate_project_metadata.py` (optional) or a small `python -m jsonschema ...` invocation
- pre-commit hook OR GitHub Actions step

### Phase 4 — Quality gates (P2)
- Detect duplicates and emit conflict list
- Optional incremental caching
- Optional global schema validation

---

## Test Plan

### Unit tests (scanner)
- Repo root detection (plain repo, worktree, nested dirs)
- Valid metadata parsed into global entry
- Invalid JSON skipped
- Missing required fields skipped
- Deterministic sorting
- Duplicate id conflict behavior

### Integration checks
- Run scanner against a synthetic `~/src` fixture tree
- Validate output against global schema (if added)

---

## Rollout Checklist

1. Create `~/.config/codex/memory/project-memory/` directory
2. Add schema(s)
3. Add scanner script + executable bit
4. Add `AGENTS.md` block
5. Add `project.metadata.json` to top N repos
6. Run scanner → verify global manifest
7. Add CI checks gradually per repo

---

## Future Extensions (optional)
- Add fields:
  - `primary_readme` pointer
  - `status` (active/paused)
  - `owner` (string)
  - `scope` (engineering/content-gen/ops)
- Add a `manifest.search.json` derivative optimized for agent lookup (precomputed lowercase tokens)
- Generate a `projects.md` human-readable table as a view artifact



---

# Architecture Pattern: Control-Oriented Tooling (Controller/Actuator Standard)

## Canonical reference
This repository/workspace standard is anchored by the **Python Tooling Standard (Proposal)** document. Treat it as the baseline requirements for robustness, control flow, adaptive controls, and CI gating.
- Canonical location (global): `~/.config/codex/memory/tool-crafting/python_standard.md`
- Repo access strategy (preferred): `.codex/memory/tool-crafting/python_standard.md -> ~/.config/codex/memory/tool-crafting/python_standard.md`

## When this pattern is REQUIRED
Apply this pattern whenever you **design, add, or materially modify**:
- a Python tool in `codex-plant-a`, `ctrlr`, or adjacent plant-a|b repos
- any “controller-like” orchestration script (pipeline drivers, scanners, validators, packet runners)
- any tool intended for reuse (not a one-off script)

## Required components (artifact checklist)
A compliant tool/pipeline must define or reference all of the following:

### 1) Manifest
A machine-readable manifest describing the tool or “plant surface”.
- For project-indexing: global `~/.config/codex/memory/project-memory/manifest.json` + per-repo `project.metadata.json`
- For a tool/pipeline: `tool.manifest.json` (or repo-local section) describing entrypoints, modes, inputs, outputs

### 2) Schema
Explicit schemas for all structured inputs/outputs.
- JSON Schema (preferred) or dataclasses/pydantic models at the boundary
- Unknown fields rejected by default
- Normalization happens before core logic

### 3) DAG
An explicit execution model.
- `dag.json` = SSOT (machine-readable)
- `dag.mmd` = generated view (no-hand-edit rule)
- Nodes have: preconditions, actions, outputs, failure terminals, reason codes

### 4) Gating
Mechanical gates that enforce contracts and prevent unsafe execution.
- Preflight gate: validates inputs, environment, allowed paths, budgets
- CI gate: lint/format, tests, type check, security scans
- Promotion gate: only promoted artifacts pass all required gates

### 5) Error handling
A stable, documented error taxonomy and predictable messages.
- Domain exceptions (small set)
- Stable, actionable error messages
- No swallowed exceptions without re-raise + context

### 6) Controller / Actuator split
Separate *what to do* from *how it touches the world*.
- **Controller**: orchestration, DAG transitions, policy selection, gating decisions
- **Core logic**: pure/side-effect-minimized functions
- **Actuators**: filesystem/network/subprocess boundaries with timeouts + retries

### 7) Adaptive controls
Built-in resilience features for scale and partial failure.
- Feature flags for risky paths (default off)
- Dynamic limits (depth/size/time) derived from input scale
- Deterministic retries (bounded attempts, fixed backoff) for transient failures
- Circuit breaker for repeated external failures
- Bulkhead isolation for heavy/risky workloads
- Idempotence and atomic writes (temp + rename)

## Minimal directory conventions (recommended)
- `control/` for schemas, dags, gates, policies
- `tools/` for executables (controllers)
- `src/<pkg>/` for reusable library components (core logic)
- `tests/` for unit + negative/error-path tests

## Minimum CI gates
- Lint/format: `ruff`
- Tests: `pytest`
- Type check: `pyright` or `mypy`
- Security: secrets scan + dependency vuln scan

## Definition of Done
- Boundary validation tests + negative tests for error paths
- Deterministic output for identical input
- Explicit branching with test coverage per branch
- Timeouts on external calls; retries bounded and deterministic
- Gates all green

## Pattern library (selection map)
Use these patterns to structure control flow and resilience:
- Chain of Responsibility: multi-step validation/normalization
- Template Method: fixed pipeline skeleton with constrained extension points
- Strategy: switch policies/modes (strict vs permissive)
- Command: queueable/reversible actions, auditable steps
- State: explicit lifecycle phases with legal transitions
- Circuit Breaker / Retry / Bulkhead: resilience boundaries



---

# Manage it like `codex-settings` (symlinked to `~/.config/codex`)

## Why this matches the `feiskyer/codex-settings` model
That repo’s primary move is: **make `~/.config/codex` a symlink to this repo**, so Codex always loads versioned config, prompts, policies, and skills from its home directory.

## Recommended operating modes
- **Private repo (recommended):** you can safely commit machine-specific paths and a generated `memory/project-memory/manifest.json`.
- **Public repo:** commit only templates + docs; keep machine-specific artifacts (like `memory/project-memory/manifest.json`) untracked.

## Suggested `~/.config/codex` repo layout
```text
~/.config/codex/                  # git repo (or symlink)
  config.toml
  AGENTS.md
  memory/
    project-memory/
      manifest.json               # generated (private) or template (public)
      project.metadata.schema.json
      global.manifest.schema.json # optional
    tool-crafting/
      controller_architecture.md  # manifest/schema/dag/gates/etc. standard
      python_standard.md          # canonical tooling baseline
      control/
        schemas/
          tool.manifest.schema.json
          dag.schema.json
        exceptions/
  dags/
    *.dag.json                    # SSOT DAGs
    *.dag.mmd                     # generated views
  policy/
    *.{rego,yaml,json}
  prompts/
    *.md
  skills/
    <skill-id>/
  bin/
    update_project_manifest.py
  justfile                        # optional
  .gitignore
```

## `.gitignore` (public-safe default)
```gitignore
# machine-specific
memory/project-memory/manifest.json

# local outputs
.codex-out/
```

## Required instruction pointers (AGENTS.md)
- Global index: `~/.config/codex/memory/project-memory/manifest.json`
- Repo-local metadata: `<repo_root>/project.metadata.json`
- Architecture pattern: `~/.config/codex/memory/tool-crafting/controller_architecture.md`
- Canonical baseline: `~/.config/codex/memory/tool-crafting/python_standard.md`
- Rule: consult global index first; do not rescan `~/src` unless requested or missing.

## Repo access strategy (preferred)
- Use repo-local symlinks for fast, consistent access:
  - `.codex/memory/project-memory/manifest.json -> ~/.config/codex/memory/project-memory/manifest.json`
  - `.codex/memory/tool-crafting/controller_architecture.md -> ~/.config/codex/memory/tool-crafting/controller_architecture.md`
  - `.codex/memory/tool-crafting/python_standard.md -> ~/.config/codex/memory/tool-crafting/python_standard.md`

## Implementation sequence
1. Keep this repo as the source of truth.
2. Symlink it into place: `ln -s ~/src/codex-settings ~/.config/codex`.
3. Copy `python_standard.md` into `memory/tool-crafting/python_standard.md`.
4. Update `AGENTS.md` to reference `memory/project-memory/manifest.json` and the pattern docs.
5. Add `bin/update_project_manifest.py` and generate `memory/project-memory/manifest.json`.
6. Add `project.metadata.json` to each repo you want indexed.
7. Optional: add a `just update` target and/or a pre-commit hook to regenerate before commits.
