#!/usr/bin/env python3
"""Textures, region masks and tier ramps for hvf, the Landfall villager (female) of Hesper (CLAUDE_CREATURE_TEXTURES.md).
Run after uv_raster.py (UVMap, HeadUV at 1024) and bake_ao_natm.py.

No native sprite: the tiers are authored. Three outfits vf_a/vf_b/vf_c recolour FOUR regions (README):
R = the coat-dress (dark slate blue cloth of piece 0), G = its off-white sleeves, under-tunic and trims (piece 0),
B = the sash (red on piece 0, the sash tail piece 10 and the knot ends), A = the hair (bun and fringe pieces 3/11, the
dark hair painted on the head shell). Gold piping and clasps, the ceramic bag and strap, earrings, the cuff light,
boots, skin and trousers stay out of every mask.
- Classes per texel by piece and colour; skin repainted as one albedo x Meshy's fine shading (the natm rule), the hair
  likewise; AO graded; ORM red = per-class specular mask, green = roughness.
- Ramps (claude_shared/region_variants.fit_ramps): a tier without a MIDS entry is fitted to the composed texture itself;
  the others to targets that keep the texture's luminance structure per texel with a new mid colour (target = mid_lin
  * lum(texel) / lum(region median)). Tier A keeps Meshy's off-white, red and hair; its coat takes the concept's slate
  blue (Meshy painted it near black). Masks padded into the gutters.
PREVIEW=1 also writes work/classes_body.png / classes_head.png. Writes textures/hvf_*."""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R
T = HERE / 'textures'; T.mkdir(exist_ok=True)
N = 1024
SKIN_MIX = 0.85
VARIANTS = ['vf_a', 'vf_b', 'vf_c']
REGIONS = ['coat', 'offwhite', 'sash', 'hair']
# mid colours (sRGB 0..255) per region and tier; a tier without an entry keeps the texture (tier A mostly)
MIDS = {'coat': {'vf_a': (70, 84, 104), 'vf_b': (70, 88, 80), 'vf_c': (88, 74, 90)},   # A: the concept's slate blue (Meshy painted it near black)
        'offwhite': {'vf_b': (230, 206, 148), 'vf_c': (194, 197, 202)},
        'sash': {'vf_b': (176, 128, 44), 'vf_c': (30, 110, 110)},
        'hair': {'vf_b': (136, 104, 66), 'vf_c': (124, 54, 28)}}
COAT_PIECES = [0]
SASH_PIECES = [0, 10, 12, 13, 27]
HAIR_PIECES = [3, 11]
SKIN_PIECES = [1, 4, 6]
CERAMIC_PIECES = [5, 7, 19, 21, 22, 26]
BOOT_PIECES = [8, 9, 23, 24]
CLASS = {'trim': 8, 'skin': 1, 'hair': 2, 'coat': 8, 'offwhite': 8, 'sash': 8, 'trousers': 8, 'leather': 8, 'gold': 9,
         'ceramic': 11, 'eye': 6}
SPEC = {'trim': 0.2, 'skin': 0.45, 'hair': 0.3, 'coat': 0.2, 'offwhite': 0.2, 'sash': 0.2, 'trousers': 0.2, 'leather': 0.35,
        'gold': 1.0, 'ceramic': 0.7, 'eye': 0.9}
ROUGH = {'trim': 0.85, 'skin': 0.5, 'hair': 0.6, 'coat': 0.85, 'offwhite': 0.85, 'sash': 0.8, 'trousers': 0.85, 'leather': 0.6,
         'gold': 0.3, 'ceramic': 0.35, 'eye': 0.2}
PREVIEW_COL = {'trim': (255, 120, 0), 'skin': (230, 170, 140), 'hair': (150, 90, 20), 'coat': (40, 60, 200), 'offwhite': (230, 230, 200),
               'sash': (230, 20, 20), 'trousers': (120, 120, 120), 'leather': (90, 50, 20), 'gold': (250, 210, 0),
               'ceramic': (0, 230, 230), 'eye': (255, 0, 255)}


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
def srgb(x):
    x = np.asarray(x, np.float64); return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(np.maximum(x, 0), 1 / 2.4) - 0.055)


def repaint(img, m, albedo, sigma=6.0, clip=(0.5, 1.5)):
    L = R.luminance(img)
    num = ndimage.gaussian_filter(np.where(m, L, 0.0), sigma); den = ndimage.gaussian_filter(m.astype(float), sigma)
    Lb = num / np.maximum(den, 1e-4)
    detail = np.clip((L / np.maximum(Lb, 1e-4)) ** 1.15, *clip)
    new = srgb(np.clip(lin(albedo)[None, :] * detail[m][:, None], 0, 1))
    out = img.copy(); out[m] = img[m] * (1 - SKIN_MIX) + new * SKIN_MIX
    return out


