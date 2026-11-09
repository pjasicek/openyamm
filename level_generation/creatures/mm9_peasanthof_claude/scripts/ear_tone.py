#!/usr/bin/env python3
"""Ears toned to the skin right beside them (r9, coordinator pre-screen of r8, 2026-11-04: r7's gains made A/B's ears saturated
leather-brown, darker and redder than the face; HOF2's ears were two-toned, a pale back and a dark brown front). Per ear (each EARS
part): its root = the ear texels within ROOT of the skin shell; the target = the median colour of the skin-shell texels within NEAR of
the root (the cheek/temple next to the ear), skin-coloured texels only (hue 4-28 deg, saturation 0.15-0.6, luminance > 90:
not the hair painted on the shell beside the ear). Every ear texel = target x (its own luminance / the ear's median luminance) ** DET:
one continuous tone with only the paint's soft shading (hollow, rim) kept at DET. Prints, per ear, luminance and hue of the ear and of
the adjacent skin before and after. Reads <prefix>_head_basecolor_preear.png (first run or RESET=1).
Args: <glb> <head prefix> [--ears 8,9] [--skin 0] [--root 0.005] [--near 0.03] [--det 0.35] [--gain 1.0]"""
import argparse, os, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpart import texel_parts
ap = argparse.ArgumentParser(); ap.add_argument('glb'); ap.add_argument('head')
ap.add_argument('--ears', default='8,9'); ap.add_argument('--skin', type=int, default=0)
ap.add_argument('--root', type=float, default=0.005); ap.add_argument('--near', type=float, default=0.03); ap.add_argument('--det', type=float, default=0.35)
ap.add_argument('--gain', type=float, default=1.0)   # r9: x1.12, the folded leaf's lower facet renders darker than the skin beside it
o = ap.parse_args()
f = Path(f'textures/{o.head}_head_basecolor.png'); bk = f.with_name(f.stem + '_preear.png')
if not bk.exists() or os.environ.get('RESET') == '1':
    shutil.copyfile(f, bk)
CUR = np.asarray(Image.open(f).convert('RGB'), float)          # the current paint: skin beside the ear as it is now
H = np.asarray(Image.open(bk).convert('RGB'), float); N = H.shape[0]
ph, part, _ = texel_parts(o.glb, 'PeasantHOFHead', N); P = np.nan_to_num(ph)
skin = part == o.skin; si = np.nonzero(skin); stree = cKDTree(P[si])
def lh(c):
    c = np.atleast_2d(c); r, g, b = c[:, 0], c[:, 1], c[:, 2]
    return np.round(c.mean(1), 1), np.round(np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360, 1)
out = CUR.copy()
for e in [int(x) for x in o.ears.split(',')]:
    ei = np.nonzero(part == e)
    if len(ei[0]) == 0: continue
    d, _ = stree.query(P[ei]); root = P[ei][d < o.root]
    if len(root) < 10: root = P[ei][np.argsort(d)[:200]]
    near = stree.query_ball_point(root, o.near); idx = np.unique(np.concatenate([np.array(x, int) for x in near if len(x)]))
    C_ = CUR[si[0][idx], si[1][idx]]; mx_, mn_ = C_.max(1), C_.min(1); sat_ = (mx_ - mn_) / np.maximum(mx_, 1)
    hue_ = np.degrees(np.arctan2(np.sqrt(3) * (C_[:, 1] - C_[:, 2]), 2 * C_[:, 0] - C_[:, 1] - C_[:, 2])) % 360
    ok_ = (hue_ > 4) & (hue_ < 28) & (sat_ > 0.15) & (sat_ < 0.6) & (C_.mean(1) > 90)      # skin, not hair painted on the shell
    T = np.median(C_[ok_] if ok_.sum() > 50 else C_, 0)
    E = H[ei]; L = E.mean(1); det = np.clip(L / max(np.median(L), 1), 0.5, 1.6) ** o.det
    new = np.clip(T[None] * o.gain * det[:, None], 0, 255)
    before = lh(np.median(CUR[ei], 0)); after = lh(np.median(new, 0)); sk = lh(T)
    out[ei] = new
    print(f'EARTONE {o.head} ear {e}: skin beside L {sk[0][0]} hue {sk[1][0]} | ear before L {before[0][0]} hue {before[1][0]} -> after L {after[0][0]} hue {after[1][0]} (root texels {len(root)}, skin texels {len(idx)})')
Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(f)
