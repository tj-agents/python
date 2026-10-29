---
name: learning
description: "Teach, assess and track Tommy's Python understanding, with delivery mode by default and learning mode only when requested. Use for Python tasks, lessons, reviews, handoffs and agreement of standards; learner data records demonstrated knowledge and goals."
kind: learning
domain: python
profile: knowledge
applicability: Python projects and learning
requires: python
provenance: house
---

# Working with Tommy on Python

Read the [learner record](../../learning/knowledge.md) for proven knowledge and the
[learning direction](../../learning/direction.md) for goals and skill-tree progress. `python:direction`
provides concern ownership and teaching sources. Read them before teaching or handing over work.

## Two modes

- **Delivery mode (default).** You write the code under the standards.
- **Learning mode, only when Tommy asks for it.** Tommy writes the project code: logic, API and tests. You
  explain in chat, review what they write and unblock them. A slower path that Tommy understands beats a fast one
  they do not; check that it landed by asking them to explain it back, or to write the next piece before you show
  yours. The rest of this skill, except "Progress", "Growing beyond the core" and "Agreeing a standard",
  applies only in learning mode.

## Calibrate to the learner record

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

- Promote a concept in the learner record only after Tommy proves it: they explain it back, or write or use it
  correctly themselves. Explaining it is not them knowing it, and Tommy is the judge. 🟡 means met but shaky;
  ✅ means fluent.
- A concept Tommy says they are struggling with goes back to 🟡.
- Delivery mode never updates the learner record.
- To update: edit `.agents/python/learning/knowledge.md` in `tj-agents/python`, run
  `pwsh .agents/sync-generated.ps1`, then commit and push.
- Update a row's status in the learning direction when Tommy levels up an area.

## Growing beyond the core

The core Python plugin is intentionally generic: core standards remain bounded, and specialised ecosystems grow
through separate scoped capabilities rather than endless branching inside core skills.

- A core standard holds only rules Tommy would want in almost every Python codebase. Application architecture,
  framework layout and domain shape are never core.
- `python:scaffold` creates one universal foundation. It never gains a preset, project-type flag or framework
  option.
- A specialised ecosystem (a web framework, browser automation, data or ML tooling) earns a capability only when
  real projects use it, never in advance. It is its own plugin that requires `python`, as C++ separates `gpp`,
  `msvc` and `win32` from `cpp`: its own tier detecting that ecosystem, standards for only what differs from
  core, and a scaffold that layers onto a `python:scaffold` project instead of replacing it.
- Core never names, branches on or defers to a scoped capability.

## Agreeing a standard

The standard skills (`python:style`, `python:structure`, `python:modules`, `python:imports`,
`python:domain-design`, `python:enums`, `python:dispatch`, `python:errors`, `python:testing`, `python:build`,
`python:libraries`, `python:explanation`) hold baseline and house rules, and every rule names its provenance:

- **Baseline** rules apply to almost every Python codebase. `ecosystem` rules come from a PEP, the official
  documentation or near-universal practice; `bootstrap default` rules are one pick among equivalent options,
  made once so no project re-decides it. Tommy adopted this baseline on 2026-10-17 as the generic core.
- **House** rules are Tommy's own decisions, made in a real project, recorded in the owning standard.

To add or change a rule:

1. When a task needs a standard that is not recorded, stop and say so.
2. Explain the concept and the realistic options with sources from `python:direction`, and recommend one.
3. Tommy decides. Popularity is not a decision. Record the rule in the owning standard skill as `house`, with
   one line of why and its source, then regenerate, commit and push. A house rule that changes a baseline rule
   replaces it.
4. A rule that fits only one framework, application shape or domain never enters a core standard: it belongs
   to a scoped capability under the growth rules above.
5. Code relies on a standard only after it is recorded. Until then the project's ruff, mypy and pytest
   configuration is the only rule.

```text
Tommy approves wrapping an untyped dependency behind a typed application boundary.
Record the decision and its reason as house guidance in python:libraries, then regenerate, commit and push.
Do not promote a typing concept in the learner record: approving a standard is not proof of fluency.
```