def ao_grade(img, ao, cov, strength=0.4, floor=0.45):
    f = np.clip(1 - strength + strength * np.maximum(ao, floor), 0, 1)
    out = img.copy(); out[cov] = img[cov] * f[cov][:, None]; return out


def classify(base, gar, piece, cov, pos):
    h, s, v = hsv(base)
    C = {}
    C['eye'] = cov & (gar == 4)
    gold = (h > 30) & (h < 62) & (s > 0.38) & (v > 0.38)
    C['gold'] = cov & gold & ~np.isin(piece, SKIN_PIECES) & ~C['eye']
    red = ((h < 16) | (h > 335)) & (s > 0.42) & (v > 0.22)
    C['sash'] = cov & np.isin(piece, SASH_PIECES) & red & ~C['gold']
    C['sash'] |= cov & (piece == 10) & ~C['gold']                        # the tail is all sash
    white = (s < 0.38) & (v > 0.55)                                     # Meshy's off-white is warm (h 30-60, s ~0.2)
    C['offwhite'] = cov & np.isin(piece, COAT_PIECES) & white & ~C['gold'] & ~C['sash']
    slate = (v < 0.45) & (((h > 150) & (h < 280)) | (s < 0.12))         # the dark slate cloth (h ~200, v ~0.19)
    C['coat'] = cov & np.isin(piece, COAT_PIECES) & slate & ~C['gold'] & ~C['sash'] & ~C['offwhite']
    C['trim'] = cov & np.isin(piece, COAT_PIECES) & ~C['coat'] & ~C['gold'] & ~C['sash'] & ~C['offwhite']   # seams, shadows: unmasked
    C['ceramic'] = cov & np.isin(piece, CERAMIC_PIECES) & ~C['gold']
    C['leather'] = cov & np.isin(piece, BOOT_PIECES) & ~C['gold']
    C['trousers'] = cov & (piece == 2)
    z, y = pos[..., 2], pos[..., 1]                                     # rest position: hair only on the scalp, not the neck
    scalp = (z > 1.585) | ((y > 0.0) & (z > 1.50))
    hair_painted = np.isin(piece, [1]) & (v < 0.36) & (s > 0.15) & (h > 5) & (h < 45) & scalp
    C['hair'] = cov & (np.isin(piece, HAIR_PIECES) | hair_painted) & ~C['gold'] & ~C['eye']
    taken = np.any([m for m in C.values()], axis=0)
    C['skin'] = cov & ~taken & np.isin(piece, SKIN_PIECES)
    C['gold'] |= cov & ~taken & ~C['skin']                                # small fittings (buttons, rings, clasps)
    return C


def build(meshy_dir, raster, ao_png, tag, albedo=None):
    base = load(meshy_dir / 'texture_urls_0_base_color.png'); normal = load(meshy_dir / 'texture_urls_0_normal.png')
    rough_m = load(meshy_dir / 'texture_urls_0_roughness.png', 'L')
    Rz = np.load(HERE / 'work' / raster); gar, piece = Rz['garment'], Rz['piece']; cov = gar >= 0
    C = classify(base, gar, piece, cov, Rz['pos'])
    if os.environ.get('PREVIEW'):
        pv = np.zeros((N, N, 3), np.uint8)
        for k, m in C.items():
            pv[m] = PREVIEW_COL[k]
        Image.fromarray(pv).save(HERE / 'work' / f'classes_{tag}.png')
    if albedo is None:                                     # the head reuses the body's albedo: no neck seam
        albedo = np.median(base[C['skin']], 0) if C['skin'].sum() > 100 else np.array([0.85, 0.65, 0.55])
    # body set: Meshy painted dark hair strands over the neck below the head cut; a tighter detail clip flattens them
    g = repaint(base, C['skin'], albedo, clip=(0.82, 1.15) if tag == 'body' else (0.5, 1.5))
    neck = C['skin'] & (Rz['pos'][..., 2] < 1.52)                       # and on the head set's neck above the cut
    if tag == 'head' and neck.sum() > 100:
        g = repaint(g, neck, albedo, clip=(0.82, 1.15))
    if C['trousers'].sum() > 100:
        # Meshy projected the coat's slate and the sash's red onto the trousers above the knees (hidden in every
        # master view), which showed as a black patch through the coat's front split below the sash (user review
        # 2026-10-22): one albedo (the shins' light grey) x Meshy's fine shading over the whole trouser piece
        lowleg = C['trousers'] & (Rz['pos'][..., 2] < 0.5)
        g = repaint(g, C['trousers'], np.median(base[lowleg], 0), clip=(0.75, 1.2))
    if C['hair'].sum() > 100:
        g = repaint(g, C['hair'], np.median(base[C['hair']], 0), clip=(0.65, 1.25))
    if tag == 'body':                                       # the neck below the head cut: Meshy carved hair strands
        nk = C['skin'] & (piece == 1)                       # into the normal map too; flat there
        normal = normal.copy(); normal[nk] = (0.5, 0.5, 1.0)
    g = ao_grade(g, load(HERE / 'work' / ao_png, 'L'), cov)
    print('CLASSES', tag, {k: int(m.sum()) for k, m in C.items()}, 'covered', int(cov.sum()),
          'skin albedo', np.round(albedo * 255).tolist())
    cls = np.zeros((N, N), np.uint8); spec = np.zeros((N, N)); rgh = np.full((N, N), 0.8)
    for k, m in C.items():
        if m.any():
            cls[m] = CLASS[k]; spec[m] = SPEC[k]; rgh[m] = np.clip(ROUGH[k] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
    return g, normal, spec, rgh, cls, C, cov, albedo


def masks(C, cov):
    out = []
    for r in REGIONS:
        m = ndimage.gaussian_filter(pad(C[r].astype(float), cov), 0.7)
        out.append(m)
    return out


g, normal, spec, rgh, cls, C, cov, ALB = build(HERE / 'meshy' / 'body_texture_v1', 'uvraster_UVMap.npz', 'ao_UVMap.png', 'body')
save(pad(g, cov), T / 'hvf_basecolor_1k.png'); save(pad(normal, cov), T / 'hvf_normal_1k.png')
save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / 'hvf_metal_rough_1k.png')
MB = masks(C, cov)
R.write_mask(MB, T / 'hvf_region_mask.png', size=N)
Image.fromarray(cls).save(T / 'hvf_material_classes.png')
hg, hn, hspec, hrgh, hcls, HC, hcov, _ = build(HERE / 'meshy' / 'head_texture_v1', 'uvraster_HeadUV.npz', 'ao_HeadUV.png', 'head', ALB)
save(pad(hg, hcov), T / 'hvf_head_basecolor_1k.png'); save(pad(hn, hcov), T / 'hvf_head_normal_1k.png')
save(np.stack([pad(hspec, hcov), pad(hrgh, hcov), np.zeros((N, N))], -1), T / 'hvf_head_metal_rough_1k.png')
MH = masks(HC, hcov)
R.write_mask(MH, T / 'hvf_head_region_mask.png', size=N)
Image.fromarray(hcls).save(T / 'hvf_head_material_classes.png')

