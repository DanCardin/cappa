# Changelog

## 0.8.7

- Allow defining custom callable as an `action`.
- Improve behavior consuming concatenated short arguments

## 0.8.6

- Improve behavior consuming concatenated short arguments

## 0.8.5

- Add metadata to package distribution

## 0.8.4

- Loosen dependency version specifiers

## 0.8.3

- Fix `Literal["one", "two"]` syntax vs `Literal["one"] | Literal["two"]`
- Apply custom completions to already "valid" arguments values
- Deduplicate the --completion helptext choices

## 0.8.2

- The command's name should now always translate to the prog name
- Explicitly provided argv should now **not** include the prog name

## 0.8.1

- Correct the version long name when long=True.

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
