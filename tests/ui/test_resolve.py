from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

import pytest

from cappa.ui.base import _resolve_target


@dataclass
class MyCommand:
    name: str


def test_named_module():
    assert _resolve_target(MyCommand) == "tests.ui.test_resolve:MyCommand"


def test_main_module_resolves_via_file(tmp_path):
    fake_file = tmp_path / "mycli.py"
    fake_file.touch()

    with patch.object(MyCommand, "__module__", "__main__"):
        with patch("inspect.getfile", return_value=str(fake_file)):
            with patch("sys.path", [str(tmp_path)]):
                assert _resolve_target(MyCommand) == "mycli:MyCommand"


def test_main_module_unresolvable_raises(tmp_path):
    fake_file = tmp_path / "mycli.py"
    fake_file.touch()

    with patch.object(MyCommand, "__module__", "__main__"):
        with patch("inspect.getfile", return_value=str(fake_file)):
            with patch("sys.path", []):
                with pytest.raises(
                    ValueError, match="Cannot determine importable module"
                ):
                    _resolve_target(MyCommand)
