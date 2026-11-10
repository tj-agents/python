from __future__ import annotations

import argparse
import ast
import subprocess
import sys
import tomllib
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Diagnostic:
    path: Path
    line: int
    rule: str
    message: str


class CheckerError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class Project:
    root: Path
    data: dict[str, object]


def _relative(root: Path, path: Path) -> Path:
    return path.resolve().relative_to(root.resolve())


def _ignored(root: Path, path: Path) -> bool:
    parts = path.parts
    return (
        ".worktrees" in parts
        or ".git" in parts
        or ".venv" in parts
        or "venv" in parts
        or "__pycache__" in parts
        or "node_modules" in parts
        or ".template" in parts
        or path.is_relative_to(Path(".agents/dependencies"))
        or path.is_relative_to(Path(".codex/skills"))
        or path.is_relative_to(Path(".claude/skills"))
        or path in {Path(".codex/hooks/snapshot.py"), Path(".codex/hooks/bootstrap.py")}
        or (
            path.is_relative_to(Path("plugins"))
            and (root / ".agents/plugins/payloads.json").is_file()
        )
        or path == Path(".agents/sync_generated.py")
    )


def _git_files(root: Path) -> set[Path] | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-co", "--exclude-standard", "-z"],
            capture_output=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CheckerError(f"git ls-files failed: {error}") from error
    if result.returncode:
        if b"not a git repository" in result.stderr:
            return None
        detail = result.stderr.decode(errors="replace").strip()
        raise CheckerError(f"git ls-files failed: {detail}")
    return {Path(name.decode()) for name in result.stdout.split(b"\0") if name}


def _in_nested_git(root: Path, path: Path) -> bool:
    for parent in (root / path).parents:
        if parent == root:
            return False
        if (parent / ".git").exists():
            return True
    return False


def _files(root: Path) -> set[Path]:
    tracked = _git_files(root)
    if tracked is not None:
        return {
            path
            for path in tracked
            if not _ignored(root, path) and not _in_nested_git(root, path)
        }
    found: set[Path] = set()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = _relative(root, path)
        if _ignored(root, relative):
            continue
        if _in_nested_git(root, relative):
            continue
        found.add(relative)
    return found


def _load_projects(root: Path, files: set[Path]) -> list[Project]:
    projects: list[Project] = []
    for path in sorted(files):
        if path.name != "pyproject.toml":
            continue
        try:
            data = tomllib.loads((root / path).read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as error:
            raise CheckerError(f"cannot read {path}: {error}") from error
        if not isinstance(data, dict):
            raise CheckerError(f"invalid TOML root in {path}")
        projects.append(Project(path.parent, data))
    return projects


def _project_value(project: Project, *keys: str) -> object | None:
    value: object = project.data
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _project_name(project: Project) -> str | None:
    value = _project_value(project, "project", "name")
    return value if isinstance(value, str) else None


def _is_script(project: Project) -> bool:
    return _project_value(project, "tool", "uv", "package") is False


def _package_name(name: str) -> str:
    return name.lower().replace("-", "_").replace(".", "_")


def _source_roots(root: Path, projects: Sequence[Project]) -> dict[Path, Path]:
    result: dict[Path, Path] = {}
    for project in projects:
        source = project.root / "src"
        if (root / source).is_dir():
            result[source] = project.root
    return result


def _tree(root: Path, path: Path) -> ast.Module:
    try:
        return ast.parse((root / path).read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeDecodeError, SyntaxError) as error:
        raise CheckerError(f"cannot parse {path}: {error}") from error


def _diag(path: Path, node: ast.AST, rule: str, message: str) -> Diagnostic:
    return Diagnostic(path, getattr(node, "lineno", 1), rule, message)


def _module_name(path: Path, source_roots: dict[Path, Path]) -> str | None:
    for source in source_roots:
        try:
            relative = path.relative_to(source)
        except ValueError:
            continue
        parts = list(relative.with_suffix("").parts)
        if not parts:
            return None
        if parts[-1] == "__init__":
            parts.pop()
        return ".".join(parts)
    return None


def _is_test(path: Path) -> bool:
    return (
        "tests" in path.parts
        or path.name.startswith("test_")
        or path.name == "conftest.py"
    )


def _imports(tree: ast.Module) -> dict[str, str]:
    names: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                names[item.asname or item.name.split(".")[0]] = (
                    item.name if item.asname else item.name.split(".")[0]
                )
        elif isinstance(node, ast.ImportFrom) and node.module:
            for item in node.names:
                names[item.asname or item.name] = f"{node.module}.{item.name}"
    return names


def _dotted(node: ast.AST, imports: dict[str, str]) -> str | None:
    if isinstance(node, ast.Name):
        return imports.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value, imports)
        return f"{base}.{node.attr}" if base else None
    return None


