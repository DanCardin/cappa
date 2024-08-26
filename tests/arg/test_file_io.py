from __future__ import annotations

import io
from contextlib import contextmanager
from dataclasses import dataclass
from typing import BinaryIO, TextIO
from unittest.mock import mock_open, patch

import pytest
from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@contextmanager
def file_content(content: str, mode: str = "r"):
    if "b" in mode:
        content = content.encode("utf-8")  # type: ignore

    mock = mock_open(read_data=content)
    with patch("builtins.open", new=mock):
        yield mock

    for call in mock.call_args[::2]:
        assert call[1] == mode


@contextmanager
def stdin(content: str):
    with patch("sys.stdin", new=io.TextIOWrapper(io.BytesIO(content.encode("utf-8")))):
        yield


@backends
def test_text_io_default(backend):
    @dataclass
    class Foo:
        bar: TextIO

    with file_content("wat"):
        test = parse(Foo, "foo.py", backend=backend)

    assert test.bar.read() == "wat"


@backends
def test_text_io(backend):
    @dataclass
    class Foo:
        bar: Annotated[TextIO, cappa.FileMode(mode="r")]

    with file_content("wat"):
        test = parse(Foo, "foo.py", backend=backend)

    assert test.bar.read() == "wat"


@backends
def test_text_io_write(backend):
    @dataclass
    class Foo:
        bar: Annotated[BinaryIO, cappa.FileMode(mode="w")]

    with file_content("wat", mode="w"):
        test = parse(Foo, "foo.py", backend=backend)

    test.bar.write("wat")


@backends
def test_binary_io_default(backend):
    @dataclass
    class Foo:
        bar: BinaryIO

    with file_content("wat", mode="rb"):
        test = parse(Foo, "foo.py", backend=backend)

    assert test.bar.read() == b"wat"


@backends
def test_binary_io(backend):
    @dataclass
    class Foo:
        bar: Annotated[BinaryIO, cappa.FileMode(mode="rb")]

    with file_content("wat", mode="rb"):
        test = parse(Foo, "foo.py", backend=backend)

    assert test.bar.read() == b"wat"


@backends
def test_binary_io_write(backend):
    @dataclass
    class Foo:
        bar: Annotated[BinaryIO, cappa.FileMode(mode="wb")]

    with file_content("wat", mode="wb"):
        test = parse(Foo, "foo.py", backend=backend)

    test.bar.write(b"wat")


@backends
def test_stdin(backend):
    @dataclass
    class Foo:
        bar: Annotated[BinaryIO, cappa.FileMode(mode="r")]

    with stdin("wat"):
        test = parse(Foo, "-", backend=backend)
        assert test.bar.read() == "wat"


@backends
def test_stdin_binary(backend):
    @dataclass
    class Foo:
        bar: Annotated[BinaryIO, cappa.FileMode(mode="rb")]

    with stdin("wat"):
        test = parse(Foo, "-", backend=backend)
        assert test.bar.read() == b"wat"


@backends
def test_stdout(backend, capsys):
    @dataclass
    class Foo:
        bar: Annotated[BinaryIO, cappa.FileMode(mode="w")]

    test = parse(Foo, "-", backend=backend)
    test.bar.write("wat")

    out = capsys.readouterr().out
    assert out == "wat"


@backends
def test_stdout_binary(backend, capsys):
    @dataclass
    class Foo:
        bar: Annotated[BinaryIO, cappa.FileMode(mode="wb")]

    test = parse(Foo, "-", backend=backend)
    test.bar.write(b"wat")

    out = capsys.readouterr().out
    assert out == "wat"


@backends
def test_invalid_mode_dash(backend):
    @dataclass
    class Foo:
        bar: Annotated[BinaryIO, cappa.FileMode(mode="tb")]

    with pytest.raises(cappa.Exit) as e:
        parse(Foo, "-", backend=backend)

    assert e.value.message == "Invalid mode 'tb' with supplied '-' file name."


@backends
def test_invalid_mode(backend):
    @dataclass
    class Foo:
        bar: Annotated[BinaryIO, cappa.FileMode(mode="tb")]

    with pytest.raises(cappa.Exit) as e:
        parse(Foo, "foo.py", backend=backend)

    assert str(e.value.message).startswith("Invalid value for 'bar'")
    assert str(e.value.message).endswith("can't have text and binary mode at once")


@backends
def test_open_oserror(backend):
    @dataclass
    class Foo:
        bar: BinaryIO

    with pytest.raises(cappa.Exit) as e:
        parse(Foo, "thisshouldneverexist.py", backend=backend)

    assert (
        e.value.message
        == "Cannot open thisshouldneverexist.py: [Errno 2] No such file or directory: 'thisshouldneverexist.py'"
    )
