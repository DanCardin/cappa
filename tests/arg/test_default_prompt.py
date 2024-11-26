from dataclasses import dataclass
from io import StringIO
from typing import Type

import pytest
from rich.prompt import Confirm as RichConfirm
from rich.prompt import Prompt as RichPrompt
from typing_extensions import Annotated

import cappa
from cappa import Confirm, Prompt
from tests.utils import backends, parse

prompt_types = pytest.mark.parametrize("prompt_type", (Prompt, RichPrompt))
confirm_types = pytest.mark.parametrize("confirm_type", (Confirm, RichConfirm))


@backends
class TestPrompt:
    @prompt_types
    def test_value(self, backend, prompt_type: Type[Prompt]):
        @dataclass
        class Test:
            name: Annotated[str, cappa.Arg(default=prompt_type("gimme text number"))]

        result = parse(Test, backend=backend, input=StringIO("two"))

        assert result.name == "two"

    @prompt_types
    def test_default(self, backend, prompt_type: Type[Prompt]):
        @dataclass
        class Test:
            name: Annotated[
                str, cappa.Arg(default=prompt_type("gimme text number"))
            ] = "one"

        result = parse(Test, backend=backend, input=StringIO(""))

        assert result.name == "one"

    @prompt_types
    def test_mapped(self, backend, prompt_type: Type[Prompt]):
        @dataclass
        class Test:
            num: Annotated[int, cappa.Arg(default=prompt_type("gimme text number"))]

        result = parse(Test, backend=backend, input=StringIO("5"))

        assert result.num == 5


@backends
class TestConfirm:
    @confirm_types
    def test_value(self, backend, confirm_type: Type[Confirm]):
        @dataclass
        class Test:
            ok: Annotated[bool, cappa.Arg(default=confirm_type("gimme text number"))]

        result = parse(Test, backend=backend, input=StringIO("y"))

        assert result.ok is True

    @confirm_types
    def test_default(self, backend, confirm_type: Type[Confirm]):
        @dataclass
        class Test:
            ok: Annotated[
                bool, cappa.Arg(default=confirm_type("gimme text number"))
            ] = False

        result = parse(Test, backend=backend, input=StringIO(""))

        assert result.ok is False
