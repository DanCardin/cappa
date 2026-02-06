"""Tests for field_name grouping in help text."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import Backend, CapsysOutput, backends, parse


@backends
def test_basic_field_grouping(backend: Backend, capsys: Any):
    """Test that multiple args with same field_name are shown on same line."""

    @dataclass
    class Args:
        verbose: Annotated[
            bool,
            cappa.Arg(short="-v", long="--verbose", help="Enable verbose output."),
            cappa.Arg(long="--debug", help="Enable debug mode."),
        ]

    with pytest.raises(cappa.Exit):
        parse(Args, "--help", backend=backend)

    output = CapsysOutput.from_capsys(capsys)
    # Bool flags combined: [-v, --verbose, --debug]
    assert "[-v, --verbose, --debug]" in output.stdout
    # Help texts should be concatenated (may wrap across lines)
    assert "Enable verbose output." in output.stdout
    assert "debug mode." in output.stdout


@backends
def test_single_arg_unaffected(backend: Backend, capsys: Any):
    """Test that single args without field_name grouping are unaffected."""

    @dataclass
    class Args:
        name: Annotated[str, cappa.Arg(short="-n", help="Your name.")]

    with pytest.raises(cappa.Exit):
        parse(Args, "--help", backend=backend)

    output = CapsysOutput.from_capsys(capsys)
    assert "-n NAME" in output.stdout
    assert "Your name." in output.stdout


@backends
def test_multiple_grouped_fields(backend: Backend, capsys: Any):
    """Test multiple different fields with grouping."""

    @dataclass
    class Args:
        verbose: Annotated[
            int,
            cappa.Arg(
                short="-v", help="Verbosity level (lowercase v).", group="Verbose"
            ),
            cappa.Arg(
                short="-V", help="Verbosity level (uppercase V).", group="Verbose"
            ),
        ] = 0

        output: Annotated[
            str,
            cappa.Arg(short="-o", help="Output file.", group="Output"),
            cappa.Arg(short="-O", help="Alternative output option.", group="Output"),
        ] = "out.txt"

    with pytest.raises(cappa.Exit):
        parse(Args, "--help", backend=backend)

    output = CapsysOutput.from_capsys(capsys)

    # Check verbose group
    assert "[-v VERBOSE, -V VERBOSE]" in output.stdout
    assert "Verbosity level (lowercase v)." in output.stdout
    assert "(uppercase V)." in output.stdout

    # Check output group
    assert "[-o OUTPUT, -O OUTPUT]" in output.stdout
    assert "Output file." in output.stdout
    assert "Alternative" in output.stdout


@backends
def test_bool_pair_combined(backend: Backend, capsys: Any):
    """Test that --foo/--no-foo pairs are combined on the same line."""

    @dataclass
    class Args:
        debug: Annotated[bool, cappa.Arg(long="--debug/--no-debug")] = False

    with pytest.raises(cappa.Exit):
        parse(Args, "--help", backend=backend)

    output = CapsysOutput.from_capsys(capsys)

    # Bool flags with no value should be combined into single brackets
    assert "[--debug, --no-debug]" in output.stdout


@backends
def test_field_grouping_with_defaults(backend: Backend, capsys: Any):
    """Test that defaults are shown correctly for grouped fields."""

    @dataclass
    class Args:
        level: Annotated[
            int,
            cappa.Arg(short="-l", help="Level option 1."),
            cappa.Arg(short="-L", help="Level option 2."),
        ] = 5

    with pytest.raises(cappa.Exit):
        parse(Args, "--help", backend=backend)

    output = CapsysOutput.from_capsys(capsys)

    # Both args should be on the same line
    assert "[-l LEVEL, -L LEVEL]" in output.stdout
    # Default should appear
    assert "Default: 5" in output.stdout


@backends
def test_same_value_name_combined(backend: Backend, capsys: Any):
    """Test that args with same value_name show value once at end."""

    @dataclass
    class Args:
        verbose: Annotated[
            int,
            cappa.Arg(short="-v", help="Verbosity (short).", group="Options"),
            cappa.Arg(long="--verbose", help="Verbosity (long).", group="Options"),
        ] = 0

    with pytest.raises(cappa.Exit):
        parse(Args, "--help", backend=backend)

    output = CapsysOutput.from_capsys(capsys)

    # Format: [-v VERBOSE, --verbose VERBOSE]
    assert "[-v VERBOSE, --verbose VERBOSE]" in output.stdout


@backends
def test_different_value_names_each_shown(backend: Backend, capsys: Any):
    """Test that args with different value_names each show their own value."""

    @dataclass
    class Args:
        output: Annotated[
            str,
            cappa.Arg(
                short="-o", value_name="file", help="Output file.", group="Output"
            ),
            cappa.Arg(
                long="--output", value_name="path", help="Output path.", group="Output"
            ),
        ] = "out.txt"

    with pytest.raises(cappa.Exit):
        parse(Args, "--help", backend=backend)

    output = CapsysOutput.from_capsys(capsys)

    # Different value_names: [-o FILE, --output PATH]
    assert "[-o FILE, --output PATH]" in output.stdout


@backends
def test_mixed_value_names_with_none(backend: Backend, capsys: Any):
    """Test args where some consume values and some don't."""

    @dataclass
    class Args:
        # This creates exclusive args with different behaviors
        mode: Annotated[
            int | bool,
            cappa.Arg(short="-m", value_name="mode", help="Mode value.", group="Mode"),
            cappa.Arg(
                long="--default",
                action=cappa.ArgAction.store_true,
                help="Use default.",
                group="Mode",
            ),
        ] = 0

    with pytest.raises(cappa.Exit):
        parse(Args, "--help", backend=backend)

    output = CapsysOutput.from_capsys(capsys)

    # Format: [-m MODE, --default] (--default is store_true so no value)
    assert "[-m MODE, --default]" in output.stdout
