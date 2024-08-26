from __future__ import annotations

import sys
from typing import Optional

from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse

if sys.version_info < (3, 13):
    import msgspec

    class PydanticCommand(msgspec.Struct):
        name: str
        foo: Annotated[int, cappa.Arg(short=True)]

    @backends
    def test_base_model(backend):
        result = parse(PydanticCommand, "meow", "-f", "4", backend=backend)
        assert result == PydanticCommand(name="meow", foo=4)

    class OptSub(msgspec.Struct):
        name: Optional[str] = None

    class OptionalSubcommand(msgspec.Struct):
        sub: cappa.Subcommands[Optional[OptSub]] = None

    @backends
    def test_optional_subcommand(backend):
        result = parse(OptionalSubcommand, backend=backend)
        assert result == OptionalSubcommand(sub=None)

        result = parse(OptionalSubcommand, "opt-sub", backend=backend)
        assert result == OptionalSubcommand(sub=OptSub(name=None))

        result = parse(OptionalSubcommand, "opt-sub", "foo", backend=backend)
        assert result == OptionalSubcommand(sub=OptSub(name="foo"))
