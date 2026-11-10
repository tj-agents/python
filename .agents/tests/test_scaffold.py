from __future__ import annotations

import contextlib
import io
import re
import runpy
import shutil
import subprocess
import tempfile
import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / ".agents/python/utility/scaffold/scripts/new_python_project.py"
FILES = {
    "pyproject.toml",
    ".python-version",
    ".gitignore",
    ".gitattributes",
    ".github/workflows/ci.yml",
    "AGENTS.md",
    "CLAUDE.md",
    "src/demo_tool/__init__.py",
    "src/demo_tool/py.typed",
    "tests/test_import.py",
}
GATE = (
    ["uv", "run", "ruff", "format", "--check"],
    ["uv", "run", "ruff", "check"],
    ["uv", "run", "mypy"],
    ["uv", "run", "pytest", "tests/test_import.py"],
)


def generate(destination: Path, *args: str) -> int:
    scaffold = SimpleNamespace(**runpy.run_path(str(SCRIPT)))
    with (
        contextlib.redirect_stdout(io.StringIO()),
        contextlib.redirect_stderr(io.StringIO()),
    ):
        return int(
            scaffold.main(
                ["--destination", str(destination), "--python", "3.13", *args]
            )
        )


def files(project: Path) -> set[str]:
    return {
        path.relative_to(project).as_posix()
        for path in project.rglob("*")
        if path.is_file()
    }


def test_project_is_the_universal_foundation_only() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        assert generate(Path(temporary), "--name", "demo-tool") == 0
        project = Path(temporary) / "demo-tool"
        assert files(project) == FILES
        assert (project / "src/demo_tool/__init__.py").read_text(encoding="utf-8") == ""
        assert (project / ".python-version").read_text(encoding="utf-8") == "3.13\n"
        assert (project / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n"
        assert "\n\n\n" not in (project / "AGENTS.md").read_text(encoding="utf-8")
        metadata = tomllib.loads(
            (project / "pyproject.toml").read_text(encoding="utf-8")
        )
        assert metadata["project"]["name"] == "demo-tool"
        assert metadata["project"]["requires-python"] == ">=3.13"
        assert metadata["project"]["dependencies"] == []
        assert "description" not in metadata["project"]
        assert "scripts" not in metadata["project"]
        assert metadata["build-system"]["build-backend"] == "uv_build"
        assert {"mypy", "pytest", "pytest-socket", "ruff"} == {
            re.split("[<>=]", item)[0] for item in metadata["dependency-groups"]["dev"]
        }
        assert metadata["tool"]["mypy"]["strict"]
        assert metadata["tool"]["pytest"]["strict"]


def test_description_is_the_only_variation() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        assert (
            generate(
                Path(temporary),
                "--name",
                "demo_tool",
                "--description",
                "Checks demo values",
            )
            == 0
        )
        project = Path(temporary) / "demo_tool"
        assert files(project) == FILES
        metadata = tomllib.loads(
            (project / "pyproject.toml").read_text(encoding="utf-8")
        )
        assert metadata["project"]["description"] == "Checks demo values"
        assert "Checks demo values" in (project / "AGENTS.md").read_text(
            encoding="utf-8"
        )


def test_every_placeholder_is_resolved_and_files_are_lf() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        generate(Path(temporary), "--name", "demo-tool")
        generate(
            Path(temporary),
            "--name",
            "described",
            "--description",
            "Checks demo values",
        )
        for path in Path(temporary).rglob("*"):
            if path.is_file():
                data = path.read_bytes()
                assert b"\r\n" not in data, path
                assert re.search(b"__[A-Z_]+__", data) is None, path


def test_rejections_write_nothing(scaffold: SimpleNamespace) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        (root / "taken").mkdir()
        assert generate(root, "--name", "taken") == 1
        assert generate(root, "--name", "class") == 1
        assert generate(root, "--name", "json") == 1
        assert generate(root, "--name", "tests") == 1
        assert generate(root, "--name", "Bad_Name") == 1
        assert generate(root, "--name", "quoted", "--description", 'say "hi"') == 1
        assert generate(root / "missing", "--name", "demo") == 1
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            assert (
                scaffold.main(
                    ["--name", "old", "--destination", str(root), "--python", "3.11"]
                )
                == 1
            )
            assert (
                scaffold.main(
                    ["--name", "loose", "--destination", str(root), "--python", "3"]
                )
                == 1
            )
        assert generate(root, "--name", "preview", "--dry-run") == 0
        assert {"taken"} == {path.name for path in root.iterdir()}


@pytest.mark.skipif(shutil.which("uv") is None, reason="uv is not installed")
def test_generated_project_passes_the_python_gate(scaffold: SimpleNamespace) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with contextlib.redirect_stdout(io.StringIO()):
            scaffold.create(root, "demo-tool", "3.13", "Checks demo values", False)
        project = root / "demo-tool"
        for command in (
            ["uv", "sync", "--quiet"],
            *GATE,
            ["uv", "sync", "--locked", "--quiet"],
        ):
            result = subprocess.run(
                command, cwd=project, capture_output=True, text=True
            )
            assert result.returncode == 0, (
                f"{' '.join(command)}\n{result.stdout}\n{result.stderr}"
            )


@pytest.fixture
def scaffold() -> SimpleNamespace:
    return SimpleNamespace(**runpy.run_path(str(SCRIPT)))
