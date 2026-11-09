#!/usr/bin/env python3
"""Tier region mask and ramps for the dwarf boy body set (one shared set, region mask + ramps).

MM9 skins of PEASANTDBOY1: a = DWARFBOY1 (row 67 Commoner Child: rust-orange tunic with blue-and-cream embroidered bands,
cream shirt, brown belt, dark checked trousers), b = DWARFBOY2 (row 68 Townsfolk Child: plain dark brown ribbed tunic,
no embroidery, braided belt, dark brown trousers). Boots and the cream shirt are the same in both.
Regions (our texels, glTF Y up, floor 0): R tunic (orange cloth), G bands (the blue embroidered bands, dilated over their
cream thread), B trousers (between the boot top and the hem, leg joints), A belt (the leather band at the belt height).
Tier a reproduces our paint (its ramps are fitted to the paint itself: our Meshy paint already matches DWARFBOY1).
Tier b takes DWARFBOY2's colours at our texel's luminance quantile, scaled by the gain that maps our tier-a region
median to MM9 a's (so b's darkness relative to a is MM9's); the bands take b's tunic colours (b has no embroidery: the
bands read as plain tunic cloth with the paint's relief). Pattern difference (b's ribbed weave) not reproduced.
Writes textures/pdboy_region_mask.png, textures/pdboy_ramps.json, textures/pdboy_tier_preview_<t>.png, review/tier_masks.png.
Usage (project folder): tiers_dboy.py <export glb> <graded basecolor png>"""
import json, sys, colorsys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from pygltflib import GLTF2

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as RV

GLB, BASE = sys.argv[1:3]
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


MAT = 'PeasantDBoy'
mesh = next(m for m in g.meshes if any(g.materials[p.material].name == MAT for p in m.primitives))
prim = next(p for p in mesh.primitives if g.materials[p.material].name == MAT)
P = acc(prim.attributes.POSITION).astype(np.float64)
UV = acc(prim.attributes.TEXCOORD_0).astype(np.float64)
JN = acc(prim.attributes.JOINTS_0).astype(int)
WT = acc(prim.attributes.WEIGHTS_0).astype(np.float64)
TRI = acc(prim.indices).reshape(-1, 3).astype(int)
names = [g.nodes[j].name for j in g.skins[0].joints]
dom = JN[np.arange(len(JN)), WT.argmax(1)]
pos = np.full((N, N, 3), np.nan)
jt = -np.ones((N, N), int)
for t in TRI:
    uv = UV[t] * N
    x0, y0 = np.floor(uv.min(0)).astype(int)
    x1, y1 = np.ceil(uv.max(0)).astype(int)
    x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, N - 1), min(y1, N - 1)
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
lin = RV.srgb_to_linear(base)
lum = lin @ W
hsv = np.array(np.vectorize(colorsys.rgb_to_hsv)(base[..., 0], base[..., 1], base[..., 2])).transpose(1, 2, 0)
H, S, V = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
low = np.char.lower(np.array(names)[np.clip(jt, 0, None)].astype(str))
legj = (np.char.find(low, 'thigh') >= 0) | (np.char.find(low, 'calf') >= 0)
armj = (np.char.find(low, 'arm') >= 0) | (np.char.find(low, 'hand') >= 0) | (np.char.find(low, 'finger') >= 0)
Xa = np.abs(np.nan_to_num(pos[..., 0]))
Y = np.nan_to_num(pos[..., 1], nan=-1)
import os
BOOT_TOP, HEM, BELT = float(os.environ.get('BOOT_TOP', 0.24)), float(os.environ.get('HEM', 0.33)), \
    (float(os.environ.get('BELT0', 0.46)), float(os.environ.get('BELT1', 0.50)))
clean = lambda m: ndimage.binary_opening(ndimage.binary_closing(m, iterations=1), iterations=1) & cov
blue = cov & (H > 185) & (H < 255) & (S > 0.22) & (Y > HEM - 0.03)
bands = clean(ndimage.binary_dilation(blue, iterations=3) & cov & (Y > HEM - 0.03) & ~((S < 0.25) & (V > 0.75) & ~ndimage.binary_dilation(blue, iterations=1)))
orange = cov & (H > 5) & (H < 45) & (S > 0.4) & (Y > HEM - 0.03) & ~bands
belt = clean(cov & ~armj & (Xa < 0.2) & (Y > BELT[0]) & (Y < BELT[1]) & (H > 5) & (H < 45) & (S > 0.3) & (V < 0.75) & ~bands)
tunic = clean(orange & ~belt)
trousers = clean(cov & (Y > BOOT_TOP) & (Y < HEM + 0.01) & legj & ~tunic & ~bands)


def pad_soft(w):
    w = ndimage.gaussian_filter(w.astype(float), 0.8) * cov
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    return w[iy, ix]


KEYS = ('tunic', 'bands', 'trousers', 'belt')
masks = {'tunic': tunic, 'bands': bands, 'trousers': trousers, 'belt': belt}
WS = [pad_soft(masks[k]) for k in KEYS]
tot = np.maximum(sum(WS), 1.0)
WS = [w / tot for w in WS]
T = Path('textures')
RV.write_mask(WS, T / 'pdboy_region_mask.png', size=N)
# MM9 skin pixels per region (128 px skins; labels from mm9_skin_labels_dboy.py: 2 vest/tunic, 6 arm block, 4 trousers;
# the belt is the strip at the bottom of the skin, rows 116-126, x < 62)
lab = np.load('work/mm9_skin_labels_pdboy_a.npz')['lab']


