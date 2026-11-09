#!/usr/bin/env python3
"""The head set led to each tier's body (user: "the graft"): the head paint is brown with sharp cracks, the torso olive with soft pebbles.
- grain: a band on the head side of the join, fading up the neck: the head's cracks give way to the torso's own skin detail, laid in neck coordinates at the torso's scale;
- colour and value: each tier's head skin ramp is rebuilt by luminance rank onto that tier's torso skin at the neck, so face, neck and chest read as one corpse;
- hard edge: the torso image's last 3 cm take the head's join colour. Writes the final head base, the head skin ramps, the torso finals. Reruns from zombie_head_basecolor_s1.png."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, 'scripts'); sys.path.insert(0, '../claude_shared')
import project_lib as PL
import region_variants as RV
import tier_textures as TT
TX = Path('textures'); F = np.load('work/faces.npz')
gauss = lambda a, s: np.stack([ndimage.gaussian_filter(a[..., c], s) for c in range(a.shape[2])], -1)
hb = np.asarray(Image.open(TX / 'zombie_head_basecolor_s1.png').convert('RGB'), np.float32) / 255
nh = F['head'] > 0; S = hb.shape[0]
pos, _, cov, bar, fid = PL.raster(F['uvh'][nh], F['co'][nh], S)
mask = np.stack([np.asarray(c.resize((S, S), Image.BILINEAR), np.float32) / 255 for c in Image.open(TX / 'zombie_head_region_mask.png').convert('RGBA').split()], -1)
skin = mask[..., 1]
ts = F['torso'] > 0
pt, _, ct, _, _ = PL.raster(F['uvt'][ts], F['co'][ts], 1536)
def px_per_m(uv, co, zone):
    a3 = np.linalg.norm(np.cross(co[:, 1] - co[:, 0], co[:, 2] - co[:, 0]), axis=1) / 2
    d1, d2 = uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]; au = np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / 2
    return np.sqrt(au[zone].sum() / a3[zone].sum())
zh = F['co'][nh][:, :, 2].mean(1) < 0.85; zt = (F['co'][ts][:, :, 2].mean(1) > 0.65) & (np.abs(F['co'][ts][:, :, 0].mean(1)) < 0.2)
rh = px_per_m(F['uvh'][nh], F['co'][nh], zh) * S; rt = px_per_m(F['uvt'][ts], F['co'][ts], zt) * 1536
print('px/m head neck %.0f, torso %.0f' % (rh, rt))
for t in 'abc':
    p = TX / f'zombie_torso_{t}_s1.png'   # torso_finish's output, before this script; remove these three after a torso_finish change
    if not p.exists(): Image.open(TX / f'zombie_torso_{t}_final.png').save(p)
a = np.asarray(Image.open(TX / 'zombie_torso_a_s1.png').convert('RGB'), np.float32) / 255
good = ct & (pt[..., 2] > 0.5) & (pt[..., 2] < 0.76) & (np.abs(pt[..., 0]) < 0.28)
N = 220; ii = ndimage.uniform_filter(good.astype(np.float32), N); cy, cx = np.unravel_index(np.argmax(ii), ii.shape)
det = (a - gauss(a, 12))[max(cy - N // 2, 0):cy + N // 2, max(cx - N // 2, 0):cx + N // 2]
det = np.concatenate([det, det[::-1]], 0); det = np.concatenate([det, det[:, ::-1]], 1)
# neck coordinates: the head's UVs stretch on the flare and split it, so colour and detail in the band come from the surface, not the texture
x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]
rad = np.hypot(x, y); u = np.arctan2(x, y) * 0.058; v = z - rad
W = np.clip((0.875 - z) / 0.075, 0, 1); W = W * W * (3 - 2 * W) * np.clip((y + 0.042) / 0.016, 0, 1)   # the neck only: the chin keeps the face's skin
nk = cov & (z < 0.92) & (skin > 0.3)
C = 0.004; u0, v0 = u[nk].min(), v[nk].min()
g = lambda q, q0: (q - q0) / C
sz = (int(g(u[nk], u0).max()) + 2, int(g(v[nk], v0).max()) + 2)
acc = np.zeros(sz + (3,), np.float64); wei = np.zeros(sz, np.float64)
iu, iv = g(u[nk], u0).astype(int), g(v[nk], v0).astype(int)
np.add.at(acc, (iu, iv), hb[nk]); np.add.at(wei, (iu, iv), 1)
sg = (3, 3); lw = ndimage.gaussian_filter(wei, sg, mode=('wrap', 'nearest')); low = np.stack([ndimage.gaussian_filter(acc[..., c], sg, mode=('wrap', 'nearest')) / np.maximum(lw, 1e-6) for c in range(3)], -1)
band = cov & (W > 0) & (skin > 0.3)
cu, cv = g(u[band], u0), g(v[band], v0)
smooth = np.stack([ndimage.map_coordinates(low[..., c], [cu, cv], order=1, mode='nearest') for c in range(3)], -1).astype(np.float32)
tu, tv = (u[band] * rt) % det.shape[1], (v[band] * rt) % det.shape[0]
grain = np.stack([ndimage.map_coordinates(det[..., c], [tv, tu], order=1, mode='grid-wrap') for c in range(3)], -1).astype(np.float32)
GAIN = float(sys.argv[1]) if len(sys.argv) > 1 else 1.9   # by the measured grain std at the neck
hb2 = hb.copy()
wb = (W * ndimage.gaussian_filter((skin > 0.3).astype(np.float32), 2))[band][:, None]
hb2[band] = np.clip(hb[band] * (1 - wb) + (smooth + grain * GAIN) * wb, 0, 1)
_, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
hb2 = hb2[iy, ix]
Image.fromarray((hb2 * 255 + 0.5).astype('u1')).save(TX / 'zombie_head_basecolor_final.png')


def rank_target(base, weight, pool):
    core = weight >= 0.9; lum = RV.luminance(base)[core]; o = np.argsort(lum)
    pl = RV.luminance(pool); pool = pool[np.argsort(pl)]
    k = max(3, len(pool) // 40); sm = np.stack([ndimage.uniform_filter1d(pool[:, c], k, mode='nearest') for c in range(3)], 1)
    idx = (np.arange(len(o)) / max(len(o) - 1, 1) * (len(sm) - 1)).astype(int)
    tgt = base.copy(); vals = np.zeros((len(o), 3), np.float32); vals[o] = sm[idx]; tgt[core] = vals
    return tgt


def hsv(rgb):
    mx, mn = rgb.max(1), rgb.min(1); sat = (mx - mn) / np.maximum(mx, 1e-6); r, g, b = rgb.T
    return np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360, sat, mx


R = json.load(open(TX / 'zombie_ramps.json'))
he = next(e for e in R['materials'] if e['base'] == 'ZombieHead')
zone = ct & (pt[..., 2] > 0.66) & (pt[..., 2] < 0.79) & (np.abs(pt[..., 0]) < 0.17)
tt = {}
src_im = {}
for t in 'abc':
    p = TX / f'zombie_torso_{t}_s1.png'
    im = np.asarray(Image.open(p).convert('RGB'), np.float32) / 255; src_im[t] = im
    px = im[zone]; h, s, v = hsv(px)
    pool = px[(h > 34) & (h < 95) & (s > 0.2) & (v > 0.16)]
    print(t, 'torso skin pool', len(pool), (pool.mean(0) * 255).round(0))
    tt[f'zombie_{t}'] = rank_target(hb2, skin, pool)
r, rep = RV.fit_ramps(hb2, tt, skin)
for v in R['variants']: he['ramps'][v][1] = r[v]
json.dump(R, open(TX / 'zombie_ramps.json', 'w'))
from scipy.spatial import cKDTree
rim = F['co'][nh].reshape(-1, 3); rim = rim[rim[:, 2] < 0.806]
wr = np.zeros(ct.shape, np.float32); tz = ct & (pt[..., 2] > 0.74)
wr[tz] = np.clip((0.006 - cKDTree(rim).query(pt[tz])[0]) / 0.003, 0, 1)
wr = ndimage.gaussian_filter(wr, 1.5)[..., None]
for t in 'abc':
    head = TT.apply(hb2.astype(np.float64), mask.astype(np.float64), he['ramps'][f'zombie_{t}']).astype(np.float32)
    j = cov & (pos[..., 2] > 0.797) & (pos[..., 2] < 0.825) & (skin > 0.6) & (pos[..., 1] < 0.04)
    jc = head[j].mean(0)
    im = src_im[t]
    wt = np.clip((pt[..., 2] - 0.755) / 0.04, 0, 1) * ct * (np.abs(pt[..., 0]) < 0.14)
    wt = ndimage.gaussian_filter(wt, 4)[..., None]
    gain = np.clip(jc / np.maximum(gauss(im, 10), 1e-3), 0.4, 2.5)
    out = im * (1 - wt) + np.clip(im * gain, 0, 1) * wt
    # the torso paint's own dark line where the old neck hole ran: the texels at the head's rim take their brighter neighbours
    near = np.stack([ndimage.percentile_filter(out[..., c], 60, size=7) for c in range(3)], -1)
    out = out * (1 - wr) + near * wr
    Image.fromarray((out * 255 + 0.5).astype('u1')).save(TX / f'zombie_torso_{t}_final.png')
    print(t, 'join colour', (jc * 255).round(0))
    hp = lambda q: (q - gauss(q, 6)) @ np.array([0.3, 0.59, 0.11], np.float32)
    bd = cov & (z < 0.835) & (skin > 0.8) & (y < 0.03)
    print(t, 'grain std head band %.4f torso neck %.4f' % (hp(head)[bd].std(), hp(im)[zone].std()))
print('HEADMATCH done')
