from dataclasses import dataclass

from typing_extensions import Annotated

import cappa
from cappa import output
from tests.utils import backends, parse


@backends
class TestTestPrompt:
    def test_value(self, backend):
        prompt = output.TestPrompt("gimme text number", default="one", input="two")

        @dataclass
        class Test:
            name: Annotated[str, cappa.Arg(default=prompt)]

        result = parse(Test, backend=backend)

        assert result.name == "two"

        expected = "gimme text number (one): "
        out = prompt.file.getvalue()
        assert out == expected

    def test_default(self, backend):
        prompt = output.TestPrompt("gimme text number", default="one", input="")

        @dataclass
        class Test:
            name: Annotated[str, cappa.Arg(default=prompt)]

        result = parse(Test, backend=backend)

        assert result.name == "one"

        expected = "gimme text number (one): "
        out = prompt.file.getvalue()
        assert out == expected

    def test_mapped(self, backend):
        prompt = output.TestPrompt("gimme text number", default="1", input="5")

        @dataclass
        class Test:
            num: Annotated[int, cappa.Arg(default=prompt)]

        result = parse(Test, backend=backend)

        assert result.num == 5
