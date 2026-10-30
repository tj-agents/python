from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class PythonTierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tier = json.loads((ROOT / ".agents/tiers/python.json").read_text(encoding="utf-8"))

    def test_applies_only_where_python_is_present(self) -> None:
        self.assertEqual("stack-present", self.tier["applies"])
        self.assertEqual(["tj-agents/python"], self.tier["owner_repository"])

    def test_detects_root_project_files(self) -> None:
        self.assertEqual(
            ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"],
            self.tier["detect"]["files"],
        )

    def test_detects_python_sources_without_a_package_manifest(self) -> None:
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
            for name in (*sources, "README.md", "main.ts", "install.ps1", "vendor/ignored.py"):
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
                    "git", "-C", directory, "ls-files", "-z", "--cached", "--others",
                    "--exclude-standard", "--", *self.tier["detect"]["globs"],
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
                timeout=15,
            )
            self.assertEqual(set(sources), set(result.stdout.rstrip("\0").split("\0")))


if __name__ == "__main__":
    unittest.main()
