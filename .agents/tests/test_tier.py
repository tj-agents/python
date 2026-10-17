from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class PythonTierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tier = json.loads((ROOT / ".agents/tiers/python.json").read_text(encoding="utf-8"))

    def test_applies_only_where_python_is_present(self) -> None:
        self.assertEqual("stack-present", self.tier["applies"])
        self.assertEqual(["tj-agents/python"], self.tier["owner_repository"])

    def test_detects_root_project_files_not_stray_scripts(self) -> None:
        self.assertEqual(
            ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"],
            self.tier["detect"]["files"],
        )
        self.assertNotIn("globs", self.tier["detect"])


if __name__ == "__main__":
    unittest.main()
