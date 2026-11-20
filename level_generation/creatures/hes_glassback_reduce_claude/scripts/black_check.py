#!/usr/bin/env python3
"""Black clay pixels a candidate has where the source has none (a fold or crack showing the body's inside): per
close-up spot of review/glbclose/<label>_<spot>_clay.png against src. Usage: black_check.py <label...>"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
R = Path(__file__).resolve().parents[1] / 'review' / 'glbclose'
for lab in sys.argv[1:]:
    out = []
    for p in sorted(R.glob(f'{lab}_*_clay.png')):
        spot = p.name[len(lab) + 1:-9]; s = R / f'src_{spot}_clay.png'
        a = np.asarray(Image.open(p).convert('L')).astype(int); b = np.asarray(Image.open(s).convert('L')).astype(int)
        n = int(((a < 25) & (b > 60)).sum())
        if n > 4:
            ys, xs = np.nonzero((a < 25) & (b > 60)); out.append(f'{spot}:{n}px@{int(xs.mean())},{int(ys.mean())}')
    print('BLACK', lab, ' '.join(out) or 'none')
