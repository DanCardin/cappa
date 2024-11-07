from __future__ import annotations

import textwrap
from dataclasses import dataclass
from typing import Literal

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import CapsysOutput, parse, strip_trailing_whitespace


@dataclass
class Args:
    required: Annotated[str, cappa.Arg(help="I'm required")]
    name: Annotated[str, cappa.Arg(help="I'm optional")] = "arg"
    short: Annotated[str, cappa.Arg(short=True, help="I'm an option")] = "opt"
    maybe: Annotated[str | None, cappa.Arg(short=True, help="maybe?")] = None


def test_default_settings(capsys):
    with pytest.raises(cappa.HelpExit) as e:
        parse(Args, "--help", completion=False)

    assert e.value.code == 0
    out = strip_trailing_whitespace(capsys.readouterr().out)

    assert out == textwrap.dedent(
        """\
        Usage: args [-s SHORT] [-m MAYBE] REQUIRED [NAME] [-h]

          Options
            [-s SHORT]    I'm an option (Default: opt)
            [-m MAYBE]    maybe?

          Arguments
            REQUIRED      I'm required
            [NAME]        I'm optional (Default: arg)

          Help
            [-h, --help]  Show this message and exit.
        """
    )


def test_override_default_format(capsys):
    with pytest.raises(cappa.HelpExit) as e:
        parse(
            Args,
            "--help",
            completion=False,
            help_formatter=cappa.HelpFormatter.default.with_default_format(
                "[Default '{default}']"
            ),
        )

    assert e.value.code == 0
    out = strip_trailing_whitespace(capsys.readouterr().out)

    assert out == textwrap.dedent(
        """\
        Usage: args [-s SHORT] [-m MAYBE] REQUIRED [NAME] [-h]

          Options
            [-s SHORT]    I'm an option [Default 'opt']
            [-m MAYBE]    maybe?

          Arguments
            REQUIRED      I'm required
            [NAME]        I'm optional [Default 'arg']

          Help
            [-h, --help]  Show this message and exit.
        """
    )


def test_override_help_format(capsys):
    with pytest.raises(cappa.HelpExit) as e:
        parse(
            Args,
            "--help",
            completion=False,
            help_formatter=cappa.HelpFormatter.default.with_arg_format(
                (
                    "{default}",
                    "{help}",
                )
            ),
        )

    assert e.value.code == 0
    out = strip_trailing_whitespace(capsys.readouterr().out)

    assert out == textwrap.dedent(
        """\
        Usage: args [-s SHORT] [-m MAYBE] REQUIRED [NAME] [-h]

          Options
            [-s SHORT]    (Default: opt) I'm an option
            [-m MAYBE]    maybe?

          Arguments
            REQUIRED      I'm required
            [NAME]        (Default: arg) I'm optional

          Help
            [-h, --help]  Show this message and exit.
        """
    )


def test_choice_options(capsys):
    @dataclass
    class Args:
        required: Annotated[Literal["one", "two", "three"], cappa.Arg(help="Required.")]

    with pytest.raises(cappa.HelpExit) as e:
        parse(
            Args,
            "--help",
            completion=False,
        )

    assert e.value.code == 0
    out = strip_trailing_whitespace(capsys.readouterr().out)

    assert out == textwrap.dedent(
        """\
        Usage: args REQUIRED [-h]

          Arguments
            REQUIRED      Required. Valid options: one, two, three.

          Help
            [-h, --help]  Show this message and exit.
        """
    )

    with pytest.raises(cappa.HelpExit) as e:
        parse(
            Args,
            "--help",
            completion=False,
            help_formatter=cappa.HelpFormatter().with_arg_format("{help}"),
        )

    assert e.value.code == 0
    out = strip_trailing_whitespace(capsys.readouterr().out)

    assert out == textwrap.dedent(
        """\
        Usage: args REQUIRED [-h]

          Arguments
            REQUIRED      Required.

          Help
            [-h, --help]  Show this message and exit.
        """
    )


def test_callable_help_formatter(capsys):
    @dataclass
    class Args:
        required: Annotated[int, cappa.Arg(help="Required.")]

    def help_formatter(arg: cappa.Arg) -> str | None:
        if arg.field_name == "required":
            return f"Num args: {arg.num_args}"
        return None

    with pytest.raises(cappa.HelpExit) as e:
        parse(
            Args,
            "--help",
            completion=False,
            help_formatter=cappa.HelpFormatter().with_arg_format(
                (
                    "{help}",
                    help_formatter,
                )
            ),
        )

    assert e.value.code == 0
    out = strip_trailing_whitespace(capsys.readouterr().out)

    assert out == textwrap.dedent(
        """\
        Usage: args REQUIRED [-h]

          Arguments
            REQUIRED      Required. Num args: 1

          Help
            [-h, --help]  Show this message and exit.
        """
    )


def test_explicitly_wrapped_formatter(capsys):
    @dataclass
    class Args:
        name: Annotated[str, cappa.Arg(help="Optional.")] = "arg"

    help_formatter = cappa.HelpFormatter(default_format="Default - {default}!")
    with pytest.raises(cappa.HelpExit) as e:
        parse(Args, "--help", help_formatter=help_formatter)

    assert e.value.code == 0
    output = CapsysOutput.from_capsys(capsys)
    assert "Optional. Default - arg!\n" in output.stdout
