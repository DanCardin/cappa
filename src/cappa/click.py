# from __future__ import annotations
#
# import typing
#
# import click
#
# if typing.TYPE_CHECKING:
#     from cappa.arg_def import ArgAction
#     from cappa.command_def import CommandDefinition
#
#
# def render(
#     command_def: CommandDefinition, argv: list[str], exit_with=None
# ) -> dict[str, typing.Any]:
#     parser = create_parser(command_def, exit_with)
#
#     try:
#         args = parser.make_context("", argv)
#     except SystemExit as e:
#         if exit_with is not None:
#             exit_with(e)
#     else:
#         return args.__dict__
#
#
# def create_parser(command_def: CommandDefinition, exit_with=None) -> click.Group:
#     parser = click.Group(
#         name=command_def.command.name,
#         help=command_def.command.help,
#     )
#
#     add_arguments(parser, command_def)
#     return parser
#
#
# def add_arguments(parser: click.Group, command_def: CommandDefinition):
#     for arg_def in command_def.arguments:
#         dash_name = arg_def.name.replace("_", "-")
#         names = []
#         if arg_def.arg.short:
#             short_name = arg_def.arg.short
#             if not isinstance(arg_def.arg.short, str):
#                 short_name = f"-{dash_name[0]}"
#             names.append(short_name)
#
#         if arg_def.arg.long:
#             long_name = arg_def.arg.long
#             if not isinstance(arg_def.arg.long, str):
#                 long_name = f"--{dash_name}"
#
#             names.append(long_name)
#
#         num_args = render_num_args(arg_def.num_args)
#         action = render_action(arg_def.action)
#         kwargs: dict[str, typing.Any] = dict(
#             **action,
#         )
#
#         if arg_def.arg.default is not ...:
#             kwargs["default"] = arg_def.arg.default
#
#         if arg_def.action is not arg_def.action.store_true:
#             kwargs["nargs"] = num_args
#             kwargs["type"] = arg_def.arg.parser
#
#         if names:
#             param = click.Option(
#                 [
#                     arg_def.name,
#                     *names,
#                 ],
#                 **kwargs,
#                 help=arg_def.arg.help,
#             )
#         else:
#             param = click.Argument(
#                 arg_def.name,
#                 **kwargs,
#             )
#
#         # breakpoint()
#
#         parser.params.append(param)
#
#     if command_def.subcommands:
#         for subcommand in command_def.subcommands.options:
#             subparser = click.Group(
#                 name=subcommand.command.real_name(),
#                 help=subcommand.command.help,
#             )
#             parser.add_command(subparser)
#             add_arguments(subparser, subcommand)
#
#
# def render_action(action: ArgAction):
#     mapping = {
#         action.set: {},
#         action.append: {"multiple": True},
#         action.store_true: {"is_flag": True},
#         action.count: {"count": True},
#     }
#     return mapping[action]
#
#
# def render_num_args(num_args: int | None) -> int | str | None:
#     if num_args is None:
#         return None
#
#     if num_args == -1:
#         return "+"
#
#     return num_args
