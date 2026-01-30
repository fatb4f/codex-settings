# Agents Runbook (Plant A)

This file defines the instruction set for operating Codex Plant A when it is
vendored as a git subtree under `.codex/`.

## Situational awareness
- **Upstream vs downstream:** This repo is the upstream Plant A source. Downstream
  repos import it as `.codex/` via git subtree.
- **Self-contained boundary:** Plant A must not require or create files outside
  `.codex/` in downstream repos. Any non-.codex changes must be explicitly allowed
  by the packet contract.
- **Update flow:** Downstream updates come from subtree pulls. Do not edit
  `.codex/` in downstream unless you intend to carry local patches.

## Directory structure (downstream)
- `.codex/agents.md` - this runbook (canonical operational instructions)
- `.codex/README.md` - repository purpose and entry points
- `.codex/plant.manifest.json` - structural manifest for drift prevention
- `.codex/schemas/` - JSON schemas for contracts and the manifest
- `.codex/packets/` - packet templates and example packets
- `.codex/skills/` - reusable skills (packet creation, packet runner)
- `.codex/tools/` - execution tools (preflight, worktree, evidence)
- `.codex/.worktrees/<packet_id>/` - isolated worktrees (WORK zone)
- `.codex/out/<packet_id>/` - evidence bundles
- `.codex/config.toml` - optional local configuration
- `.codex/TEMPLATE_VERSION` - template version marker

## Packet contract template
Use the canonical template files:
- `.codex/packets/packet_contract.template.json`
- `.codex/packets/packet_contract.template.md`

The contract is the single source of truth for boundaries and execution policy.
Copy the JSON template to a packet file and fill identity, boundaries, worktree
policy, network policy, execution, budgets, and evidence settings.

## Packet EXEC_PROMPT
Each packet must include an `EXEC_PROMPT.md` that defines the execution contract.
The prompt should include:
- The authoritative contract path.
- The execution location: `.codex/.worktrees/<packet_id>/`.
- The exact task list.
- Acceptance checks (tests, linters, or commands).
- Required evidence artifacts under `.codex/out/<packet_id>/`.

Template: `.codex/packets/EXEC_PROMPT.template.md`
Schema: `.codex/schemas/exec_prompt.schema.json` (metadata block at top of the prompt)

Recommended packet layout (directory form):
- `.codex/packets/<area>/<packet_id>/contract.json`
- `.codex/packets/<area>/<packet_id>/EXEC_PROMPT.md`

Legacy flat packets are deprecated and should be avoided for new work.
They may still exist under `.codex/packets/examples/<packet_id>.json`.
If using a flat contract, store the corresponding prompt as:
- `.codex/packets/examples/<packet_id>.EXEC_PROMPT.md`

## Execution DAG (packet crafting)
See `.codex/packets/EXECUTION_DAG.md` for the end-to-end DAG that covers packet
crafting, worktree entry, execution, evidence, and promotion.

## Tooling structure
- `.codex/tools/root_preflight.py` - S0 root preflight guardrails.
- `.codex/tools/g0_enter_work.py` - G0 worktree provisioning and checks.
- `.codex/tools/run_packet.py` - primary packet runner orchestration.
- `.codex/tools/evidence/collect_packet_evidence.py` - evidence collection.
- `.codex/tools/validate_plant.py` - plant manifest validation for drift prevention.
- `.codex/tools/validate_exec_prompt.py` - validate EXEC_PROMPT metadata blocks.
- `.codex/tools/migrate_flat_packets.py` - migrate flat packets to directory layout (dry-run by default).
- `.codex/skills/packet-template/` - packet scaffolding helpers.
- `.codex/skills/packet-runner/` - runbook and runner scripts.
