import io
import json
import runpy
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parents[2]


@pytest.fixture
def runner() -> SimpleNamespace:
    return SimpleNamespace(
        **runpy.run_path(
            str(ROOT / ".agents/python/utility/check/scripts/run_checks.py")
        )
    )


def test_edit_paths_resolves_patch_moves_and_claude_edits(
    runner: SimpleNamespace,
    tmp_path: Path,
) -> None:
    payload = {"tool_input": "*** Update File: src/old.py\n*** Move to: src/new.py\n"}
    assert runner.edit_paths(payload, tmp_path) == [
        tmp_path / "src/new.py",
        tmp_path / "src/old.py",
    ]
    assert runner.edit_paths({"tool_input": {"file_path": "src/new.py"}}, tmp_path) == [
        tmp_path / "src/new.py",
    ]


@pytest.mark.parametrize(
    "relative",
    (
        ".claude/skills/check/run.py",
        ".codex/skills/check/run.py",
        ".agents/dependencies/a.py",
        ".codex/hooks/snapshot.py",
        ".agents/sync_generated.py",
        "../outside.py",
    ),
)
def test_authored_excludes_generated_and_external_files(
    runner: SimpleNamespace,
    tmp_path: Path,
    relative: str,
) -> None:
    assert not runner.authored((tmp_path / relative).resolve(), tmp_path)


def test_authored_keeps_native_runtime_and_excludes_nested_git(
    runner: SimpleNamespace,
    tmp_path: Path,
) -> None:
    assert runner.authored(tmp_path / ".claude/runtime.py", tmp_path)
    assert runner.authored(tmp_path / ".codex/runtime.py", tmp_path)
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / ".git").write_text("gitdir: elsewhere", encoding="utf-8")
    assert not runner.authored(nested / "code.py", tmp_path)


def test_commands_limit_file_checks_and_keep_architecture_contracts(
    runner: SimpleNamespace,
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[[tool.importlinter.contracts]]\nname="layers"\ntype="layers"\n',
        encoding="utf-8",
    )
    source = tmp_path / "changed.py"
    source.touch()
    commands = runner.commands(tmp_path, [source])
    assert len(commands) == 5
    assert all(str(source) in command for command in commands[:4])
    assert commands[-1][-1] == "lint-imports"
    assert all("--no-sync" in command for command in commands[:3])


def test_deleted_and_non_python_edits_do_not_run_full_checks(
    runner: SimpleNamespace,
    tmp_path: Path,
) -> None:
    assert runner.verify(tmp_path, [tmp_path / "deleted.py"]) == []
    assert runner.verify(tmp_path, [tmp_path / "README.md"]) == []


def test_hook_reports_failed_commands_and_operational_errors(
    runner: SimpleNamespace,
    capsys: pytest.CaptureFixture[str],
) -> None:
    failed = runner.Result(("ruff", "check"), 1, "example.py: PY001 fix loop")
    assert runner.feedback([failed], True) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["decision"] == "block"
    assert "PY001 fix loop" in output["reason"]
    unavailable = runner.Result(("uv",), 2, "executable unavailable")
    assert runner.feedback([unavailable], False) == 2


def test_missing_tool_is_an_operational_failure(
    runner: SimpleNamespace,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable(*args: object, **kwargs: object) -> None:
        raise FileNotFoundError("uv missing")

    monkeypatch.setattr(subprocess, "run", unavailable)
    result = runner.execute(("uv", "run"), tmp_path)
    assert result.code == 2
    assert "uv missing" in result.output


def test_hook_uses_payload_root_and_cli_resolves_paths_under_explicit_root(
    runner: SimpleNamespace,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[Path, list[Path] | None]] = []

    def record(root: Path, paths: list[Path] | None) -> list[object]:
        calls.append((root, paths))
        return []

    monkeypatch.setitem(runner.main.__globals__, "verify", record)
    monkeypatch.setattr(
        runner.sys,
        "stdin",
        io.StringIO(
            json.dumps(
                {
                    "cwd": str(tmp_path),
                    "tool_input": {"file_path": "edited.py"},
                }
            )
        ),
    )
    assert runner.main(["--hook"]) == 0
    assert runner.main(["--root", str(tmp_path), "edited.py"]) == 0
    assert calls == [(tmp_path, [tmp_path / "edited.py"])] * 2


def test_canonical_plugin_sources_are_checked_and_generated_plugins_are_skipped(
    runner: SimpleNamespace,
    tmp_path: Path,
) -> None:
    source = tmp_path / "plugins/example/hooks/check.py"
    assert runner.authored(source, tmp_path)
    mapping = tmp_path / ".agents/plugins/payloads.json"
    mapping.parent.mkdir(parents=True)
    mapping.write_text("{}", encoding="utf-8")
    assert not runner.authored(source, tmp_path)
