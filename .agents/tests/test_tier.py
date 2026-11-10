from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, cast

import pytest

ROOT = Path(__file__).parents[2]


def test_applies_only_where_python_is_present(tier: dict[str, Any]) -> None:
    assert tier["applies"] == "stack-present"
    assert tier["owner_repository"] == ["tj-agents/python"]


def test_detects_root_project_files(tier: dict[str, Any]) -> None:
    assert tier["detect"]["files"] == [
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
    ]


def test_detects_python_sources_without_a_package_manifest(
    tier: dict[str, Any],
) -> None:
    sources = (
        "run.py",
        "scripts/refresh.py",
        ".agents/agent/runtime/permissions.py",
        ".codex/runtime/listener.py",
        ".claude/runtime/permissions.py",
        "src/example/contract.pyi",
        "one/two/three/four/five/deep.py",
    )
    with tempfile.TemporaryDirectory() as directory:
        project = Path(directory)
        subprocess.run(["git", "init", "-q", directory], check=True, timeout=15)
        for name in (
            *sources,
            "README.md",
            "main.ts",
            "install.ps1",
            "vendor/ignored.py",
        ):
            path = project / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
        (project / ".gitignore").write_text("vendor/\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", directory, "add", "--", ".codex/runtime/listener.py"],
            check=True,
            timeout=15,
        )
        result = subprocess.run(
            [
                "git",
                "-C",
                directory,
                "ls-files",
                "-z",
                "--cached",
                "--others",
                "--exclude-standard",
                "--",
                *tier["detect"]["globs"],
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
            timeout=15,
        )
        assert set(sources) == set(result.stdout.rstrip("\x00").split("\x00"))


@pytest.fixture
def tier() -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads((ROOT / ".agents/tiers/python.json").read_text(encoding="utf-8")),
    )
