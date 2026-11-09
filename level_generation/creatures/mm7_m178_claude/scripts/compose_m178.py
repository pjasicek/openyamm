#!/usr/bin/env python3
"""Textures, region masks and tier ramps for the m178 devil (CLAUDE_CREATURE_TEXTURES.md). Run after uv_raster.py
(UVMap, HeadUV at 1024) and bake_ao_natm.py.

Tiers (mm7_m178 variants.json, palette per descriptor): A = 220 Devil Worker (palette 44, ochre-brown hide: the native
frames' own palette, which the HD masters were drawn in), B = 221 Devil Warrior (45, teal-green hide), C = 222 Devil
Captain (46, red hide). Palette entries 140-215 (hide) and 62-75 (ventral plates; the native project's two mask
channels) change between the tiers; spikes, claws, teeth and eyes keep their colours. So TWO regions, in both the body
and the head set (same ramps; merge_head_material.py requires equal ramps): R = hide, G = slate-violet plates (chest,
abdomen and feet tops; violet in A/B, brownish in C).
- Classes per texel from the garment raster and Meshy's colour: bone (pale low-saturation spikes, claws, heel spurs),
  eye (bright yellow), mouth (dark red inside the mouth), plate (slate: cool hue or near-neutral dark), skin (the rest:
  the brown hide and the reddish ears), tooth (garment 1), eyeball (garment 3), spine (garment 2: tail spikes).
- AO multiplied into the base colour (strength 0.4, floor 0.45). ORM red = per-class specular mask (runtime
  openyamm_specular_mask), green roughness; the AO bake stays in work/ao_*.png and graded into the base colour.
- Ramps per tier and region: a square-root luminance curve through each tier's native median, chroma by luminance
  rank from the native region pixels (palette-44 frames mapped back to their index); tier A keeps the texture's chroma.
Writes textures/m178_*."""
import json, sys, colorsys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
NATIVE = HERE.parent / 'mm7_m178' / 'native'
N = 1024
RAMP_GAIN = 1.3
PALS = {'m178_a': 44, 'm178_b': 45, 'm178_c': 46}
VAR = json.load(open(HERE.parent / 'mm7_m178' / 'variants.json'))['variants']
REG_IDX = {r['channel']: r['native_indices'] for r in VAR[0]['regions']}       # 0 hide, 1 plates
SPEC = {'skin': 0.4, 'plate': 0.45, 'bone': 0.5, 'eye': 0.8, 'mouth': 0.6, 'tooth': 0.55, 'eyeball': 0.8, 'spine': 0.5}
ROUGH = {'skin': 0.6, 'plate': 0.55, 'bone': 0.45, 'eye': 0.2, 'mouth': 0.35, 'tooth': 0.4, 'eyeball': 0.2, 'spine': 0.45}
CLASS = {'skin': 1, 'plate': 1, 'bone': 4, 'eye': 6, 'mouth': 7, 'tooth': 5, 'eyeball': 6, 'spine': 4}


def load(path, mode='RGB', n=N):
    im = Image.open(path).convert(mode)
    return np.asarray(im.resize((n, n), Image.LANCZOS) if im.size != (n, n) else im, np.float64) / 255


def save(a, path):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path, optimize=True)


