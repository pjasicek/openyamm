#!/usr/bin/env python3
"""The pale strip along the top edge of the fringe (user review r7, 2026-11-04): the skin shell's forehead texels just under the hair
shell's lower edge (a few mm between the skin's top rim and the shell) are pale skin and show as a light line all along the hairline.
Skin-shell texels (part SKIN) within D1 of the hair shell's surface (3D distance to its texels) take the hair shell's local colour
(mean of its 8 nearest hair texels) with the skin texel's own luminance detail damped to DET; weight 1 within D0 easing to 0 at D1.
The scalp under the hair takes the hair colour too (it only shows through gaps). The fringe painted on the forehead (> D1 from the
shell) stays. Reads <prefix>_head_basecolor_prefringe.png (first run or RESET=1).
Args: <glb> <prefix> [--hair 3] [--d0 0.003] [--d1 0.007] [--det 0.4] [--dy 0] [--dz 0]"""
import argparse, os, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpart import texel_parts
ap = argparse.ArgumentParser(); ap.add_argument('glb'); ap.add_argument('prefix')
ap.add_argument('--hair', default='3'); ap.add_argument('--skin', type=int, default=0)
ap.add_argument('--d0', type=float, default=0.003); ap.add_argument('--d1', type=float, default=0.007); ap.add_argument('--det', type=float, default=0.4)
o = ap.parse_args()
f = Path(f'textures/{o.prefix}_head_basecolor.png'); bk = f.with_name(f.stem + '_prefringe.png')
if not bk.exists() or os.environ.get('RESET') == '1':
    shutil.copyfile(f, bk)
H = np.asarray(Image.open(bk).convert('RGB'), float); N = H.shape[0]
ph, part, _ = texel_parts(o.glb, 'PeasantHOFHead', N); P = np.nan_to_num(ph)
hair = np.isin(part, [int(x) for x in o.hair.split(',')]); skin = part == o.skin
hi = np.nonzero(hair); step = max(1, len(hi[0]) // 150000)
tree = cKDTree(P[hi][::step]); HC = H[hi][::step]
si = np.nonzero(skin); d, nn = tree.query(P[si], 8)
w = np.clip((o.d1 - d[:, 0]) / (o.d1 - o.d0), 0, 1); w = w * w * (3 - 2 * w)
col = HC[nn].mean(1)
L = H[si].mean(-1, keepdims=True); Ls = ndimage.gaussian_filter(H.mean(-1), 3)[si][:, None]
det = np.clip(L / np.maximum(Ls, 1), 0.6, 1.4) ** o.det
out = H.copy(); out[si] = H[si] * (1 - w[:, None]) + col * det * w[:, None]
Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(f)
print('FRINGEEDGE', o.prefix, 'skin texels toned', int((w > 0.01).sum()), 'of', len(si[0]))
