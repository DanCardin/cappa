from cappa.completion.types import ShellHandler

shells = [
    ShellHandler(
        "bash",
        template="""\
_%(safe_prog_name)s_completion() {
    local IFS=$'\\n' local response
    response=$(env COMPLETION_LINE="${COMP_WORDS[*]}" COMPLETION_LOCATION=$((COMP_CWORD+1)) $1 --completion=complete)

    for completion in $response; do
        IFS=':' read value help <<< "$completion"

        if [[ $type == 'file' ]]; then
            COMPREPLY=()
            compopt -o default
        else
            COMPREPLY+=($value)
        fi
    done
    return 0
}

_%(safe_prog_name)s_completion_setup() {
    complete -o nosort -F _%(safe_prog_name)s_completion %(prog_name)s
}

_%(safe_prog_name)s_completion_setup;
        """,
    ),
    ShellHandler(
        "zsh",
        template="""\
#compdef %(prog_name)s

_%(safe_prog_name)s_completion() {
    local -a completions
    local -a response
    (( ! $+commands[%(prog_name)s] )) && return 1

    response=("${(@f)$(env COMPLETION_LINE="${words[*]}" COMPLETION_LOCATION=$((CURRENT)) \
%(prog_name)s %(completion_arg)s=complete)}")

    if [[ -n "$completions" ]]; then
        if [[ "${completions[1]}" == "file" ]]; then
            _files
        else
            _describe 'options' completions
        fi
    fi
}

if [[ $zsh_eval_context[-1] == loadautofunc ]]; then
    _%(safe_prog_name)s_completion "$@"
else
    compdef _%(safe_prog_name)s_completion %(prog_name)s
fi
""",
    ),
    ShellHandler(
        "fish",
        template="""\
function _%(safe_prog_name)s_completion
    set -l response (env COMPLETION_LINE=(commandline -cp) COMPLETION_LOCATION=(math (commandline -C) + 1) \
%(prog_name)s %(completion_arg)s=complete)

    for completion in $response
        set -l value (string split --max 1 ":" -- $completion)

        if test $value[1] = "file"
            __fish_complete_path
        else
            echo $value[2]
        end
    end
end

complete --no-files --command %(prog_name)s --arguments "(_%(safe_prog_name)s_completion)"
""",
    ),
]
available_shells = {s.name: s for s in shells}
