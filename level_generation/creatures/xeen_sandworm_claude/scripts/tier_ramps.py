#!/usr/bin/env python3
"""Tier ramps of the sand worms (CLAUDE_CREATURE_TEXTURES.md): one shared graded paint, four regions (R body skin,
G thorn spikes, B the maw's gums, A the sand mound; the fangs, the black gullet and the rock chunks in none).
  sandworm_a  Sand Worm   the native colours: per region the COLOUR comes from the native pixels of that region in
                          Clouds 056.mon / 056.att (band-averaged chroma by luminance percentile, 15th-95th), the
                          texel keeps its own luminance, scaled so the region's mean is the native mean x GAIN (sprites
                          carry baked shading), then the shader's ramp is fitted (the electrapede's route)
  sandworm_c  Great Worm  a design recolour of A (Xeen draws both with one sprite; decision D-10: the tiers must read
                          apart at combat distance and the whole body tiers): deep rust-red / umber skin (hue 9,
                          saturation x0.95, value x0.62), near-black steel spikes (value x0.32), darker crimson gums
                          (hue 352, value x0.62). The bigger, higher-level worm reads as an older, darker, blood-rust
                          animal next to the bright orange Sand Worm, without leaving the desert family.
The mound keeps one sand-and-rock colour on both skins: its ramp is fitted to the paint itself (identity) in both.
Native region pixels (mm4.pal): body orange hue 28-40, saturation >= 0.6; spikes neutral grey (saturation < 0.08,
value 0.25-0.75); gums red (hue < 8 or > 350, saturation > 0.5).
Writes textures/worm_ramps.json (region_variants.py format) with the fit report."""
import colorsys, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import region_variants as RV

base = RV.load_srgb(ROOT / 'textures/worm_basecolor_graded.png', 1024)
mask = Image.open(ROOT / 'textures/worm_region_mask.png')
px = []
for f in ('mon_0003', 'mon_0004', 'mon_0005', 'att_0000', 'att_0001', 'att_0002', 'att_0003'):
    a = np.asarray(Image.open(ROOT / 'native' / f'{f}.png').convert('RGBA'))
    px.append(a[a[..., 3] > 0][:, :3])
nat = np.concatenate(px).astype(np.float64) / 255.0
hsv = np.array([colorsys.rgb_to_hsv(*c) for c in nat]); H = hsv[:, 0] * 360; S = hsv[:, 1]; V = hsv[:, 2]
NATIVE = {'skin': (H >= 28) & (H <= 40) & (S >= 0.6),
          'spikes': (S < 0.08) & (V >= 0.25) & (V <= 0.75),
          'gums': ((H < 8) | (H > 350)) & (S > 0.5)}
GAIN = {'skin': 1.2, 'spikes': 1.15, 'gums': 1.25}


def target_native(region, weight):
    nlin = RV.srgb_to_linear(nat[NATIVE[region]]); nl = nlin @ RV.LUMA
    order = np.argsort(nl); nlin, nl = nlin[order], nl[order]
    chroma = nlin / np.maximum(nl, 1e-4)[:, None]
    lum = RV.luminance(base)
    sel = weight > 0.05
    q = np.zeros_like(lum)
    vals = lum[sel]; ranks = np.argsort(np.argsort(vals))
    q[sel] = ranks / max(1, len(vals) - 1)
    qq = np.clip(q, 0.15, 0.95)
    nq = np.linspace(0, 1, len(nl))
    grid = np.linspace(0.15, 0.95, 33)
    table = np.array([chroma[(nq >= g - 0.1) & (nq <= g + 0.1)].mean(0) for g in grid])
    c = np.stack([np.interp(qq, grid, table[:, k]) for k in range(3)], -1)
    k = GAIN[region] * nl.mean() / max(vals.mean(), 1e-4)
    out_lin = np.clip(c * (lum * k)[..., None], 0, 1)
    enc = np.where(out_lin <= 0.0031308, out_lin * 12.92, 1.055 * out_lin ** (1 / 2.4) - 0.055)
    return np.where(sel[..., None], enc, base), dict(native_px=int(NATIVE[region].sum()), gain=round(float(k), 3),
                                                   native_median_srgb=(np.median(nat[NATIVE[region]], 0) * 255).round().tolist())


def hsv_recolour(rgb, hue_deg=None, sat_k=1.0, val_k=1.0):
    """Keep each texel's value (scaled); set its hue (or keep it when None) and scale its saturation."""
    rgb = np.clip(rgb, 0, 1)
    mx = rgb.max(-1); mn = rgb.min(-1); c = mx - mn
    s = np.clip(np.where(mx > 1e-6, c / np.maximum(mx, 1e-6), 0) * sat_k, 0, 1)
    v = np.clip(mx * val_k, 0, 1)
    if hue_deg is None:
        h = np.zeros_like(mx)
        r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
        m = c > 1e-6
        hr = m & (mx == r); hg = m & (mx == g) & ~hr; hb = m & ~hr & ~hg
        h[hr] = ((g - b)[hr] / c[hr]) % 6; h[hg] = (b - r)[hg] / c[hg] + 2; h[hb] = (r - g)[hb] / c[hb] + 4
    else:
        h = np.full_like(mx, (hue_deg / 60.0) % 6)
    i = np.floor(h).astype(int) % 6; f = h - np.floor(h)
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    out = np.zeros_like(rgb)
    for k, (a, b2, c2) in enumerate(((v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q))):
        sel = i == k
        out[sel] = np.stack([a[sel], b2[sel], c2[sel]], -1)
    return out


DESIGN_C = {'skin': (9, 0.95, 0.62), 'spikes': (20, 1.0, 0.32), 'gums': (352, 1.05, 0.62)}
variants = ['sandworm_a', 'sandworm_c']
ramps = {v: [] for v in variants}; report = {}; native = {}
for channel, region in zip('RGBA', ('skin', 'spikes', 'gums', 'sand')):
    weight = np.asarray(mask.getchannel(channel), np.float64) / 255.0
    if region == 'sand':
        tiers = {'sandworm_a': base, 'sandworm_c': base}
        native[region] = 'the paint itself (identity) on both skins'
    else:
        ta, info = target_native(region, weight)
        tiers = {'sandworm_a': ta, 'sandworm_c': hsv_recolour(ta, *DESIGN_C[region])}
        native[region] = info
    r, rep = RV.fit_ramps(base, tiers, weight)
    for v in variants:
        ramps[v].append(r[v])
    report[region] = rep
    for v in variants:
        Image.fromarray((np.clip(tiers[v], 0, 1) * 255 + 0.5).astype(np.uint8)).save(
            ROOT / 'work' / f'tier_target_{v}_{region}.png')
out = {'variants': variants,
       'materials': [{'base': 'Worm_A', 'prefix': 'Worm', 'mask': 'worm_region_mask.png', 'ramps': ramps}],
       'regions': ['R body skin (rings, head)', 'G thorn spikes', 'B maw gums', 'A sand mound (the rock chunks keep their paint)'],
       'design_c': {k: list(v) for k, v in DESIGN_C.items()},
       'native': native, 'fit_report': report}
json.dump(out, open(ROOT / 'textures/worm_ramps.json', 'w'), indent=1)
print('RAMPS', json.dumps(report))
print('NATIVE', json.dumps(native))
