---
name: dispatch
description: Python dispatch — choosing behaviour by a key through a dispatch table of Protocol-typed implementations with identical names, functools.singledispatch when the key is a type, and dispatching once at the entry point so nothing below it branches on the key again, as the generic baseline plus Tommy's recorded decisions. Read before writing or reviewing Python where behaviour differs per enum member, host, provider, mode or type, or when tempted to branch on such a key.
kind: convention
domain: python
profile: core
applicability: Python projects
requires: python
provenance: house
---

# Python dispatch

Owns how behaviour is chosen by a key. Each rule names its kind (`python:learning`). Defining the key itself
belongs to `python:enums`.

## Baseline

- Behaviour chosen by the type of a value uses `functools.singledispatch` (or `singledispatchmethod`), not an
  `isinstance` chain. Source: functools docs. [ecosystem]

## House

- Behaviour that differs per member of a closed key lives in one module (or function) per member with
  identical function names, typed by a `Protocol`. [house]
- A dispatch table, `Mapping[Key, Protocol]`, selects the implementation once at the entry point. Code below it
  receives the selected implementation and never compares the key again. Never wrap the implementations in a
  container object. [house]

Why: one decision point means a fix to one variant cannot silently skip another, and mypy checks every
implementation against the protocol. Source: Tommy, 2026-10-26, from the Claude/Codex host split in
`tj-agents/agent`; [PEP 544 protocols](https://peps.python.org/pep-0544/),
[functools.singledispatch](https://docs.python.org/3/library/functools.html#functools.singledispatch).

```python
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

import claude.plugins
import codex.plugins
from host import Host


class Plugins(Protocol):
    def refresh(self, project: Path) -> list[str]: ...


PLUGINS: Mapping[Host, Plugins] = {Host.CLAUDE: claude.plugins, Host.CODEX: codex.plugins}


def main(host: Host, project: Path) -> int:
    return len(PLUGINS[host].refresh(project))
```
