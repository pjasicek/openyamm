#!/usr/bin/env python3
"""Wrists of one design (d1 review 2026-11-02, hand close-ups): the grafted MPFB hands came out darker and browner than
the forearm paint (compose_headhand.py grades them to the face skin), and the forearm ring that cuff_trim.py cut 3 cm
before the hand joint read as a hollow cuff edge over the hand's stub.
1. Hand tone (--hand-ref forearm): hands and forearm skin meet at one broad colour T = the per-channel geometric mean
   of the forearm skin (5-12 cm before the hand joint) and the hand (0-6 cm past it); the forearm skin (up to 35 cm
   before the joint) and the hand squares are scaled to T, detail kept.
2. Wrist band: one band of the design's own wrist colour over both sides of the ring (body texels with s, along
   forearm -> hand from the hand joint, in [S0, S1]; hand texels with s < S1), plus 40 % of the paint's fine luminance
   detail and a darker 2 mm rim at each edge: MM9's dwarf women all wear something there (DF1 silver bracelets, DF2 a
   thin bracelet, DF3 leather cuffs, DF4 the sleeve's cuff band).
Body: textures/<prefix>_basecolor_graded.png; head set: <prefix>_head_basecolor.png (both after seam_tone.py; backups
*_prewrist.png, RESET=1 restarts from the current files). Writes textures/<prefix>_wrist_band_mask.png (body, 1K).
Usage (project folder): wrist_fix.py <export glb> <prefix> --band r,g,b [--hand-ref forearm|face]  (face: the hands take the cheeks' colour) [--s0 -0.043] [--s1 -0.016]"""
import argparse, os, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from pygltflib import GLTF2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
ap = argparse.ArgumentParser()
ap.add_argument('glb'); ap.add_argument('prefix'); ap.add_argument('--band', required=True)
ap.add_argument('--hand-ref', default='forearm'); ap.add_argument('--s0', type=float, default=-0.043)
ap.add_argument('--s1', type=float, default=-0.016)
o = ap.parse_args()
BAND = np.array([float(x) for x in o.band.split(',')])
g = GLTF2().load(o.glb); blob = g.binary_blob()
sk = g.skins[0]; names = [g.nodes[j].name for j in sk.joints]
a_ = g.accessors[sk.inverseBindMatrices]; bv = g.bufferViews[a_.bufferView]
IBM = np.frombuffer(blob, np.float32, a_.count * 16, (bv.byteOffset or 0) + (a_.byteOffset or 0)).reshape(-1, 4, 4)
J = {n: np.linalg.inv(IBM[k].T)[:3, 3] for k, n in enumerate(names)}


def load(name):
    f = Path(f'textures/{o.prefix}_{name}.png'); bk = f.with_name(f.stem + '_prewrist.png')
    if not bk.exists() or os.environ.get('RESET') == '1':
        shutil.copyfile(f, bk)
    return f, np.asarray(Image.open(bk).convert('RGB'), float)


def along(pos):
    """s along forearm -> hand from the hand joint and the distance from that axis, for the nearer arm (by side)"""
    P = np.nan_to_num(pos); S = np.full(P.shape[:2], np.nan); R = np.full(P.shape[:2], np.inf)
    for side in 'LR':
        a0, a1 = J[f'Bip01 {side} Forearm'], J[f'Bip01 {side} Hand']
        ax = (a1 - a0) / np.linalg.norm(a1 - a0)
        rel = P - a1; s = rel @ ax; r = np.linalg.norm(rel - s[..., None] * ax, axis=-1)
        m = (np.sign(P[..., 0]) == np.sign(a1[0])) & (r < 0.08)
        S[m] = s[m]; R[m] = r[m]
    return S, R


def skin(I):
    mx, mn = I.max(-1), I.min(-1); sat = (mx - mn) / np.maximum(mx, 1)
    r, g_, b = I[..., 0], I[..., 1], I[..., 2]
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g_ - b), 2 * r - g_ - b)) % 360
    return (hue > 8) & (hue < 40) & (sat > 0.2) & (sat < 0.75) & (mx > 100)


fb, B = load('basecolor_graded'); fh, H = load('head_basecolor')
pb, cb = texel_positions(o.glb, 'PeasantDF', B.shape[0]); ph, ch = texel_positions(o.glb, 'PeasantDFHead', H.shape[0])
sb, rb = along(pb); sh, rh = along(ph)
hand = ch & np.isfinite(sh) & (np.nan_to_num(ph[..., 1]) < 0.8)
rep = {}
# hands first take the cheeks' broad colour (compose_headhand.py's --ref-head also counts ochre hood/curl texels as skin)
from headpart import texel_parts
_, parth, _ = texel_parts(o.glb, 'PeasantDFHead', H.shape[0])
P = np.nan_to_num(ph)
cheek = (parth == 0) & (P[..., 1] > 1.0) & (P[..., 1] < 1.04) & (P[..., 2] > 0.07) & (np.abs(P[..., 0]) > 0.02) & (np.abs(P[..., 0]) < 0.05) & skin(H)
hb = hand & (sh > 0.0) & (sh < 0.06) & skin(H)
mc, mh0 = np.median(H[cheek], 0), np.median(H[hb], 0)
H = np.where(hand[..., None], H * (mc / mh0), H)
rep.update(face=mc.round().tolist(), hand_before=mh0.round().tolist())
if o.hand_ref == 'forearm':
    fa = cb & np.isfinite(sb) & (sb > -0.12) & (sb < -0.05) & skin(B)
    if fa.sum() > 50:
        mf = np.median(B[fa], 0)
        T = np.sqrt(mf * mc)               # meet half way: Meshy's forearms are pale, the cheeks warmer
        arm = cb & np.isfinite(sb) & (sb > -0.35) & (sb < o.s1 + 0.01) & skin(B)
        arm = ndimage.gaussian_filter(arm.astype(float), 1.0)
        B = B * (1 + (T / mf - 1) * arm[..., None])
        H = np.where(hand[..., None], H * (T / mc), H)
        rep.update(forearm=mf.round().tolist(), target=T.round().tolist())


def paint(I, m, s, s0, s1):
    lum = I.mean(-1); lp = ndimage.gaussian_filter(lum, 6)
    det = np.clip(lum / np.maximum(lp, 1), 0.7, 1.3) ** 0.4
    edge = np.minimum(np.abs(s - s0), np.abs(s - s1))
    dark = np.where(np.nan_to_num(edge) < 0.002, 0.7, 1.0)
    col = BAND[None, None] * det[..., None] * dark[..., None]
    w = ndimage.gaussian_filter(m.astype(float), 0.7)
    return I * (1 - w[..., None]) + col * w[..., None]


mb = cb & np.isfinite(sb) & (sb >= o.s0) & (sb <= o.s1)
mh = hand & (sh <= o.s1)
B2 = paint(B, mb, np.nan_to_num(sb), o.s0, o.s1); H2 = paint(H, mh, np.nan_to_num(sh), o.s0, o.s1)
Image.fromarray(np.uint8(np.clip(np.round(B2), 0, 255))).save(fb)
Image.fromarray(np.uint8(np.clip(np.round(H2), 0, 255))).save(fh)
Image.fromarray(np.uint8(ndimage.zoom(mb.astype(float), 1024 / mb.shape[0], order=1) * 255)).save(f'textures/{o.prefix}_wrist_band_mask.png')
print('WRISTFIX', o.prefix, rep, 'band texels body', int(mb.sum()), 'hand', int(mh.sum()))
