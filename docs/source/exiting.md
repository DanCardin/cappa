# Exiting and Exit Codes

Cappa provides an [Exit](cappa.Exit) class to allow someone to gracefully exit
the program, without emitting a traceback.

```python
import cappa

def function():
    ...
    raise cappa.Exit(message="Oh no!", code=1)
    # or
    raise cappa.Exit("Oh no!", code=1)
    # or
    raise cappa.Exit(code=1)
    # or
    raise cappa.Exit("Graceful exit")  # i.e. status code 0!

@cappa.command(invoke=function)
...
```
