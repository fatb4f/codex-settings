---
name: packet-template
description: Scaffold a packet contract and EXEC_PROMPT from the SSOT templates.
---

## Purpose
Scaffold a new packet contract and EXEC_PROMPT from the SSOT templates:
- Directory layout (default): `packets/<area>/<packet_id>/contract.json` + `EXEC_PROMPT.md`
- Legacy flat layout: `packets/examples/<packet_id>.json` + `<packet_id>.EXEC_PROMPT.md`

## Inputs
- `packet_id` (required)
- Optional overrides: `area`, `repo`, `base_ref`, `branch`
- Optional: `layout` (dir|flat), `examples` (bool), `validate_prompt` (bool)
  - Default `base_ref`: `main`

## Outputs
- `packets/<area>/<packet_id>/contract.json`
- `packets/<area>/<packet_id>/EXEC_PROMPT.md`

## Notes
This skill does not execute packets; it only scaffolds the contract and prompt.
Use `packet-runner` to execute a packet.
SSOT templates live in `.codex/packets/`.
