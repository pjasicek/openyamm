#!/usr/bin/env python3
"""Repaint the texels of the faces that despike.py reshaped (user review 2026-10-20: the unfolded biceps faces still
carried stretched vest-trim paint, a gold smear on the arm): each takes the median colour of the surrounding surface,
the nearest texels in rest-pose 3D (within RADIUS m) of the same texture set that are not on a reshaped face (body:
uvraster_UVMap.npz, head: uvraster_HeadUV.npz), in the base colour, ORM, region mask and class maps; their normal
becomes flat. Run after compose_m410.py and smooth_skin_normals.py. Args: [RADIUS=0.02]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; T = HERE / 'textures'
RADIUS = float(sys.argv[1]) if len(sys.argv) > 1 else 0.02
M = np.load(HERE / 'work' / 'moved_raster.npz')
SETS = {False: ('UVMap', ['m410_basecolor_1k.png', 'm410_metal_rough_1k.png', 'm410_region_mask.png', 'm410_material_classes.png'], 'm410_normal_1k.png'),
        True: ('HeadUV', ['m410_head_basecolor_1k.png', 'm410_head_metal_rough_1k.png', 'm410_head_region_mask.png', 'm410_head_material_classes.png'], 'm410_head_normal_1k.png')}
for head, (layer, maps, nmap) in SETS.items():
    sel = M['layer'] == head
    if not sel.any():
        continue
    R = np.load(HERE / 'work' / f'uvraster_{layer}.npz'); cov = R['piece'] >= 0
    rows, cols, pos = M['row'][sel], M['col'][sel], M['pos'][sel]
    bad = np.zeros(cov.shape, bool); bad[rows, cols] = True
    src = np.flatnonzero(cov.ravel() & ~bad.ravel()); P = R['pos'].reshape(-1, 3)[src]
    d, j = cKDTree(P).query(pos, k=24, distance_upper_bound=RADIUS)
    ok = np.isfinite(d).any(1)
    for name in maps:
        im = Image.open(T / name); a = np.asarray(im).copy(); flat = a.reshape(len(cov.ravel()), -1)
        for k in np.flatnonzero(ok):
            jj = j[k][np.isfinite(d[k])]
            vals = flat[src[jj]]
            flat[rows[k] * cov.shape[1] + cols[k]] = np.median(vals, 0).astype(a.dtype) if 'classes' not in name else \
                np.bincount(vals.ravel()).argmax()
        Image.fromarray(a, im.mode).save(T / name)
    im = Image.open(T / nmap); a = np.asarray(im.convert('RGB')).copy(); a[rows[ok], cols[ok]] = (128, 128, 255)
    Image.fromarray(a).save(T / nmap)
    print(f'REPAINT {layer}: {int(ok.sum())} of {int(sel.sum())} texels from 3D neighbours within {RADIUS * 100:.0f} cm')
