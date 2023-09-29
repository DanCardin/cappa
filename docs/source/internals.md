# Internals

Internally, cappa is (currently) implemented on top of the built-in `argparse`
library. Argparse appears to have the most direct API that enables it to be
built on top of relatively easily.

However, there **should** be no API edges that leak argparse-isms. Being based
on argparse should be considered an implementation detail. Ideally a different
backend should and will be supported at some point.
