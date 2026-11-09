#!/usr/bin/env python3
"""Grey specks on the lower face (user review 2026-11-02: "a dark smudge on the chin below the lower lip, like a goatee
shadow"). Meshy's head paint carries grey, unsaturated triangles just under the lower lip on both sides of the chin
(0.5-1.0 cm off the midline, 1-2 cm below the lip; the same marks on the split islands of both halves; MM9's face and
the head masters are clean there). Texels of the lower-face skin (head-set triangles in front of the face between the
throat and the nose base, rasterised in UV) that are darker than SHADE x and less saturated than SAT x the local skin
(normalised Gaussian of the clean skin texels, sigma SIG px) are replaced, also in the islands' gutters up to GUT px
(most of the marks sit in the gutter and bleed in at the triangle edges under mip filtering; hair-dark texels below
0.6 x the skin are never touched), by that local skin colour, grown 4 px and feathered 1 px.
Lips (saturated) and hair (outside the mask) are not touched. Reads textures/kira_head_final_r7.png (the r7 paint),
writes textures/kira_head_final.png. Args: <glb with the current head UVs> [shade 0.9] [sat 0.85]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
glb = sys.argv[1]; SHADE = float(sys.argv[2]) if len(sys.argv) > 2 else 0.9; SAT = float(sys.argv[3]) if len(sys.argv) > 3 else 0.85
SIG = 6.0; GUT = 12
here = Path(__file__).resolve().parents[1]
g = Glb(glb); m = Model(g); doc = g.json
k = next(i for i, p in enumerate(m.primitives) if p['positions'][:, 1].min() > 1.2)
mesh = doc['meshes'][doc['nodes'][m.primitives[k]['node']]['mesh']]
pr = [p for p in mesh['primitives'] if doc['accessors'][p['attributes']['POSITION']]['count'] == len(m.primitives[k]['positions'])][0]
uv = g.accessor(pr['attributes']['TEXCOORD_0']); P = m.primitives[k]['positions']; T = m.primitives[k]['triangles']
C = P[T].mean(1)
reg = (C[:, 2] > 0.03) & (C[:, 1] > 1.555) & (C[:, 1] < 1.64) & (np.abs(C[:, 0]) < 0.035)   # chin, mouth; not the ears
src = Image.open(here / 'textures/kira_head_final_r7.png').convert('RGB'); S = src.size[0]
a = np.asarray(src).astype(float)
mask = Image.new('L', src.size, 0); dr = ImageDraw.Draw(mask)
for t in T[reg]:
    if np.ptp(uv[t], axis=0).max() > 1e-4: dr.polygon([tuple(uv[v] * S) for v in t], fill=255)
mk = np.asarray(mask) > 0
L = a @ [0.299, 0.587, 0.114]; sat = a.max(2) - a.min(2)
def nconv(x, w): return ndimage.gaussian_filter(x * w, SIG) / np.maximum(ndimage.gaussian_filter(w, SIG), 1e-6)
w0 = mk.astype(float)
refL, refS = nconv(L, w0), nconv(sat, w0)
zone = ndimage.binary_dilation(mk, iterations=GUT)          # the islands' gutters too: a blob there bleeds in at the edge
refL, refS = nconv(L, w0), nconv(sat, w0)
spot = zone & (L < refL * SHADE) & (L > refL * 0.6) & (sat < refS * SAT)
spot = ndimage.binary_dilation(spot, iterations=4) & zone & (L > refL * 0.6)
clean = (mk & ~spot).astype(float)
ref = np.dstack([nconv(a[..., c], clean) for c in range(3)])
f = ndimage.gaussian_filter(spot.astype(float), 1.0) * zone
out = a * (1 - f[..., None]) + ref * f[..., None]
Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8)).save(here / 'textures/kira_head_final.png')
lab, n = ndimage.label(spot)
print('CHINPAINT mask texels', int(mk.sum()), 'spot texels', int(spot.sum()), 'spots', n,
      [(int(x.mean()), int(y.mean()), len(x)) for x, y in ((np.where(lab == i)[1], np.where(lab == i)[0]) for i in range(1, n + 1)) if len(x) > 8])
