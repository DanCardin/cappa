from typing import Union
from unittest.mock import patch

import pytest
from cappa.output import Exit
from cappa.parser import backend
from cappa.testing import CommandRunner

backends = pytest.mark.parametrize("backend", [None, backend])

runner = CommandRunner(base_args=[])


def parse(cls, *args, backend=None):
    return runner.parse(*args, obj=cls, backend=backend)


def invoke(cls, *args, **kwargs):
    return runner.invoke(*args, obj=cls, **kwargs)


def parse_completion(cls, *args, location=None) -> Union[str, None]:
    env = {
        "COMPLETION_LINE": " ".join(["test.py", *args]),
        "COMPLETION_LOCATION": location if location is not None else len(args) + 1,
    }
    with patch("os.environ", new=env):
        with pytest.raises(Exit) as e:
            parse(cls, "--completion", "complete", backend=backend)

        assert e.value.code == 0
        if e.value.message:
            return str(e.value.message)
        return None
