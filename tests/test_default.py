from cappa.default import Confirm, Default, Env, Prompt, ValueFrom
from cappa.type_view import Empty


def test_default_combination():
    assert Default().fallback(Default()) == Default()
    assert (Default() | Default()) == Default()

    assert Env("FOO") | Env("BAR") == Default(Env("FOO"), Env("BAR"), default=Empty)
    assert Default(default=4) | Env("FOO") == Default(Env("FOO"), default=4)
    assert Env("FOO") | ValueFrom(int) == Default(Env("FOO"), ValueFrom(int))

    prompt = Prompt("FOO")
    confirm = Confirm("BAR")
    assert Default() | prompt | confirm == Default(prompt, confirm)


def test_default_eval():
    default = Default()
    assert default() == (True, None)

    default = Default(Env("FOO"))
    assert default() == (True, None)

    default = Default(Env("FOO", default="foo"))
    assert default() == (False, "foo")

    default = Default(Env("FOO"), Env("BAR"), Env("BAZ", default="okay"))
    assert default() == (False, "okay")


def test_value_from():
    def fn():
        return 5

    default = ValueFrom(fn)
    assert default() == 5

    def fn2(value):
        return value + 5

    default = ValueFrom(fn2, value=4)
    assert default() == 9

    def fn3(*, value: int):
        return value + 5

    default = ValueFrom(fn3, value=4)
    assert default() == 9
