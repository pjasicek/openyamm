#!/usr/bin/env python3
"""Crawler tiers as one shared skin + region mask + ramps (CLAUDE_CREATURE_TEXTURES.md), the colours taken from the
approved concept sheet (references_hd/concept.png; there is no native sprite):
  crawler_a  10090 Acid Crawler    the pale bone-grey crawlers (large right figure + small lower-left side view)
  crawler_b  10091 Brood Crawler   the rust-brown crawler with egg pods (upper left)
  crawler_c  10092 Crawler Matron  the violet-black crawler (middle left)
Per tier figure the concept pixels are classified: background out; acid = yellow-green glow (hue 50-100, saturated);
carapace = the upper 55 % of each silhouette column (minus acid and, on B, the yellow egg pods); limbs = the lower
45 % (minus acid). For every region the ramp stop i sits at linear luminance lo + (hi - lo) i / 15 of the graded
shared base (0.5 / 99.5 % over the region) and takes the concept colour at the same luminance quantile, times one gain
per region (GAIN, linear: 1.2 carapace and limbs, 1.35 acid for the glow; the painting carries its own shading, like
the sprites; the same gain for every tier, so their relative brightness follows the sheet). The graded Meshy texture
sits at ~0.5-0.6x the concept's brightness, so the ramps lift it. Eyes: hand-set dark-to-highlight ramps (A olive, B amber, C
lime). Writes textures/hcr_region_mask.png (R carapace, G acid, B limbs, A eyes), textures/hcr_ramps.json and the
baked previews work/tier_<variant>.png; also writes the baked AO into the R channel of textures/hcr_mr_1k.png."""
import json, sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import region_variants as R

T = ROOT / 'textures'
CONCEPT = np.asarray(Image.open(ROOT / 'references_hd/concept.png').convert('RGB'), np.float64) / 255
FIGURES = {'crawler_a': [(590, 200, 1536, 1010), (20, 680, 700, 960)], 'crawler_b': [(20, 20, 620, 345)],
           'crawler_c': [(20, 350, 585, 660)]}   # C stops short of the large A figure's tail
# acid hue per tier (linear multipliers): the sheet's glow reads lime-green (A green, B yellow-green, C bright lime)
ACID_TINT = {'crawler_a': (0.78, 1.08, 0.75), 'crawler_b': (0.95, 1.0, 0.6), 'crawler_c': (0.75, 1.2, 0.55)}
# the matron's sheet carapace has bright violet highlights that a quantile match spreads over the whole plate: darken
TIER_GAIN = {'crawler_c': {'carapace': 0.62, 'limbs': 0.85}}
REGIONS = ['carapace', 'acid', 'limbs', 'eyes']
GAIN = {'carapace': 1.2, 'limbs': 1.2, 'acid': 1.35}   # linear, over the concept colours
EYES = {'crawler_a': ((0.015, 0.02, 0.008), (0.55, 0.62, 0.40)), 'crawler_b': ((0.025, 0.012, 0.0), (0.80, 0.55, 0.22)),
        'crawler_c': ((0.01, 0.04, 0.0), (0.65, 1.0, 0.25))}


