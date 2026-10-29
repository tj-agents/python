# python

Python learning companion and standards.

Published as plugin `tj-agents/python` from the `tj-agents` marketplace.

## Skills

- Knowledge: `python:direction`, `python:knowledge`.
- Policies: `python:learning`.
- Conventions, the generic baseline plus Tommy's recorded decisions: `python:build`, `python:domain-design`, `python:errors`, `python:imports`, `python:libraries`, `python:modules`, `python:structure`, `python:style`, `python:testing`.
- Utilities: `python:scaffold`.

The tier applies where a root `pyproject.toml`, `setup.py`, `setup.cfg` or `requirements.txt` exists, or
Python source or stub files occur at any depth (`tiers/python.json` `applies: stack-present`). This includes
script repositories and host runtime code beneath directories such as `.agents/`, `.codex/` and `.claude/`.

## Authoring and verification

```powershell
pwsh .agents/sync-generated.ps1
pwsh .agents/sync-generated.ps1 -Check
python -B -m unittest discover -s .agents/tests -p "test_*.py"
```

The layout, the vendored generator and CI come from [Template](https://github.com/tj-agents/template).
