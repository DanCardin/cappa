# Changelog

## 0.8.0

- Implement support for PEP-727 help text inference.

## 0.7.1

- Provide clear error message when a version Arg is supplied without a name.
- Documentation updates

## 0.7.0

- Adds native cappa parser option vs argparse
- Renames render option to "backend"
- Collapse separate `Subcommands` abstraction into Subcommand
- Renames `Subcmd` to `Subcommands`
- Adds support for autocompletion when using new parser
- Removes "rich" extra

  - Adds rich as a required extra dependency

    - It is core to custom/colored help formatting for new parser, and the now
      more-unified stdout/stderr output.

  - rich-argparse needs to now be installed separately, if used

- Adds a new `Output` implicit dependency option
- Adds new theme option (currently only applied to custom parser)
- Adds group option to `Arg` to control how arguments are grouped together in
  help text
- Adds hidden option to `Arg`, to hide arguments from help text.
- Ensures `help=` applies to all levels of subcommands
