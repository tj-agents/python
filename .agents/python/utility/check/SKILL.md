---
name: check
description: Check a Python repository against its mechanical source, layout, Ruff and mypy standards. Use when validating Python changes or diagnosing a Python standards failure; architectural judgement stays with the owning convention.
kind: utility
domain: python
profile: verification
applicability: Python projects
requires: Python 3.12+, uv and the project's dev dependencies
provenance: house
---

# Check Python standards

Runs the project's Ruff formatter/linter, mypy and the shipped source/layout checker. Install the
project's locked dev dependencies first. Checks fail with the rule and an actionable fix.

```text
python -B <skill-directory>/scripts/run_checks.py --root .
python -B <skill-directory>/scripts/run_checks.py --root . src/example/parsing.py
```

Explicit paths restrict diagnostics to changed files; source checks still read the local import graph.
With no paths, check all authored files. The checker excludes generated copies, vendored generator
files, environments and nested Git repositories. Import-linter runs when the project declares contracts.

Claude and Codex PostToolUse hooks invoke the same runner with the edited paths. Shell edits use the
current Git diff and untracked files. A changed `pyproject.toml` requires the complete configuration check.
Codex must trust the installed hooks through its native hook approval; source generation does not grant trust.

The syntax checker detects explicit evidence, including imported aliases. It cannot prove arbitrary
runtime purity or infer application layers. Define layer contracts in `[tool.importlinter]`.

An existing violation may be baselined only with an exact relative file, rule and reason; unused entries
fail a full check. Remove the baseline as the violating code is repaired.

```toml
[[tool.python-standards.exceptions]]
path = "legacy/reader.py"
rule = "PY009"
reason = "The host currently loads this script for its registration side effect; migrate its caller."
```
