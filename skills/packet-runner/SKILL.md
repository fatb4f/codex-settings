---
name: packet-runner
description: Run a packet contract in an isolated git worktree; enforce cleanliness gates and emit standardized post-run evidence.
---

## Purpose
Execute a packet contract with:
1) **Preflight** checks
2) **Isolated git worktree** provisioning
3) **Bounded execution**
4) **Post-run evidence harness** (Packet-002)

Local WORK runs are approval-free but contract-bounded; violations deny.
PROMOTE remains the integration gate; local WORK still enforces contract invariants.

This skill entrypoint delegates to the canonical runner:
- `.codex/tools/run_packet.py`

## Inputs
- `contract_path` (required): path to JSON contract.

## Outputs (Packet-002)
Always emits a bundle under:
- `.codex/out/<packet_id>/...` (see `packets/README.md`)

## Optional GitHub issue ops
If `contract.github.issue` is configured, the runner will:
1) Ensure the issue exists (created from template if missing)
2) Comment with evidence paths after the run
3) Close the issue on PASS (if configured)

## Hard gates
- Base repo must be clean unless `worktree_policy.mode=allow_dirty_allowlist`.
- Worktree must not already exist when `deny_if_worktree_exists=true`.
- `base_ref` must resolve.

## Minimal invocation
```bash
python .codex/skills/packet-runner/scripts/run_packet.py .codex/packets/examples/packet-001-worktree-collab.json
```