def _comprehensions(tree: ast.Module, path: Path) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    types = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
    for node in ast.walk(tree):
        if not isinstance(node, types):
            continue
        nested = any(
            child is not node and isinstance(child, types) for child in ast.walk(node)
        )
        if len(node.generators) > 1 or nested:
            diagnostics.append(
                _diag(path, node, "PY001", "use one comprehension generator")
            )
    return diagnostics


def _structure(root: Path, projects: Sequence[Project]) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for project in projects:
        pyproject = project.root / "pyproject.toml"
        name = _project_name(project)
        source = root / project.root / "src"
        if name and not _is_script(project):
            if not source.is_dir():
                diagnostics.append(
                    Diagnostic(
                        pyproject, 1, "PY002", "package project needs src layout"
                    )
                )
            else:
                expected = _package_name(name)
                configured = _project_value(
                    project, "tool", "uv", "build-backend", "module-name"
                )
                module = configured if isinstance(configured, str) else expected
                package = root / project.root / "src" / Path(*module.split("."))
                if not package.is_dir():
                    diagnostics.append(
                        Diagnostic(
                            pyproject,
                            1,
                            "PY004",
                            "distribution name must match import package",
                        )
                    )
                elif (package / "__init__.py").is_file() and not (
                    package / "py.typed"
                ).is_file():
                    diagnostics.append(
                        Diagnostic(
                            _relative(root, package / "__init__.py"),
                            1,
                            "PY003",
                            "package needs py.typed",
                        )
                    )
        if name and not source.is_dir() and not _is_script(project):
            diagnostics.append(
                Diagnostic(
                    pyproject,
                    1,
                    "PY005",
                    "standalone script project needs tool.uv.package = false",
                )
            )
    root_project = next(
        (project for project in projects if project.root == Path()), None
    )
    if root_project and (_is_script(root_project) or not (root / "src").is_dir()):
        for project in projects:
            name = _project_name(project)
            if project.root == Path() or name is None or _is_script(project):
                continue
            expected_package = Path("packages") / name
            if project.root != expected_package:
                diagnostics.append(
                    Diagnostic(
                        project.root / "pyproject.toml",
                        1,
                        "PY006",
                        "nested library belongs in packages/<distribution-name>",
                    )
                )
    return diagnostics


def _modules(tree: ast.Module, path: Path) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if not _is_test(path) and any(
        part in {"utils", "helpers", "common", "misc"}
        for part in path.with_suffix("").parts
    ):
        diagnostics.append(
            Diagnostic(path, 1, "PY007", "rename the module for its responsibility")
        )
    if path.name == "__init__.py":
        for index, node in enumerate(tree.body):
            if (
                index == 0
                and isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                continue
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            if _is_all_assignment(node):
                continue
            diagnostics.append(
                _diag(path, node, "PY008", "__init__.py only exports public names")
            )
    for walked in ast.walk(tree):
        if (
            isinstance(walked, (ast.FunctionDef, ast.AsyncFunctionDef))
            and walked.name == "__del__"
        ):
            diagnostics.append(
                _diag(path, walked, "PY012", "use explicit cleanup instead of __del__")
            )
        if isinstance(walked, ast.ClassDef):
            members = [
                member
                for member in walked.body
                if not (
                    isinstance(member, ast.Expr)
                    and isinstance(member.value, ast.Constant)
                    and isinstance(member.value.value, str)
                )
            ]
            all_static = bool(members)
            for member in members:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    is_static = any(
                        _dotted(item, {}) in {"staticmethod", "builtins.staticmethod"}
                        for item in member.decorator_list
                    )
                else:
                    is_static = False
                if not is_static:
                    all_static = False
                    break
            if all_static:
                diagnostics.append(
                    _diag(
                        path,
                        walked,
                        "PY015",
                        "use module functions instead of staticmethod-only class",
                    )
                )
    return diagnostics


def _is_all_assignment(node: ast.stmt) -> bool:
    target: ast.expr | None
    value: ast.expr | None
    if isinstance(node, ast.Assign):
        target = node.targets[0] if len(node.targets) == 1 else None
        value = node.value
    elif isinstance(node, ast.AnnAssign):
        target = node.target
        value = node.value
    else:
        return False
    return isinstance(target, ast.Name) and target.id == "__all__" and _all_value(value)


def _all_value(node: ast.expr | None) -> bool:
    if isinstance(node, (ast.List, ast.Tuple)):
        return all(
            isinstance(item, ast.Constant) and isinstance(item.value, str)
            for item in node.elts
        )
    return (
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Add)
        and _all_value(node.left)
        and _all_value(node.right)
    )


