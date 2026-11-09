#!/usr/bin/env python3
"""Keep set = work/keep_hand.npy + the collar (torso faces wholly above y 1.58 in the rest pose: the white stand-up collar
round the neck, the cloth_gate's collar band). The collar frames every face close-up; cut with the torso it shifted its
shading beside the chin. Writes work/keep_e2.npy."""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
d, b = glbio.read(HERE / 'before' / 'mm9_nosferatu.glb'); p = glbio.prims(d, b, 0)[0]
g = np.load(HERE / 'work' / 'glb_parts.npz'); names = [str(x) for x in g['names']]; part = g['part'][g['mat'] == 0]
P = p['POSITION'].astype(float); T = p['T']
collar = (part == names.index('torso')) & (P[T][:, :, 1].min(1) > 1.58)
keep = np.load(HERE / 'work' / 'keep_hand.npy') | collar
print('COLLAR', int(collar.sum()), 'keep total', int(keep.sum()))
np.save(HERE / 'work' / 'keep_e2.npy', keep)
