from dataclasses import dataclass

import cappa


def test_color_off():
    def no_op():
        pass

    @cappa.command(invoke=no_op)
    @dataclass
    class Example:
        args: list[str]

    cappa.invoke(Example, color=False)
