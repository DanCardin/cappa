import pandas

from cappa.output import Output
from defer_import.main import MeanCommand


def calculate_mean(command: MeanCommand, output: Output):
    if not command.numbers:
        output.output("0.0")
        return

    series = pandas.Series(command.numbers)
    result = float(series.mean())
    output.output(result)
