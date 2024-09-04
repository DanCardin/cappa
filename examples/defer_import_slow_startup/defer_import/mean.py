import pandas

from cappa.output import Output
from defer_import.main import MeanCommand


def calculate_mean(command: MeanCommand, output: Output):
    if not command.numbers:
        output.output("0.0")
        return

    df = pandas.DataFrame(command.numbers)
    output.output(df.mean()[0])
