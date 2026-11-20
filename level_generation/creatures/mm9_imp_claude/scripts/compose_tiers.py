#!/usr/bin/env python3
"""Region masks and per-tier ramps for the Imp (CLAUDE_CREATURE_TEXTURES.md): one shared body set and one head set.
Regions: R skin (both sets), G claws' green tips (body) or eyes (head). Black leather, studs, teeth and horns stay. Masks come
from the paint's own hue on the final texture. Tier A keeps the HD look; B and C take the chroma of their own MM9 skin by
luminance percentile on the MM9 skin texels (selected on IMP1), brightness by the MM9 tier/A ratio; eyes and claw tips take
MM9's tier colours (amber eyes and yellow claws on B, orange eyes and dark red claws on C). The texture keeps one design: the
wraps of B and the tongue of C are attachments. Writes textures/imp_region_mask.png, imp_head_region_mask.png, imp_ramps.json,
imp_material_classes.png, imp_head_material_classes.png, work/imp_eye_mask.png."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV
T = HERE / 'textures'
W = np.array([0.2126, 0.7152, 0.0722])
S = 1024
TIERS = {'imp_a': 'IMP1', 'imp_b': 'IMP2', 'imp_c': 'IMP3'}
K_SAT = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0


def hsv(rgb):
    mx, mn = rgb.max(2), rgb.min(2)
    sat = (mx - mn) / np.maximum(mx, 1e-4)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    return hue, sat, mx


def lin(c):
    return RV.srgb_to_linear(c)


def encode(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def load(name):
    return np.asarray(Image.open(T / name).convert('RGB').resize((S, S), Image.LANCZOS), np.float32) / 255


def feather(m):
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0)), np.float32) / 255


def covered(name):
    c = np.asarray(Image.open(T / name).convert('L'))
    return ndimage.binary_erosion(c > 0, iterations=0)


skins = {k: np.asarray(Image.open(HERE / 'source/mm9/skins' / f'{v}.png').convert('RGB'), np.float32) / 255 for k, v in TIERS.items()}
hA, sA, vA = hsv(skins['imp_a'])
msk = (hA > 25) & (hA < 80) & (sA > 0.3) & (vA > 0.2)


def bands(k):
    pal = lin(skins[k][msk]); pal = pal[np.argsort(pal @ W)]
    mid = pal[int(0.15 * len(pal)):int(0.95 * len(pal))]
    return pal, np.array([(b / np.maximum(b @ W, 1e-3)[:, None]).mean(0) for b in np.array_split(mid, 6)])


pal_a, band_a = bands('imp_a')
print('MM9 skin rgb', {k: (encode(lin(skins[k][msk]).mean(0)) * 255).round().tolist() for k in TIERS})


def skin_targets(g, weight):
    core = weight > 0.5
    glum = lin(g[core]) @ W
    rank = np.empty(glum.size); rank[np.argsort(glum)] = (np.arange(glum.size) + 0.5) / glum.size
    out = {'imp_a': g.copy()}
    for k in ('imp_b', 'imp_c'):
        pal, band = bands(k)
        x = np.clip(rank, 0, 1) * (len(band) - 1)
        i0 = np.minimum(x.astype(int), len(band) - 2); fr = (x - i0)[:, None]
        chroma = band[i0] * (1 - fr) + band[i0 + 1] * fr
        chroma = 1 + (chroma - 1) * K_SAT
        gain = float((pal @ W).mean()) / float((pal_a @ W).mean())
        t = g.copy(); t[core] = encode(np.clip(chroma * (glum * gain)[:, None], 0, 1))
        out[k] = t
    return out


def tint_targets(g, weight, tints, lo=0.0):
    core = weight > 0.5
    glum = lin(g[core]) @ W
    hi = np.percentile(glum, 97)
    out = {'imp_a': g.copy()}
    for k, (c0, c1) in tints.items():
        s = np.clip((glum - lo) / max(hi - lo, 1e-3), 0, 1)[:, None]
        t = g.copy(); t[core] = encode(np.array(c0) * (1 - s) + np.array(c1) * s)
        out[k] = t
    return out


def process(base_name, cov_name, second, tints, mat, mask_name, class_name):
    g = load(base_name)
    cov = np.asarray(Image.open(T / cov_name).convert('L').resize((S, S), Image.NEAREST)) > 0
    h, s, v = hsv(g)
    skin = (h > 12) & (h < 78) & (s > 0.32) & (v > 0.12) & cov
    green = (h > 85) & (h < 175) & (s > 0.3) & (v > 0.1) & cov
    green = ndimage.binary_opening(green, iterations=1)
    green = ndimage.binary_dilation(green, iterations=2) & cov
    skin &= ~green
    skin = ndimage.binary_closing(skin, iterations=2) & ~green & cov
    # pad into the gutters (seams), then soft edges
    def pad(m):
        _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
        return m[iy, ix]
    rs, rg = feather(pad(skin)), feather(pad(green))
    RV.write_mask([rs, rg], T / mask_name)
    ramps = {k: [] for k in TIERS}
    rep = []
    for name, w, tg in (('skin', rs, skin_targets(g, rs)), (second, rg, tint_targets(g, rg, tints))):
        fitted, r = RV.fit_ramps(g, tg, w)
        for k in TIERS:
            ramps[k].append(fitted[k])
        rep.append({'region': name, 'texels': int((w > 0.5).sum()), 'report': r})
    cl = np.full((S, S), 0, np.uint8)
    cl[cov] = 8; cl[skin] = 1
    cl[green] = 6 if second == 'eyes' else 4
    Image.fromarray(cl).save(T / class_name)
    return {'base': mat, 'prefix': mat, 'mask': mask_name, 'ramps': ramps}, rep, green


m1, r1, _ = process('imp_basecolor_graded.png', 'imp_material_classes.png', 'claws',
                    {'imp_b': ((0.22, 0.14, 0.01), (0.95, 0.72, 0.08)), 'imp_c': ((0.03, 0.005, 0.005), (0.30, 0.04, 0.03))},
                    'Imp', 'imp_region_mask.png', 'imp_classes_final.png')
m2, r2, eyes = process('imp_head_basecolor_graded.png', 'imp_head_material_classes.png', 'eyes',
                       {'imp_b': ((0.25, 0.10, 0.0), (1.0, 0.72, 0.10)), 'imp_c': ((0.02, 0.0, 0.0), (0.95, 0.30, 0.02))},
                       'ImpHead', 'imp_head_region_mask.png', 'imp_head_classes_final.png')
Image.fromarray((feather(eyes) * 255).astype(np.uint8)).save(HERE / 'work' / 'imp_eye_mask.png')
json.dump({'variants': list(TIERS), 'sources': TIERS, 'report': r1 + r2, 'materials': [m1, m2]}, open(T / 'imp_ramps.json', 'w'), indent=1)
print('TIERS', json.dumps([{k: v for k, v in x.items() if k != 'report'} for x in r1 + r2]))
for x in r1 + r2:
    print(x['region'], {k: (v.get('mean_abs_8bit') if isinstance(v, dict) else v) for k, v in x['report'].items()})
