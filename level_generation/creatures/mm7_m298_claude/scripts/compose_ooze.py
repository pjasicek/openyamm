#!/usr/bin/env python3
"""Ooze runtime maps from meshy/retexture_v1, one shared skin for the three tiers (CLAUDE_CREATURE_TEXTURES.md):
- base colour 2048: Meshy's map graded with the baked blob AO (work/ao_body.png, scripts/tex_prep.py) by
  claude_shared/grade_basecolor.py, then crease/highlight shading from the rest mesh's curvature (work/uv3d.npz):
  concave creases toward black, convex up-facing lump tops toward white, as the sprites' baked wet shading
  (mm6_ooz_claude user review: "more white-ish and black so it reads 3D");
- normal 1024 (Meshy, +y down; tools/prepare_actor_glb.py converts it); ORM 1024: R per-texel specular scale
  (openyamm_specular_mask: no sheen in creases and occlusion), G roughness ROUGH (+-0.05 from Meshy's variation),
  B metallic 0;
- region mask 1024: the whole slime is one region (R = 1 everywhere, gutters included, so no tier-A seams);
- tier ramps (textures/ooze_ramps.json): native pixels aligned across palettes 299 (A, emerald) / 300 (B,
  sapphire) / 301 (C, bloodstone), every frame of every action rendered through each palette
  (scripts/native_palettes.py -> references/native_variants); colour by luminance rank, luminance from the texel
  scaled to the native mean x GAIN (rank_ramps). The sprites' near-white highlight entries are kept (QMAX), so lifted
  lump tops take the sprites' pale highlights;
- textures/ooze_material_classes.png: 11 (other: slime) everywhere.
The pod, knob and globules have no texels of their own: export_runtime.py maps them onto the blob's top surface."""
import json, subprocess, sys, os
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import native_shading as NS
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
M = HERE / 'meshy' / 'retexture_v1'
NB, N = 2048, 1024
ROUGH = float(os.environ.get('OOZE_ROUGH', '0.42'))
CREASE_AT, CREASE_DARK, HIGHLIGHT = 0.15, 0.6, 0.6
NV = HERE / 'references' / 'native_variants'
TIERS = {'m298_a': 299, 'm298_b': 300, 'm298_c': 301}
GAIN = float(os.environ.get('OOZE_GAIN', '0.8'))   # engine gloss adds light (mm6_ooz in-game A/B: 0.9)
QMAX = 0.995
CHROMA = float(os.environ.get('OOZE_CHROMA', '1.1'))


