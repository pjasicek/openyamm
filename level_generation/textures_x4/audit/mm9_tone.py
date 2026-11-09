#!/usr/bin/env python3
"""Per-shot brightness of x4 tour shots against the native ones: mm9_tone.py MAP [MAP...] (under mm9_shots/).

Prints the median and extremes of the mean-luma ratio x4/native over each map's shots (HUD rows cropped), and the
shots below 0.93 or above 1.07, the ones to look at for a tone step."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

SHOTS = Path(__file__).resolve().parent / 'mm9_shots'
for name in sys.argv[1:]:
    ratios = []
    for native in sorted((SHOTS / name / 'native' / name).glob('[0-9]*.png')):
        x4 = SHOTS / name / 'x4' / name / native.name
        if not x4.exists():
            continue
        a = np.asarray(Image.open(native).convert('L'), float)[60:-150]
        b = np.asarray(Image.open(x4).convert('L'), float)[60:-150]
        ratios.append((round(b.mean() / max(a.mean(), 1), 3), native.stem))
    if not ratios:
        print(name, 'no pairs')
        continue
    values = [value for value, _ in ratios]
    outliers = [f'{stem} {value}' for value, stem in ratios if value < 0.93 or value > 1.07]
    print(f'{name}: {len(ratios)} shots, median {np.median(values):.2f}, range {min(values):.2f}-{max(values):.2f}',
          '; outliers: ' + ', '.join(outliers) if outliers else '')
