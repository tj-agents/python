from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("sync_generated", ROOT / ".agents" / "sync_generated.py")
sync_generated = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync_generated)

CONVENTIONS = {
    "style",
    "structure",
    "domain-design",
    "errors",
    "testing",
    "build",
    "libraries",
    "explanation",
}


class PythonCoreProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = sync_generated.load_config(ROOT)
        payloads = sync_generated.load(ROOT / ".agents/plugins/payloads.json")
        cls.plugins = sync_generated.discover(
            ROOT, cls.config["namespace"], sync_generated.mapped_resource_directories(payloads)
        )
        cls.skills = cls.plugins["python"]

    def test_python_is_the_only_plugin(self) -> None:
        self.assertEqual({"python"}, set(self.plugins))

    def test_core_is_exactly_the_conventions(self) -> None:
        core = {name for name, skill in self.skills.items() if skill["metadata"]["profile"] == "core"}
        self.assertEqual(CONVENTIONS, core)
        for name in CONVENTIONS:
            self.assertEqual("convention", self.skills[name]["kind"])

    def test_every_convention_separates_baseline_from_house(self) -> None:
        for name in CONVENTIONS:
            body = self.skills[name]["body"]
            self.assertIn("## Baseline", body, name)
            self.assertIn("## House", body, name)

    def test_structure_declares_its_file_structure_section(self) -> None:
        self.assertIn("## File structure", self.skills["structure"]["body"])

    def test_scaffold_is_its_own_profile(self) -> None:
        self.assertEqual("scaffold", self.skills["scaffold"]["metadata"]["profile"])
        self.assertEqual("utility", self.skills["scaffold"]["kind"])

    def test_knowledge_tier_keeps_its_own_profile(self) -> None:
        for name in ("learning", "knowledge", "direction"):
            self.assertEqual("knowledge", self.skills[name]["metadata"]["profile"])
        self.assertEqual("policy", self.skills["learning"]["kind"])


if __name__ == "__main__":
    unittest.main()
