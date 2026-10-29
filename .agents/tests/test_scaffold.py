from __future__ import annotations

import contextlib
import importlib.util
import io
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".agents/python/skills/scaffold/scripts/new_python_project.py"
SPEC = importlib.util.spec_from_file_location("new_python_project", SCRIPT)
scaffold = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scaffold)

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
    ["uv", "run", "pytest"],
)


def generate(destination: Path, *args: str) -> int:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return scaffold.main(["--destination", str(destination), "--python", "3.13", *args])


def files(project: Path) -> set[str]:
    return {path.relative_to(project).as_posix() for path in project.rglob("*") if path.is_file()}


class ScaffoldTests(unittest.TestCase):
    def test_project_is_the_universal_foundation_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            self.assertEqual(0, generate(Path(temporary), "--name", "demo-tool"))
            project = Path(temporary) / "demo-tool"
            self.assertEqual(FILES, files(project))
            self.assertEqual("", (project / "src/demo_tool/__init__.py").read_text(encoding="utf-8"))
            self.assertEqual("3.13\n", (project / ".python-version").read_text(encoding="utf-8"))
            self.assertEqual("@AGENTS.md\n", (project / "CLAUDE.md").read_text(encoding="utf-8"))
            self.assertNotIn("\n\n\n", (project / "AGENTS.md").read_text(encoding="utf-8"))
            metadata = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))
            self.assertEqual("demo-tool", metadata["project"]["name"])
            self.assertEqual(">=3.13", metadata["project"]["requires-python"])
            self.assertEqual([], metadata["project"]["dependencies"])
            self.assertNotIn("description", metadata["project"])
            self.assertNotIn("scripts", metadata["project"])
            self.assertEqual("uv_build", metadata["build-system"]["build-backend"])
            self.assertEqual(
                {"mypy", "pytest", "ruff"},
                {re.split(r"[<>=]", item)[0] for item in metadata["dependency-groups"]["dev"]},
            )
            self.assertTrue(metadata["tool"]["mypy"]["strict"])
            self.assertTrue(metadata["tool"]["pytest"]["strict"])

    def test_description_is_the_only_variation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            self.assertEqual(0, generate(Path(temporary), "--name", "demo_tool", "--description", "Checks demo values"))
            project = Path(temporary) / "demo_tool"
            self.assertEqual(FILES, files(project))
            metadata = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))
            self.assertEqual("Checks demo values", metadata["project"]["description"])
            self.assertIn("Checks demo values", (project / "AGENTS.md").read_text(encoding="utf-8"))

    def test_every_placeholder_is_resolved_and_files_are_lf(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            generate(Path(temporary), "--name", "demo-tool")
            generate(Path(temporary), "--name", "described", "--description", "Checks demo values")
            for path in Path(temporary).rglob("*"):
                if path.is_file():
                    data = path.read_bytes()
                    self.assertNotIn(b"\r\n", data, path)
                    self.assertIsNone(re.search(rb"__[A-Z_]+__", data), path)

    def test_rejections_write_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "taken").mkdir()
            self.assertEqual(1, generate(root, "--name", "taken"))
            self.assertEqual(1, generate(root, "--name", "class"))
            self.assertEqual(1, generate(root, "--name", "json"))
            self.assertEqual(1, generate(root, "--name", "tests"))
            self.assertEqual(1, generate(root, "--name", "Bad_Name"))
            self.assertEqual(1, generate(root, "--name", "quoted", "--description", 'say "hi"'))
            self.assertEqual(1, generate(root / "missing", "--name", "demo"))
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(1, scaffold.main(["--name", "old", "--destination", str(root), "--python", "3.11"]))
                self.assertEqual(1, scaffold.main(["--name", "loose", "--destination", str(root), "--python", "3"]))
            self.assertEqual(0, generate(root, "--name", "preview", "--dry-run"))
            self.assertEqual({"taken"}, {path.name for path in root.iterdir()})

    @unittest.skipIf(shutil.which("uv") is None, "uv is not installed")
    def test_generated_project_passes_the_python_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with contextlib.redirect_stdout(io.StringIO()):
                scaffold.create(root, "demo-tool", "3.13", "Checks demo values", False)
            project = root / "demo-tool"
            for command in (["uv", "sync", "--quiet"], *GATE, ["uv", "sync", "--locked", "--quiet"]):
                result = subprocess.run(command, cwd=project, capture_output=True, text=True)
                self.assertEqual(0, result.returncode, f"{' '.join(command)}\n{result.stdout}\n{result.stderr}")


if __name__ == "__main__":
    unittest.main()
