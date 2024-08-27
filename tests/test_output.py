import textwrap
from dataclasses import dataclass

import pytest
from rich.table import Table
from rich.text import Text
from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@backends
def test_invoke_exit_success_with_message(capsys, backend):
    def fn():
        raise cappa.Exit("With message")

    @cappa.command(invoke=fn)
    @dataclass
    class Example: ...

    with pytest.raises(cappa.Exit):
        cappa.invoke(Example, argv=[], backend=backend)

    out = capsys.readouterr().out
    assert out == "With message\n"


@backends
def test_invoke_exit_success_without_message(capsys, backend):
    def fn():
        raise cappa.Exit()

    @cappa.command(invoke=fn)
    @dataclass
    class Example: ...

    with pytest.raises(cappa.Exit):
        cappa.invoke(Example, argv=[], backend=backend)

    out = capsys.readouterr().out
    assert out == ""


@backends
def test_invoke_exit_error(capsys, backend):
    def fn():
        raise cappa.Exit("With message", code=1)

    @cappa.command(invoke=fn)
    @dataclass
    class Example: ...

    with pytest.raises(cappa.Exit) as e:
        cappa.invoke(Example, argv=[], backend=backend)

    assert e.value.code == 1
    out = capsys.readouterr().err
    assert out == "Error: With message\n"


@backends
def test_error_output_rich_text(capsys, backend):
    def fn():
        raise cappa.Exit(Text("With message"), code=1)

    @cappa.command(invoke=fn)
    @dataclass
    class Example: ...

    with pytest.raises(cappa.Exit) as e:
        cappa.invoke(Example, argv=[], backend=backend)

    assert e.value.code == 1
    out = capsys.readouterr().err
    assert out == "Error: With message\n"


@backends
def test_explicit_output_prefix(capsys, backend):
    @cappa.command(name="asdf")
    @dataclass
    class Example: ...

    output = cappa.Output(error_format="{prog}: error({code}): {message}.")
    with pytest.raises(cappa.Exit) as e:
        parse(Example, "--fooooo", backend=backend, output=output)

    assert e.value.code == 2
    out = capsys.readouterr().err
    assert out.lower() == "asdf: error(2): unrecognized arguments: --fooooo.\n"


def _debug(output: cappa.Output):
    table = Table(style="blue")
    table.add_row("one", "two")
    output.error(table)
    raise cappa.Exit(code=0)


@backends
def test_output_formatting_complex_rich_object(capsys, backend):
    @dataclass
    class Example:
        debug_info: Annotated[
            bool,
            cappa.Arg(long=True, action=_debug, num_args=0),
        ] = False

    output = cappa.Output(error_format="[red]Error[/red]:\n{message}!")
    with pytest.raises(cappa.Exit) as e:
        parse(Example, "--debug-info", output=output, backend=backend)

    assert e.value.code == 0
    out = capsys.readouterr().err
    assert out == textwrap.dedent(
        """\
        Error:
        ┏━━━━━┳━━━━━┓
        ┃     ┃     ┃
        ┡━━━━━╇━━━━━┩
        │ one │ two │
        └─────┴─────┘!
        """
    )
