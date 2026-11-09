#!/usr/bin/env python3
"""Colour tiers for PeasantHOM1 (CLAUDE_CREATURE_TEXTURES.md): one shared body + head set, region masks and per-tier ramps.

Tier phom1_a = MONSTERS rows 57 Commoner and 60 Prisoner (PeasantHOM1a: dark plum vest over a cream linen shirt,
red-brown trousers, chestnut hair) = the painted look (HD masters). Tier phom1_b = row 58 Town (PeasantHOM1b: a
green-and-ochre patterned wool jacket with brown wool sleeves and a blue/red key border, charcoal trousers, blond-grey
hair; same cream shirt front).

Regions (mask channels), from our texels' rest position (v2/work/texel_*_1k.npz, scripts/make_texels.py) and colour:
  body R vest      dark red-brown (hue 330-25, sat > 0.45, val < 0.5) on the trunk (|x| < 0.27), above the vest hem
  body G sleeves   each arm from the shoulder to the embroidered cuff band (by position), minus the vest's colours
  body B trousers  dark red-brown below the vest hem down to the leg wraps (z > -0.66)
  body A border    the vest's rust leather border (hue 13-32, sat > 0.82, val 0.2-0.75) on the trunk
  head R hair      the head shell's chestnut paint (hue 19-34, val < 0.55) above the ears' base, ears and brows
                   excluded, eroded 1 texel, weight fading with brightness (val 0.40-0.55: the fringe edge)
  head G collar    the vest collar painted into the head set (shell below z 0.80, rust/brown, not skin)
The vest hem: per 10-degree sector around the trunk, the lower edge of the densest band of border texels between z
-0.25 and 0.08 (the border runs along the hem); vest above it, trousers below.
Ramps: tier A fitted to our own base (reproduces the painted look); tier B quantile-matched to the PeasantHOM1b texels
paired with PeasantHOM1a texels of that region (both skins share one UV layout; v2/work/mm9_skin_samples.npy from
scripts/mm9_skin_samples.py), scaled by one luminance gain = our region's median / the HOM1a skin's median there.
Writes textures/phom1_region_mask.png, v2/textures/phom1_head_region_mask.png, textures/phom1_ramps.json.
Usage (project folder): ../claude_shared/gltf_venv/bin/python scripts/tier_ramps_phom1.py"""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as RV  # noqa: E402
from tier_ramps import hsv, soft, quantile_ramp  # noqa: E402

N = 1024
SHELL = 2
A, B_ = 'phom1_a', 'phom1_b'


