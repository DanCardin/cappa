from dataclasses import dataclass

import cappa
from cappa import rich
from typing_extensions import Annotated

from tests.utils import parse


class TestTestPrompt:
    def test_value(self):
        prompt = rich.TestPrompt("gimme text number", default="one", input="two")

        @dataclass
        class Test:
            name: Annotated[str, cappa.Arg(default=prompt)]

        result = parse(Test)

        assert result.name == "two"

        expected = "gimme text number (one): "
        output = prompt.file.getvalue()
        assert output == expected

    def test_default(self):
        prompt = rich.TestPrompt("gimme text number", default="one", input="")

        @dataclass
        class Test:
            name: Annotated[str, cappa.Arg(default=prompt)]

        result = parse(Test)

        assert result.name == "one"

        expected = "gimme text number (one): "
        output = prompt.file.getvalue()
        assert output == expected

    def test_mapped(self):
        prompt = rich.TestPrompt("gimme text number", default="1", input="5")

        @dataclass
        class Test:
            num: Annotated[int, cappa.Arg(default=prompt)]

        result = parse(Test)

        assert result.num == 5
