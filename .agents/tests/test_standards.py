from __future__ import annotations

import runpy
from collections.abc import Sequence
from pathlib import Path
from types import SimpleNamespace
from typing import Protocol, cast

import pytest

ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / ".agents/python/utility/check/scripts/check_python.py"


class Result(Protocol):
    line: int
    path: Path
    rule: str


class Checker(Protocol):
    CheckerError: type[Exception]

    def check(
        self, root: Path, paths: Sequence[Path] | None = None
    ) -> list[Result]: ...

    def main(self, arguments: Sequence[str] | None = None) -> int: ...


@pytest.fixture
def checker() -> Checker:
    return cast(Checker, SimpleNamespace(**runpy.run_path(str(SCRIPT))))


def write(project: Path, files: dict[str, str]) -> None:
    for name, content in files.items():
        path = project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def project(tmp_path: Path, files: dict[str, str]) -> Path:
    write(tmp_path, files)
    return tmp_path


def rules(checker: Checker, root: Path, paths: list[Path] | None = None) -> set[str]:
    return {item.rule for item in checker.check(root, paths)}


def package_pyproject(name: str = "demo-tool") -> str:
    return f'[project]\nname = "{name}"\n'


def test_reports_structure_module_and_syntax_rules(
    tmp_path: Path, checker: Checker
) -> None:
    root = project(
        tmp_path,
        {
            "pyproject.toml": package_pyproject(),
            "src/demo_tool/__init__.py": "value = 1\n",
            "src/demo_tool/utils.py": "x = [item for row in [] for item in row]\n",
            "src/demo_tool/lifetime.py": (
                "class Resource:\n    def __del__(self):\n        pass\n"
            ),
            "src/demo_tool/static.py": (
                "class Names:\n    @staticmethod\n    def one():\n        return 1\n"
            ),
        },
    )
    found = rules(checker, root)
    assert {"PY001", "PY003", "PY007", "PY008", "PY012", "PY015"} <= found


def test_import_time_io_and_process_state_are_scoped(
    tmp_path: Path, checker: Checker
) -> None:
    root = project(
        tmp_path,
        {
            "pyproject.toml": package_pyproject(),
            "src/demo_tool/__init__.py": "",
            "src/demo_tool/run.py": (
                "import os\nfrom pathlib import Path as P\nvalue = P('x').read_text()\n"
                "name = os.environ['NAME']\ndef later():\n"
                "    return os.getenv('NAME')\n"
                "def main():\n    return os.getenv('NAME')\n"
                "if __name__ == '__main__':\n    main()\n"
            ),
        },
    )
    found = rules(checker, root)
    assert "PY009" in found
    assert "PY016" in found


def test_cycles_enum_aliases_exception_roots_and_test_clock(
    tmp_path: Path, checker: Checker
) -> None:
    root = project(
        tmp_path,
        {
            "pyproject.toml": package_pyproject(),
            "src/demo_tool/__init__.py": "",
            "src/demo_tool/first.py": "from demo_tool.second import second\n",
            "src/demo_tool/second.py": "from demo_tool.first import first\n",
            "src/demo_tool/kinds.py": (
                "from enum import Enum as Base\nclass Kind(Base):\n    ONE = 1\n"
            ),
            "src/demo_tool/use.py": (
                "from demo_tool.kinds import Kind as K\nlabels = {K.ONE: 'one'}\n"
                "class OtherError(Exception):\n    pass\n"
            ),
            "tests/test_use.py": (
                "from datetime import datetime\ndef test_now() -> None:\n"
                "    datetime.now()\n"
            ),
            "tests/test_missing.py": "def test_missing() -> None:\n    pass\n",
        },
    )
    found = rules(checker, root)
    assert {"PY010", "PY011", "PY013", "PY014", "PY017"} <= found


