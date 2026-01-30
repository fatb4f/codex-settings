---
name: project-memory-skill
description: Maintain a global project manifest from repo-local metadata files.
---

## Purpose
Provide a deterministic global project index by scanning repo-local
`project.metadata.json` files under `~/src` and writing a generated manifest.

## Inputs
- Repo-local files: `<repo_root>/project.metadata.json`
- Schema: `~/.config/codex/memory/project.metadata.schema.json`

## Outputs
- Global manifest: `~/.config/codex/memory/manifest.json`
- Optional conflicts list embedded in the manifest

## Commands
- Generate/refresh:
  - `~/.config/codex/bin/update_project_manifest.py`

## Notes
- The manifest is derived; do not edit by hand.
- Invalid repo metadata files are skipped with warnings.
