# Python Tooling Standard (Proposal)

## Purpose
Define a consistent, minimal standard for Python tools built and used in the same operating context as codex-plant-a and ctrlr. The initial objective is code-quality and robustness focused on input handling, error handling, and control flow.

## Scope
Applies to:
- Python tools in codex-plant-a, ctrlr, and adjacent plant-a|b repos
- Downstream repos that follow the same runtime and CI conventions

Out of scope:
- One-off scripts not intended for reuse
- Prototypes or notebooks unless promoted to a tool

## Robustness Definition (Initial Focus)
For this standard, “robustness” means:
- Input handling: validate inputs at boundaries with clear contracts
- Error handling: explicit, consistent exceptions with predictable messages
- Control flow: deterministic, observable behavior without hidden branches

---

# Required Standard

## Input Handling
- Validate public inputs at module boundaries.
- Prefer explicit schemas or dataclasses for structured inputs.
- Reject unknown fields unless explicitly allowed.
- Normalize inputs before use (types, paths, defaults).

## Error Handling
- Raise domain-specific exceptions (or a small, documented set).
- Error messages must be stable and actionable.
- Never swallow exceptions without logging or re-raising with context.

## Control Flow
- Avoid implicit side effects (shell, network, filesystem) in core logic.
- Make branching logic explicit and test each branch.
- Deterministic output for identical input.

---

# Adaptive Controls, Reliability, Resilience

## Adaptive Controls
- Feature flags for risky or experimental paths (default off).
- Dynamic limits for size, depth, or time based on input scale.
- Graceful degradation paths when optional dependencies are missing.

## Reliability
- Stable error taxonomy (Input, Config, Runtime, External).
- Deterministic retries with fixed backoff and bounded attempts.
- Idempotent outputs and atomic writes (temp file + rename).

## Resilience
- Explicit timeouts on external calls (FS, network, subprocess).
- Circuit-breakers for repeated failures with clear error output.
- Optional state snapshots or checkpoints for long-running flows.

---

# Supporting Standards

## Packaging
- Use `pyproject.toml` with PEP 621 metadata.
- Define `project.optional-dependencies` for tooling extras.
- Base install must import without optional extras.
- Optional features must fail with a clear error naming the exact extra to install.

## Project Layout
- `src/` layout required.
- Public API exported from package `__init__.py`.
- Tool entry points via console scripts if user-facing.

## Testing
- `pytest` is the default test runner.
- Unit tests live in `tests/` and mirror module names.
- Tests must cover validation failures and error paths.
- Determinism tests required for any randomness.

## Linting and Formatting
- `ruff` for lint and formatting.
- Keep configuration in `pyproject.toml`.

## Type Checking
- Choose one: `pyright` or `mypy`.
- Core modules must be typed and pass type checks.
- Maintain a consistent strictness baseline for core code.

## Security and Dependency Hygiene
- Secrets scanning is required: `gitleaks` or `detect-secrets`.
- Dependency vulnerability scan is required: `pip-audit` or `osv-scanner`.

## Documentation
- README must include:
  - Purpose
  - Install / extras
  - Minimal usage example
  - Error behavior / guarantees

---

# CI Gates (Minimum)
- Lint/format: `ruff`
- Tests: `pytest`
- Type check: `pyright` or `mypy`
- Security: secrets scan + dependency scan

---

# Definition of Done (Initial Focus)
- Input validation tests for public interfaces
- Negative tests for error paths
- Explicit branch coverage for core control flow
- Type checks pass on core modules
- CI gates all green
- Optional extras failure message includes exact install hint

---

# Pattern References (External)
Use design pattern examples as a reference library when shaping control flow and resilience features. These are references only, not requirements.

- RefactoringGuru design patterns (Python): use for conceptual and real-world examples when choosing patterns for control flow and error handling.
- Preferred focus areas: Strategy, State, Command, Chain of Responsibility, and Template Method.
- Resilience-related patterns to adapt as needed: Circuit Breaker (when implemented), Retry with Backoff, and Bulkhead.

