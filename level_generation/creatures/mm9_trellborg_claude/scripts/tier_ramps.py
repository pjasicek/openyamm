#!/usr/bin/env python3
"""Colour tiers: MM9's three skins are one layout in three colours, so one shared set + region mask + ramps. Two regions per material: R hide (fur, skin), G horn and hoof (MM9's Elder has red horns and blue hooves). Eyes and teeth are in no region.
Tier targets on our layout: MM9's colour for the same quantile of luminance in that region (each tier its own skin, tier A included), our grain on top, then fit_ramps.
Writes textures/gezz_{body,head}_region_mask.png, gezz_ramps.json."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, '../claude_shared')
import region_variants as RV
T = Path('textures')
LUM = np.array([0.2126, 0.7152, 0.0722], np.float32)
load = lambda p: np.asarray(Image.open(p).convert('RGB'), np.float32) / 255
SK = {t: load(f'source/true/skins/gezzampt{i}.png') for t, i in (('a', 1), ('b', 2), ('c', 3))}
yy, xx = np.mgrid[0:256, 0:256]
HORN_PX = (xx > 46) & (xx < 90) & (yy > 8) & (yy < 30)
HOOF_PX = (xx > 165) & (yy > 232)
HIDE_PX = ~(HORN_PX | HOOF_PX)
def ratio_table(px, n=16):
    """for n quantile bins of tier A luminance in the MM9 region: mean colour per tier"""
    la = SK['a'][px] @ LUM
    q = np.quantile(la, np.linspace(0, 1, n + 1)); out = {}
    for t, s in SK.items():
        c = s[px]; rows = []
        for i in range(n):
            m = (la >= q[i]) & (la <= q[i + 1])
            rows.append(c[m].mean(0))
        out[t] = np.array(rows)
    return out
GAIN = 1.3          # MM9's skins carry baked shading: albedo about this much above them
TG = {'a': GAIN, 'b': GAIN, 'c': 1.12}     # the Elder's blue read far brighter than MM9's dusky one at 1.3
def target(base, w, tab, tier, gain=GAIN):
    """MM9's colour for the same quantile of our luminance in the region, times GAIN, our own grain on top"""
    lum = base @ LUM
    m = w > 0.5
    qs = np.quantile(lum[m], np.linspace(0, 1, 17))
    bin_ = np.clip(np.searchsorted(qs, lum) - 1, 0, 15)
    mean = np.array([lum[m & (bin_ == i)].mean() if (m & (bin_ == i)).any() else 0.01 for i in range(16)], np.float32)
    c = ndimage.gaussian_filter1d(tab[tier], 0.8, axis=0) * gain
    return np.clip(c[bin_] * (lum / np.maximum(mean[bin_], 1e-3))[..., None], 0, 1)
HIDE = ratio_table(HIDE_PX); HORN = ratio_table(HORN_PX); HOOF = ratio_table(HOOF_PX)
print('RATIO hide mid', np.round(HIDE['b'][8] / HIDE['a'][8], 2), np.round(HIDE['c'][8] / HIDE['a'][8], 2), 'horn', np.round(HORN['c'][8] / HORN['a'][8], 2), 'hoof', np.round(HOOF['c'][8] / HOOF['a'][8], 2))
TIERS = ('gezz_a', 'gezz_b', 'gezz_c')
# ---------------- body
base = load(T / 'gezz_body_final.png'); S = base.shape[0]
Z = np.load('work/body_pos.npz'); pos, cov = Z['pos'], Z['cov']
hoof = cov & (pos[..., 2] < -1.08)
hoof = ndimage.gaussian_filter(hoof.astype(np.float32), 1.5)
hide = np.clip(1 - hoof, 0, 1)
tg = {}
for v, t in zip(TIERS, 'abc'):
    tg[v] = target(base, hide, HIDE, t, TG[t]) * hide[..., None] + target(base, hoof, HOOF, t, 0.8) * hoof[..., None]
ramps = {v: [] for v in TIERS}
for name, w in (('hide', hide), ('hoof', hoof)):
    rp, err = RV.fit_ramps(base, tg, w)
    print('RAMPS body', name, json.dumps(err)[:240])
    for v in TIERS: ramps[v].append(rp[v])
RV.write_mask([hide, hoof], T / 'gezz_body_region_mask.png', 1024)
mats = [{'base': 'Gezzampt', 'prefix': 'Gezzampt', 'mask': 'gezz_body_region_mask.png', 'ramps': ramps}]
# ---------------- head
base = load(T / 'gezz_head_final.png'); S = base.shape[0]
Z = np.load('work/head_pos.npz'); pos, cov, prt = Z['pos'], Z['cov'], Z['prt']
x, y, z = np.abs(pos[..., 0]), pos[..., 1], pos[..., 2]
lum = base @ LUM; mx, mn = base.max(2), base.min(2); sat = (mx - mn) / np.maximum(mx, 1e-6)
horn = cov & (x > 0.10) & (x < 0.27) & (z > 1.0 + 0.25 * (x - 0.1)) & (z < 1.13) & (y < -0.11) & (y > -0.28) & (lum > 0.2) & (sat < 0.62)
horn = ndimage.binary_opening(ndimage.binary_closing(horn, iterations=2), iterations=1)
horn = ndimage.gaussian_filter(horn.astype(np.float32), 1.2)
mouth = cov & (x < 0.14) & (y < -0.25) & (z > 0.74) & (z < 0.845)
ivory = mouth & (lum > 0.3) & (sat < 0.55)         # the shell's sheaths round the tusks
ivory = ndimage.binary_closing(ivory, iterations=2)
keep = (prt >= 13) | ivory      # eyes, teeth, tusks
keep = ndimage.gaussian_filter(keep.astype(np.float32), 1.0)
hide = np.clip(1 - horn, 0, 1) * (1 - keep); horn = horn * (1 - keep)
tg = {}
for v, t in zip(TIERS, 'abc'):
    tg[v] = target(base, hide, HIDE, t, TG[t]) * hide[..., None] + target(base, horn, HORN, t) * horn[..., None] + base * keep[..., None]
ramps = {v: [] for v in TIERS}
for name, w in (('hide', hide), ('horn', horn)):
    rp, err = RV.fit_ramps(base, tg, w)
    print('RAMPS head', name, json.dumps(err)[:240])
    for v in TIERS: ramps[v].append(rp[v])
RV.write_mask([hide, horn], T / 'gezz_head_region_mask.png', 1024)
mats.append({'base': 'GezzamptHead', 'prefix': 'GezzamptHead', 'mask': 'gezz_head_region_mask.png', 'ramps': ramps})
json.dump({'variants': list(TIERS), 'materials': mats}, open(T / 'gezz_ramps.json', 'w'))
print('RAMPS done')
