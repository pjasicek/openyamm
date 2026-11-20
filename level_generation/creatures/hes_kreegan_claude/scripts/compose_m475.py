#!/usr/bin/env python3
"""Textures for the Blaster Guy (CLAUDE_CREATURE_TEXTURES.md). Run after uv_raster.py (UVMap, HeadUV at 1024) and
bake_ao_natm.py. ONE look: descriptors 457 Tolberti, 458 Robert the Wise and 459 Blaster Guy C all draw sprite group
m476 in palette 527 (manifest descriptor_animations), so there are no colour tiers, no region mask and no ramps
(build_runtime.sh then applies the material extras only, scripts/set_extras.py).
- Classes per texel from the piece raster and Meshy's paint: skin (warm, moderately saturated texels of the head and
  hand pieces), hair/beard (brown texels of the head piece), metal (the cuff buttons, belt studs and rivets, shoe
  buckles: rigid pieces 9-26 except the cuffs), cloth (everything else: black cape, shirt, trousers; purple and white
  vest); leather boots and belt are cloth-class here (one roughness band).
- AO multiplied into the base colour (strength 0.4, floor 0.45). ORM: R per-class specular mask, G roughness, B 0.
- Neck seam between the head and body atlases matched (neck_match).
Writes textures/hgd_* (body 1K, head 1K, material class maps)."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
T = HERE / 'textures'; T.mkdir(exist_ok=True)
N = 1024
SPEC = {'skin': 0.3, 'hair': 0.25, 'cloth': 0.25, 'metal': 0.85, 'eye': 0.9}
ROUGH = {'skin': 0.6, 'hair': 0.55, 'cloth': 0.75, 'metal': 0.3, 'eye': 0.2}
CLASS = {'skin': 1, 'hair': 2, 'cloth': 8, 'metal': 9, 'eye': 6}
METAL_PIECES = {9, 10, 11, 12, 13, 15, 18, 20, 21, 22, 23, 24, 25, 26}
EYE_PIECES = {14, 16, 17, 19}


def load(path, mode='RGB', n=N):
    im = Image.open(path).convert(mode)
    return np.asarray(im.resize((n, n), Image.LANCZOS) if im.size != (n, n) else im, np.float64) / 255


def save(a, path):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path, optimize=True)


def pad(img, cov):
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    out = img[iy, ix]; out[cov] = img[cov]; return out


def hsv(rgb):
    h = np.asarray(Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    return h[..., 0] * 360, h[..., 1], h[..., 2]


def compose(job, raster, ao_png):
    Rz = np.load(HERE / 'work' / raster); pc = Rz['piece']; cov = pc >= 0
    base = load(HERE / 'meshy' / job / 'texture_urls_0_base_color.png')
    rough_m = load(HERE / 'meshy' / job / 'texture_urls_0_roughness.png', 'L')
    h, s, v = hsv(base)
    C = {}
    headhand = np.isin(pc, (1, 3, 4))
    C['eye'] = cov & np.isin(pc, list(EYE_PIECES))
    C['metal'] = cov & np.isin(pc, list(METAL_PIECES))
    C['skin'] = cov & headhand & (h < 35) & (s > 0.18) & (s < 0.65) & (v > 0.35)
    C['hair'] = cov & (pc == 1) & ~C['skin'] & (h < 45) & (v < 0.6)
    C['cloth'] = cov & ~C['eye'] & ~C['metal'] & ~C['skin'] & ~C['hair']
    ao = load(HERE / 'work' / ao_png, 'L')
    f = np.clip(1 - 0.4 + 0.4 * np.maximum(ao, 0.45), 0, 1)
    g = base.copy(); g[cov] = base[cov] * f[cov][:, None]
    cls = np.zeros((N, N), np.uint8); spec = np.zeros((N, N)); rgh = np.full((N, N), 0.7)
    for name, m in C.items():
        if m.any():
            cls[m] = CLASS[name]; spec[m] = SPEC[name]
            rgh[m] = np.clip(ROUGH[name] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
    print('CLASSES', job, {n: int(m.sum()) for n, m in C.items()}, 'covered', int(cov.sum()))
    return g, cls, spec, rgh, cov


def neck_match(out):
    """The head atlas covers the head piece above z NECK_CUT (uv_raster HeadUV), the body atlas its neck below; Meshy
    painted the head atlas's bottom rows dark (a collar shadow, ~0.39/0.28/0.26) and the body atlas's neck pale
    (~0.87/0.65/0.54) against the head's neck skin (~0.69/0.50/0.42): a dark band and a tone step at the seam (user review
    2026-10-20). Front and sides only (y < +0.02, fading out by +0.04: the hair starts there):
    - head atlas: skin-hued texels of the head piece below NECK_TOP are replaced by the reference skin (median of the
      head's neck skin between NECK_TOP and NECK_TOP + 2 cm) times their own luminance ratio to the band's, clamped to +-8 %
      (a little grain kept, the darkening and its speckle removed), fading back to the original 0.5-1.5 cm above it;
    - head atlas, a strip from 1 cm below to 2.5 cm above NECK_TOP: 7-texel median (stubble dots on the neck's sides);
    - body atlas: the head piece's skin-hued neck texels are scaled to the same reference tone, and its neck above the
      collar (z >= 1.525, a speckle of collar-dark and skin texels) is repainted like the head band."""
    NECK_TOP = 1.585
    gh, covh = out['hgd_head'][0], out['hgd_head'][4]; gb, covb = out['hgd'][0], out['hgd'][4]
    Rh = np.load(HERE / 'work' / 'uvraster_HeadUV.npz'); Rb = np.load(HERE / 'work' / 'uvraster_UVMap.npz')

    def skinlike(rgb):
        h, s_, v = hsv(rgb); return (h < 35) & (s_ > 0.15) & (v > 0.25)
    ph, posh = Rh['piece'], Rh['pos']; pb, posb = Rb['piece'], Rb['pos']
    front_h = np.clip((0.04 - posh[..., 1]) / 0.02, 0, 1); front_b = np.clip((0.04 - posb[..., 1]) / 0.02, 0, 1)
    ref_m = covh & (ph == 1) & (posh[..., 2] >= NECK_TOP) & (posh[..., 2] < NECK_TOP + 0.02) & (posh[..., 1] < -0.02) & skinlike(gh)
    ref = np.median(gh[ref_m], 0)
    lum = lambda x: x @ np.array([0.2126, 0.7152, 0.0722])
    band = covh & (ph == 1) & (posh[..., 2] < NECK_TOP) & skinlike(gh)
    w = front_h * band
    rel = lum(gh) / max(float(np.median(lum(gh[band]))), 1e-3)
    new = ref[None, None, :] * np.clip(rel, 0.92, 1.08)[..., None]
    top = covh & (ph == 1) & (posh[..., 2] >= NECK_TOP) & (posh[..., 2] < NECK_TOP + 0.015) & skinlike(gh)
    w = np.maximum(w, front_h * top * np.clip(1.5 - (posh[..., 2] - NECK_TOP) / 0.01, 0, 1))
    gh[:] = gh * (1 - w[..., None]) + new * w[..., None]
    # stubble dots Meshy painted on the sides of the neck at the atlas's bottom edge: a 7-texel median over that strip
    # removes the isolated dots and keeps the solid beard
    strip = covh & (ph == 1) & (posh[..., 2] >= NECK_TOP - 0.01) & (posh[..., 2] < NECK_TOP + 0.025)
    med = np.stack([ndimage.median_filter(gh[..., k], size=7) for k in range(3)], -1)
    ws = (strip * front_h)[..., None]
    gh[:] = gh * (1 - ws) + med * ws
    nb = covb & (pb == 1) & skinlike(gb)
    scale = ref / np.maximum(np.median(gb[nb], 0), 1e-3)
    wb = front_b * nb
    gb[:] = gb * (1 - wb[..., None]) + np.clip(gb * scale, 0, 1) * wb[..., None]
    # the body atlas's neck above the collar (z >= COLLAR) was a speckle of collar-dark and skin texels (a dotted line
    # across the neck): repainted like the head band, fading in over its lowest centimetre
    COLLAR = 1.525
    up = covb & (pb == 1) & (posb[..., 2] >= COLLAR)
    relb = lum(gb) / max(float(np.median(lum(gb[up & nb]))), 1e-3)
    newb = ref[None, None, :] * np.clip(relb, 0.92, 1.08)[..., None]
    wu = (front_b * up * np.clip((posb[..., 2] - COLLAR) / 0.01, 0, 1))[..., None]
    gb[:] = gb * (1 - wu) + newb * wu
    print('NECK reference skin', np.round(ref, 3), 'head band texels', int(band.sum()), 'body neck texels', int(nb.sum()),
          'repainted above the collar', int((wu[..., 0] > 0).sum()),
          'body tone scale', np.round(scale, 3))


out = {}
for job, raster, ao, pre in (('retexture_v1', 'uvraster_UVMap.npz', 'ao_UVMap.png', 'hgd'),
                             ('head_retexture_v1', 'uvraster_HeadUV.npz', 'ao_HeadUV.png', 'hgd_head')):
    out[pre] = compose(job, raster, ao)
neck_match(out)
for job, pre in (('retexture_v1', 'hgd'), ('head_retexture_v1', 'hgd_head')):
    g, cls, spec, rgh, cov = out[pre]
    save(pad(g, cov), T / f'{pre}_basecolor_1k.png')
    save(pad(load(HERE / 'meshy' / job / 'texture_urls_0_normal.png'), cov), T / f'{pre}_normal_1k.png')
    save(np.stack([pad(spec, cov), pad(rgh, cov), np.zeros((N, N))], -1), T / f'{pre}_metal_rough_1k.png')
    Image.fromarray(cls).save(T / f'{pre}_material_classes.png')
