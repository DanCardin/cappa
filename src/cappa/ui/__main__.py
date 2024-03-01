import sys

from cappa.ui import run

cls = __import__(sys.argv[1])

run(cls)
