#!/usr/bin/env python3
"""Textures, region masks and tier ramps for the hydra (CLAUDE_CREATURE_TEXTURES.md; route of mm6_hyd_claude: a body
set and a head set, here without a bake: every map comes straight from the retextures through our own UVs).

Sets (material: images):
  Hydra (body and lofts, part 0): base colour 2K (meshy/body_retexture_v2), normal / ORM / region mask 1K
  HydraHeads (heads, part k):     atlas 1536x1024, one 512x512 tile per head (meshy/head<k>_retexture_v1, tile k at
                                  column (k-1) % 3, row (k-1) // 3 from the top, as uv_hydra.py maps it); normal /
                                  ORM / mask 768x512
Base colour graded by the rest-pose AO (work/ao_body.png, work/ao_heads.png; bake_ao_hydra.py), padded into the
gutters. ORM: R specular class mask (openyamm_specular_mask), G roughness (Meshy's, recentred per class), B 0.

Tiers: palettes 267 Fire Hydra (A, olive-yellow hide), 57 Air Hydra (B, the bitmaps' own blue-grey), 269 Chaos Hydra
(C, red-brown). The native recolour is one region: the reptile hide, palette indices 64..191 (sprite restoration
manifest 'blue_reptile_skin'; ivory horns and claws, silver belly plates, red mouths, the rust head 5 and the teal head
4 stay). Region R in both materials = the blue/violet hide texels (hue 195-300 deg, saturation ramp 0.07-0.15; head 1's
cyan fins from 180 deg; head 4's grey-teal skin excluded, hue from 215 deg there). Ramps: the hide pixels of the
native standing and walking frames (all five directions) in each palette, sorted by luminance; each stop takes the
tier's colour at the texel's luminance quantile, scaled so the region's mean is the native mean x RAMP_GAIN (texel
luminance kept: histogram matching copies the sprites' painted shading, mm6 cobra / manticore rule).
Writes textures/m266_* and textures/m266_ramps.json; work/m266_mask_preview.png."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
M = HERE / 'meshy'
PALS = {'m266_a': 267, 'm266_b': 57, 'm266_c': 269}
RAMP_GAIN = 1.05      # 1.3 read pastel next to the dark-shaded sprites (tier C pink)
DARK_DESAT = 0.45     # the darkest native hide entries are pure blue / red: their stops lose this share of chroma
HEAD4_GAIN = 1.45     # head 4's grey-teal skin came back near black from its retexture
HEAD_COLS, HEAD_ROWS, TILE = 3, 2, 512
UV = np.load(HERE / 'work' / 'uv_tris.npz')


def save(a, path):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path, optimize=True)


def load(path, size=None, mode='RGB'):
    im = Image.open(path).convert(mode)
    if size and im.size != size:
        im = im.resize(size, Image.LANCZOS)
    return np.asarray(im, np.float64) / 255


def hsv(rgb):
    h = np.asarray(Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    return h[..., 0] * 360, h[..., 1], h[..., 2]


def coverage(sel, W, H, label=None):
    """per texel: covered by the selected UV triangles (and the part id when label)"""
    im = Image.new('I', (W, H), -1); dr = ImageDraw.Draw(im)
    for uv, p in zip(UV['uv'][sel], UV['part'][sel]):
        dr.polygon([(u * W, (1 - v) * H) for u, v in uv], fill=int(p), outline=int(p))
    a = np.asarray(im)
    return a


def pad(img, cov):
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    out = img[iy, ix]; out[cov] = img[cov]; return out


def atlas(name, mode='RGB'):
    """the five head maps (2048) into the 1536x1024 atlas"""
    ch = 3 if mode == 'RGB' else 1
    A = np.zeros((HEAD_ROWS * TILE, HEAD_COLS * TILE, ch))
    for k in range(1, 6):
        a = load(M / f'head{k}_retexture_v1' / f'texture_urls_0_{name}.png', (TILE, TILE), mode)
        if ch == 1:
            a = a[..., None]
        c, r = (k - 1) % HEAD_COLS, (k - 1) // HEAD_COLS
        A[r * TILE:(r + 1) * TILE, c * TILE:(c + 1) * TILE] = a
    return A if ch == 3 else A[..., 0]


def classes(base, part):
    h, s, v = hsv(base)
    cov = part >= 0
    ivory = cov & (h >= 22) & (h <= 62) & (s > 0.1) & (s < 0.62) & (v > 0.5)
    red = cov & ((h < 15) | (h > 335)) & (s > 0.45) & (v > 0.3)
    plate = cov & (s < 0.10) & (v > 0.42) & ~ivory
    # body and heads 1-3: everything is hide but ivory, silver plates and red mouths (the dark low-saturation
    # blue-grey is hide too: a hue rule left it blue on the olive and red tiers); heads 4 (teal skin, rust frill) and
    # 5 (rust) keep only their blue neck scales
    keep = ndimage.binary_dilation(ivory | red | plate, iterations=1)
    hide_w = (cov & ~keep).astype(float)
    blue = np.clip((s - 0.05) / 0.06, 0, 1) * ((h >= 205) & (h <= 300))
    for k in (4, 5):
        t = part == k
        hide_w[t] = blue[t] * ~keep[t]
    return hide_w, {'hide': cov & (hide_w > 0.5), 'ivory': ivory, 'mouth': red, 'plate': plate}, cov


SPEC = {'hide': 0.15, 'plate': 0.55, 'ivory': 0.5, 'mouth': 0.35, 'other': 0.2}
ROUGH = {'hide': 0.75, 'plate': 0.45, 'ivory': 0.45, 'mouth': 0.4, 'other': 0.7}
CLS = {'hide': 1, 'plate': 1, 'ivory': 4, 'mouth': 7, 'other': 1}

sets = {}
for mat, sel, size, small, src in (
        ('Hydra', UV['part'] == 0, (2048, 2048), (1024, 1024), 'body'),
        ('HydraHeads', UV['part'] > 0, (1536, 1024), (768, 512), 'heads')):
    W, H = size
    part = coverage(sel, W, H); cov = part >= 0
    part_s = coverage(sel, *small); cov_s = part_s >= 0
    if src == 'body':
        base = load(M / 'body_retexture_v2' / 'texture_urls_0_base_color.png', size)
        normal = load(M / 'body_retexture_v2' / 'texture_urls_0_normal.png', small)
        rough = load(M / 'body_retexture_v2' / 'texture_urls_0_roughness.png', small, 'L')
        ao = load(HERE / 'work' / 'ao_body.png', size, 'L')
    else:
        base = atlas('base_color')
        normal = np.asarray(Image.fromarray((atlas('normal') * 255).astype(np.uint8)).resize(small, Image.LANCZOS),
                            np.float64) / 255
        rough = np.asarray(Image.fromarray((atlas('roughness', 'L') * 255).astype(np.uint8)).resize(small, Image.LANCZOS),
                           np.float64) / 255
        ao = load(HERE / 'work' / 'ao_heads.png', size, 'L')
    f = np.clip(0.6 + 0.4 * np.maximum(ao, 0.45), 0, 1)
    g = base.copy(); g[cov] = base[cov] * f[cov][:, None]
    if src == 'heads':
        hh, hs, hv = hsv(base)
        t4 = (part == 4) & ~((hh < 40) & (hs > 0.3)) & ~((hh > 330) & (hs > 0.4))     # not the rust frill or mouth
        g[t4] = np.clip(g[t4] * HEAD4_GAIN, 0, 1)
    save(pad(g, cov), T / f'm266_{src}_basecolor.png')
    base_s = np.asarray(Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8)).resize(small, Image.LANCZOS),
                        np.float64) / 255
    hide_w, C, _ = classes(base_s, part_s)
    other = cov_s & ~(C['hide'] | C['ivory'] | C['mouth'] | C['plate'])
    C['other'] = other
    cls = np.zeros(small[::-1], np.uint8); spec = np.zeros(small[::-1]); rgh = np.full(small[::-1], 0.7)
    for name in ('other', 'hide', 'plate', 'ivory', 'mouth'):
        m = C[name]; cls[m] = CLS[name]; spec[m] = SPEC[name]
        if m.any():
            rgh[m] = np.clip(ROUGH[name] + (rough[m] - np.median(rough[m])) * 0.5, 0.1, 1)
    save(pad(normal, cov_s), T / f'm266_{src}_normal.png')
    save(np.stack([pad(spec, cov_s), pad(rgh, cov_s), np.zeros(small[::-1])], -1), T / f'm266_{src}_metal_rough.png')
    Image.fromarray(cls).save(T / f'm266_{src}_material_classes.png')
    mask = ndimage.gaussian_filter(pad(hide_w, cov_s), 0.7)
    R.write_mask([mask], T / f'm266_{src}_region_mask.png', size=small[0])
    if small[0] != small[1]:                     # write_mask makes squares: rewrite at the atlas aspect
        Image.fromarray(np.stack([(np.clip(mask, 0, 1) * 255 + 0.5).astype(np.uint8)] + [np.zeros(small[::-1], np.uint8)] * 3, -1),
                        'RGBA').save(T / f'm266_{src}_region_mask.png')
    sets[mat] = dict(src=src, base=base_s, hide=C['hide'], cov=cov_s)
    print('SET', mat, {n: int(m.sum()) for n, m in C.items()}, 'covered', int(cov_s.sum()))
    prev = base_s.copy(); prev[C['hide']] = prev[C['hide']] * 0.4 + np.array([1.0, 0.0, 1.0]) * 0.6
    save(prev, HERE / 'work' / f'm266_{src}_mask_preview.png')

# ---------------------------------------------------------------- native hide colours per tier
SPR = ROOT / 'assets_dev' / 'engine' / 'sprites'                  # merged MM7 families live in engine/
acts = {p: np.frombuffer((ROOT / 'assets_dev/worlds/mm7/textures' / f'pal{p:03d}.act').read_bytes()[:768], np.uint8)
        .reshape(256, 3).astype(np.float64) / 255 for p in PALS.values()}
idx = []
for f in sorted(SPR.glob('m266s*.bmp')) + sorted(SPR.glob('m266w*.bmp')):
    a = np.asarray(Image.open(f)); idx.append(a[(a >= 64) & (a <= 191)])
idx = np.concatenate(idx)
nat = {k: acts[p][idx] for k, p in PALS.items()}
ramps = {k: [] for k in PALS}
report = {}
for mat, S in sets.items():
    lum = R.luminance(S['base'][S['hide']]); lo, hi = np.percentile(lum, [2, 98]); srt = np.sort(lum)
    tex_mean = float(lum.mean())
    order = np.argsort(R.luminance(nat['m266_b']))                 # same pixels, ranked by the B (bitmap) palette
    for k in PALS:
        X = R.srgb_to_linear(nat[k][order]); LX = X @ R.LUMA
        kgain = float(LX.mean()) * RAMP_GAIN ** 2.2 / max(tex_mean, 1e-4)
        cols = []
        for i in range(16):
            Li = lo + (hi - lo) * i / 15
            q = np.searchsorted(srt, Li) / len(srt)
            j = int(q * (len(X) - 1)); w = max(30, len(X) // 60)
            c = np.median(X[max(0, j - w):j + w + 1], 0)
            c = c * (Li * kgain / max(float(c @ R.LUMA), 1e-5))
            if i < 5:                                                      # dark end: toward grey of the same luminance
                c = c + (float(c @ R.LUMA) - c) * DARK_DESAT * (1 - i / 5)
            cols.append([round(float(x), 6) for x in np.clip(c, 0, 1)])
        ramps.setdefault((mat, k), {'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': cols})
        report[f'{mat}/{k}'] = {'native_mean_srgb': np.round(nat[k].mean(0) * 255).tolist(), 'mid_stop': cols[8]}
cfg = {'variants': list(PALS), 'palettes': PALS, 'report': report,
       'materials': [{'base': mat, 'prefix': mat, 'mask': f"m266_{S['src']}_region_mask.png", 'regions': ['hide'],
                      'ramps': {k: [ramps[(mat, k)]] for k in PALS}} for mat, S in sets.items()]}
(T / 'm266_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
print('RAMPS', json.dumps(report))
