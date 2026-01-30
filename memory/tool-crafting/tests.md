# Tool-Crafting Tests

## Purpose
Verify that Codex applies the tool-crafting standards, respects schemas, and references the correct canonical documents.

## Preconditions
- `~/.config/codex` is a symlink to `~/src/codex-settings`.
- Tool-crafting docs exist under `~/.config/codex/memory/tool-crafting/`.
- Schemas exist under `~/.config/codex/memory/tool-crafting/control/schemas/`.

## Tests

### 1) Standards awareness
**Prompt:** "What standards apply when adding a controller tool?"

**Expected behavior:**
- Agent references `controller_architecture.md` and `python_standard.md`.
- Agent lists required components (manifest, schema, DAG, gates, error taxonomy, controller/actuator split, adaptive controls).

**Pass criteria:**
- Response matches the standard’s checklist.

### 2) Schema reference correctness
**Prompt:** "Where are the tool manifest and DAG schemas?"

**Expected behavior:**
- Agent points to `~/.config/codex/memory/tool-crafting/control/schemas/`.

**Pass criteria:**
- Paths are correct and consistent with the repo.

### 3) Template usage
**Prompt:** "Generate a starter tool.manifest.json and dag.json."

**Expected behavior:**
- Agent uses templates under `memory/tool-crafting/templates/`.
- Output conforms to the schemas.

**Pass criteria:**
- Fields match template and schema requirements.

### 4) Exception policy adherence
**Prompt:** "This tool cannot implement a DAG; what do we do?"

**Expected behavior:**
- Agent instructs creating an exception under `~/.config/codex/memory/tool-crafting/control/exceptions/` and referencing it in `tool.manifest.json`.

**Pass criteria:**
- Exception location and required fields are stated.

### 5) Controller/actuator split
**Prompt:** "Sketch the architecture for a new tool."

**Expected behavior:**
- Agent separates controller, core logic, and actuators.

**Pass criteria:**
- Clear split with side-effects isolated to actuators.
