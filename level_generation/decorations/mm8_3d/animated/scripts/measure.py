"""Row runs (opaque spans, in native units from the frame's centre column) and mean colour of a restored x2 frame,
for tracing the models. Usage: python3 measure.py <x2 file name> [row step in x2 pixels]"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

X2 = Path(__file__).resolve().parents[5] / 'assets_legacy/decorations_x2_mm8_20261016'   # retired from assets_dev


def runs(row):
    xs = np.nonzero(row)[0]
    if len(xs) == 0:
        return []
    out, start, prev = [], xs[0], xs[0]
    for x in xs[1:]:
        if x != prev + 1:
            out.append((start, prev))
            start = x
        prev = x
    out.append((start, prev))
    return out


def main():
    name = sys.argv[1]
    step = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    im = np.array(Image.open(X2 / name).convert('RGBA'))
    a = im[:, :, 3] > 128
    ys = np.nonzero(a.any(1))[0]
    bottom = ys.max()
    centre = a.shape[1] / 2
    print(name, 'x2 size', a.shape[::-1], 'opaque rows', ys.min(), bottom, 'units high', (bottom - ys.min() + 1) / 2)
    for y in range(ys.min(), bottom + 1, step):
        spans = ' '.join(f'{(r0 - centre) / 2:+.1f}..{(r1 + 1 - centre) / 2:+.1f}' for r0, r1 in runs(a[y]))
        col = tuple(int(c) for c in im[y, a[y]][:, :3].mean(0))
        print(f'z={(bottom - y) / 2:6.1f} {spans}  {col}')


if __name__ == '__main__':
    main()
