# Packet Execution DAG

This DAG is the canonical flow for crafting and executing packets in Plant A.
It is designed to be complete enough for packet-driven ops without extra
human-in-the-loop instructions.

```
[Author Packet]
  |-- contract.json (from packet_contract.template.json)
  |-- EXEC_PROMPT.md
  v
[S0 Root Preflight]
  v
[G0 Enter WORK]
  v
[S1 Execute in WORK]
  v
[S2 Evidence]
  v
[PROMOTE]
```

## Nodes
- **Author Packet**: Create or update the contract and execution prompt.
- **S0 Root Preflight**: Validate base invariants (clean root unless contract allows).
- **G0 Enter WORK**: Provision/validate `.codex/.worktrees/<packet_id>/`.
- **S1 Execute in WORK**: Run tasks strictly within the worktree and contract bounds.
- **S2 Evidence**: Emit required evidence under `.codex/out/<packet_id>/`.
- **PROMOTE**: Repo-specific integration gate outside Plant A.

## Tools
- S0: `.codex/tools/root_preflight.py`
- G0: `.codex/tools/g0_enter_work.py`
- S1/S2: `.codex/tools/run_packet.py` + `.codex/tools/evidence/collect_packet_evidence.py`
