from cappa.argparse import value_error
from cappa.testing import CommandRunner

runner = CommandRunner(base_args=["test.py"], exit_with=value_error)


def parse(cls, *args):
    return runner.parse(*args, obj=cls)


def invoke(cls, *args, **kwargs):
    return runner.invoke(*args, obj=cls, exit_with=value_error, **kwargs)
