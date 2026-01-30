# Codex Global Project Memory + Tool-Crafting

## Purpose
Provide a global, deterministic project index for fast lookups without scanning
`~/src` during agent execution, and point to canonical tool-crafting standards.

## Source of truth
- Repo-local metadata lives at `<repo_root>/project.metadata.json`.
- The global manifest is derived and **must not** be edited by hand.

## Global manifest
- Path: `/home/src404/.config/codex/memory/project-memory/manifest.json`
- Schema: `/home/src404/.config/codex/memory/project-memory/project.metadata.schema.json`

## Tool-crafting standards
- Architecture pattern: `/home/src404/.config/codex/memory/tool-crafting/controller_architecture.md`
- Canonical baseline: `/home/src404/.config/codex/memory/tool-crafting/python_standard.md`
- Schemas: `/home/src404/.config/codex/memory/tool-crafting/control/schemas/`

## Knowledge base
- Canonical knowledge entries live under `/home/src404/src/knowledge/`.
- Prefer those entries for domain context and definitions before ad-hoc web search.

## Agent behavior
- Consult the global manifest first for project lookup.
- Do not rescan `~/src` unless the manifest is missing, stale, or the user requests it.

## Access strategy (default)
- Prefer repo-local symlinks for fast access:
  - `.codex/memory/project-memory/manifest.json -> /home/src404/.config/codex/memory/project-memory/manifest.json`
  - `.codex/memory/tool-crafting/controller_architecture.md -> /home/src404/.config/codex/memory/tool-crafting/controller_architecture.md`
  - `.codex/memory/tool-crafting/python_standard.md -> /home/src404/.config/codex/memory/tool-crafting/python_standard.md`

## Regeneration
- Run: `/home/src404/.config/codex/bin/update_project_manifest.py`
