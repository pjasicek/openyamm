#!/usr/bin/env python3
"""Sideburn outline (ear sweep 2026-11-02, `claude_shared/mm9_overview/ear_sweep_20261102.png` rows 11-12: an outline drawn round
the hair patch on each cheek, dark on phom1_a, lighter on phom1_b).

MM9's PeasantHOM1 has that patch: the hair bowl comes down in front of each ear to the jaw (`references_hd/mm9_head_views_a.png`,
_b; the Codex head turnaround too), so the sideburn stays and only its outline goes.
Cause: not the paint. Meshy's head paint (`v2/work/phom1_head_basecolor_composed.png`) has a soft sideburn edge. hairline_fix.py
(the wave-1 fringe lesson) darkens every hair-mask texel within 8 texels of the hair border to at most 1.1 x the hair median: on
the fringe that removed the pale strand tips, but round the sideburns (and the temples and nape) the border texels are a soft
mix of hair and skin, and darkening them to hair luminance drew a dark line along the whole border; row 58's blond ramp maps
that dark line to a darker band (the lighter outline there).
Fix (after hand_clean.py, before tier_ramps_phom1.py): head texels (texel_head_1k.npz cov: head faces only, the hand squares
are untouched) outside the fringe window take the composed paint back, i.e. hairline_fix acts on the fringe only. Fringe weight
= front (y < FRINGE_Y, faded over FADE) x middle (|x| < FRINGE_X, faded over FADE); blend out = fringe w x current + (1 - w) x
composed. Reads the *_preear.png backup (made from v2/textures/phom1_head_basecolor.png on the first run; delete it after the
chain rewrites the colour), writes v2/textures/phom1_head_basecolor.png and review/fix_sideburn_mask.png.
Second part, `mask` (after tier_ramps_phom1.py): with the outline gone, row 58 still showed a brown frame round each blond
sideburn: the chestnut texels of the soft border lie outside the hair mask (or under its brightness fade) and keep tier A's
colour. In the sideburn box (SB_*), head-shell texels within GROW texels (1K) of the hair mask take a hair weight from their
paint: 0 at the skin's luminance (cheek median), 1 from STEEP of the way to the hair's median, max with the current weight; ears (|x| > 0.165) and
below z 0.80 and the brows stay out, as in tier_ramps_phom1.py. Reads v2/textures/phom1_head_region_mask_preear.png (backup), writes the mask
and review/fix_sideburn_maskgrow.png.
Usage (project folder): fix_sideburn_phom1.py colour   (after hand_clean.py)
                        fix_sideburn_phom1.py mask     (after tier_ramps_phom1.py)"""
import sys
import shutil
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

FRINGE_Y, FRINGE_X, FADE = -0.075, 0.10, 0.02     # m, texel_head_1k.npz frame (z up, face towards -y)
GROW = 6                                           # texels (1K): mask growth into the sideburn border
SB_Z, SB_Y, SB_X = 1.00, (-0.09, 0.04), 0.06        # the sideburn box (mask part)
STEEP, SOFT = 0.35, 0.7                           # full weight from STEEP of the way skin -> hair; blur (texels)
MODE = sys.argv[1] if len(sys.argv) > 1 else 'colour'
th = np.load('v2/work/texel_head_1k.npz')
X, cov = th['xyz'], th['cov']
y, ax = np.nan_to_num(X[..., 1]), np.abs(np.nan_to_num(X[..., 0]))
w = np.clip((FRINGE_Y + FADE - y) / FADE, 0, 1) * np.clip((FRINGE_X + FADE - ax) / FADE, 0, 1)
F = Path('v2/textures/phom1_head_basecolor.png')
if MODE == 'colour':
    BK = F.with_name(F.stem + '_preear.png')
    if not BK.exists():
        shutil.copyfile(F, BK)
    cur = np.asarray(Image.open(BK).convert('RGB'), float)
    comp = np.asarray(Image.open('v2/work/phom1_head_basecolor_composed.png').convert('RGB'), float)
    N = cur.shape[0]
    side = cov.astype(float) * (1 - w)                            # 1: take the composed paint
    side = ndi.binary_dilation(cov, iterations=2) * ndi.maximum_filter(side, 3)   # the 1K map's island edges at 2K
    side2k = np.asarray(Image.fromarray(np.uint8(np.clip(side, 0, 1) * 255)).resize((N, N), Image.BILINEAR), float) / 255
    head2k = np.asarray(Image.fromarray(np.uint8(ndi.binary_dilation(cov, iterations=2)) * 255).resize((N, N), Image.NEAREST)) > 0
    side2k *= head2k
    out = cur * (1 - side2k[..., None]) + comp * side2k[..., None]
    Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(F)
    changed = np.abs(out - cur).max(-1) > 0.5
    vis = cur.astype(np.uint8).copy()
    vis[changed] = (255, 0, 255)
    Image.fromarray(vis).resize((1024, 1024), Image.NEAREST).save('review/fix_sideburn_mask.png')
    print('SIDEBURN colour texels changed', int(changed.sum()), 'of head', int(head2k.sum()))
else:
    M = Path('v2/textures/phom1_head_region_mask.png')
    MB = M.with_name(M.stem + '_preear.png')
    if not MB.exists():
        shutil.copyfile(M, MB)
    mk = np.asarray(Image.open(MB), np.uint8).copy()          # RGBA, R hair, G collar
    n = mk.shape[0]
    col = np.asarray(Image.open(F).convert('RGB').resize((n, n), Image.LANCZOS), float)
    lum = col @ [0.299, 0.587, 0.114]
    hairw = mk[..., 0] / 255.0
    z = np.nan_to_num(X[..., 2])
    hair_l = np.median(lum[hairw > 0.9])
    cheek = cov & (hairw < 0.01) & (y < -0.06) & (ax > 0.06) & (ax < 0.12) & (z > 0.80) & (z < 0.92)
    skin_l = np.median(lum[cheek])
    near = ndi.binary_dilation(hairw > 0.3, iterations=GROW)
    brows = (y < -0.08) & (z < 1.0) & (ax < 0.13)                # as tier_ramps_phom1.py
    burn = (z < SB_Z) & (y > SB_Y[0]) & (y < SB_Y[1]) & (ax > SB_X)    # the sideburns only
    grow = cov & near & (ax < 0.165) & (z > 0.80) & (w < 1) & ~brows & burn
    wnew = np.clip((skin_l - lum) / max(STEEP * (skin_l - hair_l), 1e-3), 0, 1) * (1 - w)
    wnew = ndi.gaussian_filter(wnew, SOFT)                      # no hard, jagged step at the edge
    neww = np.where(grow, np.maximum(hairw, wnew), hairw)
    mk[..., 0] = np.clip(np.round(neww * 255), 0, 255).astype(np.uint8)
    Image.fromarray(mk, 'RGBA').save(M)
    vis = np.zeros((n, n, 3), np.uint8)
    vis[..., 1] = (hairw * 255).astype(np.uint8)
    vis[..., 0] = (np.clip(neww - hairw, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(vis).save('review/fix_sideburn_maskgrow.png')
    print('SIDEBURN mask hair lum %.1f skin lum %.1f' % (hair_l, skin_l), 'texels raised', int((neww > hairw + 0.02).sum()))
