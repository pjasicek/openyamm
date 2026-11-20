#!/usr/bin/env python3
"""DF2's kerchief hem (MM9 PeasantDF2b: a narrow dark embroidered band along the kerchief's lower edge): head-set texels of
the hair/kerchief part within BAND of the shell's lowest point at their angle round the head axis take a darker band
with small stitched lozenges (the kerchief ramp recolours it with the rest of the cloth, so it stays a darker band).
Usage (project folder): kerchief_hem.py <export glb> <prefix> [--band 0.02]"""
import argparse, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpart import texel_parts
ap = argparse.ArgumentParser(); ap.add_argument('glb'); ap.add_argument('prefix'); ap.add_argument('--band', type=float, default=0.02)
o = ap.parse_args()
f = Path(f'textures/{o.prefix}_head_basecolor.png')
H = np.asarray(Image.open(f).convert('RGB'), float)
pos, part, _ = texel_parts(o.glb, 'PeasantDFHead', H.shape[0]); P = np.nan_to_num(pos)
hair = part == 1
ang = np.degrees(np.arctan2(P[..., 0], P[..., 2])) % 360
bins = (ang // 10).astype(int)
low = np.full(36, 9.0)
for b in range(36):
    m = hair & (bins == b)
    if m.any(): low[b] = P[m, 1].min()
d = P[..., 1] - low[bins]
band = hair & (d < o.band) & (d > 0.004) & (P[..., 2] < 0.01)   # back and sides only (r4: at the front it pinked the face opening)
# lozenges: along the hem (angle) and across it (height)
t = ang / 360 * 90; q = (d - 0.004) / max(o.band - 0.004, 1e-6)
loz = (np.abs((t % 1.0) - 0.5) + np.abs(q - 0.5)) < 0.32
w = ndimage.gaussian_filter(band.astype(float), 0.8) * np.clip((0.01 - P[..., 2]) / 0.03, 0, 1)
dark = np.where(loz, 0.45, 0.68)
H2 = H * (1 - w[..., None]) + H * dark[..., None] * w[..., None]
Image.fromarray(np.uint8(np.clip(np.round(H2), 0, 255))).save(f)
print('KERCHIEFHEM', o.prefix, int(band.sum()))
