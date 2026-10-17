#!/usr/bin/env python3
from __future__ import annotations

import argparse
import keyword
from pathlib import Path
import re
import sys

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
NAME = re.compile(r"^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*$")
PYTHON = re.compile(r"^3\.(\d+)$")
OLDEST_MINOR = 12
PLACEHOLDER = re.compile(r"__[A-Z_]+__")
RESERVED = {"src", "tests", "test", "conftest"}
FILES = (
    ("pyproject.toml.in", "pyproject.toml"),
    ("python-version.in", ".python-version"),
    ("gitignore.in", ".gitignore"),
    ("gitattributes.in", ".gitattributes"),
    ("ci.yml.in", ".github/workflows/ci.yml"),
    ("AGENTS.md.in", "AGENTS.md"),
    ("CLAUDE.md.in", "CLAUDE.md"),
    ("init.py.in", "src/__PACKAGE__/__init__.py"),
    ("py.typed.in", "src/__PACKAGE__/py.typed"),
    ("test_import.py.in", "tests/test_import.py"),
)


class ScaffoldError(Exception):
    pass


def substitute(text: str, values: dict[str, str]) -> str:
    for token in PLACEHOLDER.findall(text):
        if token not in values:
            raise ScaffoldError(f"template uses unknown placeholder {token}")
        text = text.replace(token, values[token])
    return text


def render(template: str, values: dict[str, str | None]) -> str:
    if not template:
        return ""
    present = {token: value for token, value in values.items() if value is not None}
    lines: list[str] = []
    dropped = False
    for line in template.splitlines():
        if any(token in values and values[token] is None for token in PLACEHOLDER.findall(line)):
            dropped = True
            continue
        if dropped and not line and lines and not lines[-1]:
            continue
        dropped = False
        lines.append(substitute(line, present))
    return "\n".join(lines) + "\n"


def plan(name: str, python: str, description: str | None) -> dict[str, str]:
    package = name.replace("-", "_")
    if (
        not NAME.fullmatch(name)
        or name in RESERVED
        or package in RESERVED
        or keyword.iskeyword(package)
        or package in sys.stdlib_module_names
    ):
        raise ScaffoldError(f"invalid project name: {name}")
    version = PYTHON.fullmatch(python)
    if version is None or int(version.group(1)) < OLDEST_MINOR:
        raise ScaffoldError(f"python must be a minor version 3.{OLDEST_MINOR} or newer, such as 3.13, not {python}")
    if description is not None and (not description.strip() or any(char in description for char in '"\\\n')):
        raise ScaffoldError("description must be one non-empty line without quotes or backslashes")
    values = {
        "__NAME__": name,
        "__PACKAGE__": package,
        "__PYTHON__": python,
        "__DESCRIPTION__": description,
    }
    return {
        substitute(destination, {"__PACKAGE__": package}): render(
            (TEMPLATES / source).read_text(encoding="utf-8"), values
        )
        for source, destination in FILES
    }


def create(destination: Path, name: str, python: str, description: str | None, dry_run: bool) -> Path:
    if not destination.is_dir():
        raise ScaffoldError(f"destination does not exist: {destination}")
    project = destination / name
    if project.exists():
        raise ScaffoldError(f"project already exists: {project}")
    files = plan(name, python, description)
    if dry_run:
        for relative in files:
            print(project / relative)
        return project
    for relative, text in files.items():
        path = project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
    print(f"created {project}")
    return project


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a Python project in the python:structure layout.")
    parser.add_argument("--name", required=True, help="distribution name, lowercase with - or _ separators")
    parser.add_argument("--destination", required=True, type=Path, help="existing parent directory")
    parser.add_argument("--python", help="minor version such as 3.13; defaults to the running interpreter's")
    parser.add_argument("--description", help="one-line description for pyproject.toml and AGENTS.md")
    parser.add_argument("--dry-run", action="store_true", help="list the files without writing them")
    args = parser.parse_args(argv)
    python = args.python or f"{sys.version_info.major}.{sys.version_info.minor}"
    try:
        create(args.destination, args.name, python, args.description, args.dry_run)
    except ScaffoldError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