def _is_main_guard(node: ast.If) -> bool:
    return (
        isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "__name__"
        and len(node.test.ops) == 1
        and isinstance(node.test.ops[0], ast.Eq)
        and len(node.test.comparators) == 1
        and isinstance(node.test.comparators[0], ast.Constant)
        and node.test.comparators[0].value == "__main__"
    )


def _executed_nodes(tree: ast.Module) -> Iterable[ast.AST]:
    def visit(node: ast.AST) -> Iterable[ast.AST]:
        yield node
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                yield from visit(decorator)
            for default in [*node.args.defaults, *node.args.kw_defaults]:
                if default:
                    yield from visit(default)
            return
        if isinstance(node, ast.Lambda):
            for default in [*node.args.defaults, *node.args.kw_defaults]:
                if default:
                    yield from visit(default)
            return
        if isinstance(node, ast.If) and _is_main_guard(node):
            yield from visit(node.test)
            for statement in node.orelse:
                yield from visit(statement)
            return
        for child in ast.iter_child_nodes(node):
            yield from visit(child)

    for statement in tree.body:
        yield from visit(statement)


def _executed_calls(tree: ast.Module) -> Iterable[ast.Call]:
    return (node for node in _executed_nodes(tree) if isinstance(node, ast.Call))


def _io(tree: ast.Module, path: Path) -> list[Diagnostic]:
    imports = _imports(tree)
    diagnostics: list[Diagnostic] = []
    calls = {
        "open",
        "builtins.open",
        "io.open",
        "subprocess.run",
        "subprocess.check_call",
        "subprocess.check_output",
        "subprocess.Popen",
        "socket.create_connection",
        "urllib.request.urlopen",
        "requests.get",
        "requests.post",
        "requests.request",
        "logging.basicConfig",
        "logging.config.fileConfig",
        "logging.config.dictConfig",
    }
    path_calls = {
        "open",
        "read_text",
        "read_bytes",
        "write_text",
        "write_bytes",
        "unlink",
        "mkdir",
        "iterdir",
        "glob",
        "rglob",
    }
    path_values: set[str] = set()
    for node in _executed_nodes(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Call)
            and _dotted(node.value.func, imports) in {"pathlib.Path", "Path"}
        ):
            path_values.add(node.targets[0].id)
    for call in _executed_calls(tree):
        name = _dotted(call.func, imports)
        is_path_call = (
            isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Call)
            and _dotted(call.func.value.func, imports) in {"pathlib.Path", "Path"}
            and call.func.attr in path_calls
        )
        is_bound_path_call = (
            isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name)
            and call.func.value.id in path_values
            and call.func.attr in path_calls
        )
        if name in calls or is_path_call or is_bound_path_call:
            diagnostics.append(
                _diag(
                    path,
                    call,
                    "PY009",
                    "move I/O into main() or an explicit function",
                )
            )
    for node in _executed_nodes(tree):
        if (
            isinstance(node, ast.Subscript)
            and _dotted(node.value, imports) == "os.environ"
        ):
            diagnostics.append(
                _diag(
                    path,
                    node,
                    "PY009",
                    "move environment reads into main() or an explicit function",
                )
            )
    return diagnostics


def _relative_import(module: str, path: Path, node: ast.ImportFrom) -> str | None:
    package = module if path.name == "__init__.py" else module.rpartition(".")[0]
    if not node.level:
        return node.module
    if not package:
        return None
    parts = package.split(".")
    base = parts[: len(parts) - node.level + 1]
    if node.module:
        base.extend(node.module.split("."))
    return ".".join(base)