# the neck below the head cut (body set, 710 coarse texels in the V of the collar): Meshy painted hair strands there;
# one flat colour = the head set's neck median, graded by the body AO (no strands, no seam at the cut)
RZB = np.load(HERE / 'work' / 'uvraster_UVMap.npz'); RZH = np.load(HERE / 'work' / 'uvraster_HeadUV.npz')
nk_b = C['skin'] & (RZB['piece'] == 1)
nk_h = HC['skin'] & (RZH['pos'][..., 2] < 1.52)
if nk_b.any() and nk_h.sum() > 100:
    ao_b = load(HERE / 'work' / 'ao_UVMap.png', 'L')
    flat = np.median(hg[nk_h], 0)
    g[nk_b] = flat[None, :] * np.clip(1 - 0.4 + 0.4 * np.maximum(ao_b[nk_b], 0.45), 0, 1)[:, None]
    save(pad(g, cov), T / 'hvf_basecolor_1k.png')
    print('NECK body texels', int(nk_b.sum()), 'flat', np.round(flat * 255).tolist())

# ramps: one fit per region over the body and head texels together (both materials share them: no neck seam)
gp, hp = pad(g, cov), pad(hg, hcov)
both = np.concatenate([gp, hp], 0)
report = {}
RR = {}
for ri, r in enumerate(REGIONS):
    w = np.concatenate([MB[ri], MH[ri]], 0)
    core = w >= 0.9
    L = R.luminance(both); Lm = float(np.median(L[core]))
    targets = {v: both for v in VARIANTS}
    for v, mid in MIDS[r].items():
        mid_lin = R.srgb_to_linear(np.array(mid, np.float64) / 255)
        t_lin = np.clip(mid_lin[None, None, :] * (L / max(Lm, 1e-4))[..., None], 0, 1)
        tgt = both.copy(); tgt[core] = srgb(t_lin[core]); targets[v] = tgt
    RR[r], report[r] = R.fit_ramps(both, targets, w)
ramps = {k: [RR[r][k] for r in REGIONS] for k in VARIANTS}
mats = [{'base': 'HVF_A', 'prefix': 'HVF', 'mask': 'hvf_region_mask.png', 'regions': REGIONS, 'ramps': ramps},
        {'base': 'HVFHead_A', 'prefix': 'HVFHead', 'mask': 'hvf_head_region_mask.png', 'regions': REGIONS, 'ramps': ramps}]
(T / 'hvf_ramps.json').write_text(json.dumps({'variants': VARIANTS, 'mids': MIDS, 'fit_report': report,
                                              'materials': mats}, indent=1) + '\n')
for r in REGIONS:
    print('RAMPFIT', r, report[r])
for k in VARIANTS:
    print('RAMP', k, {r: [round(float(srgb(x)) * 255) for x in RR[r][k]['colors'][8]] for r in REGIONS})
