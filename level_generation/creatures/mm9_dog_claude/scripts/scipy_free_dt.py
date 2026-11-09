"""Largest empty square of a bool mask (numpy only: Blender's python has no scipy)."""
import numpy as np


def largest_square(mask):
    """Centre x, y and half size of the largest all-False square of mask (dynamic programming)."""
    h, w = mask.shape
    d = np.zeros((h, w), np.int32)
    for y in range(h):
        row = ~mask[y]
        if y == 0:
            d[y] = row
            continue
        for x in range(w):
            if row[x]:
                d[y, x] = 1 + (min(d[y - 1, x], d[y, x - 1], d[y - 1, x - 1]) if x else 0)
    y, x = np.unravel_index(d.argmax(), d.shape)
    s = int(d[y, x])
    return x - s / 2, y - s / 2, s / 2
