---
name: enums
description: Python enums — a closed set of choices is an Enum or StrEnum, handled exhaustively with match and assert_never, with each member carrying its own data through the enum's __init__, as the generic baseline plus Tommy's recorded decisions. Read before writing or reviewing Python that defines or handles a closed set of choices; choosing behaviour by a member is python:dispatch.
kind: standard
domain: python
profile: core
applicability: Python projects
requires: python
provenance: house
---

# Python enums

Owns how a closed set of choices is defined and handled. Each rule names its provenance (`python:learning`). Choosing
behaviour per member belongs to `python:dispatch`.

## Baseline

- A closed set of choices is an `enum.Enum` (`StrEnum` when the value must be a string), never loose string
  constants. Code that handles every member ends in `assert_never`, so mypy flags a missing case. Source: enum
  docs; typing docs, `assert_never`. [ecosystem]

## House

- Data that differs per member lives on the member, assigned in the enum's `__init__`, never in a parallel
  dict or an `if` on the member. [house]

Why: a member then carries everything that varies with it, so adding a member is one edit. Source: Tommy,
2026-10-26, from the Claude/Codex host split in `tj-agents/agent`;
[enum HOWTO, Planet example](https://docs.python.org/3/howto/enum.html#planet).

```python
from enum import Enum
from pathlib import Path
import os


class Host(Enum):
    CLAUDE = ("claude", "CLAUDE_CONFIG_DIR", ".claude")
    CODEX = ("codex", "CODEX_HOME", ".codex")

    def __init__(self, executable: str, home_variable: str, home_directory: str) -> None:
        self.executable = executable
        self.home_variable = home_variable
        self.home_directory = home_directory

    @property
    def home(self) -> Path:
        return Path(os.environ.get(self.home_variable) or Path.home() / self.home_directory)
```
