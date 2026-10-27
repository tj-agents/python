---
name: build
description: Python build and tooling — uv as the one project tool, `pyproject.toml` as the only metadata and configuration file, the uv_build backend, the Python version policy, the committed lockfile, dependency groups and bounds, the ruff, mypy and pytest gate and CI, as the generic baseline plus Tommy's recorded decisions. Read before writing or reviewing Python project setup, dependencies or CI; only what is recorded here applies.
kind: convention
domain: python
profile: core
applicability: Python projects
requires: python
provenance: house
---

# Python build

Owns the toolchain, the Python version policy, `pyproject.toml` metadata, dependency declarations, the
verification gate and CI. Each rule names its kind (`python:learning`).

## Baseline

- uv is the one tool for installing Python, creating environments, adding and locking dependencies, running
  commands and building. No pip, pip-tools, Poetry, Pipenv or conda workflow, and no `requirements*.txt`.
  Why: one tool covers the whole lifecycle, so no project re-decides it. Source: uv docs. [bootstrap default]
- All metadata and tool configuration lives in `pyproject.toml`; no `setup.py`, `setup.cfg`, `tox.ini`,
  `pytest.ini`, `mypy.ini` or `ruff.toml`. Source: PEP 621; Packaging User Guide. [ecosystem]
- The build backend is `uv_build`, as `uv init --package` writes it. Source: uv docs. [bootstrap default]
- `requires-python = ">=X.Y"` and `.python-version` name the same minor, 3.12 or newer, and change together.
  Source: uv docs, "Python versions". [bootstrap default]
- `uv.lock` is committed, and CI installs with `uv sync --locked` so a stale lock fails. Source: uv docs,
  "Locking and syncing". [ecosystem]
- Runtime dependencies are added with `uv add` and keep the lower bound it writes; an upper bound appears only
  for a known incompatibility. Development tools sit in the PEP 735 `dev` dependency group (`uv add --dev`).
  Source: uv docs; PEP 735. [ecosystem]
- The gate runs locally and in CI on Windows and Ubuntu, and every step must pass:

  ```text
  uv sync --locked
  uv run ruff format --check
  uv run ruff check
  uv run mypy
  uv run pytest
  ```

  Source: the uv, ruff, mypy and pytest docs. [bootstrap default]
- Lint selects ruff `E`, `W`, `F`, `I`, `N`, `UP`, `B`, `A`, `BLE`, `C4`, `SIM`, `PTH`, `PIE`, `RET` and `RUF`.
  mypy runs `strict` with `warn_unreachable` over `src` and `tests`. pytest uses native `[tool.pytest]` with
  `strict = true` and warnings as errors. `python:scaffold`'s `pyproject.toml` template is the exact
  configuration. Source: ruff, mypy and pytest docs. [bootstrap default]
- A new project starts from `python:scaffold`. [bootstrap default]

## House

- In a script repository (`python:structure`), mypy `files` and pytest `testpaths` name the authored script and
  test directories, and generated copies are excluded from the gate. The 3.12 floor applies to shipped scripts
  too: a `sys.version_info` guard checks `(3, 12)`, and documentation naming a minimum names 3.12.
  Tommy, 2026-10-18. [house]
- Repository-owned libraries (`python:structure`) declare build metadata and runtime dependencies in each
  package member's `pyproject.toml`; their workspace shares the root `uv.lock`. Other repositories declare
  ordinary package dependencies in their own projects and lockfiles, following `python:libraries` for source
  selection. A Git dependency on a nested package specifies its `subdirectory`. The deployed entry point must
  use an interpreter environment containing those dependencies; a development environment or dependency
  declaration alone does not supply imports to a host-invoked script. Verify the deployed entry point on
  Windows and Linux with the producer checkout unavailable.
  Why: dependency delivery must work independently of a developer's local repositories.
  Tommy, 2026-10-27. [house]

```text
Producer: packages/launch-paths/pyproject.toml defines the installable launch-paths distribution.
Consumer: declare launch-paths using python:libraries' source policy; for Git, select packages/launch-paths.
Install: update uv.lock, then use uv sync --locked; the launcher uses that environment's Python.
Verify: hide the producer checkout and invoke the installed entry point on Windows and Linux.
Result: from launch_paths.search_path import prepend resolves the delivered package.
```

Source: [uv dependency sources](https://docs.astral.sh/uv/concepts/projects/dependencies/#git).