def _runtime_imports(
    tree: ast.Module, module: str, path: Path, known: set[str]
) -> set[str]:
    result: set[str] = set()

    def visit(nodes: Sequence[ast.stmt], guarded: bool = False) -> None:
        for node in nodes:
            if isinstance(node, ast.If):
                check = _dotted(node.test, {})
                is_type = (
                    isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING"
                ) or check == "typing.TYPE_CHECKING"
                visit(node.body, guarded or is_type)
                visit(node.orelse, guarded)
            elif not guarded and isinstance(node, ast.Import):
                for item in node.names:
                    if item.name in known:
                        result.add(item.name)
            elif not guarded and isinstance(node, ast.ImportFrom):
                base = _relative_import(module, path, node)
                if not base:
                    continue
                for item in node.names:
                    candidate = f"{base}.{item.name}"
                    if candidate in known:
                        result.add(candidate)
                if base in known:
                    result.add(base)

    visit(tree.body)
    return result


def _cycles(
    trees: dict[Path, ast.Module], modules: dict[Path, str]
) -> list[Diagnostic]:
    paths = {module: path for path, module in modules.items()}
    graph = {
        module: _runtime_imports(trees[path], module, path, set(paths))
        for module, path in paths.items()
    }
    stack: list[str] = []
    visiting: set[str] = set()
    complete: set[str] = set()
    found: set[frozenset[str]] = set()

    def visit(module: str) -> None:
        if module in complete:
            return
        if module in visiting:
            found.add(frozenset(stack[stack.index(module) :]))
            return
        visiting.add(module)
        stack.append(module)
        for target in graph[module]:
            visit(target)
        stack.pop()
        visiting.remove(module)
        complete.add(module)

    for module in graph:
        visit(module)
    diagnostics: list[Diagnostic] = []
    for cycle in found:
        for module in cycle:
            diagnostics.append(
                Diagnostic(
                    paths[module],
                    1,
                    "PY010",
                    "move the shared contract into its owner",
                )
            )
    return diagnostics


def _enum_classes(
    trees: dict[Path, ast.Module], modules: dict[Path, str]
) -> tuple[set[str], set[tuple[Path, str]]]:
    classes: set[str] = set()
    local: set[tuple[Path, str]] = set()
    for path, tree in trees.items():
        imports = _imports(tree)
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and any(
                (_dotted(base, imports) or "").rsplit(".", 1)[-1]
                in {"Enum", "StrEnum", "IntEnum"}
                for base in node.bases
            ):
                local.add((path, node.name))
                if module := modules.get(path):
                    classes.add(f"{module}.{node.name}")
    return classes, local


