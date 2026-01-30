# Packets

Packets are **mechanical, auditable units of work** executed through Codex skills.

## Concepts
- **Contract**: a JSON file that declares intent, boundaries, and allowed moves.
- **Worktree**: each packet executes inside an isolated git worktree under `.codex/.worktrees/<packet_id>`.
- **Evidence**: each run emits immutable artifacts under `.codex/out/<packet_id>/`.

## Required invariants
- No execution on a dirty base repo (unless explicitly allowed by `worktree_policy`).
- Packet execution occurs in an isolated worktree.
- Evidence is always emitted (manifest + hashes).

## Files
- `packet_contract.template.md`: canonical contract template to copy into a packet contract file.
- `EXEC_PROMPT.template.md`: canonical execution prompt template to copy into a packet prompt file.
- `../schemas/exec_prompt.schema.json`: schema for the EXEC_PROMPT metadata block.

## Typical usage
1) Create contract under `packets/<area>/<packet_id>/contract.json`.
2) Create prompt under `packets/<area>/<packet_id>/EXEC_PROMPT.md`.
3) Run `packet-runner` with the contract path.
4) Review evidence under `.codex/out/<packet_id>/`.

Legacy flat layout (deprecated, keep for backward compatibility only):
- Contract: `packets/examples/<packet_id>.json`
- Prompt: `packets/examples/<packet_id>.EXEC_PROMPT.md`

Migration helper (dry-run by default):
```
python tools/migrate_flat_packets.py --area <area>
python tools/migrate_flat_packets.py --area <area> --apply
```