def hsv(rgb):
    h = np.asarray(Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    return h[..., 0] * 360, h[..., 1], h[..., 2]


def pad(img, cov):
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    out = img[iy, ix]; out[cov] = img[cov]; return out


def lin(x): return R.srgb_to_linear(x)


def ao_grade(img, ao, cov, strength=0.4, floor=0.45):
    f = np.clip(1 - strength + strength * np.maximum(ao, floor), 0, 1)
    out = img.copy(); out[cov] = img[cov] * f[cov][:, None]; return out


def classify(base, gar, cov):
    hue, sat, val = hsv(base)
    C = {}
    sk = cov & (gar == 0)
    C['eye'] = sk & (hue > 38) & (hue < 70) & (sat > 0.5) & (val > 0.55)
    C['bone'] = sk & ~C['eye'] & (sat < 0.3) & (val >= 0.45)
    C['mouth'] = sk & ~C['eye'] & ~C['bone'] & ((hue < 18) | (hue > 330)) & (sat > 0.35) & (val < 0.3)
    C['plate'] = sk & ~C['eye'] & ~C['bone'] & ~C['mouth'] & ((((hue > 180) & (hue < 330)) & (sat < 0.55)) | ((sat < 0.14) & (val < 0.45)))
    C['skin'] = sk & ~C['eye'] & ~C['bone'] & ~C['mouth'] & ~C['plate']
    C['tooth'] = cov & (gar == 1); C['eyeball'] = cov & (gar == 3); C['spine'] = cov & (gar == 2)
    return C


# ---------------------------------------------------------------- native region colours per tier
pal = lambda n: np.frombuffer((REPO / f'assets_dev/worlds/mm7/textures/pal{n:03d}.act').read_bytes()[:768], np.uint8).reshape(256, 3)
P = {k: pal(p) for k, p in PALS.items()}
lut = {tuple(c): i for i, c in enumerate(pal(44))}
FR = [f'm178sa{i}' for i in range(5)] + [f'm178w{c}0' for c in 'abcdefgh'] + [f'm178a{c}0' for c in 'abcdefgh'] + ['m178na0', 'm178nb0']
idx = []; miss = 0
for f in FR:
    im = np.asarray(Image.open(NATIVE / f'{f}.png').convert('RGBA'))
    px = im[im[..., 3] > 0][:, :3]
    for c in px:
        i = lut.get(tuple(c))
        if i is None:
            miss += 1
        else:
            idx.append(i)
idx = np.array(idx)
NATIVE_REG = {}
for ch, name in ((0, 'hide'), (1, 'plate')):
    reg = idx[np.isin(idx, REG_IDX[ch])]
    NATIVE_REG[name] = {}
    for k in PALS:
        X = P[k][reg].astype(np.float64) / 255; L = R.luminance(X); keep = L > 0.01
        o = np.argsort(L[keep]); NATIVE_REG[name][k] = X[keep][o]
    print('NATIVE', name, 'pixels', len(reg), 'of', len(idx), '(unmapped', miss, ')',
          {k: np.round(np.median(v, 0) * 255).tolist() for k, v in NATIVE_REG[name].items()})


def ramps_for(native, texel_rgb, base_tier):
    """As compose_m418/m470: the ramp keeps the texture's luminance order over its 2nd-98th percentile range on a
    square-root curve through (texel median -> native median x gain), with chroma by luminance rank from the tier's
    native region pixels; the base tier keeps the texture's own chroma."""
    texel_lum = R.luminance(texel_rgb)
    lo, hi = np.percentile(texel_lum, [2, 98]); tmed = float(np.median(texel_lum)); srt_t = np.sort(texel_lum); t_ord = np.argsort(texel_lum)
    out = {}
    for k in PALS:
        X = native[k]; Ls = R.luminance(X)
        gain = float(np.clip(np.median(Ls) * RAMP_GAIN ** 2.2 / tmed, 0.08, 25.0))
        cols = []
        for i in range(16):
            Li = lo + (hi - lo) * i / 15
            q = np.searchsorted(srt_t, Li) / len(srt_t)
            j0, j1 = int(max(0, q - 0.06) * len(X)), int(min(1, q + 0.06) * len(X)) + 1
            Xw = X[j0:j1]; ch_i = np.mean(lin(Xw) / np.maximum(R.luminance(Xw), 1e-4)[:, None], 0); ch_i /= ch_i @ R.LUMA
            if k == base_tier:
                Tw = texel_rgb[t_ord[int(0.1 * len(t_ord)):int(0.8 * len(t_ord))]]
                ch_i = np.median(lin(Tw) / np.maximum(R.luminance(Tw), 1e-4)[:, None], 0); ch_i /= ch_i @ R.LUMA
            c = ch_i * (tmed * gain) * (max(Li, 1e-4) / tmed) ** 0.5
            c = c / max(1.0, float(c.max()) / 0.92)
            cols.append([round(float(v), 6) for v in c])
        out[k] = {'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': cols}
        print('RAMPFIT', k, 'gain', round(gain, 2), 'mid', [round(x, 3) for x in cols[8]])
    return out


def compose(base, rough_m, raster, ao_png):
    Rz = np.load(HERE / 'work' / raster); gar = Rz['garment']; cov = gar >= 0
    C = classify(base, gar, cov)
    g = ao_grade(base.copy(), load(HERE / 'work' / ao_png, 'L'), cov)
    cls = np.zeros((N, N), np.uint8); spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8)
    for name, m in C.items():
        if m.any():
            cls[m] = CLASS[name]; spec[m] = SPEC[name]
            rgh[m] = np.clip(ROUGH[name] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
    print('CLASSES', raster, {n: int(m.sum()) for n, m in C.items()}, 'covered', int(cov.sum()))
    return g, cls, spec, rgh, cov, C


M = HERE / 'meshy' / 'retexture_v1'
base = load(M / 'texture_urls_0_base_color.png')
g, cls, spec, rgh, cov, C = compose(base, load(M / 'texture_urls_0_roughness.png', 'L'), 'uvraster_UVMap.npz', 'ao_UVMap.png')
HM = HERE / 'meshy' / 'head_retexture_v1'
hb = load(HM / 'texture_urls_0_base_color.png')
hg, hcls, hspec, hrgh, hcov, HC = compose(hb, load(HM / 'texture_urls_0_roughness.png', 'L'), 'uvraster_HeadUV.npz', 'ao_HeadUV.png')
RAMPS = {}
for name, key in (('hide', 'skin'), ('plate', 'plate')):
    trgb = np.concatenate([g[C[key]], hg[HC[key]]])
    RAMPS[name] = ramps_for(NATIVE_REG[name], trgb, 'm178_a')
ramps = {k: [RAMPS['hide'][k], RAMPS['plate'][k]] for k in PALS}
print('MEDIANS body', {n: np.round(np.median(g[m], 0) * 255).tolist() for n, m in C.items() if m.any()})


def mask(Cs, cv):
    return [ndimage.gaussian_filter(pad(Cs[k].astype(float), cv), 0.7) for k in ('skin', 'plate')]


save(pad(g, cov), T / 'm178_basecolor_1k.png'); save(pad(load(M / 'texture_urls_0_normal.png'), cov), T / 'm178_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / 'm178_metal_rough_1k.png')
R.write_mask(mask(C, cov), T / 'm178_region_mask.png', size=N)
Image.fromarray(cls).save(T / 'm178_material_classes.png')
save(pad(hg, hcov), T / 'm178_head_basecolor_1k.png'); save(pad(load(HM / 'texture_urls_0_normal.png'), hcov), T / 'm178_head_normal_1k.png')
save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm178_head_metal_rough_1k.png')
R.write_mask(mask(HC, hcov), T / 'm178_head_region_mask.png', size=N)
Image.fromarray(hcls).save(T / 'm178_head_material_classes.png')
cfg = {'variants': list(PALS),
       'materials': [{'base': 'Devil_A', 'prefix': 'Devil', 'mask': 'm178_region_mask.png', 'regions': ['hide', 'plates'], 'palettes': PALS, 'ramps': ramps},
                     {'base': 'DevilHead_A', 'prefix': 'DevilHead', 'mask': 'm178_head_region_mask.png', 'regions': ['hide', 'plates'], 'palettes': PALS, 'ramps': ramps}]}
(T / 'm178_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
for k in PALS:
    print('RAMP', k, 'hide mid', ramps[k][0]['colors'][8], 'plate mid', ramps[k][1]['colors'][8])
