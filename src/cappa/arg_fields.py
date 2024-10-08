from __future__ import annotations

import enum
from dataclasses import dataclass, field
from functools import cached_property
from typing import TYPE_CHECKING, Callable, TypeVar, Union

from typing_extensions import TypeAlias

if TYPE_CHECKING:
    pass


@enum.unique
class ArgAction(enum.Enum):
    """`Arg` action typee.

    Options:
      - set: Stores the given CLI value directly.
      - store_true: Stores a literal `True` value, causing options to not attempt to
        consume additional CLI arguments
      - store_false: Stores a literal `False` value, causing options to not attempt to
        consume additional CLI arguments
      - append: Produces a list, and accumulates the given value on top of prior values.
      - count: Increments an integer starting at 0
      - help: Cancels argument parsing and prints the help text
      - version: Cancels argument parsing and prints the CLI version
      - completion: Cancels argument parsing and enters "completion mode"
    """

    set = "store"
    store_true = "store_true"
    store_false = "store_false"
    append = "append"
    count = "count"

    help = "help"
    version = "version"
    completion = "completion"

    @classmethod
    def meta_actions(cls) -> set[ArgAction]:
        return {cls.help, cls.version, cls.completion}

    @classmethod
    def is_custom(cls, action: ArgAction | Callable | None):
        return action is not None and not isinstance(action, ArgAction)

    @classmethod
    def is_non_value_consuming(cls, action: ArgAction | Callable | None):
        return action in {
            ArgAction.store_true,
            ArgAction.store_false,
            ArgAction.count,
            ArgAction.version,
            ArgAction.help,
        }

    @property
    def is_bool_action(self):
        return self in {self.store_true, self.store_false}


T = TypeVar("T")
ArgActionType: TypeAlias = Union[ArgAction, Callable]


@dataclass(frozen=True)
class Group:
    """Object used to control argument/subcommand grouping in generated help text.

    Args:
        order: A number representing the relative ordering among different argument
            groups. Groups with the same order will be displayed alphabetically by
            name.
        name: The display name of the group in help text.
        exclusive: Whether arguments in the group should be considered mutually exclusive
            of one another.
        section: A secondary level of ordering. Sections have a higher order precedence
            than ``order``, in order to facilitate meta-ordering amongst kinds of groups
            (such as "meta" arguments (``--help``, ``--version``, etc) and subcommands).
            The default ``section`` for any normal argument/``Group`` is 0, for
            ``Subcommand``s it is 1, and for "meta" arguments it is 2.
    """

    order: int = field(default=0, compare=False)
    name: str = ""
    exclusive: bool = False
    section: int = 0

    @cached_property
    def key(self):
        return (self.section, self.order, self.name, self.exclusive)