def raster_attrs(data, names, n):
    """Rest-pose attributes per texel (barycentric over the blob's UV triangles in work/uv3d.npz); NaN outside."""
    out = {k: np.full((n, n) + data[k].shape[2:], np.nan) for k in names}
    for k, uv in enumerate(data['uv']):
        p = np.stack([uv[:, 0] * n, (1 - uv[:, 1]) * n], 1)
        x0, y0 = np.maximum(np.floor(p.min(0)).astype(int), 0)
        x1, y1 = np.minimum(np.ceil(p.max(0)).astype(int), n - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = p
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12:
            continue
        w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / d
        w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / d
        w2 = 1 - w0 - w1
        inside = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
        ys, xs = np.nonzero(inside)
        for name in names:
            v = data[name][k]
            val = (w0[inside, None] * v[0] + w1[inside, None] * v[1] + w2[inside, None] * v[2]) if v.ndim == 2 else \
                (w0[inside] * v[0] + w1[inside] * v[1] + w2[inside] * v[2])
            out[name][y0 + ys, x0 + xs] = val
    return out


def pad(img, cov):
    from scipy import ndimage
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    return img[iy, ix]


def native_pixels():
    cols = {p: [] for p in TIERS.values()}
    for path in sorted(NV.glob('m298*_299.png')):
        stem = path.name[:-len('_299.png')]
        imgs = {p: np.asarray(Image.open(NV / f'{stem}_{p}.png').convert('RGBA'), np.float64) / 255
                for p in TIERS.values()}
        mask = imgs[299][..., 3] > 0.9
        for p in TIERS.values():
            cols[p].append(imgs[p][mask][:, :3])
    cols = {p: np.concatenate(v) for p, v in cols.items()}
    lum = NS.srgb_to_linear(cols[299]) @ NS.LUMA
    keep = lum <= np.quantile(lum, QMAX)
    return {'region': np.zeros(int(keep.sum()), int), 'region_names': np.array(['slime']),
            **{f'p{p}': c[keep] for p, c in cols.items()}}


def rank_ramps(base, pixels):
    """Per tier: stop i sits at the base's slime luminance Li (p0.5..p99.5); its colour (hue, saturation) is the
    tier's native pixel at the same luminance RANK (the palette-299 order, the same pixels read in every palette), and
    its luminance is the texel's own, scaled so the slime's mean equals the native mean x GAIN (linear). Matching by
    absolute luminance (transfer_ramps) read pastel: Meshy's slime is brighter than the sprite, so mid stops picked the
    sprites' near-white glints. The darkest stops are desaturated toward grey (their native hue is noise)."""
    lum = (NS.srgb_to_linear(base) @ NS.LUMA).ravel()
    srt = np.sort(lum)
    lo, hi = np.percentile(lum, 0.5), np.percentile(lum, 99.5)
    ref = NS.srgb_to_linear(pixels['p299'])
    order = np.argsort(ref @ NS.LUMA)
    k = float((ref @ NS.LUMA).mean()) * GAIN / max(float(lum.mean()), 1e-5)
    ramps = {}
    for variant, pal in TIERS.items():
        X = NS.srgb_to_linear(pixels[f'p{pal}'])[order]
        cols = []
        for i in range(16):
            Li = lo + (hi - lo) * i / 15
            q = np.searchsorted(srt, Li) / len(srt)
            j = int(q * (len(X) - 1))
            w = max(len(X) // 200, 20)
            c = np.median(X[max(0, j - w):j + w + 1], 0)
            grey = float(c @ NS.LUMA)
            sat = CHROMA * min(1.0, 0.35 + i / 4)                  # darkest stops desaturated
            c = grey + (c - grey) * sat
            c = np.clip(c, 1e-5, None) * (Li * k / max(float(c @ NS.LUMA), 1e-6))
            cols.append([round(float(x), 6) for x in np.clip(c, 0, 1)])
        ramps[variant] = [{'range': [round(float(lo), 6), round(float(hi), 6)], 'colors': cols}]
    print('RANK gain k', round(k, 3), 'native mean', round(float((ref @ NS.LUMA).mean()), 4), 'tex mean',
          round(float(lum.mean()), 4))
    return ramps


raw = HERE / 'work' / 'ooze_basecolor_raw.png'
Image.open(M / 'texture_urls_0_base_color.png').convert('RGB').resize((NB, NB), Image.LANCZOS).save(raw)
ao = Image.open(HERE / 'work' / 'ao_body.png').convert('L').resize((NB, NB), Image.LANCZOS)
ao.save(HERE / 'work' / 'ao_2k.png')
subprocess.run([sys.executable, str(HERE.parent / 'claude_shared' / 'grade_basecolor.py'), '--ao',
                str(HERE / 'work' / 'ao_2k.png'), '--ao-strength', '0.6', '--local', '0.4', '--contrast', '1.08',
                '--saturation', '1.1', str(raw)], check=True)
graded = HERE / 'work' / 'ooze_basecolor_raw_graded.png'
data = np.load(HERE / 'work' / 'uv3d.npz')
attrs = raster_attrs(data, ['curv', 'nz'], NB)
cov = ~np.isnan(attrs['curv'])
curv = pad(np.nan_to_num(attrs['curv']), cov)
nz = pad(np.nan_to_num(attrs['nz']), cov)
base = np.asarray(Image.open(graded).convert('RGB'), np.float64) / 255
crease = np.clip(curv / CREASE_AT, 0, 1) ** 0.8
top = np.clip((-curv - 0.12) / 0.3, 0, 1) * np.clip(nz, 0, 1) ** 1.5
base = base * (1 - CREASE_DARK * crease[..., None])
base = base + (1 - base) * (HIGHLIGHT * top[..., None])
Image.fromarray((np.clip(base, 0, 1) * 255 + 0.5).astype(np.uint8)).save(T / 'ooze_basecolor_2k.png', optimize=True)
print('CAVITY crease texels', int((crease > 0.5).sum()), 'highlight texels', int((top > 0.5).sum()),
      'covered', round(float(cov.mean()), 3))
Image.open(M / 'texture_urls_0_normal.png').convert('RGB').resize((N, N), Image.LANCZOS).save(T / 'ooze_normal_1k.png')
mr = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((N, N), Image.LANCZOS),
                np.float64) / 255
rough = np.clip(ROUGH + 0.05 * (mr - mr.mean()) / max(mr.std(), 1e-3), ROUGH - 0.12, ROUGH + 0.12)
crease1 = np.asarray(Image.fromarray((crease * 255).astype(np.uint8)).resize((N, N), Image.LANCZOS), np.float64) / 255
ao1 = np.asarray(ao.resize((N, N), Image.LANCZOS), np.float64) / 255
spec = np.clip(1 - 0.95 * crease1, 0, 1) * ao1 ** 1.5
orm = np.stack([spec, rough, np.zeros_like(rough)], -1)
Image.fromarray((orm * 255 + 0.5).astype(np.uint8)).save(T / 'ooze_metal_rough_1k.png')
Image.fromarray(np.full((N, N), 11, np.uint8), 'L').save(T / 'ooze_material_classes.png')
weight = np.ones((N, N))
R.write_mask([weight], T / 'ooze_region_mask.png', size=N)
pixels = native_pixels()
base_s = R.load_srgb(T / 'ooze_basecolor_2k.png')
ramps = rank_ramps(base_s, pixels)
config = {'variants': list(TIERS),
          'materials': [{'base': 'Ooze_A', 'prefix': 'Ooze', 'mask': 'ooze_region_mask.png', 'regions': ['slime'],
                         'palettes': TIERS, 'ramps': ramps, 'gain': GAIN, 'chroma': CHROMA,
                         'native_pixels': int(len(pixels['region']))}]}
(T / 'ooze_ramps.json').write_text(json.dumps(config, indent=1) + '\n')
for v in ramps:
    c = np.array(ramps[v][0]['colors'])
    print('RAMP', v, ramps[v][0]['range'], 'stops 0/8/15 sRGB',
          [list((NS.linear_to_srgb(c[i]) * 255).round().astype(int)) for i in (0, 8, 15)])
print('COMPOSED')
