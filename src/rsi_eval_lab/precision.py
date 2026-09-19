"""The precision a computed difference is compared at.

Every threshold in this auditor is a declaration: a gap of 0.05 or more is worth
reporting, a score within 0.05 below a gate is close to it, a drop of more than 0.05 is a
regression. Whether a gap of exactly 0.05 counts should be answerable by reading the
declaration. It was not.

Comparing a score straight against a threshold is exact, because both sides are decimals
the file supplied and the same decimal parses to the same double. The trouble is a
difference the tool computed first:

    >>> 0.83 - 0.78
    0.04999999999999993
    >>> 0.55 - 0.50
    0.050000000000000044

Two gaps a reader would call identical, on opposite sides of a declared 0.05. Across
scores at two decimal places and thresholds from 0.01 to 0.20, that put 661 of 1810
exactly-at-the-boundary pairs on the wrong side of the gate margin and 654 on the wrong
side of the paired-gap tolerance.

`scorecard.py` already avoided this by rounding each difference where it is computed, so
its plateau boundary was always exact. This states that rule once, at the precision it
already used, for the modules that did not.

The rule, which is the point: a difference is compared at four decimal places, so a value
exactly at a declared boundary is on the inside of it. Scores are bounded to 0 and 1 and
are written at two or three places in practice, so four is far below anything a trace
means to express and far above where doubles stop being reliable.
"""

from __future__ import annotations

COMPARISON_PLACES = 4


def difference(minuend: float, subtrahend: float) -> float:
    """`minuend - subtrahend`, at the precision thresholds are compared at.

    Use this wherever a subtraction is about to meet a declared threshold. Comparing the
    raw subtraction makes the answer depend on which decimals happened to be involved,
    which is not a thing the declaration can be read to say.

    The result keeps its sign and the arguments are not required to be in any order;
    callers pass the earlier score first and read a rise as negative.
    """
    return round(minuend - subtrahend, COMPARISON_PLACES)