def hsv(rgb):
    mx = rgb.max(-1); mn = rgb.min(-1); d = mx - mn
    s = np.where(mx > 1e-4, d / np.maximum(mx, 1e-4), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    sd = np.maximum(d, 1e-5)
    h = np.where(mx == r, ((g - b) / sd) % 6, np.where(mx == g, (b - r) / sd + 2, (r - g) / sd + 4)) * 60
    return np.where(d > 1e-5, h, 0), s, mx


def concept_pixels(variant):
    out = {k: [] for k in ('carapace', 'acid', 'limbs')}
    for (x0, y0, x1, y1) in FIGURES[variant]:
        px = CONCEPT[y0:y1, x0:x1]
        bgc = np.median(np.concatenate([px[:6, :6].reshape(-1, 3), px[-6:, -6:].reshape(-1, 3)]), 0)
        h, s, v = hsv(px)
        fg = (np.linalg.norm(px - bgc, axis=-1) > 0.10) | (s > 0.25)
        acid = fg & (h > 50) & (h < 100) & (s > 0.40) & (v > 0.25)
        pods = fg & (h > 40) & (h < 62) & (s > 0.3) & (v > 0.45) if variant == 'crawler_b' else np.zeros_like(fg)
        rows = np.arange(px.shape[0])[:, None]
        top = np.where(fg.any(0), fg.argmax(0), 0)[None]
        bottom = np.where(fg.any(0), px.shape[0] - 1 - fg[::-1].argmax(0), 0)[None]
        frac = (rows - top) / np.maximum(bottom - top, 1)
        car = fg & ~acid & ~pods & (frac < 0.55)
        limb = fg & ~acid & (frac >= 0.55)
        out['carapace'].append(px[car]); out['acid'].append(px[acid]); out['limbs'].append(px[limb])
    res = {}
    for k, v in out.items():
        p = np.concatenate(v)
        res[k] = p[np.argsort(R.srgb_to_linear(p) @ R.LUMA)]
    return res


def ramp_eval(colors, t):
    c = np.array(colors); x = np.clip(t, 0, 1) * 15
    i = np.minimum(x.astype(int), 14); f = (x - i)[..., None]
    return c[i] * (1 - f) + c[i + 1] * f


def main():
    base = R.load_srgb(T / 'hcr_basecolor_graded.png')
    w = np.load(T / 'hcr_region_weights.npz')
    weights = [np.asarray(w[n], np.float64) for n in REGIONS]
    R.write_mask(weights, T / 'hcr_region_mask.png')
    lum_all = R.luminance(base)
    pix = {v: concept_pixels(v) for v in FIGURES}
    ramps = {v: [] for v in FIGURES}
    report = {}
    for ri, name in enumerate(REGIONS):
        core = weights[ri] > 0.9
        lum = lum_all[core]
        lo, hi = float(np.percentile(lum, 0.5)), float(np.percentile(lum, 99.5))
        stops = lo + (hi - lo) * np.arange(16) / 15
        q = np.searchsorted(np.sort(lum), stops) / len(lum)
        if name == 'eyes':
            for v in FIGURES:
                d, l = (np.array(c) for c in EYES[v])
                cols = [d + (l - d) * (i / 15) ** 1.6 for i in range(16)]
                ramps[v].append({'range': [round(lo, 6), round(hi, 6)], 'colors': np.round(cols, 6).tolist()})
            continue
        a_med = float(np.median(R.srgb_to_linear(pix['crawler_a'][name]) @ R.LUMA))
        gain_lin = GAIN[name]
        report[name] = {'range': [round(lo, 4), round(hi, 4)], 'gain_linear': gain_lin,
                        'texture_to_concept_a': round(float(np.median(lum)) / max(a_med, 1e-4), 3)}
        for v in FIGURES:
            native = pix[v][name]
            cols = []
            for qq in q:
                c = int(np.clip(qq, 0, 1) * (len(native) - 1)); half = max(len(native) // 100, 2)
                win = native[max(c - half, 0):c + half + 1]
                col = R.srgb_to_linear(np.median(win, 0)) * gain_lin * TIER_GAIN.get(v, {}).get(name, 1.0)
                if name == 'acid':
                    col = col * np.array(ACID_TINT[v])
                cols.append(np.clip(col, 0, 0.9))
            ramps[v].append({'range': [round(lo, 6), round(hi, 6)], 'colors': np.round(cols, 6).tolist()})
            report[name][v] = {'pixels': int(len(native)), 'median_srgb': np.round(np.median(native, 0), 3).tolist()}
    config = {'variants': list(FIGURES),
              'materials': [{'base': 'Crawler_A', 'prefix': 'Crawler', 'mask': 'hcr_region_mask.png', 'regions': REGIONS,
                             'source': 'references_hd/concept.png tier figures', 'ramps': ramps, 'report': report}]}
    (T / 'hcr_ramps.json').write_text(json.dumps(config, indent=1) + '\n')
    # previews with the shader's rule
    lin = R.srgb_to_linear(base)
    # per channel: resizing an RGBA image premultiplies by alpha (the eyes channel)
    mask = np.stack([np.asarray(ch.resize(base.shape[1::-1], Image.BILINEAR)) / 255.0
                     for ch in Image.open(T / 'hcr_region_mask.png').split()], -1)
    for v in FIGURES:
        out = lin.copy()
        for ri, reg in enumerate(ramps[v]):
            t = (lum_all - reg['range'][0]) / (reg['range'][1] - reg['range'][0])
            out = out * (1 - mask[..., ri:ri + 1]) + ramp_eval(reg['colors'], t) * mask[..., ri:ri + 1]
        srgb = np.where(out <= 0.0031308, out * 12.92, 1.055 * np.clip(out, 0, None) ** (1 / 2.4) - 0.055)
        Image.fromarray((np.clip(srgb, 0, 1) * 255 + 0.5).astype(np.uint8)).save(ROOT / 'work' / f'tier_{v}.png')
    # AO into the metal/roughness red channel (ORM packing; not referenced as occlusionTexture)
    mr = np.asarray(Image.open(T / 'hcr_mr_1k.png').convert('RGB')).copy()
    ao = np.asarray(Image.open(T / 'hcr_ao_2k.png').convert('L').resize((1024, 1024), Image.BOX))
    mr[..., 0] = ao
    Image.fromarray(mr).save(T / 'hcr_mr_1k.png')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
