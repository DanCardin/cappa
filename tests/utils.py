from cappa.testing import CommandRunner


def value_error(message, code=127):
    raise ValueError(message)


runner = CommandRunner(base_args=["test.py"], exit_with=value_error)


def parse(cls, *args):
    return runner.parse(*args, obj=cls)


def invoke(cls, *args, **kwargs):
    return runner.invoke(*args, obj=cls, exit_with=value_error, **kwargs)
