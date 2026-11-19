import argparse
import json
import re
import subprocess
import sys
import tomllib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Result:
    command: tuple[str, ...]
    code: int
    output: str


def execute(command: Sequence[str], root: Path) -> Result:
    try:
        process = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return Result(tuple(command), 2, f"Cannot run {' '.join(command)}: {error}")
    return Result(tuple(command), process.returncode, process.stdout + process.stderr)


def authored(path: Path, root: Path) -> bool:
    if not path.is_relative_to(root):
        return False
    relative = path.relative_to(root)
    if set(relative.parts) & {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".worktrees",
        ".template",
    }:
        return False
    if (
        "plugins" in relative.parts
        and (root / ".agents/plugins/payloads.json").is_file()
    ):
        return False
    if relative in {
        Path(".agents/sync_generated.py"),
        Path(".codex/hooks/snapshot.py"),
        Path(".codex/hooks/bootstrap.py"),
    } or any(
        relative.is_relative_to(Path(directory))
        for directory in (
            ".agents/dependencies",
            ".claude/skills",
            ".codex/skills",
        )
    ):
        return False
    return all(
        not (parent / ".git").exists()
        for parent in path.parents
        if parent != root and parent.is_relative_to(root)
    )


def changed(root: Path) -> list[Path]:
    paths: set[Path] = set()
    for arguments in (
        ("diff", "--name-only", "-z", "--"),
        ("diff", "--cached", "--name-only", "-z", "--"),
        ("ls-files", "--others", "--exclude-standard", "-z"),
    ):
        result = execute(("git", *arguments), root)
        if result.code:
            raise ValueError(result.output.strip())
        paths.update(
            (root / item).resolve() for item in result.output.split("\0") if item
        )
    return sorted(path for path in paths if authored(path, root))


def edit_paths(payload: dict[str, object], root: Path) -> list[Path]:
    value = payload.get("tool_input", {})
    names: list[str] = []
    patch = value if isinstance(value, str) else ""
    if isinstance(value, dict):
        filename = value.get("file_path")
        if isinstance(filename, str):
            names.append(filename)
        patch_value = value.get("patch", value.get("input", ""))
        if isinstance(patch_value, str):
            patch = patch_value
    names.extend(
        re.findall(
            r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$",
            patch,
            re.MULTILINE,
        )
    )
    if not names:
        return changed(root)
    paths = {(root / name).resolve() for name in names}
    return sorted(path for path in paths if authored(path, root))


def commands(root: Path, paths: Sequence[Path] | None) -> list[tuple[str, ...]]:
    config_path = root / "pyproject.toml"
    if not config_path.is_file():
        raise ValueError(
            "Python standards require pyproject.toml; "
            "regenerate the Python project configuration."
        )
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    selected = (
        []
        if paths is None
        else [
            str(path)
            for path in paths
            if path.suffix in {".py", ".pyi"} and path.is_file()
        ]
    )
    checker = Path(__file__).with_name("check_python.py")
    tool = config.get("tool", {})
    standards = tool.get("python-standards", {})
    groups = standards.get("mypy-groups")
    type_targets = [selected]
    if groups is not None:
        if not isinstance(groups, list) or not groups:
            raise ValueError(
                "python-standards.mypy-groups must be nonempty lists of paths."
            )
        type_targets = []
        matched: set[str] = set()
        for group in groups:
            if (
                not isinstance(group, list)
                or not group
                or any(not isinstance(path, str) or not path for path in group)
            ):
                raise ValueError(
                    "python-standards.mypy-groups must be nonempty lists of paths."
                )
            targets = list(group) if paths is None else []
            if paths is not None:
                bases = [(root / base).resolve() for base in group]
                for path in selected:
                    if any(Path(path).is_relative_to(base) for base in bases):
                        targets.append(path)
            if targets:
                type_targets.append(targets)
                matched.update(targets)
        if paths is not None and (remaining := sorted(set(selected) - matched)):
            type_targets.append(remaining)
    output = [
        ("uv", "run", "--offline", "--no-sync", "ruff", "format", "--check", *selected),
        (
            "uv",
            "run",
            "--offline",
            "--no-sync",
            "ruff",
            "check",
            "--force-exclude",
            *selected,
        ),
        *[
            ("uv", "run", "--offline", "--no-sync", "mypy", *targets)
            for targets in type_targets
        ],
        (sys.executable, "-B", str(checker), "--root", str(root), *selected),
    ]
    imports = tool.get("importlinter", {}) if isinstance(tool, dict) else {}
    if isinstance(imports, dict) and imports.get("contracts"):
        output.append(("uv", "run", "--offline", "--no-sync", "lint-imports"))
    return output


def verify(root: Path, paths: Sequence[Path] | None) -> list[Result]:
    if paths is not None:
        if any(
            path.name == "pyproject.toml"
            or (path.suffix in {".py", ".pyi"} and not path.is_file())
            for path in paths
        ):
            paths = None
        elif not any(
            path.suffix in {".py", ".pyi"} and path.is_file() for path in paths
        ):
            return []
    return [execute(command, root) for command in commands(root, paths)]


def feedback(results: Sequence[Result], hook: bool) -> int:
    failed = [result for result in results if result.code]
    text = "\n".join(
        f"{' '.join(result.command)}\n{result.output.strip()}" for result in failed
    )
    if hook:
        if failed:
            print(
                json.dumps(
                    {
                        "decision": "block",
                        "reason": (
                            f"Python standards failed. Fix these diagnostics:\n{text}"
                        ),
                    }
                )
            )
        elif results:
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "PostToolUse",
                            "additionalContext": (
                                "Python standards passed for the edited files."
                            ),
                        }
                    }
                )
            )
        return 0
    for result in results:
        if result.output.strip():
            print(result.output.strip())
    return 2 if any(result.code == 2 for result in failed) else int(bool(failed))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run mechanical Python standards checks."
    )
    parser.add_argument("--root", type=Path)
    parser.add_argument("--hook", action="store_true")
    parser.add_argument("--mypy-only", action="store_true")
    parser.add_argument("paths", type=Path, nargs="*")
    arguments = parser.parse_args(argv)
    try:
        payload: dict[str, object] = {}
        if arguments.hook:
            decoded: object = json.load(sys.stdin)
            if not isinstance(decoded, dict):
                raise ValueError("Hook input must be a JSON object.")
            payload = decoded
        cwd = payload.get("cwd")
        root = (
            arguments.root or (Path(cwd) if isinstance(cwd, str) else Path.cwd())
        ).resolve()
        paths = (
            edit_paths(payload, root)
            if arguments.hook
            else [(root / path).resolve() for path in arguments.paths] or None
        )
        if arguments.mypy_only:
            results = [
                execute(command, root)
                for command in commands(root, paths)
                if len(command) > 4 and command[4] == "mypy"
            ]
            return feedback(results, False)
        return feedback(verify(root, paths), arguments.hook)
    except (OSError, ValueError) as error:
        result = Result(("python-standards",), 2, str(error))
        return feedback([result], arguments.hook)


if __name__ == "__main__":
    raise SystemExit(main())
