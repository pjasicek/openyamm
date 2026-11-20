#!/usr/bin/env python3
"""Glassback texture sets from the Meshy retextures (body: meshy/retexture_v1 with Meshy's own layout copied back;
head: meshy/head_retexture_v1 on HeadUV), per CLAUDE_CREATURE_TEXTURES.md: one shared skin + region mask + ramps.

Classes per texel from the UV rasters (work/uvraster_*.npz: rest position, normal, eyeball flag) and the Meshy colour:
  glass toes (foot texels below 13 cm that are dark), the beak (head texels in front of y -1.30 that are dark),
  eyes (the eyeball pieces), belly (pale texels below the flanks), hide (the rest).
Region mask (RGBA): R hide, G belly, B unused, A rust streaks (procedural 3D noise on the upper hide, continuous across
UV seams: tiers A and B map it with their hide ramp, tier C with rust red). Glass toes, beak and eyes are in no
region (black glass, dark beak, eyes as painted). Ramps per tier from the design brief's colours (no native sprite).
Writes textures/hgb_{basecolor,normal,metal_rough,region_mask,material_classes}_1k.png, the hgb_head_* equivalents,
hgb_ramps.json and review/tier_swatches.png. ORM: R = specular mask (openyamm_specular_mask, as the guard), G
roughness by class, B metallic 0."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / 'textures'
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import region_variants as R

N = 1024
W = np.array([0.2126, 0.7152, 0.0722])


def load(path, mode='RGB'):
    im = Image.open(path).convert(mode)
    if im.size != (N, N):
        im = im.resize((N, N), Image.LANCZOS)
    a = np.asarray(im, np.float64) / 255
    return a


def save(a, path, mode='RGB'):
    Image.fromarray(np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8), mode).save(path, optimize=True)


def pad_index(valid):
    interior = ndimage.binary_erosion(valid, iterations=1)
    _, (iy, ix) = ndimage.distance_transform_edt(~interior, return_indices=True)
    return interior, iy, ix


def pad(a, interior, iy, ix):
    o = a[iy, ix]; o[interior] = a[interior]; return o


def hsv_sat(c):
    mx = c.max(-1); mn = c.min(-1)
    return np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0)


def noise3(pos, scale, seed):
    """Smooth value noise sampled at 3D points (trilinear over a random lattice)."""
    rng = np.random.default_rng(seed)
    G = 48
    lat = ndimage.gaussian_filter(rng.standard_normal((G, G, G)), 1.0, mode='wrap')
    lat /= lat.std()
    p = pos * scale
    return ndimage.map_coordinates(lat, [p[..., 0] % G, p[..., 1] % G, p[..., 2] % G], order=1, mode='wrap')


def ramp(stops_srgb):
    """3 sRGB stops (dark, mid, light) -> 16 linear colours."""
    s = np.array(stops_srgb, np.float64) / 255
    lin = R.srgb_to_linear(s)
    t = np.linspace(0, 1, 16)
    out = np.empty((16, 3))
    for c in range(3):
        out[:, c] = np.interp(t, [0, 0.5, 1], lin[:, c])
    return out.round(5).tolist()


TIERS = {
    'hgb_a': {'hide': [(50, 49, 50), (88, 86, 84), (128, 125, 121)], 'belly': [(96, 94, 90), (142, 139, 133), (184, 180, 172)]},
    'hgb_b': {'hide': [(38, 38, 41), (62, 62, 65), (94, 93, 93)], 'belly': [(84, 82, 80), (124, 121, 117), (164, 160, 153)]},
    'hgb_c': {'hide': [(31, 30, 31), (44, 42, 42), (68, 64, 62)], 'belly': [(70, 66, 63), (104, 98, 92), (142, 134, 126)],
              'rust': [(48, 24, 16), (96, 42, 24), (140, 66, 36)]},
}


def classify(base, ras, head):
    pos, nrm, valid, eye = ras['pos'], ras['nrm'], ras['valid'], ras['eye']
    lum = R.luminance(base)
    lum_s = ndimage.gaussian_filter(lum, 2)
    sat = hsv_sat(base)
    x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]
    toe = valid & (z < 0.13) & (lum_s < 0.06)
    beak = valid & head & (y < -1.30) & (lum_s < 0.07) if head else np.zeros_like(valid)
    eyes = valid & eye
    pale = (lum_s > 0.22) & (sat < 0.32)
    belly = valid & pale & (z < 0.80) & (nrm[..., 2] < 0.55) & ~toe & ~beak & ~eyes
    belly = ndimage.binary_opening(belly, iterations=1)
    hide = valid & ~belly & ~toe & ~beak & ~eyes
    return hide, belly, toe, beak, eyes


def build(prefix, base_path, normal_path, rough_path, ras_path, head, gain=None):
    ras = dict(np.load(ras_path))
    for k in ('valid', 'eye'):
        ras[k] = ras[k].astype(bool)
    base = load(base_path)
    valid = ras['valid']
    interior, iy, ix = pad_index(valid)
    base = pad(base, interior, iy, ix)
    hide, belly, toe, beak, eyes = classify(base, ras, head)
    if gain is not None:
        base = np.clip(base * gain, 0, 1)
    soft = lambda m: ndimage.gaussian_filter(m.astype(np.float64), 1.5)
    w_hide, w_belly = soft(hide), soft(belly)
    keep = (toe | beak | eyes)
    tot = np.maximum(w_hide + w_belly, 1e-6)
    w_hide = np.where(keep, 0, w_hide / np.maximum(tot, 1))
    w_belly = np.where(keep, 0, w_belly / np.maximum(tot, 1))
    # rust streaks: stretched 3D noise on the upper flanks and back plates
    pos = ras['pos']
    ridge = np.clip(1 - np.abs(noise3(pos * np.array([1.0, 1.0, 0.25]), 9.0, 7)) / 0.35, 0, 1) ** 2   # thin vertical streaks
    patch = np.clip((noise3(pos, 3.0, 9) + 0.2) / 0.8, 0, 1)                                        # where they gather
    rust = ridge * patch * np.clip((pos[..., 2] - 0.45) / 0.2, 0, 1) * w_hide
    mask = np.stack([w_hide, w_belly, np.zeros_like(w_hide), rust], -1)
    mask = pad(mask, interior, iy, ix)
    mask[keep] = 0
    save(mask, T / f'{prefix}_region_mask_1k.png', 'RGBA')
    classes = np.zeros(valid.shape, np.uint8)
    classes[valid] = 1; classes[toe] = 4; classes[beak] = 4; classes[eyes] = 6
    Image.fromarray(classes, 'L').save(T / f'{prefix}_material_classes_1k.png')
    rough = np.full(valid.shape, 0.86); rough[toe] = 0.26; rough[beak] = 0.42; rough[eyes] = 0.15
    spec = np.full(valid.shape, 0.12); spec[belly] = 0.08; spec[toe] = 0.9; spec[beak] = 0.55; spec[eyes] = 1.0
    rough = pad(ndimage.gaussian_filter(rough, 1), interior, iy, ix)
    spec = pad(ndimage.gaussian_filter(spec, 1), interior, iy, ix)
    # the beak: dark grey-black horn (Meshy painted it brown)
    if beak.any():
        bl = (base[beak] @ np.array([0.3, 0.5, 0.2]))[:, None]
        base[beak] = np.clip(bl * 0.55 + np.array([0.06, 0.065, 0.075]), 0, 1)
    # glass toes a touch darker and bluer so they read as black glass, eyes kept
    base[toe] = base[toe] * 0.75 + np.array([0.035, 0.04, 0.05]) * 0.25
    save(base, T / f'{prefix}_basecolor_1k.png')
    save(np.stack([spec, rough, np.zeros_like(rough)], -1), T / f'{prefix}_metal_rough_1k.png')
    nm = pad(load(normal_path), interior, iy, ix)
    save(nm, T / f'{prefix}_normal_1k.png')
    return base, mask, valid, hide, belly


def main():
    body = build('hgb', ROOT / 'meshy/retexture_v1/texture_urls_0_base_color.png',
                 ROOT / 'meshy/retexture_v1/texture_urls_0_normal.png', None, ROOT / 'work/uvraster_UVMap.npz', False)
    # grade the body (AO + local contrast), then match the head's hide luminance to the body's at the neck
    subprocess.run([sys.executable, str(ROOT.parent / 'claude_shared/grade_basecolor.py'), '--ao',
                    str(T / 'hgb_ao_1k.png'), '--local', '0.45', '--contrast', '1.08', '--saturation', '1.0',
                    str(T / 'hgb_basecolor_1k.png')], check=True)
    bras = np.load(ROOT / 'work/uvraster_UVMap.npz'); hras = np.load(ROOT / 'work/uvraster_HeadUV.npz')
    graded = load(T / 'hgb_basecolor_1k_graded.png')
    bl = R.luminance(graded)
    neck_b = body[3] & (bras['pos'][..., 1] > -1.04) & (bras['pos'][..., 1] < -0.92) & (bras['pos'][..., 2] > 0.5)
    hbase = load(ROOT / 'meshy/head_retexture_v1/texture_urls_0_base_color.png')
    hv = hras['valid'].astype(bool)
    hl = R.luminance(hbase)
    neck_h = hv & (hras['pos'][..., 1] > -1.12) & (hras['pos'][..., 2] > 0.5) & (hl < 0.2)
    gain = float(np.median(bl[neck_b]) / max(np.median(hl[neck_h]), 1e-4)) ** (1 / 2.2)
    print('SEAM gain', round(gain, 3), 'body neck', int(neck_b.sum()), 'head neck', int(neck_h.sum()))
    head = build('hgb_head', ROOT / 'meshy/head_retexture_v1/texture_urls_0_base_color.png',
                 ROOT / 'meshy/head_retexture_v1/texture_urls_0_normal.png', None, ROOT / 'work/uvraster_HeadUV.npz',
                 True, gain=gain)
    subprocess.run([sys.executable, str(ROOT.parent / 'claude_shared/grade_basecolor.py'), '--ao',
                    str(T / 'hgb_ao_1k.png'), '--ao-strength', '0', '--local', '0.45', '--contrast', '1.08',
                    '--saturation', '1.0', str(T / 'hgb_head_basecolor_1k.png')], check=True)
    hgraded = load(T / 'hgb_head_basecolor_1k_graded.png')
    # ranges over both sets together (body and head share one ramp set; merge_head_material requires it)
    regions = {}
    for name, ch in (('hide', 0), ('belly', 1), ('rust', 3)):
        lum = np.concatenate([R.luminance(graded)[body[1][..., ch] > 0.9], R.luminance(hgraded)[head[1][..., ch] > 0.9]])
        if name == 'rust':
            lum = np.concatenate([R.luminance(graded)[body[1][..., 0] > 0.9], R.luminance(hgraded)[head[1][..., 0] > 0.9]])
        lo, hi = np.percentile(lum, 2), np.percentile(lum, 98)
        regions[name] = [round(float(lo), 4), round(float(hi), 4)]
    print('RANGES', regions)
    ramps = {}
    for tier, cols in TIERS.items():
        hide = {'range': regions['hide'], 'colors': ramp(cols['hide'])}
        belly = {'range': regions['belly'], 'colors': ramp(cols['belly'])}
        rust = {'range': regions['rust'], 'colors': ramp(cols.get('rust', cols['hide']))}
        blank = {'range': [0.0, 1.0], 'colors': ramp(cols['hide'])}
        ramps[tier] = [hide, belly, blank, rust]
    cfg = {'variants': list(TIERS), 'materials': [
        {'base': 'Glassback_A', 'prefix': 'Glassback', 'mask': 'hgb_region_mask_1k.png', 'ramps': ramps},
        {'base': 'GlassbackHead_A', 'prefix': 'GlassbackHead', 'mask': 'hgb_head_region_mask_1k.png', 'ramps': ramps}],
        'notes': 'regions R hide, G belly, B unused (blank ramp, empty mask), A rust streaks (C only; A/B = hide); '
                 'colours from the design brief (no native sprite): A grey hide, B darker, C near-black with rust'}
    json.dump(cfg, open(T / 'hgb_ramps.json', 'w'), indent=1)
    # tier swatches: body texture as each tier would render (engine rule), for a quick look
    from viewer_bake import bake
    rows = []
    for tier in TIERS:
        rows.append(np.concatenate([bake(graded, body[1], ramps[tier]), bake(hgraded, head[1], ramps[tier])], 1))
    sheet = np.concatenate(rows, 0)
    Image.fromarray((np.clip(sheet, 0, 1) * 255).astype(np.uint8)).resize((1024, 768)).save(ROOT / 'review/tier_swatches.png')


if __name__ == '__main__':
    sys.path.insert(0, str(ROOT / 'scripts'))
    main()
