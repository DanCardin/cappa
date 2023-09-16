import cappa
from cappa.argparse import value_error


def parse(cls, *args):
    return cappa.parse(cls, argv=["test.py", *args], exit_with=value_error)


def invoke(cls, *args):
    return cappa.invoke(cls, argv=["test.py", *args], exit_with=value_error)