---

# Common Patterns We Expect to Encounter

## Input and validation flow
- Chain of Responsibility: sequential validators or normalizers
- Template Method: fixed validation pipeline with overridable steps

## Error handling and recovery
- Strategy: swap error handling policy (strict vs. permissive)
- Command: structured actions for retries or rollbacks
- Circuit Breaker: short-circuit repeated failures

## Control flow and orchestration
- State: explicit lifecycle of a tool or pipeline step
- Command: queueable or auditable operations
- Template Method: stable orchestration with small extension points

## Resilience boundaries
- Bulkhead: isolate workloads or resource pools
- Retry with Backoff: transient failures on external calls

---

# Pattern Selection Map (Problem -> Pattern)

| Problem | Recommended pattern |
| --- | --- |
| Multiple validation steps with early exit | Chain of Responsibility |
| Fixed pipeline with a few custom steps | Template Method |
| Swap behavior based on mode or config | Strategy |
| Queueable or reversible actions | Command |
| Tool lifecycle with explicit phases | State |
| Repeated external failures | Circuit Breaker |
| Transient external errors | Retry with Backoff |
| Isolate heavy or risky workloads | Bulkhead |

---

# Minimal Pattern Snippets (Python-Idiomatic)

## Chain of Responsibility (validation)
```python
from typing import Callable, Iterable

Validator = Callable[[dict], dict]

def run_validators(raw: dict, validators: Iterable[Validator]) -> dict:
    current = raw
    for validate in validators:
        current = validate(current)
    return current
```

## Strategy (error policy)
```python
from typing import Callable

ErrorPolicy = Callable[[Exception], None]

def strict_policy(err: Exception) -> None:
    raise err

def log_only_policy(err: Exception) -> None:
    print(f"warn: {err}")

def handle(err: Exception, policy: ErrorPolicy) -> None:
    policy(err)
```

## Template Method (pipeline)
```python
def run_pipeline(raw: dict, pre, core, post):
    validated = pre(raw)
    result = core(validated)
    return post(result)
```

## Command (queueable action)
```python
from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class Command:
    name: str
    action: Callable[[], None]

    def run(self) -> None:
        self.action()
```

## State (lifecycle)
```python
from enum import Enum

class Phase(Enum):
    INIT = "init"
    RUN = "run"
    DONE = "done"

TRANSITIONS = {
    Phase.INIT: {Phase.RUN},
    Phase.RUN: {Phase.DONE},
    Phase.DONE: set(),
}
```

## Circuit Breaker (simple)
```python
from dataclasses import dataclass
import time

@dataclass
class Breaker:
    failures: int = 0
    opened_at: float | None = None
    threshold: int = 3
    cooldown_s: float = 30.0

    def allow(self) -> bool:
        if self.opened_at is None:
            return True
        return (time.time() - self.opened_at) >= self.cooldown_s

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.threshold:
            self.opened_at = time.time()
```

## Retry with Backoff (deterministic)
```python
import time

def retry(fn, attempts=3, delay_s=0.1):
    for i in range(attempts):
        try:
            return fn()
        except Exception:
            if i == attempts - 1:
                raise
            time.sleep(delay_s)
```

## Bulkhead (bounded pool)
```python
from concurrent.futures import ThreadPoolExecutor

BULKHEAD = ThreadPoolExecutor(max_workers=2)
```

---

# Adoption Notes
- When migrating an existing tool, prioritize:
  1) Input validation and error-path tests
  2) ruff + pytest gates
  3) type checking
  4) security scans

- If a repo cannot meet a requirement, document the exception and timeline.

---

# Appendix: Example Invariants
Use these to guide Semgrep/CodeQL/Pysa rules:

- All public inputs validate at the boundary
- All errors are typed and documented
- No shell execution in controller/runtime code
- All path checks use `resolve()` + `relative_to()`
- Contract parsing must schema-validate
- Optional deps must raise with the exact extra name to install
