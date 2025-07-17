from __future__ import annotations

from pathlib import Path
from typing import Any


def successful_test_run(
    pytester: Any, *, count: int | None = None, skipped_count: int = 0
):
    pytester.copy_example()
    result = pytester.runpytest_inprocess(
        "-vv", "--log-cli-level=WARNING", "--log-level=WARNING", "conftest.py"
    )
    result.assert_outcomes(passed=count, skipped=skipped_count, failed=0)


def test_kitchen_sink(pytester: Any):
    successful_test_run(pytester, count=1)


def test_docutils(pytester: Any):
    build_path: Path = pytester.path / "_build"
    path = build_path / "index.html"
    path.unlink(missing_ok=True)

    pytester.copy_example(name="docutils")
    pytester.run("sphinx-build", "-W", "--jobs=2", pytester.path, build_path)

    output = path.read_text()
    assert "Usage: foo" in output
