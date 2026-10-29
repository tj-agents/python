from __future__ import annotations

import json
from fnmatch import fnmatch
from pathlib import Path
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
        for path in (
            "run.py",
            "scripts/refresh.py",
            ".agents/agent/runtime/permissions.py",
            ".codex/runtime/listener.py",
            ".claude/runtime/permissions.py",
            "src/example/contract.pyi",
        ):
            with self.subTest(path=path):
                self.assertTrue(
                    any(fnmatch(Path(path).name, pattern) for pattern in self.tier["detect"]["globs"])
                )

    def test_does_not_detect_unrelated_sources(self) -> None:
        for path in ("README.md", "main.ts", "install.ps1", "install.sh"):
            with self.subTest(path=path):
                self.assertFalse(
                    any(fnmatch(Path(path).name, pattern) for pattern in self.tier["detect"]["globs"])
                )


if __name__ == "__main__":
    unittest.main()
