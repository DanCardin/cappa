import example
import pytest


def test_help():
    with pytest.raises(SystemExit):
        example.main(["--help"])