def test_changed_paths_filter_after_full_graph_validation(
    tmp_path: Path, checker: Checker
) -> None:
    root = project(
        tmp_path,
        {
            "pyproject.toml": package_pyproject(),
            "src/demo_tool/__init__.py": "",
            "src/demo_tool/first.py": "from demo_tool.second import second\n",
            "src/demo_tool/second.py": "from demo_tool.first import first\n",
        },
    )
    diagnostics = checker.check(root, [Path("src/demo_tool/first.py")])
    assert diagnostics
    assert {item.path for item in diagnostics} == {Path("src/demo_tool/first.py")}
    assert any(item.rule == "PY010" for item in diagnostics)


def test_isolates_generated_and_nested_git_and_fixtures_without_git(
    tmp_path: Path, checker: Checker
) -> None:
    root = project(
        tmp_path,
        {
            "pyproject.toml": "[tool.uv]\npackage = false\n",
            ".agents/plugins/payloads.json": "{}\n",
            ".codex/skills/bad.py": "x = [a for b in [] for a in b]\n",
            "plugins/python/bad.py": "x = [a for b in [] for a in b]\n",
            "vendor/.git": "gitdir: elsewhere\n",
            "vendor/bad.py": "x = [a for b in [] for a in b]\n",
            "good.py": "x = [a for a in []]\n",
        },
    )
    assert rules(checker, root) == set()


def test_checks_canonical_plugins_without_generated_payloads(
    tmp_path: Path, checker: Checker
) -> None:
    root = project(
        tmp_path,
        {
            "pyproject.toml": "[tool.uv]\npackage = false\n",
            "plugins/infonetica/check.py": "x = [a for b in [] for a in b]\n",
        },
    )
    assert "PY001" in rules(checker, root)


def test_exceptions_require_exact_reason_and_stale_only_full_scan(
    tmp_path: Path, checker: Checker
) -> None:
    root = project(
        tmp_path,
        {
            "pyproject.toml": (
                "[tool.uv]\npackage = false\n[tool.python-standards]\n"
                "exceptions = [{ path = 'bad.py', rule = 'PY001', "
                "reason = 'legacy' }]\n"
            ),
            "bad.py": "x = [a for b in [] for a in b]\n",
        },
    )
    assert rules(checker, root) == set()
    write(root, {"bad.py": "x = [a for a in []]\n"})
    assert "PY000" in rules(checker, root)
    assert "PY000" not in rules(checker, root, [Path("bad.py")])
    write(
        root,
        {
            "pyproject.toml": (
                "[tool.python-standards]\n"
                "exceptions = [{ path = 'bad.py', rule = 'PY001', reason = '' }]\n"
            )
        },
    )
    assert "PY000" in rules(checker, root)


def test_parse_and_cli_errors_are_operational(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], checker: Checker
) -> None:
    root = project(tmp_path, {"bad.py": "def broken(:\n"})
    with pytest.raises(checker.CheckerError, match="cannot parse"):
        checker.check(root)
    assert checker.main(["--root", str(root)]) == 2
    assert "cannot parse" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("files", "rule"),
    [
        ({"pyproject.toml": package_pyproject()}, "PY002"),
        (
            {
                "pyproject.toml": package_pyproject(),
                "src/wrong/__init__.py": "",
            },
            "PY004",
        ),
        ({"pyproject.toml": package_pyproject("script")}, "PY005"),
        (
            {
                "pyproject.toml": "[tool.uv]\npackage = false\n",
                "library/pyproject.toml": package_pyproject("library"),
            },
            "PY006",
        ),
    ],
)
def test_structure_rules_report_incorrect_project_graphs(
    tmp_path: Path, checker: Checker, files: dict[str, str], rule: str
) -> None:
    assert rule in rules(checker, project(tmp_path, files))


