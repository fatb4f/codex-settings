# Codex Settings (Example Repo)

This repo is a reference layout for a Git-backed Codex configuration at
`~/.config/codex`. It is intentionally minimal and is meant to be copied or
symlinked into that location.

## Layout
- `config.toml` - primary Codex CLI config
- `configs/` - alternate provider configs
- `mcp/` - example MCP server snippets
- `prompts/` - custom prompt templates
- `skills/` - discoverable skills (`SKILL.md`)
- `policy/` - codex policy files
- `patterns/` - reusable design patterns
- `control/` - control schemas
- `memory/` - project memory schemas and manifest
- `bin/` - helper scripts
- `.codex/` - codex-plant-a subtree

## Install
```bash
# Backup existing config (optional)
mv ~/.config/codex ~/.config/codex.bak

# Clone here
git clone https://github.com/fatb4f/codex-settings.git ~/.config/codex
```

## MCP
Example MCP configs live under `mcp/`. Copy entries into your active config as
needed.

## Project Memory
Project memory is packaged as a skill and assets in this repo:
- Schema + manifest: `memory/`
- Generator: `bin/update_project_manifest.py`
- Skill: `skills/project-memory-skill/`

Refresh the manifest:
```bash
~/.config/codex/bin/update_project_manifest.py
```

## Notes
- Treat `memory/manifest.json` as generated output; do not edit by hand.
- Skills are discovered from `skills/**/SKILL.md`.
