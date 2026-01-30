---
name: tool-crafting
description: Apply controller/actuator standards and validate tooling manifests and DAGs.
---

## Purpose
Provide execution guidance for tool-crafting standards and schema validation.

## Inputs
- Tool manifests: `tool.manifest.json`
- DAGs: `dag.json`
- Schemas: `~/.config/codex/memory/tool-crafting/control/schemas/`
- Templates: `~/.config/codex/memory/tool-crafting/templates/`

## Outputs
- Validation results (pass/fail with reason codes)
- Optional generated views (e.g., `dag.mmd`) when a generator is provided

## Commands
- Validation scripts live under `scripts/`

## Notes
- Schemas are authoritative; unknown fields should be rejected by default.
- Exceptions must be recorded under `~/.config/codex/memory/tool-crafting/control/exceptions/`.
