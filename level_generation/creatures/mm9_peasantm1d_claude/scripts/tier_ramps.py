#!/usr/bin/env python3
"""Colour tiers for PeasantM1d (CLAUDE_CREATURE_TEXTURES.md): one shared body + head set, region masks and per-tier ramps.

Tier pm1d_c = MONSTERS row 22 (PeasantM1c: blond hair, orange suede tunic, plum breeches) = the painted look (HD masters).
Tier pm1d_d = row 28 (PeasantM1d: green wool jacket open over a cream shirt, red-brown breeches, dark brown hair).

Regions (mask channels), from our texels' rest-pose position (v2/work/texel_*_1k.npz, scripts/texel_xyz.py) and colour:
  body R tunic   orange suede (hue 15-36, sat > 0.7) from the hem to the neck, minus the front panel; sleeves included, belt, gold hem
                 trim, cuffs and laces left out
  body G panel   the tunic's front band |x| < PANEL_HALF, y < 0, from the hem to the neck: where row 28's cream shirt shows
                 between the jacket fronts (measured on the MM9 mesh: |x| < 0.065-0.075, z 0.0-0.6)
  body B breeches plum (hue 345-15, sat 0.3-0.75) between the boots and the hem
  body A trim    the gold hem band (hue 36-58): row 28's jacket has none, so its tier D ramp is the jacket's green
  head G collar  the tunic collar painted into the head set (orange texels of the neck shell below z 0.75)
  head R hair    the hair parts (every head part but the face/neck shell, eyes, lids and mouth) plus the shell's scalp
Ramps: tier C is fitted to our own base (region_variants.fit_ramps(base, base, w): reproduces the painted look); tier D
is quantile-matched: each stop's luminance percentile in our region picks the colour at the same percentile of the
row-28 skin texels of that region (pairs of MM9 skin texels at the same UV, sampled over the MM9 mesh,
v2/work/mm9_skin_samples.npy), scaled by one luminance gain = our region's median / the row-22 skin's median there.
Writes textures/pm1d_region_mask.png, v2/textures/pm1d_head_region_mask.png, textures/pm1d_ramps.json and a report.
Usage (project folder): ../claude_shared/gltf_venv/bin/python scripts/tier_ramps.py"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as RV  # noqa: E402

PANEL_HALF = 0.06
N = 1024
EYES_MOUTH = {5, 31, 24, 38, 9, 26, 39}       # head_split.py part numbers: eyeballs, lids, mouth pieces
SHELL = 2


def hsv(a):
    mx = a.max(-1); mn = a.min(-1); d = mx - mn + 1e-9; r, g, b = a[..., 0], a[..., 1], a[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, d / (mx + 1e-9), mx


def lin(s):
    return RV.srgb_to_linear(s)


def soft(mask, cov):
    """Pad into the gutters from the nearest covered texel (like the colour), then feather 1.5 texels."""
    m = mask.astype(np.float64)
    idx = ndi.distance_transform_edt(~cov, return_distances=False, return_indices=True)
    m = m[idx[0], idx[1]]
    return np.clip(ndi.gaussian_filter(m, 1.2), 0, 1)


def quantile_ramp(base_srgb, w, d_srgb, c_srgb, gain=None):
    """Tier D ramp for one region: range = our region's luminance 2-98 %, stops quantile-matched to D."""
    core = w > 0.9
    lum = RV.luminance(base_srgb)[core]
    lo, hi = np.percentile(lum, [2, 98])
    dl = lin(d_srgb); dlum = dl @ RV.LUMA
    order = np.argsort(dlum); dl, dlum = dl[order], dlum[order]
    if gain is None:
        gain = np.median(lum) / max(np.median(lin(c_srgb) @ RV.LUMA), 1e-4)
    srt = np.sort(lum)
    cols = []
    for k in range(16):
        L = lo + (hi - lo) * k / 15
        p = np.searchsorted(srt, L) / len(srt)
        i = int(np.clip(p * len(dl), 0, len(dl) - 1)); j0, j1 = max(0, i - len(dl) // 40), min(len(dl), i + len(dl) // 40 + 1)
        cols.append(np.clip(dl[j0:j1].mean(0) * gain, 0, 1))
    return {'range': [float(lo), float(hi)], 'colors': [[round(float(x), 5) for x in c] for c in cols]}, float(gain)


def main():
    rep = {}
    S = np.load('v2/work/mm9_skin_samples.npy')            # x, y, z (Blender frame), C rgb, D rgb
    hc, sc, vc = hsv(S[:, 3:6]); hd, sd, vd = hsv(S[:, 6:9])
    orange = (hc > 8) & (hc < 42) & (sc > 0.6) & (vc > 0.2)
    pairs = {
        'tunic': orange & (hd > 45) & (hd < 120),
        'panel': orange & (sd < 0.4) & (vd > 0.45) & (np.abs(S[:, 0]) < 0.1) & (S[:, 1] < 0),
        'breeches': (S[:, 2] > -0.45) & (S[:, 2] < -0.02) & (np.abs(S[:, 0]) < 0.3) & ((hc > 340) | (hc < 18)) & (vc < 0.5),
        'hair': (S[:, 2] > 0.72) & (hc > 25) & (hc < 55) & (vc > 0.5) & (vd < 0.4),
    }
    # body
    t = np.load('v2/work/texel_body_1k.npz'); X, cov = t['xyz'], t['cov']
    B = np.asarray(Image.open('textures/pm1d_basecolor_graded.png').convert('RGB').resize((N, N), Image.LANCZOS), float) / 255
    h, s, v = hsv(B); x, y, z = X[..., 0], X[..., 1], X[..., 2]
    tunic = cov & (h > 12) & (h < 36) & (v > 0.15) & (z > 0.0) & (z < 0.80) & ((s > 0.7) | ((z > 0.50) & (s > 0.62)))
    panel = tunic & (np.abs(x) < PANEL_HALF) & (y < 0)
    breeches = cov & ((h > 345) | (h < 15)) & (s > 0.3) & (s < 0.78) & (v < 0.5) & (z > -0.47) & (z < 0.03)
    trim = cov & (h >= 36) & (h < 58) & (s > 0.45) & (v > 0.2) & (z > -0.06) & (z < 0.10)
    W = {'tunic': soft(tunic & ~panel, cov), 'panel': soft(panel, cov), 'breeches': soft(breeches, cov), 'trim': soft(trim, cov)}
    # head
    th = np.load('v2/work/texel_head_1k.npz'); XH, covh, comp = th['xyz'], th['cov'], th['comp']
    H = np.asarray(Image.open('v2/textures/pm1d_head_basecolor.png').convert('RGB').resize((N, N), Image.LANCZOS), float) / 255
    hh, sh, vh = hsv(H)
    ear = (np.abs(XH[..., 0]) > 0.085) & (XH[..., 2] > 0.735) & (XH[..., 2] < 0.875)
    parts = covh & (comp >= 0) & (comp != SHELL) & ~np.isin(comp, list(EYES_MOUTH))
    # scalp: the shell's top and back, and the blond paint on the forehead above z 0.812 (skin there is hue ~17, the
    # painted hair 23-27; it showed as a pale jagged band under row 28's dark fringe)
    scalp = covh & (comp == SHELL) & ((XH[..., 2] > 0.855) | ((XH[..., 1] > 0.03) & (XH[..., 2] > 0.70)) | (XH[..., 2] > 0.812)) & (hh >= 22.5) & ~ear
    # hair parts whole (their undersides carry skin-toned paint that showed as pale patches under the dark fringe), the
    # shell's scalp by colour
    hair = parts | (scalp & (hh > 20) & (hh < 40) & (vh > 0.3))
    collar = covh & (comp == SHELL) & (hh > 12) & (hh < 36) & (sh > 0.7) & (vh > 0.15) & (XH[..., 2] < 0.75)
    WH = {'hair': soft(hair, covh), 'collar': soft(collar, covh)}
    sq = np.zeros((N, N), bool); sq[N - int(0.8 * N):, :int(0.8 * N)] = True    # the head square (HEAD_SCALE 0.8, lower left)
    for k in WH:
        WH[k] *= ndi.gaussian_filter(sq.astype(float), 1.0)                       # never into the hands' squares
    rep['texels'] = {k: int((m > 0.9).sum()) for k, m in {**W, **WH}.items()}
    # ramps
    ramps_body = {'pm1d_c': [], 'pm1d_d': []}
    gains = {}
    for name in ('tunic', 'panel', 'breeches', 'trim'):
        rc, err = RV.fit_ramps(B, {'pm1d_c': B}, W[name]); ramps_body['pm1d_c'].append(rc['pm1d_c'])
        p = pairs['tunic' if name == 'trim' else name]       # row 28 has no hem trim: its jacket hem is the jacket's green
        rd, gain = quantile_ramp(B, W[name], S[p, 6:9], S[p, 3:6], gains.get('tunic') if name == 'trim' else None)
        gains[name] = gain
        ramps_body['pm1d_d'].append(rd)
        rep[name] = {'fit_c': err['pm1d_c'], 'mm9_pairs': int(p.sum()), 'gain': round(gain, 3),
                     'mm9_c_median': (np.median(S[p, 3:6], 0) * 255).round(0).tolist(),
                     'mm9_d_median': (np.median(S[p, 6:9], 0) * 255).round(0).tolist(),
                     'ours_median': (np.median(B[W[name] > 0.9], 0) * 255).round(0).tolist()}
    rc, errh = RV.fit_ramps(H, {'pm1d_c': H}, WH['hair'])
    p = pairs['hair']
    rd, gain = quantile_ramp(H, WH['hair'], S[p, 6:9], S[p, 3:6])
    ramps_head = {'pm1d_c': [rc['pm1d_c']], 'pm1d_d': [rd]}
    # the tunic collar painted into the head set (the head faces above the neck cut include the collar's rise at the
    # sides and back): the jacket's ramp
    rcc, errc = RV.fit_ramps(H, {'pm1d_c': H}, WH['collar'])
    rdc, _ = quantile_ramp(H, WH['collar'], S[pairs['tunic'], 6:9], S[pairs['tunic'], 3:6], gains['tunic'])
    ramps_head['pm1d_c'].append(rcc['pm1d_c']); ramps_head['pm1d_d'].append(rdc)
    rep['collar'] = {'fit_c': errc['pm1d_c'], 'texels': int((WH['collar'] > 0.9).sum())}
    rep['hair'] = {'fit_c': errh['pm1d_c'], 'mm9_pairs': int(p.sum()), 'gain': round(gain, 3),
                   'mm9_c_median': (np.median(S[p, 3:6], 0) * 255).round(0).tolist(),
                   'mm9_d_median': (np.median(S[p, 6:9], 0) * 255).round(0).tolist(),
                   'ours_median': (np.median(H[WH['hair'] > 0.9], 0) * 255).round(0).tolist()}
    # masks (1K RGBA; unused channels 0)
    def mask_png(ws, path):
        img = np.zeros((N, N, 4), np.uint8)
        for i, w in enumerate(ws):
            img[..., i] = np.clip(w * 255 + 0.5, 0, 255).astype(np.uint8)
        Image.fromarray(img, 'RGBA').save(path)
    mask_png([W['tunic'], W['panel'], W['breeches'], W['trim']], 'textures/pm1d_region_mask.png')
    mask_png([WH['hair'], WH['collar']], 'v2/textures/pm1d_head_region_mask.png')
    cfg = {'variants': ['pm1d_c', 'pm1d_d'],
           'materials': [{'base': 'PM1d', 'prefix': 'PM1d', 'mask': 'pm1d_region_mask.png', 'ramps': ramps_body},
                         {'base': 'PM1dHead', 'prefix': 'PM1dHead', 'mask': '../v2/textures/pm1d_head_region_mask.png',
                          'ramps': ramps_head}],
           'report': rep}
    Path('textures/pm1d_ramps.json').write_text(json.dumps(cfg, indent=1))
    print('TIERS', json.dumps(rep))


if __name__ == '__main__':
    main()