def test_namespace_package_with_owned_py_typed_is_valid(
    tmp_path: Path, checker: Checker
) -> None:
    root = project(
        tmp_path,
        {
            "pyproject.toml": (
                "[project]\nname = 'acme-cli'\n[tool.uv.build-backend]\n"
                "module-name = 'acme.cli'\n"
            ),
            "src/acme/cli/__init__.py": "",
            "src/acme/cli/py.typed": "",
        },
    )
    found = rules(checker, root)
    assert "PY003" not in found
    assert "PY004" not in found


def test_import_time_io_distinguishes_known_apis_and_main_guard(
    tmp_path: Path, checker: Checker
) -> None:
    root = project(
        tmp_path,
        {
            "pyproject.toml": "[tool.uv]\npackage = false\n",
            "safe.py": (
                "data = {}.get('key')\nclass Runner:\n    def run(self):\n"
                "        return 1\n"
                "callback = lambda: Runner().run()\n"
                "if __name__ == '__main__':\n    from pathlib import Path\n"
                "    Path('value').read_text()\n"
            ),
            "bad.py": (
                "from pathlib import Path\np = Path('value')\np.read_text()\n"
                "@Path('other').read_text()\ndef decorated():\n    pass\n"
                "class Reads:\n    value = Path('class').read_text()\n"
            ),
        },
    )
    diagnostics = checker.check(root)
    assert any(
        item.path == Path("bad.py") and item.rule == "PY009" for item in diagnostics
    )
    assert not any(
        item.path == Path("safe.py") and item.rule == "PY009" for item in diagnostics
    )


def test_entry_process_state_relative_cycles_and_type_checking(
    tmp_path: Path, checker: Checker
) -> None:
    root = project(
        tmp_path,
        {
            "pyproject.toml": (
                "[project]\nname = 'demo-tool'\n[project.scripts]\n"
                "demo = 'demo_tool.entry:main'\n"
            ),
            "src/demo_tool/__init__.py": "",
            "src/demo_tool/py.typed": "",
            "src/demo_tool/entry.py": (
                "import os\ndef helper():\n    return os.getenv('BAD')\n"
                "def main():\n    return os.getenv('OK')\n"
            ),
            "src/demo_tool/one.py": "from .two import two\n",
            "src/demo_tool/two.py": "from .one import one\n",
            "src/demo_tool/types.py": (
                "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n"
                "    from .one import one\n"
            ),
        },
    )
    diagnostics = checker.check(root)
    assert any(
        item.path == Path("src/demo_tool/entry.py") and item.rule == "PY016"
        for item in diagnostics
    )
    assert any(
        item.path == Path("src/demo_tool/one.py") and item.rule == "PY010"
        for item in diagnostics
    )
    assert not any(
        item.path == Path("src/demo_tool/types.py") and item.rule == "PY010"
        for item in diagnostics
    )


def test_script_enum_and_local_exception_hierarchy_are_resolved(
    tmp_path: Path, checker: Checker
) -> None:
    root = project(
        tmp_path,
        {
            "pyproject.toml": package_pyproject(),
            "src/demo_tool/__init__.py": "",
            "src/demo_tool/py.typed": "",
            "src/demo_tool/errors.py": (
                "class DemoToolError(Exception):\n    pass\n"
                "class ChildError(DemoToolError):\n    pass\n"
            ),
            "script.py": (
                "from enum import Enum\nclass Colour(Enum):\n    RED = 1\n"
                "labels = {Colour.RED: 'red'}\n"
            ),
        },
    )
    diagnostics = checker.check(root)
    assert any(
        item.path == Path("script.py") and item.rule == "PY013" for item in diagnostics
    )
    assert not any(item.rule == "PY011" for item in diagnostics)


def test_bad_exception_config_is_visible_in_changed_mode(
    tmp_path: Path, checker: Checker
) -> None:
    root = project(
        tmp_path,
        {
            "pyproject.toml": (
                "[tool.python-standards]\n"
                "exceptions = [{ path = 'bad.py', rule = 'PY001', reason = '' }]\n"
            ),
            "bad.py": "x = [item for item in []]\n",
        },
    )
    assert "PY000" in rules(checker, root, [Path("bad.py")])


