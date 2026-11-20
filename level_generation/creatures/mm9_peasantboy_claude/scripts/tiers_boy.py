#!/usr/bin/env python3
"""Tier region mask and ramps for the PeasantBoy body set (CLAUDE_CREATURE_TEXTURES.md: one shared set, region mask + ramps).

MM9 skins of the one boy body: a = PEASANTBOY1 (row 69 Commoner Child: dark brown laced vest, tan shirt sleeves, braided
cream cord belt, dark checked trousers), b = PEASANTBOY3 on PEASANTBOY2 (row 70 Townsfolk Child: olive-green open vest
over a cream shirt, cream sleeves, dark brown leather belt, brown trousers), e = PEASANTBOY2 on PEASANTBOY1E (row 73
Commoner Child elf: green tunic, green sleeves, brown belt, dark brown trousers). The boots are the same in all three.
Regions (our texels, glTF Y up, floor 0): R vest (torso above the hem, not belt or sleeve), G sleeves (|x| beyond the
vest's armhole, light shirt), B trousers (thigh/calf below the hem, above the boot top), A belt (the braid band).
Every tier, A included, takes its own MM9 skin's region colours at our texel's luminance quantile, scaled by the gain
that maps MM9 A's region onto our paint (our Meshy paint is orange-brown where MM9's vest is dark brown). Pattern
differences (b's open vest showing the cream shirt, e's embroidered trim) are not reproduced: a deviation in the README.
Writes textures/pboy_region_mask.png, textures/pboy_ramps.json, textures/pboy_tier_preview_<t>.png, review/tier_masks.png.
Usage (project folder): tiers_boy.py <export glb> <graded basecolor png> <classes png>"""
import json, os, sys
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


mesh = next(m for m in g.meshes if any(g.materials[p.material].name == 'PeasantBoy' for p in m.primitives))
prim = next(p for p in mesh.primitives if g.materials[p.material].name == 'PeasantBoy')
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
jn = np.array(names)[np.clip(jt, 0, None)]
low = np.char.lower(jn.astype(str))
X = np.abs(np.nan_to_num(pos[..., 0], nan=0))
Y = np.nan_to_num(pos[..., 1], nan=-1)
BOOT_TOP, HEM, BELT = 0.345, 0.595, (0.742, 0.802)
armj = (np.char.find(low, 'arm') >= 0) | (np.char.find(low, 'hand') >= 0) | (np.char.find(low, 'clavicle') >= 0)
legj = (np.char.find(low, 'thigh') >= 0) | (np.char.find(low, 'calf') >= 0)
metal = cls == 9
clean = lambda m: ndimage.binary_opening(ndimage.binary_closing(m, iterations=2), iterations=1) & cov
sleeves = clean(cov & armj & ((X > 0.17) | ((X > 0.133) & (lum > 0.07))) & (Y > 0.78))
belt = clean(cov & (Y > BELT[0]) & (Y < BELT[1]) & (X < 0.2) & ~sleeves & ~metal)
trousers = clean(cov & (Y > BOOT_TOP) & (Y < HEM + 0.03) & legj & ~belt)
vest = clean(cov & (Y > HEM - 0.04) & ~sleeves & ~belt & ~trousers & ~metal)


def pad_soft(w):
    w = ndimage.gaussian_filter(w.astype(float), 0.8) * cov
    w = np.where(cov, np.maximum(w, 0), 0)
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    return w[iy, ix]


KEYS = ('vest', 'sleeves', 'trousers', 'belt')
masks = {'vest': vest, 'sleeves': sleeves, 'trousers': trousers, 'belt': belt}
WS = [pad_soft(masks[k]) for k in KEYS]
tot = np.maximum(sum(WS), 1.0)
WS = [w / tot for w in WS]
T = Path('textures')
RV.write_mask(WS, T / 'pboy_region_mask.png', size=N)
SKLAB = {'vest': 2, 'sleeves': 6, 'trousers': 4, 'belt': 7}
TIERS = {'pboy_a': 'pboy1', 'pboy_b': 'pboy2', 'pboy_e': 'pboy1e'}


def skin_pixels(mid, key):
    lab = np.load(f'work/mm9_skin_labels_{mid}.npz')['lab']
    m = lab == SKLAB[key]
    if key == 'belt':                       # the belt strip at the bottom of the skin (not vest texels at belt height)
        m[:112] = False
    a = np.asarray(Image.open(f'source/mm9/skins/{mid}.png').convert('RGB'), np.float64) / 255
    px = a[m]
    # drop light outliers: b's open vest shows the cream shirt, e's sleeve block carries light trim; our paint has no
    # such pattern, so they would only brighten the ramp's top (b's vest read beige in the viewer)
    lum = px @ np.array([0.2126, 0.7152, 0.0722])
    if key != 'belt':                       # a's belt is a light braid: keep it
        px = px[lum <= np.median(lum) * 1.6 + 8 / 255]
    return RV.srgb_to_linear(px)


