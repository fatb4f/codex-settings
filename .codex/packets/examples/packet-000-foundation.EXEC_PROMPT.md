# EXEC_PROMPT

```json
{
  "schema_version": "1.0.0",
  "contract_path": ".codex/packets/examples/packet-000-foundation.json",
  "worktree_root": ".codex/.worktrees/packet-000-foundation/",
  "tasks": [
    "Validate the packet runner end-to-end using this contract."
  ],
  "acceptance_checks": [
    "python .codex/tools/run_packet.py .codex/packets/examples/packet-000-foundation.json"
  ],
  "evidence": [
    "summary.md",
    "raw/diffstat.txt"
  ]
}
```

## Tasks
1) Validate the packet runner end-to-end using this contract.

## Acceptance checks
- `python .codex/tools/run_packet.py .codex/packets/examples/packet-000-foundation.json`

## Evidence
Required artifacts under `.codex/out/packet-000-foundation/`:
- `summary.md`
- `raw/diffstat.txt`