def test_main_guard_is_exact_and_else_still_runs_at_import(
    tmp_path: Path, checker: Checker
) -> None:
    root = project(
        tmp_path,
        {
            "pyproject.toml": "[tool.uv]\npackage = false\n",
            "not_guard.py": (
                "from pathlib import Path\nif __name__ != '__main__':\n"
                "    Path('value').read_text()\n"
            ),
            "guard_else.py": (
                "from pathlib import Path\nif __name__ == '__main__':\n    pass\n"
                "else:\n    Path('value').read_text()\n"
            ),
        },
    )
    diagnostics = checker.check(root)
    assert {item.path for item in diagnostics if item.rule == "PY009"} == {
        Path("not_guard.py"),
        Path("guard_else.py"),
    }


def test_configured_package_requires_exact_path_and_py_typed(
    tmp_path: Path, checker: Checker
) -> None:
    root = project(
        tmp_path,
        {
            "pyproject.toml": (
                "[project]\nname = 'acme-cli'\n[tool.uv.build-backend]\n"
                "module-name = 'acme.cli'\n"
            ),
            "src/acme/__init__.py": "",
            "src/acme/cli/__init__.py": "",
        },
    )
    assert "PY003" in rules(checker, root)
    missing = project(
        tmp_path / "missing",
        {
            "pyproject.toml": (
                "[project]\nname = 'acme-cli'\n[tool.uv.build-backend]\n"
                "module-name = 'acme.missing'\n"
            ),
            "src/acme/__init__.py": "",
        },
    )
    assert "PY004" in rules(checker, missing)


def test_init_exports_only_static_all_and_authored_test_inits_are_rejected(
    tmp_path: Path, checker: Checker
) -> None:
    root = project(
        tmp_path,
        {
            "pyproject.toml": "[tool.uv]\npackage = false\n",
            "package/__init__.py": "__all__ = names()\n",
            ".agents/tests/__init__.py": "",
        },
    )
    diagnostics = checker.check(root)
    assert any(
        item.path == Path("package/__init__.py") and item.rule == "PY008"
        for item in diagnostics
    )
    assert any(
        item.path == Path(".agents/tests/__init__.py") and item.rule == "PY014"
        for item in diagnostics
    )


def test_configured_entry_callable_is_allowed_but_class_main_is_not(
    tmp_path: Path, checker: Checker
) -> None:
    root = project(
        tmp_path,
        {
            "pyproject.toml": (
                "[project]\nname = 'demo-tool'\n[project.scripts]\n"
                "demo = 'demo_tool.entry:launch'\n"
            ),
            "src/demo_tool/__init__.py": "",
            "src/demo_tool/py.typed": "",
            "src/demo_tool/entry.py": (
                "import os\ndef launch():\n    return os.getenv('OK')\n"
                "class Wrong:\n    def main(self):\n        return os.getenv('BAD')\n"
            ),
        },
    )
    diagnostics = checker.check(root)
    state = [
        item
        for item in diagnostics
        if item.path == Path("src/demo_tool/entry.py") and item.rule == "PY016"
    ]
    assert len(state) == 1


def test_entry_decorators_and_defaults_do_not_read_process_state(
    tmp_path: Path, checker: Checker
) -> None:
    root = project(
        tmp_path,
        {
            "pyproject.toml": "[tool.uv]\npackage = false\n",
            "entry.py": (
                "import os\ndef decorate(value):\n    return value\n"
                "@decorate(os.getenv('DECORATOR'))\n"
                "def main(value=os.getenv('DEFAULT')):\n    return os.getenv('BODY')\n"
                "if __name__ == '__main__':\n    main()\n"
            ),
        },
    )
    diagnostics = checker.check(root)
    state = [
        item
        for item in diagnostics
        if item.path == Path("entry.py") and item.rule == "PY016"
    ]
    assert {item.line for item in state} == {4, 5}
