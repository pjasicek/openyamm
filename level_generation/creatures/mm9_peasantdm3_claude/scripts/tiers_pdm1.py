#!/usr/bin/env python3
"""Tier region mask and ramps for the PeasantDM1 body set (CLAUDE_CREATURE_TEXTURES.md: one shared set, region mask + ramps).

MM9 PeasantDM1 skins: A (PEASANTDM1A, row 8 Commoner, the shared paint) dark slate-blue wool tunic with gold knotwork
bands and a silver medallion; B (PEASANTDM1B, rows 13/14 Shopkeeper) the same cut in ochre / mustard-brown wool with a thin
gold edging. Linen undersleeves, belt and boots are the same design in both skins (B's a little brighter); the faces are
different men (tier B head image, tier_head.py). Regions:
  R (0) tunic: the blue wool (body, sleeves, skirt), not the trim, medallion, belt or linen;
  G (1) trim: the gold knotwork bands on the tunic (A gold; B ochre wool with a gold edge: B's own trim pixels);
  (no leggings region: MM9 B's are only a little brighter, and a dark-texel leggings mask took the boot cuffs too).
Ramps: A fitted to our graded paint itself (A = the accepted look). B's target per texel is the MM9 B region colour at the
texel's luminance quantile, times the gain that maps MM9 A's region onto our paint (median linear luminance), as
tiers_pm1.py. Writes textures/pdm1_region_mask.png, textures/pdm1_ramps.json, textures/pdm1_tier_preview_<t>.png.
Usage (project folder): tiers_pdm1.py <export glb> <graded basecolor png> <classes png>"""
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


mesh = next(m for m in g.meshes if any(g.materials[p.material].name == 'PeasantDM1' for p in m.primitives))
prim = next(p for p in mesh.primitives if g.materials[p.material].name == 'PeasantDM1')
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
low = np.char.lower(jn.astype(str))
Y = np.nan_to_num(pos[..., 1], nan=-1)
boot_top = float(os.environ.get("BOOT_TOP", 0.24))
hem = float(os.environ.get("HEM", 0.39))
blue = cov & (hue > 170) & (hue < 260) & (sat > 0.08) & (Y > hem - 0.02) & (cls != 9)
gold = cov & (hue > 25) & (hue < 65) & (sat > 0.35) & (lum > 0.08) & (Y > hem - 0.02) & (cls != 9)
clean = lambda m: ndimage.binary_opening(ndimage.binary_closing(m, iterations=2), iterations=1) & cov
blue = clean(blue)
gold = clean(gold) & ~blue
# the linen undersleeves' olive-gold stripes passed the gold test (tier B turned them orange): trim is gold on the dark
# wool, so keep gold texels whose non-gold surroundings are dark
ng = (~gold & cov).astype(float)
neigh = ndimage.gaussian_filter(lum * ng, 4) / np.maximum(ndimage.gaussian_filter(ng, 4), 1e-6)
gold = gold & (neigh < 0.06)
# forearm skin (fix_collar_pdm1.py repainted it to tier A's face skin; its mask): B takes tier B's face skin
fore = np.asarray(Image.open('textures/pdm1_forearm_skin_mask.png').convert('L').resize((N, N), Image.BILINEAR), np.float64) / 255
band = np.asarray(Image.open('textures/pdm1_wrist_band_mask.png').convert('L').resize((N, N), Image.BILINEAR), np.float64) / 255
fore = fore * (1 - band)      # the leather wrist bands (wrist_band_pdm1.py) are shared, not skin
# (tried 2026-11-01: the knotwork's dark gaps joined to R so B shows ochre gaps; the feathered mask then blued A's thin
# gold strands, so the gaps stay unmasked: B's knotwork reads gold on near-black)
legs = cov & (Y > boot_top) & (Y < hem + 0.01) & ~blue & ~gold & (lum < 0.2)


def pad_soft(w):
    w = ndimage.gaussian_filter(w.astype(float), 0.8) * cov
    w = np.where(cov, np.maximum(w, 0), 0)
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    return w[iy, ix]


wR, wG, wB = pad_soft(blue), pad_soft(gold), pad_soft(legs)
T = Path('textures')
wB = pad_soft(fore > 0.5) * 0 + np.where(cov, fore, 0)
_, (iy_, ix_) = ndimage.distance_transform_edt(~cov, return_indices=True)
wB = wB[iy_, ix_]
RV.write_mask([wR, wG, wB], T / 'pdm1_region_mask.png', size=N)

# MM9 skin regions (256 px coordinates, the same layout in both skins) with per-tier hue filters
REG = {'tunic': [(10, 125, 115, 235), (125, 125, 165, 195)], 'trim': [(0, 97, 120, 117), (170, 120, 195, 200)],
       'leggings': [(197, 82, 252, 155)]}
HUE = {'tunic': ((170, 260), (15, 60)), 'trim': ((25, 65), (25, 65)), 'leggings': (None, None)}