def hem_height(x, y, z, border):
    ang = np.degrees(np.arctan2(y, x)) % 360
    hem = np.full(36, -0.05)
    for k in range(36):
        m = border & (ang >= k * 10) & (ang < k * 10 + 10) & (z > -0.25) & (z < 0.08)
        if m.sum() > 30:
            # the densest 1 cm band of border texels, extended down while the density stays above 20 % of its peak
            # (a 5th percentile caught the shirt tail's embroidered band 17 cm below the front hem)
            hist, edges = np.histogram(z[m], bins=np.arange(-0.25, 0.0801, 0.01))
            hist = ndi.uniform_filter1d(hist.astype(float), 3)
            i = int(np.argmax(hist))
            while i > 0 and hist[i - 1] > 0.2 * hist.max():
                i -= 1
            hem[k] = edges[i]
    hem = ndi.median_filter(hem, 3, mode='wrap')
    # front half (y < 0): the vest fronts end at the belt line (-0.05 in the masters); the shirt tail's embroidery
    # between them reads as a border band at -0.21
    hem[18:] = np.maximum(hem[18:], -0.07)
    return hem[(ang // 10).astype(int) % 36], hem


def main():
    rep = {}
    S = np.load('v2/work/mm9_skin_samples.npy')
    ha, sa, va = hsv(S[:, 3:6])
    sx, sy, sz = S[:, 0], S[:, 1], S[:, 2]
    dark_red_a = ((ha > 330) | (ha < 25)) & (va < 0.5)
    pairs = {
        'vest': dark_red_a & (np.abs(sx) < 0.24) & (sz > 0.05) & (sz < 0.6),
        'sleeves': (np.abs(sx) > 0.32) & (np.abs(sx) < 0.72) & (sz > 0.3) & (ha > 22) & (ha < 50) & (sa < 0.55) & (va > 0.45),   # no hands
        'trousers': dark_red_a & (sz > -0.55) & (sz < -0.12),
        'border': (ha > 8) & (ha < 32) & (sa > 0.55) & (va > 0.3) & (np.abs(sx) < 0.27) & (sz > -0.1) & (sz < 0.75) & ~(sa < 0.4),
        'hair': (sz > 0.95) & (sy > -0.05) & (ha > 15) & (ha < 45) & (va < 0.6),
    }
    t = np.load('v2/work/texel_body_1k.npz'); X, cov = t['xyz'], t['cov']
    B = np.asarray(Image.open('textures/phom1_basecolor_graded.png').convert('RGB').resize((N, N), Image.LANCZOS), float) / 255
    h, s, v = hsv(B); x, y, z = X[..., 0], X[..., 1], X[..., 2]
    trunk = cov & (np.abs(x) < 0.27) & (z < 0.86)
    border = trunk & (h > 13) & (h < 32) & (s > 0.82) & (v > 0.2) & (v < 0.75) & (z > -0.25)
    hz, hem = hem_height(x, y, z, border)
    rep['hem'] = [round(float(q), 3) for q in hem]
    darkred = cov & ((h > 330) | (h < 25)) & (s > 0.45) & (v < 0.5)
    vest = trunk & darkred & (z > hz) & ~border
    trousers = darkred & (z <= hz) & (z > -0.66) & (np.abs(x) < 0.4)
    # sleeves by geometry (by colour they came out blotchy: shaded folds fell outside the cream range): each arm from
    # 15 cm before the shoulder joint (|x| > 0.17, clear of the shirt front) to the embroidered cuff band (17 cm before the wrist joint), radius 24 cm,
    # minus the vest's colours; the cuff band and the lining inside the cuff keep the painted look
    hj = json.load(open('v2/work/hands_v1.json'))
    sleeves = np.zeros_like(cov)
    for side, sg in (('L', -1), ('R', 1)):
        Wj = np.array(hj['frames'][side]['W']); Sj = np.array([sg * 0.28, 0.0, 0.54])
        d = (Wj - Sj) / np.linalg.norm(Wj - Sj); L = np.linalg.norm(Wj - Sj)
        tt = (X - Sj) @ d; rad = np.linalg.norm(X - Sj - tt[..., None] * d, axis=-1)
        sleeves |= cov & (np.sign(x) == sg) & (np.abs(x) > 0.17) & (rad < 0.24) & (z > 0.15) & (tt > -0.15) & (tt < L - 0.17)
    rust = (h > 13) & (h < 32) & (s > 0.82) & (v > 0.2) & (v < 0.75)
    sleeves &= ~darkred & ~rust
    W = {'vest': soft(vest, cov), 'sleeves': soft(sleeves, cov), 'trousers': soft(trousers, cov), 'border': soft(border & (z > hz - 0.03), cov)}
    th = np.load('v2/work/texel_head_1k.npz'); XH, covh, comp = th['xyz'], th['cov'], th['comp']
    H = np.asarray(Image.open('v2/textures/phom1_head_basecolor.png').convert('RGB').resize((N, N), Image.LANCZOS), float) / 255
    hh, sh, vh = hsv(H)
    shell = covh & (comp == SHELL)
    ear = np.abs(XH[..., 0]) > 0.165
    hair = shell & ~ear & (XH[..., 2] > 0.80) & (hh > 19) & (hh < 34) & (vh < 0.55) & (sh > 0.45)
    collar = shell & (XH[..., 2] < 0.80) & (hh > 12) & (hh < 30) & (sh > 0.65) & (vh < 0.62)
    # fringe edge (the wave-1 lesson; here a pale halo round row 58's blond hair): the brows stay out (front face
    # below z 1.0), the hard mask is eroded by one texel before feathering, and the weight fades with brightness
    # between value 0.30 and 0.40 within 5 texels of its border (forehead skin 0.65-0.73, the fringe 0.24-0.39), so bright transition texels
    # keep the painted skin instead of taking the top of the hair ramp
    brows = (XH[..., 1] < -0.08) & (XH[..., 2] < 1.0) & (np.abs(XH[..., 0]) < 0.13)
    # the dark strands (hue/saturation outside the band) left holes that stayed brown in row 58's blond: close the
    # mask and take every dark texel (value < 0.45) inside it
    region = ndi.binary_fill_holes(ndi.binary_closing(hair, iterations=4))
    hair = (hair | (region & (vh < 0.45))) & shell & ~ear & ~brows & (XH[..., 2] > 0.80)
    # erosions treat uncovered texels as hair, so UV island borders are not eroded (that drew brown seam lines)
    hair_w = soft(ndi.binary_erosion(hair | ~covh, iterations=1) & hair, covh)
    edge = ~ndi.binary_erosion(hair | ~covh, iterations=5)      # within 5 texels of the hair border only (a fade
    hair_w = np.where(edge, hair_w * np.clip((0.40 - vh) / 0.10, 0, 1), hair_w)   # everywhere streaked the hair)
    WH = {'hair': hair_w, 'collar': soft(collar, covh)}
    sq = np.zeros((N, N), bool); sq[N - int(0.8 * N):, :int(0.8 * N)] = True
    for k in WH:
        WH[k] *= ndi.gaussian_filter(sq.astype(float), 1.0)
    rep['texels'] = {k: int((m > 0.9).sum()) for k, m in {**W, **WH}.items()}
    ramps_body = {A: [], B_: []}
    gains = {}
    for name in ('vest', 'sleeves', 'trousers', 'border'):
        rc, err = RV.fit_ramps(B, {A: B}, W[name]); ramps_body[A].append(rc[A])
        p = pairs[name]
        # the vest: gain 1 (our paint is darker than MM9's; the luminance gain made row 58's olive jacket read as brown)
        rd, gain = quantile_ramp(B, W[name], S[p, 6:9], S[p, 3:6], 1.0 if name == 'vest' else None)
        gains[name] = gain
        ramps_body[B_].append(rd)
        rep[name] = {'fit_a': err[A], 'mm9_pairs': int(p.sum()), 'gain': round(gain, 3),
                     'mm9_a_median': (np.median(S[p, 3:6], 0) * 255).round(0).tolist(),
                     'mm9_b_median': (np.median(S[p, 6:9], 0) * 255).round(0).tolist(),
                     'ours_median': (np.median(B[W[name] > 0.9], 0) * 255).round(0).tolist()}
    ramps_head = {A: [], B_: []}
    for name, pr in (('hair', 'hair'), ('collar', 'border')):
        rc, err = RV.fit_ramps(H, {A: H}, WH[name]); ramps_head[A].append(rc[A])
        p = pairs[pr]
        rd, gain = quantile_ramp(H, WH[name], S[p, 6:9], S[p, 3:6], gains.get('border') if name == 'collar' else None)
        if name == 'hair':
            # the brightest stops (HOM1b's sun-bleached strands, above our hair's 45th percentile) are capped at stop 6:
            # bright fringe-edge texels otherwise took the palest blond and outlined the hairline
            rd['colors'] = rd['colors'][:6] + [rd['colors'][6]] * 10
        ramps_head[B_].append(rd)
        rep[name] = {'fit_a': err[A], 'mm9_pairs': int(p.sum()), 'gain': round(gain, 3),
                     'mm9_a_median': (np.median(S[p, 3:6], 0) * 255).round(0).tolist(),
                     'mm9_b_median': (np.median(S[p, 6:9], 0) * 255).round(0).tolist(),
                     'ours_median': (np.median(H[WH[name] > 0.9], 0) * 255).round(0).tolist()}

    def mask_png(ws, path):
        img = np.zeros((N, N, 4), np.uint8)
        for i, w in enumerate(ws):
            img[..., i] = np.clip(w * 255 + 0.5, 0, 255).astype(np.uint8)
        Image.fromarray(img, 'RGBA').save(path)
    mask_png([W['vest'], W['sleeves'], W['trousers'], W['border']], 'textures/phom1_region_mask.png')
    mask_png([WH['hair'], WH['collar']], 'v2/textures/phom1_head_region_mask.png')
    cfg = {'variants': [A, B_],
           'materials': [{'base': 'PHOM1', 'prefix': 'PHOM1', 'mask': 'phom1_region_mask.png', 'ramps': ramps_body},
                         {'base': 'PHOM1Head', 'prefix': 'PHOM1Head', 'mask': '../v2/textures/phom1_head_region_mask.png',
                          'ramps': ramps_head}],
           'report': rep}
    Path('textures/phom1_ramps.json').write_text(json.dumps(cfg, indent=1))
    print('TIERS', json.dumps(rep))


if __name__ == '__main__':
    main()
