#!/usr/bin/env python3
"""Skin paint on the sleeves (user review 2026-11-01, "hands sticking through the sleeves"): besides the grafted stub poking
out (sleeve_tuck.py), the 4K body retexture painted skin-coloured wedges onto the sleeve cloth just above the cuffs, where
the HD masters' wrists crossed the sleeve. Body-set texels whose surface point lies within REACH of a hand joint and that are
skin-coloured (warm orange hue, saturation 0.25-0.75, brighter than the cloth) take the colour of the nearest cloth texel
of the same region, then a 1 px blend. Reads the runtime GLB for texel positions (LOD0 body primitive, bind pose) and
textures/mk_tp_basecolor_graded.png (the ungraded original kept as work/mk_tp_basecolor_graded_orig.png on the first run).
Usage (project folder): sleeve_paint_fix.py <runtime glb> [reach 0.12]"""
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402

GLBP = sys.argv[1]
REACH = float(sys.argv[2]) if len(sys.argv) > 2 else 0.12
SRC = Path('work/mk_tp_basecolor_graded_orig.png')
OUT = Path('textures/mk_tp_basecolor_graded.png')
if not SRC.exists():
    shutil.copyfile(OUT, SRC)
img = np.asarray(Image.open(SRC).convert('RGB')).astype(np.float64) / 255
N = img.shape[0]
glb = Glb(Path(GLBP)); model = Model(glb)
doc = glb.json
names = [n.get('name') for n in doc['nodes']]
idx = {n: i for i, n in enumerate(names)}
W = model.world({})
hands = [W[idx[f'Bip01 {s} Hand']][:3, 3] for s in 'LR']
node0 = model.primitives[0]['node']
mesh = doc['meshes'][doc['nodes'][node0]['mesh']]
k_body = next(i for i, p in enumerate(mesh['primitives']) if 'Head' not in doc['materials'][p.get('material', 0)]['name'])
pr = model.primitives[k_body]
X = model.skinned_positions(W)[k_body][0]
uv = glb.accessor(mesh['primitives'][k_body]['attributes']['TEXCOORD_0']).astype(np.float64)
I = pr['triangles']
near_tri = np.min([np.linalg.norm(X[I].mean(1) - h, axis=1) for h in hands], axis=0) < REACH
pos_near = np.zeros((N, N), bool)
for tri in I[near_tri]:
    q = uv[tri] * N
    x0, y0 = np.floor(q.min(0)).astype(int); x1, y1 = np.ceil(q.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, N)), np.arange(max(y0, 0), min(y1, N)))
    if xs.size == 0:
        continue
    pts = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
    a, b, c = q
    m = np.array([[b[0] - a[0], c[0] - a[0]], [b[1] - a[1], c[1] - a[1]]])
    if abs(np.linalg.det(m)) < 1e-12:
        continue
    l = np.linalg.solve(m, (pts - a).T).T
    ok = (l >= -0.02).all(1) & (l.sum(1) <= 1.02)
    pos_near[pts[ok, 1].astype(int), pts[ok, 0].astype(int)] = True
mx, mn = img.max(2), img.min(2)
sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
r, g, bb = img[..., 0], img[..., 1], img[..., 2]
hue_ok = (r > g * 1.12) & (g > bb * 1.05)
lum = img @ np.array([0.299, 0.587, 0.114])
skin = pos_near & hue_ok & (sat > 0.25) & (sat < 0.78) & (lum > 0.30)
skin = ndi.binary_opening(skin, iterations=1)
skin = ndi.binary_dilation(skin, iterations=2) & pos_near
cloth = pos_near & ~ndi.binary_dilation(skin, iterations=1)
idx2 = ndi.distance_transform_edt(~cloth, return_distances=False, return_indices=True)
out = img.copy()
out[skin] = img[idx2[0][skin], idx2[1][skin]]
blur = ndi.gaussian_filter(out, (0.8, 0.8, 0))
out[skin] = blur[skin]
Image.fromarray(np.uint8(np.clip(out, 0, 1) * 255 + 0.5)).save(OUT)
vis = (img * 255).astype(np.uint8).copy(); vis[skin] = (255, 0, 255); vis[pos_near & ~skin] //= 2
Image.fromarray(vis).resize((1024, 1024), Image.NEAREST).save('review/sleeve_paint_fix_mask.png')
print('SLEEVE_PAINT near-hand texels', int(pos_near.sum()), 'skin repainted', int(skin.sum()))
