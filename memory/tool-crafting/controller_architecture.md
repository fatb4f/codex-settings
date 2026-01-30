# Architecture Pattern: Control-Oriented Tooling (Controller/Actuator Standard)

## Canonical reference
This repository/workspace standard is anchored by the **Python Tooling Standard (Proposal)** document. Treat it as the baseline requirements for robustness, control flow, adaptive controls, and CI gating.
- Canonical location (global): `~/.config/codex/memory/tool-crafting/python_standard.md`
- Repo access strategy (preferred): `.codex/memory/tool-crafting/python_standard.md -> ~/.config/codex/memory/tool-crafting/python_standard.md`

## When this pattern is REQUIRED
Apply this pattern whenever you **design, add, or materially modify**:
- a Python tool in `codex-plant-a`, `ctrlr`, or adjacent plant-a|b repos
- any “controller-like” orchestration script (pipeline drivers, scanners, validators, packet runners)
- any tool intended for reuse (not a one-off script)

## Codex agent tool-crafting workflow (summary)
1. **Clarify scope and mode**: identify tool intent, safety constraints, and required modes (strict/permissive).
2. **Define contracts first**: draft `tool.manifest.json`, input/output schemas, and `dag.json`.
3. **Split controller vs core vs actuator**: isolate side effects to actuators with timeouts/retries.
4. **Implement gates**: preflight validation, CI gates, and promotion gate.
5. **Add resilience**: retries, circuit breakers, bulkheads, atomic writes.
6. **Test negative paths**: error taxonomy + deterministic failures.
7. **Ship with docs**: include manifest, schemas, DAG, and exception (if any).

**Templates (start here)**
- Tool manifest: `~/.config/codex/memory/tool-crafting/templates/tool.manifest.template.json`
- DAG: `~/.config/codex/memory/tool-crafting/templates/dag.template.json`

## Required components (artifact checklist)
A compliant tool/pipeline must define or reference all of the following:

### 1) Manifest
A machine-readable manifest describing the tool or “plant surface”.
- For project-indexing: global `~/.config/codex/memory/manifest.json` + per-repo `project.metadata.json`
- For a tool/pipeline: `tool.manifest.json` (or repo-local section) describing entrypoints, modes, inputs, outputs
- Required schema (global): `~/.config/codex/memory/tool-crafting/control/schemas/tool.manifest.schema.json`
- Repo access strategy (preferred): `.codex/memory/tool-crafting/control/schemas/tool.manifest.schema.json -> ~/.config/codex/memory/tool-crafting/control/schemas/tool.manifest.schema.json`

### 2) Schema
Explicit schemas for all structured inputs/outputs.
- JSON Schema (preferred) or dataclasses/pydantic models at the boundary
- Unknown fields rejected by default
- Normalization happens before core logic

### 3) DAG
An explicit execution model.
- `dag.json` = SSOT (machine-readable)
- `dag.mmd` = generated view (no-hand-edit rule)
- Nodes have: preconditions, actions, outputs, failure terminals, reason codes
- Required schema (global): `~/.config/codex/memory/tool-crafting/control/schemas/dag.schema.json`
- Repo access strategy (preferred): `.codex/memory/tool-crafting/control/schemas/dag.schema.json -> ~/.config/codex/memory/tool-crafting/control/schemas/dag.schema.json`

### 4) Gating
Mechanical gates that enforce contracts and prevent unsafe execution.
- Preflight gate: validates inputs, environment, allowed paths, budgets
- CI gate: lint/format, tests, type check, security scans
- Promotion gate: only promoted artifacts pass all required gates

### 5) Error handling
A stable, documented error taxonomy and predictable messages.
- Domain exceptions (small set)
- Stable, actionable error messages
- No swallowed exceptions without re-raise + context

### 6) Controller / Actuator split
Separate *what to do* from *how it touches the world*.
- **Controller**: orchestration, DAG transitions, policy selection, gating decisions
- **Core logic**: pure/side-effect-minimized functions
- **Actuators**: filesystem/network/subprocess boundaries with timeouts + retries

### 7) Adaptive controls
Built-in resilience features for scale and partial failure.
- Feature flags for risky paths (default off)
- Dynamic limits (depth/size/time) derived from input scale
- Deterministic retries (bounded attempts, fixed backoff) for transient failures
- Circuit breaker for repeated external failures
- Bulkhead isolation for heavy/risky workloads
- Idempotence and atomic writes (temp + rename)

## Minimal directory conventions (recommended)
- `control/` for schemas, dags, gates, policies
- `tools/` for executables (controllers)
- `src/<pkg>/` for reusable library components (core logic)
- `tests/` for unit + negative/error-path tests

## Minimum CI gates
- Lint/format: `ruff`
- Tests: `pytest`
- Type check: `pyright` or `mypy`
- Security: secrets scan + dependency vuln scan

## Exception policy (waivers)
If a tool cannot meet a required component, an exception is mandatory.
- Store as `~/.config/codex/memory/tool-crafting/control/exceptions/<tool_id>.md`
- Must include: scope, rationale, risk assessment, compensating controls, approver, and expiry date
- Reference the exception in `tool.manifest.json`

## Definition of Done
- Boundary validation tests + negative tests for error paths
- Deterministic output for identical input
- Explicit branching with test coverage per branch
- Timeouts on external calls; retries bounded and deterministic
- Gates all green

## Pattern library (selection map)
Use these patterns to structure control flow and resilience:
- Chain of Responsibility: multi-step validation/normalization
- Template Method: fixed pipeline skeleton with constrained extension points
- Strategy: switch policies/modes (strict vs permissive)
- Command: queueable/reversible actions, auditable steps
- State: explicit lifecycle phases with legal transitions
- Circuit Breaker / Retry / Bulkhead: resilience boundaries
