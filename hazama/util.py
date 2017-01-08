"""Common util codes."""
from math import fabs, floor, copysign


def my_fround(x):
    """Similar to built-in round, Numbers like 1.5
    will be rounded to smaller one (1.0)."""
    x = float(x)
    absx = fabs(x)
    y = floor(x)
    if absx - y > 0.5:
        y += 1.0
    return copysign(y, x)
