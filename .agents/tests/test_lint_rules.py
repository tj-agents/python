import socket
import subprocess
import sys
from pathlib import Path

import pytest
from pytest_socket import SocketBlockedError

ROOT = Path(__file__).parents[2]


@pytest.mark.parametrize(
    ("rule", "source"),
    (
        ("PGH004", "value = 1  # noqa\n"),
        ("ANN401", "from typing import Any\ndef read() -> Any:\n    return None\n"),
        (
            "G004",
            (
                "import logging\nlog = logging.getLogger(__name__)\nlog.in"
                "fo(f'value {1}')\n"
            ),
        ),
        ("PLW1514", "stream = open('data.txt')\n"),
        ("LOG002", "import logging\nlogging.getLogger(__file__)\n"),
        ("LOG015", "import logging\nlogging.info('message')\n"),
        ("PLC2701", "from example._internal import value\n"),
        ("ICN001", "import numpy\n"),
        ("TID251", "import sys\nsys.path.append('other-checkout')\n"),
        (
            "TRY300",
            "def parse(text):\n    try:\n        value = int(text)\n"
            "        return value\n    except ValueError:\n        return 0\n",
        ),
        ("PT009", "def test_value(self):\n    self.assertEqual(1, 1)\n"),
        (
            "PT011",
            (
                "import pytest\ndef test_value():\n    with pytest.raises("
                "ValueError):\n        int('x')\n"
            ),
        ),
        (
            "PT006",
            (
                "import pytest\n@pytest.mark.parametrize('first,second', "
                "[(1, 2)])\ndef test_value(first, second):\n    assert fir"
                "st < second\n"
            ),
        ),
        ("PLR6301", "class Example:\n    def value(self) -> int:\n        return 1\n"),
    ),
)
def test_lint_rejects_the_new_standard(tmp_path: Path, rule: str, source: str) -> None:
    script = tmp_path / "example.py"
    script.write_text(source, encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--config",
            str(ROOT / "pyproject.toml"),
            "--select",
            rule,
            str(script),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=30,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert result.stdout.strip(), result.stderr


@pytest.mark.parametrize(
    ("code", "source"),
    (
        ("ignore-without-code", "value: str = 1  # type: ignore\n"),
        (
            "exhaustive-match",
            (
                "from enum import Enum\nclass Choice(Enum):\n    FIRST = 1"
                "\n    SECOND = 2\ndef choose(value: Choice) -> None:\n    "
                "match value:\n        case Choice.FIRST:\n            pas"
                "s\n"
            ),
        ),
    ),
)
def test_types_reject_the_new_standard(tmp_path: Path, code: str, source: str) -> None:
    script = tmp_path / "example.py"
    script.write_text(source, encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            "--config-file",
            str(ROOT / "pyproject.toml"),
            str(script),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert f"[{code}]" in result.stdout, result.stdout + result.stderr


def test_tests_cannot_open_network_sockets() -> None:
    with (
        pytest.warns(UserWarning, match="socket"),
        pytest.raises(SocketBlockedError, match="socket"),
    ):
        socket.socket()
