#!/usr/bin/env python3
"""Tier region mask and ramps for the PeasantDM2 body set (CLAUDE_CREATURE_TEXTURES.md: one shared set, region mask + ramps).

MM9 PeasantDM2 skins: A (PEASANTDM2A, row 8 Commoner, the shared paint) dark slate-blue wool tunic with gold knotwork
bands and a silver medallion; B (PEASANTDM2B, rows 13/14 Shopkeeper) the same cut in ochre / mustard-brown wool with a thin
gold edging. Linen undersleeves, belt and boots are the same design in both skins (B's a little brighter); the faces are
different men (tier B head image, tier_head.py). Regions:
  R (0) tunic: the blue wool (body, sleeves, skirt), not the trim, medallion, belt or linen;
  G (1) trim: the gold knotwork bands on the tunic (A gold; B ochre wool with a gold edge: B's own trim pixels);
  (no leggings region: MM9 B's are only a little brighter, and a dark-texel leggings mask took the boot cuffs too).
Ramps: A fitted to our graded paint itself (A = the accepted look). B's target per texel is the MM9 B region colour at the
texel's luminance quantile, times the gain that maps MM9 A's region onto our paint (median linear luminance), as
tiers_pm1.py. Writes textures/pdm2_region_mask.png, textures/pdm2_ramps.json, textures/pdm2_tier_preview_<t>.png.
Usage (project folder): tiers_pdm2.py <export glb> <graded basecolor png> <classes png>"""
import json, os
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from pygltflib import GLTF2

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as RV

GLB, BASE, CLASSES = sys.argv[1:4]
N = 1024
W = np.array([0.2126, 0.7152, 0.0722])
g = GLTF2().load(GLB)
blob = g.binary_blob()


def acc(i):
    a = g.accessors[i]
    bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a.type]
    dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a.componentType]
    return np.frombuffer(blob, dt, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)


mesh = next(m for m in g.meshes if any(g.materials[p.material].name == 'PeasantDM2' for p in m.primitives))
prim = next(p for p in mesh.primitives if g.materials[p.material].name == 'PeasantDM2')
P = acc(prim.attributes.POSITION).astype(np.float64)
UV = acc(prim.attributes.TEXCOORD_0).astype(np.float64)
JN = acc(prim.attributes.JOINTS_0).astype(int)
WT = acc(prim.attributes.WEIGHTS_0).astype(np.float64)
TRI = acc(prim.indices).reshape(-1, 3).astype(int)
skin = g.skins[0]
names = [g.nodes[j].name for j in skin.joints]
IBM = acc(skin.inverseBindMatrices).reshape(-1, 4, 4)
head = {n: np.linalg.inv(IBM[k].T)[:3, 3] for k, n in enumerate(names)}   # glTF column-major
dom = JN[np.arange(len(JN)), WT.argmax(1)]

# rasterise: texel -> position, dominant joint
pos = np.full((N, N, 3), np.nan)
jt = -np.ones((N, N), int)
for t in TRI:
    uv = UV[t] * N
    # glTF UV: v grows down the image (compose_texpass.py coverage), no flip
    x0, y0 = np.floor(uv.min(0)).astype(int)
    x1, y1 = np.ceil(uv.max(0)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0)
    x1, y1 = min(x1, N - 1), min(y1, N - 1)
    if x1 < x0 or y1 < y0:
        continue
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    a, b, c = uv
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-12:
        continue
    l0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
    l1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
    l2 = 1 - l0 - l1
    ins = (l0 >= -1e-3) & (l1 >= -1e-3) & (l2 >= -1e-3)
    if not ins.any():
        continue
    L = np.stack([l0, l1, l2], -1)[ins]
    yy, xx = (ys[ins] - 0.5).astype(int), (xs[ins] - 0.5).astype(int)
    pos[yy, xx] = L @ P[t]
    jt[yy, xx] = dom[t][L.argmax(1)]
cov = jt >= 0

base = np.asarray(Image.open(BASE).convert('RGB').resize((N, N), Image.LANCZOS), np.float64) / 255
cls = np.asarray(Image.open(CLASSES).convert('L').resize((N, N), Image.NEAREST))
lin = RV.srgb_to_linear(base)
lum = lin @ W
mx, mn = base.max(2), base.min(2)
sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
r, gg, bb = base[..., 0], base[..., 1], base[..., 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (gg - bb), 2 * r - gg - bb)) % 360


jn = np.array(names)[np.clip(jt, 0, None)]
Y = np.nan_to_num(pos[..., 1], nan=-1)
import collections
for n in sorted(set(jn[cov].tolist())):
    m = cov & (jn == n)
    print(n, int(m.sum()), 'Y %.3f..%.3f' % (np.percentile(Y[m], 2), np.percentile(Y[m], 98)), 'lum %.3f' % np.median(lum[m]), 'hue %.0f sat %.2f' % (np.median(hue[m]), np.median(sat[m])))
np.savez('work/tier_probe.npz', Y=Y, jt=jt, cov=cov, hue=hue, sat=sat, lum=lum)
print('NAMES', names)
