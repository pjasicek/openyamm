#!/usr/bin/env python3
"""Textures, region masks and tier ramps for the m470 ghoul (CLAUDE_CREATURE_TEXTURES.md). Run after uv_raster.py
(UVMap, HeadUV at 1024) and bake_ao_natm.py.

Tiers: descriptors 454 Ghast (palette 511, ash-blond hair), 455 Ghoul (517, black) and 456 Revenant (525,
orange-brown) (mm7_m470 manifest). The palettes change only the hair in the native frames, so ONE region: the hair,
which lies in the head set; the body set gets an empty mask with the SAME ramps (merge_head_material.py requires equal
ramps). Skin, leather, eyelets, eyes, teeth and claws keep their colours.
- Classes per texel from the garment raster and Meshy's colour: skin (pale), leather (brown, saturated), claw (dark on
  the hands/feet), hair, tooth, eye, lacing (cloth), eyelet (metal).
- AO multiplied into the base colour (strength 0.4, floor 0.45). ORM red = per-class specular mask, green roughness.
- Ramps per tier: a square-root luminance curve through each tier's native median, chroma by luminance rank from the
  native hair pixels (palette-511 frames mapped back to their index; the indices whose colour differs between the
  three palettes); tier A keeps the texture's own chroma.
Writes textures/m470_*."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
NATIVE = HERE.parent / 'mm7_m470' / 'native'
N = 1024
RAMP_GAIN = 1.3
PALS = {'m470_a': 511, 'm470_b': 517, 'm470_c': 525}
SPEC = {'skin': 0.35, 'leather': 0.35, 'claw': 0.6, 'hair': 0.3, 'tooth': 0.5, 'eye': 0.9, 'cloth': 0.2, 'metal': 0.9}
ROUGH = {'skin': 0.6, 'leather': 0.6, 'claw': 0.4, 'hair': 0.55, 'tooth': 0.4, 'eye': 0.2, 'cloth': 0.85, 'metal': 0.3}
CLASS = {'skin': 1, 'leather': 8, 'claw': 4, 'hair': 2, 'tooth': 5, 'eye': 6, 'cloth': 8, 'metal': 9}


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


def classify(base, gar, cov, head, pos=None):
    hue, sat, val = hsv(base)
    C = {}
    skin_g = cov & (gar == 0)
    C['claw'] = skin_g & (val < 0.18) & (sat < 0.35)
    C['leather'] = skin_g & ~C['claw'] & (hue > 8) & (hue < 50) & (sat > 0.3) & (val < 0.75)
    C['skin'] = skin_g & ~C['claw'] & ~C['leather']
    C['hair'] = cov & (gar == 1); C['tooth'] = cov & (gar == 2); C['eye'] = cov & (gar == 3)
    C['cloth'] = cov & (gar == 4); C['metal'] = cov & (gar == 5)
    return C, np.zeros_like(cov)


# ---------------------------------------------------------------- native region colours per tier
pal = lambda n: np.frombuffer((REPO / f'assets_dev/worlds/mm7/textures/pal{n:03d}.act').read_bytes()[:768], np.uint8).reshape(256, 3)
P = {k: pal(p) for k, p in PALS.items()}
lut = {tuple(c): i for i, c in enumerate(pal(511))}
FR = [f'm470sa{i}' for i in range(5)] + [f'm470w{c}0' for c in 'abcdefgh'] + [f'm470a{c}0' for c in 'abcdef'] + ['m470na0', 'm470nb0']
idx = []
for f in FR:
    im = np.asarray(Image.open(NATIVE / f'{f}.png').convert('RGBA'))
    px = im[im[..., 3] > 0][:, :3]
    idx.extend(lut[tuple(c)] for c in px)
idx = np.array(idx)
# only the entries that really change between the tier palettes (a few of 174-247 are equal in all three: pale
# highlights and fletching, which pulled the ramps' top half to white)
CHG = np.array([any((P[k][i] != P['m470_a'][i]).any() for k in PALS) for i in range(256)])
reg = idx[CHG[idx]]
native = {}
for k in PALS:
    X = P[k][reg].astype(np.float64) / 255; L = R.luminance(X); keep = L > 0.02
    o = np.argsort(L[keep]); native[k] = X[keep][o]
print('NATIVE region pixels', len(reg), 'of', len(idx), {k: np.round(np.median(v, 0) * 255).tolist() for k, v in native.items()})


def ramps_for(texel_lum, texel_rgb=None, base_tier=None):
    """Per tier: the ramp keeps the texture's own luminance (identity over the region's 2nd-98th percentile range)
    scaled by GAIN = native median luminance x RAMP_GAIN / texel median luminance (each tier's own brightness), with
    the tier's native chroma (median linear colour / luminance of its saturated region pixels). Rank-matching the
    native pixels copied the sprite's baked white highlights into the top third of the ramp (grey cloth; gob2 lesson)."""
    lo, hi = np.percentile(texel_lum, [2, 98]); tmed = float(np.median(texel_lum)); srt_t = np.sort(texel_lum); t_ord = np.argsort(texel_lum)
    out = {}
    for k in PALS:
        X = native[k]; Ls = R.luminance(X); hsvx = np.array([__import__('colorsys').rgb_to_hsv(*c) for c in X])
        sat = hsvx[:, 1] > (0.15 if np.median(hsvx[:, 1]) > 0.15 else -1)   # the white tier: all pixels
        chroma = np.median(lin(X[sat]) / Ls[sat][:, None], 0); chroma /= chroma @ R.LUMA
        gain = float(np.clip(np.median(Ls) * RAMP_GAIN ** 2.2 / tmed, 0.08, 25.0))   # m470: the black-haired tier needs a gain well below 1
        cols = []
        for i in range(16):
            # (m270: the chain texture is high-contrast (bright link highlights, dark gaps): a straight gain of 5-8 put
            # most stops at white; a square-root curve through (texel median -> native median x gain) keeps the links
            Li = lo + (hi - lo) * i / 15
            # chroma by rank: the stop takes the mean chroma of the native pixels at the same luminance rank as Li
            # among the texels (+-6 %): the Lich's chain is grey in its light entries and blue-violet in its dark ones
            q = np.searchsorted(srt_t, Li) / len(srt_t)
            j0, j1 = int(max(0, q - 0.06) * len(X)), int(min(1, q + 0.06) * len(X)) + 1
            Xw = X[j0:j1]; ch_i = np.mean(lin(Xw) / np.maximum(R.luminance(Xw), 1e-4)[:, None], 0); ch_i /= ch_i @ R.LUMA
            if k == base_tier and texel_rgb is not None:
                # the base tier is the palette the HD masters were drawn in: keep the texture's own chroma per rank
                # (one chroma: the median of the bulk of the chain texels; its brightest texels pick up the gold trim)
                Tw = texel_rgb[t_ord[int(0.1 * len(t_ord)):int(0.8 * len(t_ord))]]
                ch_i = np.median(lin(Tw) / np.maximum(R.luminance(Tw), 1e-4)[:, None], 0); ch_i /= ch_i @ R.LUMA
            c = ch_i * (tmed * gain) * (max(Li, 1e-4) / tmed) ** 0.5
            c = c / max(1.0, float(c.max()) / 0.92)          # keep the hue at the top (no channel clipping)
            cols.append([round(float(v), 6) for v in c])
        out[k] = [{'range': [round(float(lo), 5), round(float(hi), 5)], 'colors': cols}]
        print('RAMPFIT', k, 'chroma', np.round(chroma, 3).tolist(), 'gain', round(gain, 2), 'saturated px', int(sat.sum()))
    return out


def compose(base, normal, rough_m, raster, ao_png, head):
    Rz = np.load(HERE / 'work' / raster); gar = Rz['garment']; cov = gar >= 0
    C, red = classify(base, gar, cov, head, Rz['pos'])
    g = base.copy()
    g = ao_grade(g, load(HERE / 'work' / ao_png, 'L'), cov)
    cls = np.zeros((N, N), np.uint8); spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8)
    for name, m in C.items():
        if m.any():
            cls[m] = CLASS[name]; spec[m] = SPEC[name]
            rgh[m] = np.clip(ROUGH[name] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
    print('CLASSES', 'head' if head else 'body', {n: int(m.sum()) for n, m in C.items()}, 'covered', int(cov.sum()))
    return g, cls, spec, rgh, cov, C, red


# ---------------------------------------------------------------- body and head sets
# second triangle cut (reduce_textured.py): the maps rebaked onto the new UV layout (rebake_uv.py)
M = HERE / 'texturing' / 'rebake_v2' / 'body' if (HERE / 'texturing' / 'rebake_v2' / 'body').exists() else HERE / 'meshy' / 'retexture_v1'
base = load(M / 'texture_urls_0_base_color.png')
g, cls, spec, rgh, cov, C, _ = compose(base, None, load(M / 'texture_urls_0_roughness.png', 'L'), 'uvraster_UVMap.npz', 'ao_UVMap.png', False)
# second triangle cut (reduce_textured.py): the maps rebaked onto the new UV layout (rebake_uv.py)
HM = HERE / 'texturing' / 'rebake_v2' / 'head' if (HERE / 'texturing' / 'rebake_v2' / 'head').exists() else HERE / 'meshy' / 'head_retexture_v1'
hb = load(HM / 'texture_urls_0_base_color.png')
hg, hcls, hspec, hrgh, hcov, HC, _ = compose(hb, None, load(HM / 'texture_urls_0_roughness.png', 'L'), 'uvraster_HeadUV.npz', 'ao_HeadUV.png', True)
_trgb = hg[HC['hair']]
chain_ramps = ramps_for(R.luminance(_trgb), _trgb, 'm470_a')
print('MEDIANS body', {n: np.round(np.median(g[m], 0) * 255).tolist() for n, m in C.items() if m.any()})
save(pad(g, cov), T / 'm470_basecolor_1k.png'); save(pad(load(M / 'texture_urls_0_normal.png'), cov), T / 'm470_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / 'm470_metal_rough_1k.png')
R.write_mask([np.zeros((N, N))], T / 'm470_region_mask.png', size=N)            # no hair in the body set
Image.fromarray(cls).save(T / 'm470_material_classes.png')
save(pad(hg, hcov), T / 'm470_head_basecolor_1k.png'); save(pad(load(HM / 'texture_urls_0_normal.png'), hcov), T / 'm470_head_normal_1k.png')
save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'm470_head_metal_rough_1k.png')
R.write_mask([ndimage.gaussian_filter(pad(HC['hair'].astype(float), hcov), 0.7)], T / 'm470_head_region_mask.png', size=N)
Image.fromarray(hcls).save(T / 'm470_head_material_classes.png')
cfg = {'variants': list(PALS),
       'materials': [{'base': 'Ghoul_A', 'prefix': 'Ghoul', 'mask': 'm470_region_mask.png', 'regions': ['hair'], 'palettes': PALS, 'ramps': chain_ramps},
                     {'base': 'GhoulHead_A', 'prefix': 'GhoulHead', 'mask': 'm470_head_region_mask.png', 'regions': ['hair'], 'palettes': PALS, 'ramps': chain_ramps}]}
(T / 'm470_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
for k in PALS:
    print('RAMP', k, 'mid', [round(x, 3) for x in chain_ramps[k][0]['colors'][8]], 'range', chain_ramps[k][0]['range'])
