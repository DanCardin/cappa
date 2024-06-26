# Changelog

## 0.22.0

- feat: Allow "attribute docstrings" as additional method of documenting args.

## 0.21

### 0.21.2
- fix: action inference when `default` is an `Env`.

### 0.21.1

- feat: Update automatic inference to support `date`, `time`, and `datetime` parsing (for isoformat).

### 0.21.0

- feat: Add `help_formatter` system wherein help text rendering can be customized
  to include or exclude things like default values, or choices. Notably changes
  to include default values in help text by default.

## 0.20

### 0.20.1

- feat: Improve union error message.

### 0.20.0

- feat: Implement exclusive argument groups.

## 0.19

### 0.19.1

- fix: Eagerly attempt pydantic BaseModel import to ensure its skipped if unavailable.

### 0.19.0

- feat: Add support for `msgspec` based class definitions.

## 0.18

### 0.18.1

- feat: Add deprecated option to command/arg.

## 0.18

## 0.18.1

- feat: Add `deprecated` option, allowing deprecation of args, options, and subcommands
>>>>>>> 142825c (feat: Implement exclusive groups.)

### 0.18.0

- feat: Add `default_short=False` and `default_long=False` options to command
  for ease of defining option-heavy commands.

## 0.17

### 0.17.3

- fix: Ensure class default combined with `default=Env(...)` still attempts to
  read env var (rather than just unconditionally taking the class default).

### 0.17.2

- Increase minimum typing_extensions bound to reflect actual dependency.

### 0.17.1

- Fixes bounded-tuple options like `tuple[str, str]` to infer as `num_args=2`
- Fixes bounded-tuple options to fail parsing if you give it a different number
  of values
- Fixes "double sequence" inference on explicit `num_args=N` values which would
  produce sequences. I.e. infer `action=ArgAction.set` in such cases to avoid
  e.x. `num_args=3, action=ArgAction.append`; resulting in nonsensical nested
  sequence `["[]"]`

### 0.17.0

- feat: Add `hidden=True/False` option to Command, which allows hiding
  individual subcommands options.

## 0.16

### 0.16.6

- fix: Correct the testing.CommandRunner deps signature.

### 0.16.5

- fix: Error short help should be contextual to the failing command.

### 0.16.4

- fix: Ensure optional bool retains bool action inference.

### 0.16.3

- fix: Use eval_type_backport to allow new syntax in python 3.8/9.

### 0.16.2

- feat: Improve parse error formatting. Include short help by default.

### 0.16.1

- feat: Support `Dep` on function based commands.

### 0.16.0

- feat: Add support for `BinaryIO` and `TextIO` for representing preconfigured
  file objects to be returned the caller.

## 0.15

### 0.15.4

- feat: Support pydantic v1.

### 0.15.3

- fix: Incorrect error message when using an invalid base class type.

### 0.15.2

- fix: Process `action` inference, taking into account `Optional`/`| None`.

### 0.15.1

- feat: Support explicit context managers as invoke dependencies.

### 0.15.0

- feat: Add docutils directive extension.

## 0.14

### 0.14.3

- fix: Handle TypeError in mapping failures

### 0.14.2

- fix: Default bool fields to `False` when omitted.

### 0.14.1

- fix: zsh completion script error

### 0.14.0

- feat: Support functions as interface for simple CLIs.

## 0.13

### 0.13.2

- Support "discriminated unions" (i.e. unions which have type distinctions that
  affect how they're mapped.)

### 0.13.1

- Prefer the field default (if set), if an `Env` is used, but no default is
  supplied.

### 0.13.0

- Support `yield` in invoke dependencies to support context-manager-like
  dependencies (for example those which require cleanup).

## 0.12

### 0.12.1

- When used in combination with `parse=...`, handle the "optional" part of
  `T | None` **before** `parse`.

### 0.12.0

- Add `invoke_async` to support async invoke functions and dependencies

## 0.11

### 0.11.6

- Disallow certain combinations of apparently incompatible annotations, i.e.
  sequences and scalars

### 0.11.5

- Fix double dash following an invalid option (with num_args>0)

### 0.11.4

- Fix num_args=-1 on options

### 0.11.3

- Continue to parse docstrings without docstring_parser extra
- Fix rendering issue with markdown in docstrings

### 0.11.2

- Make docstring_parser dependency optional
- Fix parser error if option followed unknown argument

### 0.11.1

- (Hopefully) Configure rich properly to deal with line overflow when printing
  terminal escape codes.

### 0.11.0

- Add option for explicit Output object, and add `error_format` option to allow
  customizing output formatting.

## 0.10

### 0.10.2

- Disallow explicit `required=False` in combination with the lack of a field
  level default.

### 0.10.1

- Fix regression resulting from `value_name`/`field_name` split.

### 0.10.0

- Split Arg `value_name`/`field_name`. `value_name` controls help/error output
  naming. `field_name` controls the the destination field on the dataclass
  object.

## 0.9

### 0.9.3

- Ensure output of missing required options is deterministically ordered
- Output all required options when listing out missing required options
- Fix ignore num_args=0 override

### 0.9.2

- Invoke the specific callable subcommand instance being targeted.

### 0.9.1

- Supply the parsed Command instance as an invoke dependency.

### 0.9.0

- Change default backend to `cappa.parser.backend`. To opt into argparse
  backend, explicitly supply it with `backend=cappa.argparse.backend`.

## 0.8

### 0.8.9

- Avoid mutating command when adding meta arguments
- Avoid setting global NO_COLOR env var when disabling color

### 0.8.8

- Clean up help text output formatting
- Show rich-style help text when using argparse backend

### 0.8.7

- Allow defining custom callable as an `action`.
- Improve behavior consuming concatenated short arguments

### 0.8.6

- Improve behavior consuming concatenated short arguments

### 0.8.5

- Add metadata to package distribution

### 0.8.4

- Loosen dependency version specifiers

### 0.8.3

- Fix `Literal["one", "two"]` syntax vs `Literal["one"] | Literal["two"]`
- Apply custom completions to already "valid" arguments values
- Deduplicate the --completion helptext choices

### 0.8.2

- The command's name should now always translate to the prog name
- Explicitly provided argv should now **not** include the prog name

### 0.8.1

- Correct the version long name when long=True.

### 0.8.0

- Implement support for PEP-727 help text inference.

## 0.7

### 0.7.1

- Provide clear error message when a version Arg is supplied without a name.
- Documentation updates

### 0.7.0

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
