#!/usr/bin/env python3
"""Colour tiers on one shared body set + region mask + ramps (from mm9_bigfoot_claude/scripts/tier_ramps.py). The shared paint is the
Forest Giant's outfit (bare chest and thighs, fur and leather shin wraps); the Plain Giant wears a leather vest, leather leggings and
steel greaves over the same places, so those regions take MM9's colours of that tier at the same body position.
Ramps by histogram match per region and tier: our luminance quantile -> MM9's skin colour at the same quantile of its own luminance,
MM9's skin read at the same place on the body (MM9 mesh in the same 0.3 scale and bind). Value follows MM9.
Body regions: R torso skin (belt to collar, front and back), G thigh and knee skin, B shins (wraps and bands, to the ankle), A nape hair.
Head: per-tier images (tier_head.py), no ramps. Mallet: R head wood, G iron; Forest Giant's steel head as a ramp.
Writes textures/gi_body_region_mask.png, gi_head_region_mask.png, gi_ramps.json."""
import json, sys
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
SK = {'a': load('source/true/skins/giant2.png'), 'b': load('source/true/skins/giant3.png')}
GAIN = {'a': 1.0, 'b': 1.0}
TIERS = ('gi_a', 'gi_b')
g = GLTF2().load('source/true/giant2_true.glb'); pr = g.meshes[0].primitives[0]; blob = g.binary_blob()
def acc(i, n, tp='f4'):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    return np.frombuffer(blob, tp, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(-1, n)
V = acc(pr.attributes.POSITION, 3); UV = acc(pr.attributes.TEXCOORD_0, 2)
ia = g.accessors[pr.indices]; I = acc(pr.indices, 1, 'u2' if ia.componentType == 5123 else 'u4').reshape(-1, 3)
Vb = np.c_[V[:, 0], -V[:, 2], V[:, 1]]
w = np.random.default_rng(1).dirichlet((1, 1, 1), 60)
Sp = np.einsum('sk,tkd->tsd', w, Vb[I]).reshape(-1, 3); Su = np.einsum('sk,tkd->tsd', w, UV[I]).reshape(-1, 2)
tree = cKDTree(Sp)
def mm9_at(p):
    _, i = tree.query(p); u = (Su[i] * 256).astype(int) % 256
    return {t: s[u[:, 1], u[:, 0]] for t, s in SK.items()}
def fit(base, regions, pos):
    L = base @ LUM; out = {v: [] for v in TIERS}
    for name, wg in regions:
        m = wg > 0.5
        c = mm9_at(pos[m][::3]); tg = {}
        for v in TIERS:
            t = v[-1]; col = c[t]; o = np.argsort(col @ LUM); bins = np.array_split(col[o], 16)
            tab = ndimage.gaussian_filter1d(np.array([b.mean(0) for b in bins]), 0.8, axis=0) * GAIN[t]
            qs = np.quantile(L[m], np.linspace(0, 1, 17)); bn = np.clip(np.searchsorted(qs, L) - 1, 0, 15)
            mean = np.array([L[m & (bn == i)].mean() if (m & (bn == i)).any() else 0.01 for i in range(16)], np.float32)
            tg[v] = np.clip(tab[bn] * (L / np.maximum(mean[bn], 1e-3))[..., None], 0, 1)
        rp, err = RV.fit_ramps(base, tg, wg); print('RAMPS', name, json.dumps(err)[:160])
        for v in TIERS: out[v].append(rp[v])
    return out
base = load(T / 'gi_body_final.png'); Z = np.load('work/body_pos.npz'); pos, cov = Z['pos'], Z['cov']
x, y, z = np.abs(pos[..., 0]), pos[..., 1], pos[..., 2]
ss = lambda e0, e1, v: (lambda u: u * u * (3 - 2 * u))(np.clip((v - e0) / (e1 - e0), 0, 1))
r_, g_, b_ = base[..., 0], base[..., 1], base[..., 2]; lum = base @ LUM
sat = (base.max(2) - base.min(2)) / np.maximum(base.max(2), 1e-6)
skin = ss(1.02, 1.14, r_ / np.maximum(g_, 1e-3)) * ss(0.2, 0.3, lum) * ss(0.82, 0.7, lum) * ss(0.18, 0.28, sat)
skin = ndimage.gaussian_filter(ndimage.median_filter(skin, 5), 2.0) * cov
torso = skin * ss(0.215, 0.235, z) * ss(0.70, 0.62, z) * ss(0.33, 0.27, x)
thigh = skin * ss(-0.80, -0.72, z) * ss(0.05, -0.03, z) * ss(0.45, 0.38, x)
shin = cov * ss(-1.16, -1.10, z) * ss(-0.58, -0.66, z) * ss(0.45, 0.40, x)
thigh = thigh * (1 - shin); torso = torso * (1 - thigh) * (1 - shin)
# A: the nape's hair below the head set: the shared paint has the Forest Giant's brown there, the Plain Giant's is copper
hair = cov * ss(0.78, 0.82, z) * np.maximum(ss(-0.03, 0.02, y), ss(0.06, 0.09, x)) * ss(0.22, 0.17, x) * ss(0.24, 0.16, lum)      # the nape, and the dark wedges at the neck's front sides
hair = ndimage.gaussian_filter(hair, 2.0) * cov * (1 - torso)
rb = fit(base, [('torso', torso), ('thigh', thigh), ('shin', shin), ('hair', hair)], pos)
RV.write_mask([torso, thigh, shin, hair], T / 'gi_body_region_mask.png', 1024)
mats = [{'base': 'Giant', 'prefix': 'Giant', 'mask': 'gi_body_region_mask.png', 'ramps': rb}]
# head: no regions (each tier has its own image); one empty channel so the per-tier materials exist
hb = load(T / "gi_head_a_final.png"); zero = np.zeros(hb.shape[:2], np.float32); zero[:64, :64] = 1.0
rh, _ = RV.fit_ramps(hb, {v: hb for v in TIERS}, zero)
RV.write_mask([np.zeros((64, 64), np.float32)], T / 'gi_head_region_mask.png', 64)
mats.append({'base': 'GiantHead', 'prefix': 'GiantHead', 'mask': 'gi_head_region_mask.png', 'ramps': {v: [rh[v]] for v in TIERS}})
# mallet: A keeps the base (fit to itself), B: steel head (cool grey over the wood's value), dark iron bands
mb = load(T / 'gi_mallet_base.png'); mm = np.asarray(Image.open(T / 'gi_mallet_region_mask.png').convert('RGBA'), np.float32) / 255
wood, iron, boss = mm[..., 0], mm[..., 1], mm[..., 2]
L = mb @ LUM
def steel(Lv, lo, hi, tint):
    q = (Lv - Lv[wood > 0.5].min()) / max(np.ptp(Lv[wood > 0.5]), 1e-3)
    return np.clip((lo + (hi - lo) * np.clip(q, 0, 1))[..., None] * np.array(tint), 0, 1)
tgw = {'gi_a': mb, 'gi_b': steel(L, 0.40, 0.60, (0.86, 0.89, 0.93))}        # third pass: a narrow value range (the oak's grain mostly gone), cool and mid-dark: plates, not planks
tgi = {'gi_a': mb, 'gi_b': np.clip(mb * np.array([0.75, 0.62, 0.55]) * 0.85, 0, 1)}
tgb = {'gi_a': mb, 'gi_b': np.clip(mb * 1.6 * np.array([0.98, 0.99, 1.0]) + 0.05, 0, 1)}        # B: polished silver bosses on the steel head
rw, ew = RV.fit_ramps(mb, tgw, wood); ri, ei = RV.fit_ramps(mb, tgi, iron); rbs, eb = RV.fit_ramps(mb, tgb, boss); print('RAMPS mallet', json.dumps(ew)[:100])
mats.append({'base': 'GiantMallet', 'prefix': 'GiantMallet', 'mask': 'gi_mallet_region_mask.png', 'ramps': {v: [rw[v], ri[v], rbs[v]] for v in TIERS}})
json.dump({'variants': list(TIERS), 'materials': mats}, open(T / 'gi_ramps.json', 'w')); print('RAMPS done')
