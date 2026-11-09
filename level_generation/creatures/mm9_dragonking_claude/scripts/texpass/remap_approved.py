#!/usr/bin/env python3
"""Approved graded colours resampled onto the new layouts, for comparisons and the tone pin (body, head)."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import tp
HERE = Path(__file__).resolve().parents[2]
W, B = HERE / 'work' / 'texpass', HERE / 'work' / 'before_texpass' / 'textures'
for name, old in (('body', 'dragonking_basecolor_graded.png'), ('head', 'dragonking_head_basecolor.png')):
    out, cover = tp.resample(tp.load(B / old), np.load(W / f'pairs_{name}.npz'), 2048)
    tp.save(out, W / f'{name}_approved_remap.png')
    np.save(W / f'{name}_cover.npy', cover)
