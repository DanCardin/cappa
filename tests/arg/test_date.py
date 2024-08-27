from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time

from typing_extensions import Annotated

import cappa
from tests.utils import backends, parse


@backends
def test_datetime(backend):
    @dataclass
    class ArgTest:
        datetime_arg: datetime
        datetime_opt: Annotated[datetime, cappa.Arg(long=True)]

    test = parse(
        ArgTest,
        "2020-01-01T01:02:03",
        "--datetime-opt=2021-02-03T04:05:06",
        backend=backend,
    )
    assert test.datetime_arg == datetime(2020, 1, 1, 1, 2, 3)
    assert test.datetime_opt == datetime(2021, 2, 3, 4, 5, 6)


@backends
def test_date(backend):
    @dataclass
    class ArgTest:
        date_arg: date
        date_opt: Annotated[date, cappa.Arg(long=True)]

    test = parse(ArgTest, "2020-01-01", "--date-opt=2021-02-03", backend=backend)
    assert test.date_arg == date(2020, 1, 1)
    assert test.date_opt == date(2021, 2, 3)


@backends
def test_time(backend):
    @dataclass
    class ArgTest:
        date_arg: time
        date_opt: Annotated[time, cappa.Arg(long=True)]

    test = parse(ArgTest, "01:02:03", "--date-opt=04:05:06", backend=backend)
    assert test.date_arg == time(1, 2, 3)
    assert test.date_opt == time(4, 5, 6)
