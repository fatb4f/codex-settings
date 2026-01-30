# Project Memory Tests

## Purpose
Verify that Codex consults the global manifest, avoids rescans, and returns accurate project lists.

## Preconditions
- `~/.config/codex` is a symlink to `~/src/codex-settings`.
- Global manifest exists at `~/.config/codex/memory/project-memory/manifest.json`.
- Repo-local metadata exists in multiple repos under `~/src`.

## Tests

### 1) List current projects
**Prompt:** "List current projects."

**Expected behavior:**
- Agent uses `~/.config/codex/memory/project-memory/manifest.json`.
- Response lists projects present in `projects[]`.
- No filesystem rescan unless manifest is missing or stale.

**Pass criteria:**
- Returned list matches the manifest entries (same ids and count).
- Agent states it used the manifest (or implies no rescan).

### 2) Project lookup by id
**Prompt:** "What is `<id>`?"

**Expected behavior:**
- Agent returns the `one_liner`, `path`, and any tags/stack from the manifest.

**Pass criteria:**
- Values match manifest entry for `<id>`.

### 3) Missing manifest behavior
**Setup:** Temporarily move the manifest out of the way.

**Prompt:** "List current projects."

**Expected behavior:**
- Agent requests regeneration or indicates the manifest is missing.
- Agent does not guess or hallucinate results.

**Pass criteria:**
- Response explicitly calls out missing/stale manifest and proposes regeneration.

### 4) No rescan without request
**Prompt:** "List current projects. Do not rescan."

**Expected behavior:**
- Agent uses manifest only.

**Pass criteria:**
- No mention of scanning `~/src`.

### 5) Stale manifest detection (manual)
**Setup:** Add a new repo with `project.metadata.json`, do not regenerate manifest.

**Prompt:** "List current projects."

**Expected behavior:**
- Agent answers from manifest and does not include the new repo.
- If asked, agent suggests regenerating.

**Pass criteria:**
- Output matches manifest, not filesystem.