def skin_pixels(tier, key):
    a = np.asarray(Image.open(f'source/mm9/skins/pdm1{tier}.png').convert('RGB'), np.float64) / 255
    out = []
    for x0, y0, x1, y1 in REG[key]:
        px = a[y0:y1, x0:x1].reshape(-1, 3)
        h = HUE[key][0 if tier == 'a' else 1]
        if h is not None:
            mx_, mn_ = px.max(1), px.min(1)
            hh = np.degrees(np.arctan2(np.sqrt(3) * (px[:, 1] - px[:, 2]), 2 * px[:, 0] - px[:, 1] - px[:, 2])) % 360
            px = px[(hh > h[0]) & (hh < h[1]) & (mx_ - mn_ > 0.04)]
        out.append(px)
    return RV.srgb_to_linear(np.concatenate(out))


report = {}
ramps = {'pdm1_a': [], 'pdm1_b': []}
FACE_A = np.array([208.0, 124.0, 89.0]) / 255      # cheek medians of the two head paints (fix_neck_pdm1.py)
FACE_B = np.array([183.0, 92.0, 67.0]) / 255
for k, (key, w) in enumerate((('tunic', wR), ('trim', wG), ('forearm', wB))):
    if key == 'forearm':
        core = w > 0.9
        gain_b = RV.srgb_to_linear(FACE_B[None])[0] / RV.srgb_to_linear(FACE_A[None])[0]
        t_lin = lin.copy(); t_lin[core] = np.clip(lin[core] * gain_b, 0, 1)
        target = np.where(t_lin <= 0.0031308, t_lin * 12.92, 1.055 * np.power(np.clip(t_lin, 0, 1), 1 / 2.4) - 0.055)
        fit, err = RV.fit_ramps(base, {'pdm1_a': base, 'pdm1_b': target}, w)
        for v in ramps:
            ramps[v].append(fit[v])
        report[key] = {'texels_core': int(core.sum()), 'gain_b_linear': gain_b.round(3).tolist(), 'fit_8bit': err}
        continue
    core = w > 0.9
    la = skin_pixels('a', key)
    lb = skin_pixels('b', key)
    gain = np.median(lum[core]) / np.median(la @ W)
    q = np.zeros_like(lum)
    rank = np.argsort(np.argsort(lum[core]))
    q[core] = rank / max(len(rank) - 1, 1)

    def quantile_target(px):
        order = np.argsort(px @ W)
        t_lin = lin.copy()
        idx = np.clip((q[core] * (len(order) - 1)).astype(int), 0, len(order) - 1)
        t_lin[core] = np.clip(px[order[idx]] * gain, 0, 1)
        return np.where(t_lin <= 0.0031308, t_lin * 12.92, 1.055 * np.power(np.clip(t_lin, 0, 1), 1 / 2.4) - 0.055)
    target = quantile_target(lb)
    fit, err = RV.fit_ramps(base, {'pdm1_a': base, 'pdm1_b': target}, w)
    for v in ramps:
        ramps[v].append(fit[v])
    report[key] = {'texels_core': int(core.sum()), 'mm9_a_px': len(la), 'mm9_b_px': len(lb),
                   'gain_mm9a_to_ours': round(float(gain), 3), 'fit_8bit': err}
doc = {'variants': ['pdm1_a', 'pdm1_b'],
       'materials': [{'base': 'PeasantDM1', 'prefix': 'PeasantDM1', 'mask': 'pdm1_region_mask.png', 'ramps': ramps}],
       'regions': ['R tunic (A slate-blue wool, B ochre wool)', 'G trim (A gold knotwork, B gold-edged ochre)',
                   'B forearm skin (fix_collar_pdm1.py mask): A face skin, B tier B face skin', 'leggings, belt, boots and linen are shared (MM9 B only a little brighter; a leggings mask took the boot cuffs)'],
       'source': 'MM9 PEASANTDM1A (a: row 8), PEASANTDM1B (b: rows 13, 14); tiers_pdm1.py', 'report': report}
json.dump(doc, open(T / 'pdm1_ramps.json', 'w'), indent=1)


def apply(v):
    out = lin.copy()
    for k, w in enumerate((wR, wG, wB)):
        rp = ramps[v][k]
        lo, hi = rp['range']
        tt = np.clip((lum - lo) / (hi - lo), 0, 1) * 15
        i0 = np.floor(tt).astype(int).clip(0, 15)
        i1 = (i0 + 1).clip(0, 15)
        f = (tt - i0)[..., None]
        C = np.array(rp['colors'])
        col = C[i0] * (1 - f) + C[i1] * f
        out = out * (1 - w[..., None]) + col * w[..., None]
    s = np.where(out <= 0.0031308, out * 12.92, 1.055 * np.power(np.clip(out, 0, 1), 1 / 2.4) - 0.055)
    Image.fromarray(np.uint8(np.clip(s, 0, 1) * 255)).save(T / f'pdm1_tier_preview_{v}.png')


for v in ramps:
    apply(v)
print('TIERS', json.dumps(report))
