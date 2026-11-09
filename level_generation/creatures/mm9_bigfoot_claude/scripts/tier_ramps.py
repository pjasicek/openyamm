#!/usr/bin/env python3
"""Colour tiers: one shared set + region mask + ramps; the Yeti's head has its own image (design: snarl). Ramps by histogram match: per region and tier, our luminance quantile -> MM9's colour at the same quantile of its own luminance, MM9's skin read at the same place on the body. Value follows MM9 (Gezzampt's lesson).
Body regions: R fur, G chest and belly, B bare hands and toes, A Sasquatch's silver saddle. Head: R fur, G crest, B face. Writes textures/bf_{body,head}_region_mask.png, bf_ramps.json."""
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
SK = {t: load(f'source/true/skins/bigfoot{i}.png') for t, i in (('a', 1), ('b', 2), ('c', 3))}
GAIN = {'a': 1.05, 'b': 1.12, 'c': 0.88}
TIERS = ('bf_a', 'bf_b', 'bf_c')
g = GLTF2().load('source/true/bigfoot1_true.glb'); pr = g.meshes[0].primitives[0]; blob = g.binary_blob()
def acc(i, n, tp='f4'):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    k = {'f4': 4, 'u2': 2, 'u4': 4}[tp]
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
def fit(base, regions, pos, tiers=TIERS, sel=None):
    """regions: list of (name, weight). Returns ramps per tier"""
    L = base @ LUM; out = {v: [] for v in tiers}
    for name, wg in regions:
        m = wg > 0.5
        c = mm9_at(pos[m & sel][::3] if sel is not None and name in ('fur', 'hood') else pos[m][::3]); tg = {}
        for v in tiers:
            t = v[-1]; col = c[t]; o = np.argsort(col @ LUM); bins = np.array_split(col[o], 16)
            tab = ndimage.gaussian_filter1d(np.array([b.mean(0) for b in bins]), 0.8, axis=0) * GAIN[t]
            if name == 'saddle' and t == 'b': tab = tab[np.linspace(6, 15, 16).astype(int)] * 1.0      # the silver saddle reads over our dark base
            qs = np.quantile(L[m], np.linspace(0, 1, 17)); bn = np.clip(np.searchsorted(qs, L) - 1, 0, 15)
            mean = np.array([L[m & (bn == i)].mean() if (m & (bn == i)).any() else 0.01 for i in range(16)], np.float32)
            tg[v] = np.clip(tab[bn] * (L / np.maximum(mean[bn], 1e-3))[..., None], 0, 1)
        rp, err = RV.fit_ramps(base, tg, wg); print('RAMPS', name, json.dumps(err)[:150])
        for v in tiers: out[v].append(rp[v])
    return out
base = load(T / 'bf_body_final.png'); Z = np.load('work/body_pos.npz'); pos, cov = Z['pos'], Z['cov']
x, y, z = np.abs(pos[..., 0]), pos[..., 1], pos[..., 2]
sat = (base.max(2) - base.min(2)) / np.maximum(base.max(2), 1e-6); lum = base @ LUM
ss = lambda e0, e1, v: (lambda u: u * u * (3 - 2 * u))(np.clip((v - e0) / (e1 - e0), 0, 1))
hp = lum - ndimage.gaussian_filter(lum, 5)                        # the paint's own fur grain breaks the region edges up
# run 2: the chest panel from the body position alone, an ellipse on the front with a wide soft edge. r6 picked low-saturation
# texels in a box and blurred them in UV space: a jagged hard edge and a pale keyhole on the breastbone (Yeti's blue patch)
ec = (x / 0.33) ** 2 + ((z - 0.32) / 0.36) ** 2 - hp * 1.5      # top kept under the head set: the Yeti head's white throat read as a collar over a blue that reached it
chest = cov * ss(1.12, 0.62, ec) * ss(-0.27, -0.40, y)
ext = cov & (((x > 0.82) & (z < -0.2)) | ((z < -1.33) & (y < -0.42)))
ext = ndimage.gaussian_filter(ext.astype(np.float32), 2)
# run 2: the Sasquatch's back panel as an ellipse over the back and onto the flanks, as MM9's, soft-edged and speckled by the grain (r6: a blurred box)
es = (x / 0.45) ** 2 + ((z - 0.33) / 0.42) ** 2 - hp * 2.0
saddle = cov * ss(1.2, 0.7, es) * ss(-0.32, -0.15, y)
chest = chest * (1 - ext); saddle = saddle * (1 - ext) * (1 - chest)
fur = np.clip(1 - chest - ext - saddle, 0, 1)
rb = fit(base, [('fur', fur), ('chest', chest), ('ext', ext), ('saddle', saddle)], pos, sel=cov & ((z < -0.2) | (x > 0.45)))       # MM9's Sasquatch has light speckle over the whole torso panel: fur colours come from limbs
# the shader mixes the channels in order (fur, then chest over it, ...): fur must cover everything, or where fur = 1 - chest
# the base paint shows through the soft edges (a red-orange band at the belly in r7). The fits above keep the partition.
RV.write_mask([np.where(cov, 1.0, fur), chest, ext, saddle], T / 'bf_body_region_mask.png', 1024)
mats = [{'base': 'Bigfoot', 'prefix': 'Bigfoot', 'mask': 'bf_body_region_mask.png', 'ramps': rb}]
import os
if os.environ.get('BODY_ONLY'):
    old = json.load(open(T / 'bf_ramps.json')); old['materials'][0] = mats[0]
    json.dump(old, open(T / 'bf_ramps.json', 'w')); print('RAMPS body only'); sys.exit(0)
base = load(T / 'bf_head_final.png'); Z = np.load('work/head_pos.npz'); pos, cov, prt = Z['pos'], Z['cov'], Z['prt']
x, y, z = np.abs(pos[..., 0]), pos[..., 1], pos[..., 2]
ey = ndimage.gaussian_filter((prt == 13).astype(np.float32), 1)
fc = ndimage.gaussian_filter((cov & (y < -0.40) & (z < 0.945) & (x < 0.16)).astype(np.float32), 6)
cr = ndimage.gaussian_filter((cov & (z >= 0.945) & (y < -0.16) & (x < 0.17)).astype(np.float32), 6)
hood = np.clip(1 - fc - cr, 0, 1) * (1 - ey); fc = fc * (1 - ey); cr = cr * (1 - ey)
ht = ('bf_a', 'bf_b')
rh = fit(base, [('hood', hood), ('crest', cr), ('face', fc)], pos, ht, sel=cov & (z > 0.97) & (y > -0.2))
RV.write_mask([hood, cr, fc], T / 'bf_head_region_mask.png', 1024)
rh['bf_c'] = rh['bf_a']        # never drawn: tier C's head material has its own image and no ramps (tier_head_c.py)
mats.append({'base': 'BigfootHead', 'prefix': 'BigfootHead', 'mask': 'bf_head_region_mask.png', 'ramps': rh})
json.dump({'variants': list(TIERS), 'materials': mats}, open(T / 'bf_ramps.json', 'w')); print('RAMPS done')
