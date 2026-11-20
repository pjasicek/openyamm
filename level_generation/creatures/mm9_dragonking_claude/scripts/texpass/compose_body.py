#!/usr/bin/env python3
"""Body set from the 4K texture-pass retexture (TEXTURE_QUALITY_PASS.md steps 4, 2026-10-30); replaces compose_dragon.py.
Run from anywhere; meshy/body_retexture_texpass/ maps are on work/texpass/uv_final.blend's UVMap.

Inputs: the Meshy maps, work/texpass/uv3d_body.npz (dump_uv3d.py on the final blend), work/texpass/pairs_body.npz,
textures/dragonking_ao_2k.png (re-baked on the new UVs), work/before_texpass/textures/ (the approved set).
Writes textures/: dragonking_basecolor.png (padded 4K -> 2K once; graded afterwards by grade_basecolor.py),
dragonking_normal_1k.png, dragonking_metal_rough_1k.png (R AO, G roughness 0.45-0.9, B 0), and
dragonking_material_classes.png from the new paint's own colours and the triangle's rig group, the rules of
compose_dragon.py (1 skin, 3 membrane, 4 claw/horn; never the old mask: the bat's mask transfer left blotches along the
wing bones, 2026-10-14). Colours are smoothed over MEM_SMOOTH texels at 1K first: the 4K paint's scale net is far
finer than the old paint's, and at 3 texels the membrane rule would follow single cells."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
import tp

HERE = Path(__file__).resolve().parents[2]
T, W, M, B = HERE / 'textures', HERE / 'work' / 'texpass', HERE / 'meshy' / 'body_retexture_texpass', HERE / 'work' / 'before_texpass' / 'textures'
N, S = 2048, 1024
MEM_SMOOTH, MEM_V = 9, 0.30
d = np.load(W / 'uv3d_body.npz')
pairs = np.load(W / 'pairs_body.npz')
uv = pairs['new']
base4 = tp.load(M / 'texture_urls_0_base_color.png')
R = base4.shape[0]
print('meshy size', base4.shape)
cov4 = tp.raster(uv, R) >= 0
cov2, cov1 = tp.raster(uv, N) >= 0, tp.raster(uv, S) >= 0
tp.save(tp.down(tp.pad(base4, cov4), N), T / 'dragonking_basecolor.png')
nrm = tp.load(M / 'texture_urls_0_normal.png')
tp.save(tp.down(tp.pad(nrm, cov4), S), T / 'dragonking_normal_1k.png')
rough = tp.load(M / 'texture_urls_0_roughness.png', 'L')
rough = np.clip(tp.pad(tp.down(rough, S), cov1), 0.45 * 255, 0.9 * 255)
ao = tp.load(T / 'dragonking_ao_2k.png', 'L')
ao = tp.pad(tp.down(ao, S), cov1)
tp.save(np.stack([ao, rough, np.zeros_like(ao)], -1), T / 'dragonking_metal_rough_1k.png')
old = tp.load(B / 'dragonking_material_classes.png', 'L')
tri = tp.raster(d['uv'], S)
t = np.maximum(tri, 0)
chain = d['limb'].max(1)[t]
piece = d['part'][t] == 2
z = d['xyz'][:, :, 2].mean(1)[t]
sm = ndimage.uniform_filter(tp.down(base4, S) / 255, (MEM_SMOOTH, MEM_SMOOTH, 1))
mx, mn = sm.max(-1), sm.min(-1)
sat, val = (mx - mn) / (mx + 1e-9), mx
wing = np.isin(chain, (5, 6))
limb_tip = np.isin(chain, (1, 2, 3, 4)) & (z < 3.0) | np.isin(chain, (1, 2)) & (sat < 0.25)
classes = np.ones((S, S), np.uint8)
membrane = wing & (val < MEM_V)
classes[membrane] = 3
classes[(sat < 0.22) & (val > 0.12) & ~membrane & (limb_tip | wing | (chain == 7) | piece)] = 4
classes[~cov1] = 0
Image.fromarray(classes.astype(np.uint8)).save(T / 'dragonking_material_classes.png')
names = {0: 'empty', 1: 'skin', 3: 'membrane', 4: 'claw_horn', 5: 'tooth', 6: 'eye', 7: 'mouth'}
share = {names[k]: round(float((classes == k).mean()), 4) for k in names}
old_share = {names[k]: round(float((old == k).mean()), 4) for k in names}
json.dump({'class_share': share, 'approved_class_share': old_share}, open(T / 'dragonking_compose.json', 'w'), indent=1)
print('COMPOSED', share, 'approved', old_share)
