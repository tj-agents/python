from __future__ import annotations

import runpy
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

ROOT = Path(__file__).parents[2]
CONVENTIONS = {
    "style",
    "structure",
    "modules",
    "imports",
    "domain-design",
    "enums",
    "dispatch",
    "errors",
    "testing",
    "build",
    "libraries",
    "explanation",
}


def test_python_is_the_only_plugin(plugins: dict[str, dict[str, Any]]) -> None:
    assert {"python"} == set(plugins)


def test_core_is_exactly_the_conventions(plugins: dict[str, dict[str, Any]]) -> None:
    core = {
        name
        for name, skill in plugins["python"].items()
        if skill["metadata"]["profile"] == "core"
    }
    assert core == CONVENTIONS
    for name in CONVENTIONS:
        assert plugins["python"][name]["kind"] == "convention"


def test_every_convention_separates_baseline_from_house(
    plugins: dict[str, dict[str, Any]],
) -> None:
    for name in CONVENTIONS:
        body = plugins["python"][name]["body"]
        assert "## Baseline" in body, name
        assert "## House" in body, name


def test_structure_declares_its_file_structure_section(
    plugins: dict[str, dict[str, Any]],
) -> None:
    assert "## File structure" in plugins["python"]["structure"]["body"]


def test_scaffold_is_its_own_profile(plugins: dict[str, dict[str, Any]]) -> None:
    assert plugins["python"]["scaffold"]["metadata"]["profile"] == "scaffold"
    assert plugins["python"]["scaffold"]["kind"] == "utility"


def test_knowledge_tier_keeps_its_own_profile(
    plugins: dict[str, dict[str, Any]],
) -> None:
    for name in ("learning", "knowledge", "direction"):
        assert plugins["python"][name]["metadata"]["profile"] == "knowledge"
    assert plugins["python"]["learning"]["kind"] == "policy"


@pytest.fixture
def plugins() -> dict[str, dict[str, Any]]:
    generator = SimpleNamespace(
        **runpy.run_path(str(ROOT / ".agents/sync_generated.py"))
    )
    config = generator.load_config(ROOT)
    payloads = generator.load(ROOT / ".agents/plugins/payloads.json")
    return cast(
        dict[str, dict[str, Any]],
        generator.discover(
            ROOT, config["namespace"], generator.mapped_resource_directories(payloads)
        ),
    )
