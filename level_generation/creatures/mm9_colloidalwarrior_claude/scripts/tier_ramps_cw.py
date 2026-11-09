#!/usr/bin/env python3
"""Colour tiers (colloidal warrior, from mm9_bigfoot_claude/tier_ramps.py): one shared set + region mask + ramps. Ramps by
histogram match: per region and tier, our luminance quantile -> MM9's colour at the same quantile of its own luminance, MM9's
skin read at the same place on the body (COLLOIDAL1/2/3 on Box06).
Body regions: R slime (1 everywhere, drawn first), G arms and hands (MM9 paints them lighter). Head: R slime (fitted to MM9's
torso, so head and body draw the same tone), G eyes (B orange as painted, A and C red as MM9's), B mouth (lips and teeth kept
as painted). Writes textures/cw_{body,head}_region_mask.png, cw_ramps.json."""
import json, sys, os
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
from pygltflib import GLTF2
sys.path.insert(0, '../claude_shared')
import region_variants as RV
T = Path('textures'); LUM = np.array([0.2126, 0.7152, 0.0722], np.float32)
load = lambda p: np.asarray(Image.open(p).convert('RGB'), np.float32) / 255
SK = {t: load(f'source/true/skins/colloidal{i}.png') for t, i in (('a', 1), ('b', 2), ('c', 3))}
GAIN = {'a': float(os.environ.get('GA', 0.80)), 'b': float(os.environ.get('GB', 1.0)), 'c': float(os.environ.get('GC', 1.0))}
# saturation (second pass, 2026-10-31): under the same viewer light (review/tone_cmp.png, scripts/tone_measure.py) our tiers were
# 12-14 % more saturated than MM9's own models with their skins, while MM9's were 8-24 % lighter; saturation x0.88 matches them
SAT = {'a': float(os.environ.get('SA', 1.0)), 'b': float(os.environ.get('SB', 0.88)), 'c': float(os.environ.get('SC', 0.88))}
TIERS = ('cw_a', 'cw_b', 'cw_c')
g = GLTF2().load('source/true/colloidal1_true.glb'); blob = g.binary_blob()
pr = next(m for m in g.meshes if m.name == 'Box06').primitives[0]
def acc(i, n, tp='f4'):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    return np.frombuffer(blob, tp, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(-1, n)
V = acc(pr.attributes.POSITION, 3); UV = acc(pr.attributes.TEXCOORD_0, 2)
ia = g.accessors[pr.indices]; I = acc(pr.indices, 1, 'u2' if ia.componentType == 5123 else 'u4').reshape(-1, 3)
Vb = np.c_[V[:, 0], -V[:, 2], V[:, 1]]
w = np.random.default_rng(1).dirichlet((1, 1, 1), 60)
Sp = np.einsum('sk,tkd->tsd', w, Vb[I]).reshape(-1, 3); Su = np.einsum('sk,tkd->tsd', w, UV[I]).reshape(-1, 2)
# MM9's face is painted on the head: never sample it for slime colours
keep = ~((Sp[:, 2] > 0.45) & (Sp[:, 1] < 0.0) & (np.abs(Sp[:, 0]) < 0.32))
Sp, Su = Sp[keep], Su[keep]
tree = cKDTree(Sp)
def mm9_at(p):
    _, i = tree.query(p); u = (Su[i] * 256).astype(int) % 256
    return {t: s[u[:, 1], u[:, 0]] for t, s in SK.items()}
def hist_target(base, m, col, gain, sat=1.0):
    L = base @ LUM; o = np.argsort(col @ LUM); bins = np.array_split(col[o], 16)
    tab = ndimage.gaussian_filter1d(np.array([b.mean(0) for b in bins]), 0.8, axis=0) * gain
    g = (tab @ LUM)[:, None]; tab = g + (tab - g) * sat
    qs = np.quantile(L[m], np.linspace(0, 1, 17)); bn = np.clip(np.searchsorted(qs, L) - 1, 0, 15)
    mean = np.array([L[m & (bn == i)].mean() if (m & (bn == i)).any() else 0.01 for i in range(16)], np.float32)
    return np.clip(tab[bn] * (L / np.maximum(mean[bn], 1e-3))[..., None], 0, 1)
def fit_hist(base, wg, samples):
    m = wg > 0.5; c = mm9_at(samples); tg = {v: hist_target(base, m, c[v[-1]], GAIN[v[-1]], SAT[v[-1]]) for v in TIERS}
    rp, err = RV.fit_ramps(base, tg, wg); return rp, err
ss = lambda e0, e1, v: (lambda u: u * u * (3 - 2 * u))(np.clip((v - e0) / (e1 - e0), 0, 1))
# ---- body
base = load(T / 'cw_body_final.png'); Z = np.load('work/body_pos.npz'); pos, cov = Z['pos'], Z['cov']
x, z = np.abs(pos[..., 0]), pos[..., 2]
arms = cov * ss(0.62, 0.78, x) * ss(-0.75, -0.55, z)            # beyond the shoulders and above the feet: arms and hands
slime = cov.astype(np.float32)
rb = {v: [] for v in TIERS}
tors = pos[cov & (x < 0.55) & (z > -0.6)][::3]
rp, err = fit_hist(base, slime, tors); print('RAMPS body slime', json.dumps(err)[:160]); [rb[v].append(rp[v]) for v in TIERS]
armp = pos[cov & (arms > 0.5)][::3]
rp, err = fit_hist(base, arms, armp); print('RAMPS body arms', json.dumps(err)[:160]); [rb[v].append(rp[v]) for v in TIERS]
arms = ndimage.grey_dilation(arms, size=5)       # into the gutters
RV.write_mask([np.ones(cov.shape), arms], T / 'cw_body_region_mask.png', 1024)      # slime drawn everywhere, gutters included: a 0 there showed the base paint at island edges
mats = [{'base': 'Colloidal', 'prefix': 'Colloidal', 'mask': 'cw_body_region_mask.png', 'ramps': rb}]
# ---- head
base = load(T / 'cw_head_final.png'); Z = np.load('work/head_pos.npz'); pos, cov = Z['pos'], Z['cov']
x, y, z = np.abs(pos[..., 0]), pos[..., 1], pos[..., 2]
hsv_s = (base.max(2) - base.min(2)) / np.maximum(base.max(2), 1e-4)
front = cov & (y < -0.28) & (x < 0.27) & (z > 0.55) & (z < 0.95)
eyes = front & (z > 0.70) & (base[..., 0] > 0.50) & (hsv_s > 0.50) & (base[..., 0] > base[..., 1] * 1.3)      # orange: red well over green (the slime is yellow-green)
eyes = ndimage.binary_closing(eyes, iterations=2); eyes = ndimage.gaussian_filter(eyes.astype(np.float32), 1.2)
box = front & (z > 0.56) & (z < 0.69) & (x < 0.18)
lumh = base @ LUM
mouth = box & ((lumh < 0.10) | ((hsv_s < 0.40) & (lumh > 0.30)))     # the dark gap and the ivory teeth; the lips take the slime ramp
mouth = ndimage.binary_opening(mouth, iterations=1); mouth = ndimage.binary_dilation(mouth, iterations=1)
mouth = ndimage.gaussian_filter(mouth.astype(np.float32), 1.0) * (1 - eyes)
hslime = cov.astype(np.float32)
rh = {v: [] for v in TIERS}
rp, err = fit_hist(base, hslime, tors); print('RAMPS head slime', json.dumps(err)[:160]); [rh[v].append(rp[v]) for v in TIERS]
me = eyes > 0.5; tg = {}
for v in TIERS:
    if v == 'cw_b': tg[v] = base.copy()
    else:
        L = base @ LUM; red = np.stack([np.clip(base[..., 0] * 1.05 + 0.05, 0, 1), base[..., 1] * 0.18, base[..., 2] * 0.18], -1)
        tg[v] = np.where((L > 0.12)[..., None], red, base)
rp, err = RV.fit_ramps(base, tg, eyes); print('RAMPS head eyes', json.dumps(err)[:160]); [rh[v].append(rp[v]) for v in TIERS]
rp, err = RV.fit_ramps(base, {v: base.copy() for v in TIERS}, mouth); print('RAMPS head mouth', json.dumps(err)[:160]); [rh[v].append(rp[v]) for v in TIERS]
RV.write_mask([np.ones(cov.shape), eyes, mouth], T / 'cw_head_region_mask.png', 1024)
print('EYES texels', int(me.sum()), 'MOUTH', int((mouth > 0.5).sum()))
mats.append({'base': 'ColloidalHead', 'prefix': 'ColloidalHead', 'mask': 'cw_head_region_mask.png', 'ramps': rh})
json.dump({'variants': list(TIERS), 'materials': mats}, open(T / 'cw_ramps.json', 'w')); print('RAMPS done')
