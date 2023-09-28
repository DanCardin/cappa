from __future__ import annotations

try:
    import rich
    import rich.prompt
    from rich.console import Console
except ImportError:  # pragma: no cover
    print = None
    prompt_types: tuple[type, ...] = ()
else:
    import io

    print = rich.print
    prompt_types = (rich.prompt.Prompt, rich.prompt.Confirm)

    class TestPrompt(rich.prompt.Prompt):
        def __init__(self, prompt, *, input, default=..., **kwargs):
            self.file = io.StringIO()
            self.default = default
            self.stream = io.StringIO(input)

            console = Console(file=self.file)
            super().__init__(prompt=prompt, console=console, **kwargs)

        def __call__(self):
            return super().__call__(default=self.default, stream=self.stream)