def skin_px(mid, key):
    a = np.asarray(Image.open(f'source/mm9/skins/{mid}.png').convert('RGB'), np.float64) / 255
    if key == 'belt':
        px = a[116:126, 0:62].reshape(-1, 3)
    elif key == 'trousers':
        px = a[lab == 4]
    else:
        px = a[(lab == 2) | (lab == 6)]
        hh = np.array([colorsys.rgb_to_hsv(*p)[0] * 360 for p in px])
        if mid == 'pdboy_a':                         # a: the orange cloth only (not the blue bands / cream)
            px = px[(hh > 5) & (hh < 45)]
    l = px @ W
    px = px[(l > np.percentile(l, 3)) & (l < np.percentile(l, 97))]
    return RV.srgb_to_linear(px)


report = {}
ramps = {'pdboy_a': [], 'pdboy_b': []}
for key, w in zip(KEYS, WS):
    core = w > 0.9
    pa = skin_px('pdboy_a', 'tunic' if key == 'bands' else key)
    pb = skin_px('pdboy_b', 'tunic' if key == 'bands' else key)
    if key == 'bands':                               # the bands take b's tunic at the tunic's gain (not the bands' own lum)
        cref = masks['tunic'] & cov
        gain = np.median(lum[cref]) / np.median(pa @ W)
    else:
        gain = np.median(lum[core]) / np.median(pa @ W)
    q = np.zeros_like(lum)
    rank = np.argsort(np.argsort(lum[core]))
    q[core] = rank / max(len(rank) - 1, 1)
    order = np.argsort(pb @ W)
    t_lin = lin.copy()
    idx = np.clip((q[core] * (len(order) - 1)).astype(int), 0, len(order) - 1)
    t_lin[core] = np.clip(pb[order[idx]] * gain, 0, 1)
    tb = np.where(t_lin <= 0.0031308, t_lin * 12.92, 1.055 * np.power(np.clip(t_lin, 0, 1), 1 / 2.4) - 0.055)
    fit, err = RV.fit_ramps(base, {'pdboy_a': base, 'pdboy_b': tb}, w)
    for v in ramps:
        ramps[v].append(fit[v])
    report[key] = {'texels_core': int(core.sum()), 'gain': round(float(gain), 3), 'fit_8bit': err,
                   'mm9_b_median_srgb': [int(x) for x in (255 * np.median(np.where(pb <= 0.0031308, pb * 12.92, 1.055 * pb ** (1 / 2.4) - 0.055), 0))]}
# b has no embroidery: its band ramp is one brown (b's tunic median x the tunic gain) on a gentle 0.8-1.1 slope, so the
# a-tier scrollwork reads as faint relief on plain cloth instead of a light pattern
bi = KEYS.index('bands')
pbt = skin_px('pdboy_b', 'tunic')
brown = np.clip(np.median(pbt, 0) * report['tunic']['gain'], 0, 1)
ramps['pdboy_b'][bi]['colors'] = [[float(c) for c in np.clip(brown * (0.8 + 0.3 * k / 15), 0, 1)] for k in range(16)]
report['bands']['b_plain'] = [round(float(c), 4) for c in brown]
doc = {'variants': list(ramps),
       'materials': [{'base': MAT, 'prefix': MAT, 'mask': 'pdboy_region_mask.png', 'ramps': ramps}],
       'regions': ['R tunic (a rust-orange, b dark brown)', 'G embroidered bands (a blue/cream, b as its tunic)',
                   'B trousers (a dark checked, b dark brown)', 'A belt (a brown leather, b braided)'],
       'source': 'MM9 DWARFBOY1 (a: row 67), DWARFBOY2 (b: row 68); tiers_dboy.py', 'report': report}
json.dump(doc, open(T / 'pdboy_ramps.json', 'w'), indent=1)


def apply(v):
    out = lin.copy()
    for k, w in enumerate(WS):
        rp = ramps[v][k]
        lo, hi = rp['range']
        tt = np.clip((lum - lo) / (hi - lo), 0, 1) * 15
        i0 = np.floor(tt).astype(int).clip(0, 15)
        i1 = (i0 + 1).clip(0, 15)
        f = (tt - i0)[..., None]
        C = np.array(rp['colors'])
        out = out * (1 - w[..., None]) + (C[i0] * (1 - f) + C[i1] * f) * w[..., None]
    s = np.where(out <= 0.0031308, out * 12.92, 1.055 * np.power(np.clip(out, 0, 1), 1 / 2.4) - 0.055)
    Image.fromarray(np.uint8(np.clip(s, 0, 1) * 255)).save(T / f'pdboy_tier_preview_{v}.png')


for v in ramps:
    apply(v)
dbg = np.zeros((N, N, 3)); dbg[..., 0] = WS[0]; dbg[..., 1] = WS[1]; dbg[..., 2] = WS[2]; dbg += WS[3][..., None] * 0.8
Image.fromarray(np.uint8(np.clip(dbg, 0, 1) * 255)).save('review/tier_masks.png')
print('TIERS', json.dumps(report))
