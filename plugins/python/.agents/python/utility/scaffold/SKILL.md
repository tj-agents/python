---
name: scaffold
description: Create a new Python project with the universal foundation `python:structure` and `python:build` record — a src-layout package with `pyproject.toml`, uv, ruff, mypy, pytest, CI and agent files — and nothing else. It has one shape, no presets and no framework options. Use when starting any Python project; never run it over an existing tree.
kind: utility
domain: python
profile: scaffold
applicability: new Python projects
requires: python
provenance: house
---

# Python project scaffold

Creates the File structure `python:structure` records with the toolchain `python:build` records, then stops: no
application code, no sample logic, no framework and no empty architectural layers (`python:learning`).

It has exactly one shape. It never gains a preset, project-type flag or framework option; a specialised ecosystem
gets its own scoped capability that layers onto this result (`python:direction`).

## Create a project

```text
python -B <skill-directory>/scripts/new_python_project.py --name my-tool --destination ~/source/repos
```

- The result is `<destination>/<name>`, importing as the name with `-` replaced by `_`. The destination must
  exist and the project must not. `--dry-run` lists the files without writing. There is no overwrite mode and no
  `git init`.
- `--python 3.X` sets `requires-python` and `.python-version`, otherwise the running interpreter's minor; 3.12 is
  the oldest accepted.
- `--description "…"` adds a one-line description to `pyproject.toml` and `AGENTS.md`.
- A name that is a keyword or shadows a standard-library module is refused.

Requires Python 3.12+ to run, and uv to build the result.

The tier gate blocks `python:*` where no root Python project file exists, including an empty destination; set
`AGENTS_TIER_OVERRIDE=python` for that session.

## Build and adapt

The project gets `pyproject.toml` with the agreed metadata, dev group and ruff, mypy and pytest configuration,
`.python-version`, `src/<package>/__init__.py` and `py.typed`, `tests/test_import.py`, `.gitignore`,
`.gitattributes`, a Windows and Ubuntu CI workflow, and an `AGENTS.md`/`CLAUDE.md` pair. `tests/test_import.py`
is the one test, so pytest has something to collect until real tests replace it.

Templates live in `templates/` beside this file and ship with the skill. Change them there, then regenerate; when
a tool's lower bound in `pyproject.toml.in` moves, update `python:build` with it.

## Validation and publication

Inside the new project, create the environment and lockfile, then run the gate:

```text
uv sync
uv run ruff format --check
uv run ruff check
uv run mypy
uv run pytest
```

Commit `uv.lock` with the first commit; CI runs `uv sync --locked`.
