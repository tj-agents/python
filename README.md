# python

Python learning companion and standards.

Published as plugin `tj-agents/python` from the `tj-agents` marketplace.

## Skills

- Learning: `python:learning`.
- Reference: `python:direction`.
- Standards, the generic baseline plus Tommy's recorded decisions: `python:build`, `python:dispatch`,
  `python:domain-design`, `python:enums`, `python:errors`, `python:explanation`, `python:imports`,
  `python:libraries`, `python:modules`, `python:structure`, `python:style`, `python:testing`.
- Operation: `python:scaffold`.

Canonical skills live at `.agents/python/skills/<subject>/SKILL.md`, independently of kind.
The supporting [learner record](.agents/python/learning/knowledge.md) and
[learning direction](.agents/python/learning/direction.md) retain demonstrated knowledge, goals and progress;
`python:learning` owns their updates. They are ordinary resources rather than discovery entries.

The tier applies only where a root `pyproject.toml`, `setup.py`, `setup.cfg` or `requirements.txt` exists
(`.agents/tiers/python.json` `applies: stack-present`).

## Authoring and verification

```powershell
pwsh .agents/sync-generated.ps1
pwsh .agents/sync-generated.ps1 -Check
python -B -m unittest discover -s .agents/tests -p "test_*.py"
```

The layout, the vendored generator and CI come from [Template](https://github.com/tj-agents/template).