def _enum_dicts(
    trees: dict[Path, ast.Module], modules: dict[Path, str]
) -> list[Diagnostic]:
    enums, local = _enum_classes(trees, modules)
    diagnostics: list[Diagnostic] = []
    for path, tree in trees.items():
        imports = _imports(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            for key in node.keys:
                name = (
                    _dotted(key.value, imports)
                    if isinstance(key, ast.Attribute)
                    else None
                )
                is_local = (
                    isinstance(key, ast.Attribute)
                    and isinstance(key.value, ast.Name)
                    and (path, key.value.id) in local
                )
                if name in enums or is_local:
                    diagnostics.append(
                        _diag(path, node, "PY013", "put enum data on the enum member")
                    )
                    break
    return diagnostics


def _exceptions(
    trees: dict[Path, ast.Module], modules: dict[Path, str]
) -> list[Diagnostic]:
    definitions: dict[str, tuple[Path, ast.ClassDef, list[str]]] = {}
    for path, tree in trees.items():
        imports = _imports(tree)
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                definitions[f"{modules[path]}.{node.name}"] = (
                    path,
                    node,
                    [_dotted(base, imports) or "" for base in node.bases],
                )
    for name, (path, node, bases) in tuple(definitions.items()):
        module = modules[path]
        resolved = [
            f"{module}.{base}" if f"{module}.{base}" in definitions else base
            for base in bases
        ]
        definitions[name] = (path, node, resolved)
    custom: set[str] = set()
    changed = True
    while changed:
        changed = False
        for name, (_, _, bases) in definitions.items():
            if name not in custom and any(
                base.rsplit(".", 1)[-1]
                in {
                    "Exception",
                    "RuntimeError",
                    "ValueError",
                    "TypeError",
                    "LookupError",
                    "OSError",
                }
                or base in custom
                for base in bases
            ):
                custom.add(name)
                changed = True
    diagnostics: list[Diagnostic] = []
    for package in {module.split(".")[0] for module in modules.values() if module}:
        expected = f"{package.title().replace('_', '')}Error"
        members = {name for name in custom if name.split(".")[0] == package}
        roots: set[str] = set()
        for name in members:
            is_child = False
            for base in definitions[name][2]:
                if base in members:
                    is_child = True
                    break
            if not is_child:
                roots.add(name)
        desired = {name for name in roots if name.rsplit(".", 1)[-1] == expected}
        if members and (len(roots) != 1 or len(desired) != 1):
            for name in roots:
                path, node, _ = definitions[name]
                diagnostics.append(
                    _diag(
                        path,
                        node,
                        "PY011",
                        f"custom exceptions need one {expected} root",
                    )
                )
    return diagnostics


def _has_main_guard(tree: ast.Module) -> bool:
    return any(isinstance(node, ast.If) and _is_main_guard(node) for node in tree.body)


def _entry_modules(projects: Sequence[Project]) -> dict[str, str]:
    entries: dict[str, str] = {}
    for project in projects:
        scripts = _project_value(project, "project", "scripts")
        if isinstance(scripts, dict):
            for value in scripts.values():
                if isinstance(value, str) and ":" in value:
                    module, _, callable_name = value.partition(":")
                    entries[module] = callable_name
    return entries


def _process_state(
    trees: dict[Path, ast.Module], modules: dict[Path, str], projects: Sequence[Project]
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    entries = _entry_modules(projects)
    for path, tree in trees.items():
        imports = _imports(tree)
        module = modules.get(path)
        entry_points: set[str] = set()
        if path.name == "__main__.py" or _has_main_guard(tree):
            entry_points.add("main")
        if module is not None and module in entries:
            entry_points.add(entries[module])

        def visit(
            node: ast.AST,
            in_entry: bool = False,
            scope_depth: int = 0,
            current_path: Path = path,
            allowed_entries: set[str] = entry_points,
            names: dict[str, str] = imports,
        ) -> None:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                in_entry = scope_depth == 0 and node.name in allowed_entries
                scope_depth += 1
            elif isinstance(node, ast.ClassDef):
                scope_depth += 1
            name = (
                _dotted(node, names)
                if isinstance(node, (ast.Name, ast.Attribute))
                else None
            )
            used = name in {"os.environ", "os.getenv", "sys.argv"}
            if used and not in_entry:
                diagnostics.append(
                    _diag(
                        current_path,
                        node,
                        "PY016",
                        "process state belongs in an entry-point main()",
                    )
                )
            for child in ast.iter_child_nodes(node):
                visit(
                    child, in_entry, scope_depth, current_path, allowed_entries, names
                )

        visit(tree)
    return diagnostics


def _clock_reads(trees: dict[Path, ast.Module]) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    blocked = {
        "datetime.datetime.now",
        "datetime.datetime.utcnow",
        "datetime.now",
        "datetime.utcnow",
        "time.time",
        "time.monotonic",
        "time.perf_counter",
    }
    for path, tree in trees.items():
        if not _is_test(path):
            continue
        imports = _imports(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _dotted(node.func, imports) in blocked:
                diagnostics.append(
                    _diag(path, node, "PY017", "tests need controlled time")
                )
    return diagnostics


def _tests(
    root: Path, projects: Sequence[Project], files: set[Path]
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    test_inits = {
        path for path in files if path.name == "__init__.py" and "tests" in path.parts
    }
    for path in sorted(test_inits):
        diagnostics.append(Diagnostic(path, 1, "PY014", "tests must not be a package"))
    for project in projects:
        source = root / project.root / "src"
        tests = root / project.root / "tests"
        if not tests.is_dir():
            continue
        if not source.is_dir():
            continue
        sources = {
            module.stem
            for module in source.rglob("*.py")
            if module.name not in {"__init__.py", "__main__.py"}
        }
        for test in tests.rglob("test_*.py"):
            if (
                test.name == "test_import.py"
                or test.stem.removeprefix("test_") in sources
            ):
                continue
            diagnostics.append(
                Diagnostic(
                    _relative(root, test),
                    1,
                    "PY014",
                    "test module has no matching source module",
                )
            )
    return diagnostics


def _exceptions_config(
    root: Path, projects: Sequence[Project], files: set[Path], full: bool
) -> tuple[dict[tuple[Path, str], str], list[Diagnostic]]:
    root_project = next(
        (project for project in projects if project.root == Path()), None
    )
    if not root_project:
        return {}, []
    configured = _project_value(root_project, "tool", "python-standards", "exceptions")
    if configured is None:
        return {}, []
    diagnostics: list[Diagnostic] = []
    exceptions: dict[tuple[Path, str], str] = {}
    if not isinstance(configured, list):
        return {}, [
            Diagnostic(Path("pyproject.toml"), 1, "PY000", "exceptions must be a list")
        ]
    for item in configured:
        if not isinstance(item, dict):
            diagnostics.append(
                Diagnostic(
                    Path("pyproject.toml"),
                    1,
                    "PY000",
                    "exception needs path, rule and reason",
                )
            )
            continue
        path, rule, reason = item.get("path"), item.get("rule"), item.get("reason")
        if (
            not isinstance(path, str)
            or not isinstance(rule, str)
            or not isinstance(reason, str)
            or not reason
            or set(item) != {"path", "rule", "reason"}
            or any(token in path for token in "*?[")
        ):
            diagnostics.append(
                Diagnostic(
                    Path("pyproject.toml"),
                    1,
                    "PY000",
                    "exception needs exact path, rule and reason",
                )
            )
            continue
        relative = Path(path)
        if relative.is_absolute() or relative not in files:
            diagnostics.append(
                Diagnostic(
                    Path("pyproject.toml"),
                    1,
                    "PY000",
                    "exception path is not an authored file",
                )
            )
            continue
        exceptions[(relative, rule)] = reason
    return exceptions, diagnostics


def check(root: Path, paths: Sequence[Path] | None = None) -> list[Diagnostic]:
    root = root.resolve()
    if not root.is_dir():
        raise CheckerError(f"root is not a directory: {root}")
    files = _files(root)
    projects = _load_projects(root, files)
    python_files = sorted(
        path for path in files if path.suffix == ".py" and (root / path).is_file()
    )
    trees = {path: _tree(root, path) for path in python_files}
    sources = _source_roots(root, projects)
    modules = {
        path: name for path in python_files if (name := _module_name(path, sources))
    }
    diagnostics = _structure(root, projects)
    for path, tree in trees.items():
        diagnostics.extend(_comprehensions(tree, path))
        diagnostics.extend(_modules(tree, path))
        diagnostics.extend(_io(tree, path))
    source_trees = {path: trees[path] for path in modules}
    diagnostics.extend(_cycles(source_trees, modules))
    diagnostics.extend(_enum_dicts(trees, modules))
    diagnostics.extend(_exceptions(source_trees, modules))
    diagnostics.extend(_tests(root, projects, files))
    diagnostics.extend(_process_state(trees, modules, projects))
    diagnostics.extend(_clock_reads(trees))
    exceptions, config_diagnostics = _exceptions_config(
        root, projects, files, paths is None
    )
    suppressed = {(item.path, item.rule) for item in diagnostics}
    diagnostics = [
        item for item in diagnostics if (item.path, item.rule) not in exceptions
    ]
    if paths is None:
        for key in exceptions:
            if key not in suppressed:
                config_diagnostics.append(
                    Diagnostic(Path("pyproject.toml"), 1, "PY000", "stale exception")
                )
    diagnostics.extend(config_diagnostics)
    if paths is not None:
        selected: set[Path] = set()
        for path in paths:
            candidate = path if path.is_absolute() else root / path
            try:
                selected.add(_relative(root, candidate))
            except ValueError as error:
                raise CheckerError(f"path is outside root: {path}") from error
        diagnostics = [
            item
            for item in diagnostics
            if item.path in selected or item in config_diagnostics
        ]
    return sorted(
        set(diagnostics),
        key=lambda item: (item.path.as_posix(), item.line, item.rule, item.message),
    )


def main(arguments: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("paths", nargs="*", type=Path)
    parsed = parser.parse_args(arguments)
    try:
        diagnostics = check(parsed.root, parsed.paths or None)
    except CheckerError as error:
        print(error, file=sys.stderr)
        return 2
    for diagnostic in diagnostics:
        location = f"{diagnostic.path}:{diagnostic.line}:"
        print(f"{location} {diagnostic.rule} {diagnostic.message}")
    return 1 if diagnostics else 0


if __name__ == "__main__":
    raise SystemExit(main())