report = {}
ramps = {v: [] for v in TIERS}
for key, w in zip(KEYS, WS):
    core = w > 0.9
    px = {v: skin_pixels(mid, key) for v, mid in TIERS.items()}
    gain = np.median(lum[core]) / np.median(px['pboy_a'] @ W)
    q = np.zeros_like(lum)
    rank = np.argsort(np.argsort(lum[core]))
    q[core] = rank / max(len(rank) - 1, 1)

    def quantile_target(p):
        order = np.argsort(p @ W)
        t_lin = lin.copy()
        idx = np.clip((q[core] * (len(order) - 1)).astype(int), 0, len(order) - 1)
        t_lin[core] = np.clip(p[order[idx]] * gain, 0, 1)
        return np.where(t_lin <= 0.0031308, t_lin * 12.92, 1.055 * np.power(np.clip(t_lin, 0, 1), 1 / 2.4) - 0.055)
    fit, err = RV.fit_ramps(base, {v: quantile_target(px[v]) for v in TIERS}, w)
    for v in ramps:
        ramps[v].append(fit[v])
    report[key] = {'texels_core': int(core.sum()), 'mm9_px': {v: len(p) for v, p in px.items()},
                   'gain_mm9a_to_ours': round(float(gain), 3), 'fit_8bit': err}
# second pass (orchestrator 2026-11-02): MM9's b and e trousers are plain brown; the fitted ramp kept our paint's woven
# check (dark/light luminance alternation). Their trouser ramp is one brown (the median of the MM9 tier's trouser pixels x
# the gain) with only a gentle 0.85-1.05 slope across the range, so the check reads as faint weave, not a pattern.
ki = KEYS.index('trousers')
for v in ('pboy_b', 'pboy_e'):
    px = skin_pixels(TIERS[v], 'trousers')
    g = report['trousers']['gain_mm9a_to_ours']
    brown = np.clip(np.median(px, 0) * g, 0, 1)
    rp = ramps[v][ki]
    rp['colors'] = [[float(c) for c in np.clip(brown * (0.85 + 0.20 * k / 15), 0, 1)] for k in range(16)]
    report['trousers'].setdefault('plain', {})[v] = [round(float(c), 4) for c in brown]
# b's open vest: a cream shirt panel down the front (MM9 PEASANTBOY3), in its own mask: the panel's vest texels move from
# R (vest) to G (sleeves: b's sleeve ramp is the cream shirt). Front (z > 0), from the belt top to the collar, 1.2 cm half
# width at the belt widening to 4 cm at the neck.
Xs = np.nan_to_num(pos[..., 0]); Zs = np.nan_to_num(pos[..., 2])
hw = 0.012 + np.clip((Y - 0.80) / (1.12 - 0.80), 0, 1) * 0.028
panel = cov & (Zs > 0.02) & (np.abs(Xs) < hw) & (Y > 0.80) & (Y < 1.13)
pw = np.clip(ndimage.gaussian_filter(panel.astype(float), 1.0), 0, 1)
WB = [w.copy() for w in WS]
WB[1] = WB[1] + WB[0] * pw
WB[0] = WB[0] * (1 - pw)
RV.write_mask(WB, T / 'pboy_region_mask_b.png', size=N)
report['panel_b_texels'] = int(panel.sum())
# b's sleeve ramp then must turn the dark vest texels of the panel cream too: its range is widened down to the panel's
# 5th luminance percentile and its colours are b's cream shirt (MM9 b sleeve median x gain) on a 0.72-1.05 slope, so the
# sleeves keep their fold shading and the panel reads as the shirt between the open vest's edges
gi = KEYS.index('sleeves')
rp = ramps['pboy_b'][gi]
cream = np.clip(np.median(skin_pixels(TIERS['pboy_b'], 'sleeves'), 0) * report['sleeves']['gain_mm9a_to_ours'], 0, 1)
lo_panel = float(np.percentile(lum[panel], 5))
rp['range'] = [min(lo_panel, rp['range'][0]), rp['range'][1]]
rp['colors'] = [[float(c) for c in np.clip(cream * (0.72 + 0.33 * k / 15), 0, 1)] for k in range(16)]
report['panel_b_ramp'] = {'range': [round(x, 4) for x in rp['range']], 'cream': [round(float(c), 4) for c in cream]}
doc = {'variants': list(TIERS),
       'materials': [{'base': 'PeasantBoy', 'prefix': 'PeasantBoy', 'mask': 'pboy_region_mask.png', 'ramps': ramps}],
       'variant_masks': {'pboy_b': 'pboy_region_mask_b.png'},
       'regions': ['R vest (a dark brown, b olive green, e green)', 'G sleeves (a tan, b cream, e green)',
                   'B trousers (a dark checked, b brown, e dark brown)', 'A belt (a braided cream cord, b/e brown leather)'],
       'source': 'MM9 PEASANTBOY1 (a: row 69), PEASANTBOY3 (b: row 70), PEASANTBOY2 (e: row 73); tiers_boy.py', 'report': report}
json.dump(doc, open(T / 'pboy_ramps.json', 'w'), indent=1)


def apply(v):
    out = lin.copy()
    for k, w in enumerate(WB if v == 'pboy_b' else WS):
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
    Image.fromarray(np.uint8(np.clip(s, 0, 1) * 255)).save(T / f'pboy_tier_preview_{v}.png')


for v in ramps:
    apply(v)
dbg = np.zeros((N, N, 3)); dbg[..., 0] = WS[0]; dbg[..., 1] = WS[1]; dbg[..., 2] = WS[2]; dbg += WS[3][..., None] * 0.8
Image.fromarray(np.uint8(np.clip(dbg, 0, 1) * 255)).save('review/tier_masks.png')
print('TIERS', json.dumps(report))
