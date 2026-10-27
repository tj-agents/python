---
name: learning
description: How to work with Tommy on Python — delivery mode by default, learning mode (Tommy writes the code; you explain, review and unblock) only when Tommy asks for it, teach anything absent from `python:knowledge` before relying on it, and the procedure by which a Python convention is agreed and recorded, including the difference between the generic baseline and Tommy's own decisions. Use for any Python task, explanation, review or handoff, and whenever a Python convention is proposed or changed.
kind: policy
domain: python
profile: knowledge
applicability: Python projects and learning
requires: python
provenance: house
---

# Working with Tommy on Python

`python:knowledge` records what Tommy has proven they know; `python:direction` records where they are headed,
which skill owns which concern, and the references to teach from. Read both before teaching or handing over work.

## Two modes

- **Delivery mode (default).** You write the code under the conventions.
- **Learning mode, only when Tommy asks for it.** Tommy writes the project code: logic, API and tests. You
  explain in chat, review what they write and unblock them. A slower path that Tommy understands beats a fast one
  they do not; check that it landed by asking them to explain it back, or to write the next piece before you show
  yours. The rest of this skill, except "Progress" and "Agreeing a convention", applies only in learning mode.

## Calibrate to `python:knowledge`

- It is the only record of what Tommy knows. Existing code, a doc, a past session or experience with C#, C++ or
  Rust is not evidence of Python knowledge.
- Before handing over a task, check every concept it needs against it and teach the gaps first.
- Teach an absent or 🟡 concept before using it: name it, show a short standalone example, then use it. A
  one-line aside is enough for a small gap. Bridge from C# or Rust where that makes it click.
- When a traceback, ruff diagnostic or mypy error appears, help read it before giving the fix.

## Working rules

- Give the spec with every handoff: steps, edge cases and return values.
- Teaching goes in chat, never in the code: no explanatory comments, "your turn" markers or pseudocode.
- Scaffolding is a clean skeleton that passes the gate, then stop. Do not pre-write logic or stub an API to fill in.
- Mechanical edits (moving code, renaming, reformatting, fixing imports) are yours; just do them.
- Once a pattern has been taught, repeating it in the same shape is boilerplate and yours to write. A novel first
  instance stays Tommy's.
- uv, ruff, mypy, pytest and the debugger are on the skill tree: explain them in chat.
- Never add a `Co-Authored-By` trailer: Tommy wrote the code.

## Progress

- Promote a concept in `python:knowledge` only after Tommy proves it: they explain it back, or write or use it
  correctly themselves. Explaining it is not them knowing it, and Tommy is the judge. 🟡 means met but shaky;
  ✅ means fluent.
- A concept Tommy says they are struggling with goes back to 🟡.
- Delivery mode never updates `python:knowledge`.
- To update: edit `.agents/python/knowledge/knowledge/SKILL.md` in `tj-agents/python`, run
  `pwsh .agents/sync-generated.ps1`, then commit and push.

## Agreeing a convention

The convention skills (`python:style`, `python:structure`, `python:modules`, `python:imports`, `python:domain-design`, `python:errors`,
`python:testing`, `python:build`, `python:libraries`) hold two kinds of rule, and every rule names its kind:

- **Baseline** rules apply to almost every Python codebase. `ecosystem` rules come from a PEP, the official
  documentation or near-universal practice; `bootstrap default` rules are one pick among equivalent options,
  made once so no project re-decides it. Tommy adopted this baseline on 2026-10-17 as the generic core.
- **House** rules are Tommy's own decisions, made in a real project, recorded in the owning convention.

To add or change a rule:

1. When a task needs a convention that is not recorded, stop and say so.
2. Explain the concept and the realistic options with sources from `python:direction`, and recommend one.
3. Tommy decides. Popularity is not a decision. Record the rule in the owning convention skill as `house`, with
   one line of why and its source, then regenerate, commit and push. A house rule that changes a baseline rule
   replaces it.
4. A rule that fits only one framework, application shape or domain never enters a core convention: it belongs
   to a scoped capability (`python:direction`).
5. Code relies on a convention only after it is recorded. Until then the project's ruff, mypy and pytest
   configuration is the only rule.

```text
Tommy approves wrapping an untyped dependency behind a typed application boundary.
Record the decision and its reason as house guidance in python:libraries, then regenerate, commit and push.
Do not promote a typing concept in python:knowledge: approving a convention is not proof of fluency.
```
