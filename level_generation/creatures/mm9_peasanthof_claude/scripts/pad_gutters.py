#!/usr/bin/env python3
"""Re-pad a texture's gutters after paint edits (user review r7, 2026-11-04: thin light lines down the cheek near the ear and on the
chin, still there with the normal map flat and the vertex normals averaged: the later paint steps (neck_even, ear_tone,
skin_seam_blend, ...) changed the islands but not the gutter texels around them, so bilinear and mip sampling at the UV seams mixed
in the old, lighter padding). Every texel no triangle of MATERIAL covers takes the colour of its nearest covered texel.
Args: <glb> <material> <png> [--grow 0] (grow: covered texels within N of a gutter also re-sampled from 1 texel deeper)"""
import argparse, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
ap = argparse.ArgumentParser(); ap.add_argument('glb'); ap.add_argument('material'); ap.add_argument('png')
o = ap.parse_args()
im = Image.open(o.png); mode = im.mode; I = np.asarray(im.convert('RGB'))
_, cov = texel_positions(o.glb, o.material, I.shape[0])
cov = ndimage.binary_erosion(cov, iterations=1) | (cov & ~ndimage.binary_erosion(cov, iterations=1))   # (the covered set itself)
idx = ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True)
out = I[idx[0], idx[1]]
changed = int((np.abs(out.astype(int) - I.astype(int)).sum(-1) > 6).sum())
Image.fromarray(out).save(o.png)
print('PADGUTTERS', o.png, 'covered', int(cov.sum()), 'gutter texels changed', changed)
