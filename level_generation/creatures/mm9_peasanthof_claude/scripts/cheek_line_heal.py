#!/usr/bin/env python3
"""Pale side panel on one cheek (r10, 2026-11-04): tier B's fresh head paint (b3) is ~12 L brighter on her right cheek side (66-78 mm
from the face midline, 1.66-1.77 m) than the cheek beside it, with a visible edge where it starts (the viewer front and 3/4 show a
pale vertical band beside the braid); her left side darkens outward instead. Since the face is now mirror-symmetric
(jaw_mirror3.py), the narrow side's broad tone is taken from the mirror image of the other side: for skin-shell texels with
XLO < (x - CX) * SIDE < XHI (CX = the face midline x), Y0 < y < Y1, z > ZMIN, broad colour = 3D Gaussian mean (SIGMA) of the skin
texels round the texel; the texel is scaled per channel by broad(mirror point) / broad(own) (detail kept), with a smooth weight
(EASE at every edge). Reads <prefix>_head_basecolor_preline.png (made on the first run or RESET=1), writes the head basecolor.
Args: <glb> <prefix> [--side 1] [--cx -0.0086] [--xlo 0.045] [--xhi 0.095] [--y0 1.655] [--y1 1.775] [--zmin -0.06]
[--sigma 0.008] [--ease 0.01] [--skin 0] [--flatlo 0 --flathi 0 (off) --fsig 0.012 --fdet 0.003]"""
import argparse, os, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpart import texel_parts
ap = argparse.ArgumentParser(); ap.add_argument('glb'); ap.add_argument('prefix')
for k, d in (('side', 1.0), ('cx', -0.0086), ('xlo', 0.045), ('xhi', 0.095), ('y0', 1.655), ('y1', 1.775), ('zmin', -0.06),
             ('sigma', 0.008), ('ease', 0.01), ('skin', 0.0), ('flatlo', 0.0), ('flathi', 0.0), ('fsig', 0.012), ('fdet', 0.003)):
    ap.add_argument('--' + k, type=float, default=d)
o = ap.parse_args()
f = Path(f'textures/{o.prefix}_head_basecolor.png'); bk = f.with_name(f.stem + '_preline.png')
if not bk.exists() or os.environ.get('RESET') == '1':
    shutil.copyfile(f, bk)
img = np.asarray(Image.open(bk).convert('RGB'), float); N = img.shape[0]
pos, part, _ = texel_parts(o.glb, 'PeasantHOFHead', N)
skin = part == int(o.skin)
hsv_s = (img.max(-1) - img.min(-1)) / np.maximum(img.max(-1), 1)
skincol = skin & (img.max(-1) > 90) & (hsv_s < 0.66)                 # hair painted on the shell stays out of the averages
x = (pos[..., 0] - o.cx) * o.side; y = pos[..., 1]; z = pos[..., 2]
def ss(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)
L = lambda a: a @ np.array([0.299, 0.587, 0.114])
w = ss((x - o.xlo) / o.ease) * ss((o.xhi - x) / o.ease) * ss((y - o.y0) / o.ease) * ss((o.y1 - y) / o.ease) * ss((z - o.zmin) / o.ease)
w = np.where(skincol, np.nan_to_num(w), 0.0)
tgt = w > 0
m = 3 * o.sigma
near = skincol & (np.abs(pos[..., 0] - o.cx) > o.xlo - m) & (y > o.y0 - m) & (y < o.y1 + m) & (z > o.zmin - m)
P = pos[near]; C = img[near]; tree = cKDTree(P)
def broad(Q):
    out = np.zeros((len(Q), 3))
    idx = tree.query_ball_point(Q, 2.5 * o.sigma)
    for k, ii in enumerate(idx):
        if not ii: out[k] = np.nan; continue
        d2 = ((P[ii] - Q[k]) ** 2).sum(1); g = np.exp(-d2 / (2 * o.sigma ** 2))
        out[k] = (g[:, None] * C[ii]).sum(0) / g.sum()
    return out
Q = pos[tgt]; Qm = Q.copy(); Qm[:, 0] = 2 * o.cx - Qm[:, 0]
own, mir = broad(Q), broad(Qm)
ok = np.isfinite(mir).all(1) & np.isfinite(own).all(1)
gain = np.ones_like(own); gain[ok] = mir[ok] / np.maximum(own[ok], 1)
new = img.copy(); new[tgt] = img[tgt] * gain
ww = w[..., None]
res = img * (1 - ww) + new * ww
if o.flathi > o.flatlo:
    # second step, both sides: the outermost cheek strip beside the ears (FLATLO < |x - CX| < FLATHI) is ~15 L brighter than the
    # cheek inside it in the paint, on both sides (the left one hides behind the braid): structures between FDET and FSIG are
    # flattened there, texel = texel x broad(FSIG) / broad(FDET), weight eased over EASE
    ax = np.abs(pos[..., 0] - o.cx)
    wf = ss((ax - o.flatlo) / o.ease) * ss((o.flathi - ax) / o.ease) * ss((y - o.y0) / o.ease) * ss((o.y1 - y) / o.ease) * ss((z - o.zmin) / o.ease)
    wf = np.where(skincol, np.nan_to_num(wf), 0.0); tf = wf > 0
    near2 = skincol & (ax > o.flatlo - 3 * o.fsig) & (y > o.y0 - 3 * o.fsig) & (y < o.y1 + 3 * o.fsig) & (z > o.zmin - 3 * o.fsig)
    P2 = pos[near2]; C2 = res[near2]; tree2 = cKDTree(P2)
    def broad2(Q, sg):
        out = np.zeros((len(Q), 3)); idx = tree2.query_ball_point(Q, 2.5 * sg)
        for k, ii in enumerate(idx):
            d2 = ((P2[ii] - Q[k]) ** 2).sum(1); g = np.exp(-d2 / (2 * sg ** 2)); out[k] = (g[:, None] * C2[ii]).sum(0) / g.sum()
        return out
    Qf = pos[tf]; gainf = broad2(Qf, o.fsig) / np.maximum(broad2(Qf, o.fdet), 1)
    nf = res.copy(); nf[tf] = res[tf] * gainf
    before = res.copy(); res = res * (1 - wf[..., None]) + nf * wf[..., None]
    print('CHEEKFLAT texels', int(tf.sum()), 'mean |dL|', round(float(np.abs(L(res[tf]) - L(before[tf])).mean()), 2))
Image.fromarray(np.clip(res + 0.5, 0, 255).astype(np.uint8)).save(f)
print('CHEEKMIRROR', o.prefix, 'texels', int(tgt.sum()), 'mirror found', int(ok.sum()), 'broad L own -> mirror', round(float(L(own[ok]).mean()), 1),
      '->', round(float(L(mir[ok]).mean()), 1), 'mean |dL|', round(float(np.abs(L(res[tgt]) - L(img[tgt])).mean()), 2))
