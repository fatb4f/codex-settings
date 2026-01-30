# Codex Settings (Example Repo)

This repo is the **source of truth** for a Git-backed Codex configuration and
is intended to be **symlinked** to `~/.config/codex`.

## Layout
- `config.toml` - primary Codex CLI config
- `configs/` - alternate provider configs
- `implementation.md` - implementation notes and standards
- `prompts/` - custom prompt templates
- `skills/` - discoverable skills (`SKILL.md`)
- `policy/` - codex policy files
- `memory/` - project memory + tool-crafting metadata
- `.codex/` - codex-plant-a subtree

## Install
```bash
# Backup existing config (optional)
mv ~/.config/codex ~/.config/codex.bak

# Symlink this repo into place
ln -s ~/src/codex-settings ~/.config/codex
```

## Project Memory
Project memory is split into metadata and execution:
- Metadata: `memory/project-memory/`
- Execution: `skills/project-memory/`

## Tool Crafting
Tool-crafting is split into metadata and execution:
- Metadata: `memory/tool-crafting/`
- Execution: `skills/tool-crafting/`

## Notes
- Treat `memory/project-memory/manifest.json` as generated output; do not edit by hand.
- Skills are discovered from `skills/**/SKILL.md`.
