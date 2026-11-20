#!/usr/bin/env python3
"""Colour tiers on the shared sets: region masks + ramps. MM9's three skins differ only in the hide (and the Revenant's nose): leather, belt and hair stay.
Body set: R skin. Head set: R skin, G nose hollow (tier C only goes dark). Ramps: tier A fitted to its own graded paint; B and C by luminance rank onto the hide pixels of MM9's own skins.
Writes textures/ghoul_region_mask.png, ghoul_head_region_mask.png, ghoul_ramps.json, work/dark_uv.json."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, '../claude_shared'); sys.path.insert(0, 'scripts')
import region_variants as RV
import project_lib as PL
TX = Path('textures')
F = np.load('work/faces.npz')
S = 2048


def hsv(rgb):
    mx, mn = rgb.max(2), rgb.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360, sat, mx


def soft(m, s=1.0): return np.clip(ndimage.gaussian_filter(m.astype(np.float32), s) * 1.2, 0, 1)
def clean(m): return ndimage.binary_opening(ndimage.binary_closing(m, iterations=2), iterations=1)


# MM9's hide pixels per tier: where tier 1 is a light olive texel
sk = [np.asarray(Image.open(f'source/g{t}/skins/ghoul{t}.png').convert('RGB'), np.float32) / 255 for t in (1, 2, 3)]
h1, s1, v1 = hsv(sk[0])
hide = (h1 > 40) & (h1 < 75) & (v1 > 0.3) & (s1 > 0.12)
print('MM9 hide texels', int(hide.sum()))


def rank_target(base, weight, pool):
    core = weight >= 0.9
    lum = RV.luminance(base)[core]
    o = np.argsort(lum)
    pl = RV.luminance(pool); pool = pool[np.argsort(pl)]
    k = max(3, len(pool) // 30)
    sm = np.stack([ndimage.uniform_filter1d(pool[:, c], k, mode='nearest') for c in range(3)], 1)
    idx = (np.arange(len(o)) / max(len(o) - 1, 1) * (len(sm) - 1)).astype(int)
    tgt = base.copy(); vals = np.zeros((len(o), 3), np.float32); vals[o] = sm[idx]
    tgt[core] = vals
    return tgt


entries = []
TONE = (0.80, 0.78, 0.74)
for setname, uvk, sel, basef, maskf in (('Ghoul', 'uvb', (F['head'] == 0) & (F['part'] != 3), 'ghoul_basecolor_final.png', 'ghoul_region_mask.png'), ('GhoulHead', 'uvh', F['head'] != 0, 'ghoul_head_basecolor_final.png', 'ghoul_head_region_mask.png')):
    base = np.asarray(Image.open(TX / basef).convert('RGB'), np.float32) / 255
    pos, nor, cov, bar, fid = PL.raster(F[uvk][sel], F['co'][sel], S)
    parts = F['part'][sel]
    h, s, v = hsv(base)
    if setname == 'Ghoul':
        skin = (h > 38) & (h < 85) & (v > 0.25) & (s > 0.10) & (s < 0.72) & cov & ~np.isin(parts[fid], (3,))
        # brass strips of the belt, tan bands of the shorts are hide-coloured: only limbs and torso outside the leather zones are skin
        z, x = pos[..., 2], np.abs(pos[..., 0])
        belt = (z > -0.13) & (z < 0.318) & (x < 0.30)
        claw = np.asarray(Image.open(TX / 'ghoul_claw_mask.png'), np.float32) / 255 > 0.02
        wrap = ((x > 0.42) & (x < 0.78) & (z > 0.3)) | ((z > -1.03) & (z < -0.62))
        y_up = belt
        # the shorts' tan folds are hide-coloured: the lower rim of the zone keeps only texels with a calm neighbourhood (skin), the folds are striped
        lum = RV.luminance(base)
        mu = ndimage.uniform_filter(lum, 21); sd = np.sqrt(np.maximum(ndimage.uniform_filter(lum * lum, 21) - mu * mu, 0))
        rim = (((z > -0.24) & (z < 0.05)) | (z > 0.21)) & (sd < 0.055)
        keep = (~belt | rim) & ~claw
        skin = skin & keep
        hidehue = (h > 34) & (h < 90) & (v > 0.3) & (s < 0.75) & cov & ~claw & ~np.isin(parts[fid], (3, 6, 7))
        grown = ndimage.binary_dilation(skin, iterations=16, mask=hidehue & (z < 0.06))     # the hem of the shorts
        spine = (y_b := pos[..., 1]) > 0.04
        grown2 = ndimage.binary_dilation(skin, iterations=70, mask=hidehue & spine & (x < 0.07) & (z > 0.18))  # the spine's lower end above the belt
        skin = skin | grown | grown2
    else:
        pf = parts[fid]
        skin = (h > 14) & (h < 95) & (v > 0.18) & (s < 0.9) & cov & ~np.isin(pf, (11, 12, 13))
        skin |= (h > 30) & (h < 85) & (v > 0.42) & cov & (pf == 11)     # skin-coloured paint on the hair mass under the ears
    skin = clean(skin)
    w = soft(skin)
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    wf = w[iy, ix]
    print(setname, 'skin share %.3f' % (skin.sum() / cov.sum()))
    masks = [wf]
    if setname == 'Ghoul':
        # MM9's Ghoul has glossy pale veins on the limbs and back: the bright lines of GHOUL2 carried over from MM9's own surface (our mesh is fitted onto its bind pose)
        import veins
        wv = veins.mask(pos, cov, sk[1], sk[2])[iy, ix] * wf
        masks = [wf, wv]          # regions mix in order, in the shader too: the later one lies over the full first
    if setname == 'GhoulHead':
        # the Revenant's nose: the tip and alae of the nose rot to a hollow in MM9's C skin
        nx, ny, nz = pos[..., 0], pos[..., 1], pos[..., 2]
        nose = (((nx / 0.030) ** 2 + ((nz - 0.748) / 0.016) ** 2) < 1) & (ny < -0.11) & cov & (parts[fid] == 10)
        wn = np.clip(soft(nose, 3.0), 0, 1)[iy, ix]
        masks = [wf, wn]
    RV.write_mask(masks, TX / maskf, 1024)
    names_ = ('ghoul_a', 'ghoul_b', 'ghoul_c')
    ramps = {k: [] for k in names_}
    for mi, m in enumerate(masks):
        tt = {}
        for t, name in enumerate(names_):
            if mi == 0: tt[name] = rank_target(base, m, sk[t][hide] * TONE[t])
            elif setname == 'Ghoul': tt[name] = np.clip(rank_target(base, np.maximum(masks[0], m), sk[t][hide] * TONE[t]) * (1.3 if t == 1 else 1.0), 0, 1)
            else: tt[name] = rank_target(base, np.maximum(masks[0], m), sk[t][hide] * TONE[t]) if t != 2 else np.clip(base * np.array([0.13, 0.13, 0.15]), 0, 1)
        if setname == 'Ghoul' and mi == 1:
            # the veins: the hide's own ramp, lighter on the Ghoul only (a fit on so few texels gave tan smudges)
            for t, k in enumerate(names_):
                e = json.loads(json.dumps(ramps[k][0]))
                if t == 1: e['colors'] = np.round(np.clip(np.array(e['colors']) * 1.2, 0, 1), 6).tolist()
                ramps[k].append(e)
            continue
        r, rep = RV.fit_ramps(base, tt, m)
        print(setname, mi, rep)
        for k in names_: ramps[k].append(r[k])
    entries.append({'base': setname, 'prefix': setname, 'mask': maskf, 'ramps': ramps})
    if setname == 'GhoulHead':
        lum = RV.luminance(base).copy(); lum[~cov] = 9; lum = ndimage.minimum_filter(lum, 5)
        hy, hx = np.unravel_index(np.argmin(np.where(cov, ndimage.uniform_filter(RV.luminance(base), 9), 9)), lum.shape)
        json.dump({'u': float((hx + 0.5) / S), 'v': float(1 - (hy + 0.5) / S)}, open('work/dark_uv.json', 'w'))
        print('dark texel', hx, hy, base[hy, hx])
json.dump({'variants': ['ghoul_a', 'ghoul_b', 'ghoul_c'], 'materials': entries}, open(TX / 'ghoul_ramps.json', 'w'))
print('RAMPS')
