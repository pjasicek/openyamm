#!/usr/bin/env python3
"""Warmer, lighter faces (coordinator review r4, 2026-11-02: the faces read stern, heavy-shadowed and older than MM9's;
the skin tanned/greyish). Runs after wrist_fix.py on one design's maps.
1. Skin tone: every skin-like texel (warm hue 8-40 deg, saturation 0.18-0.72, value > 90) of the head set's skin shell
   and of the body set takes a per-channel gain = (PEACH / the cheeks' median) ** 0.5 (half way to a light peach),
   feathered at the skin's edge; hair, hoods, cloth and lips (redder than hue 8) are left alone.
2. Eye sockets: head skin texels within 2.3 cm of each eye centre, except the eye itself (8.5 mm) and the brow above
   (more than 1.1 cm over the eye), have their broad luminance (Gaussian low-pass) pulled LIFT of the way up to the cheeks'
   (only where darker), the paint's fine detail (lashes, creases) kept; the head normal map there eases 35 % toward flat.
Eye centres: the eyeball cups' centres measured before they were dropped (Blender rest x +0.018 / -0.028, y -0.092,
z 0.437) in the export frame (glTF y up, floor at 0, +z front). Backups *_prewarm.png; RESET=1 restarts from the current files.
Usage (project folder): face_warm.py <export glb> <prefix> [--lift 0.6]"""
import argparse, os, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
from headpart import texel_parts
ap = argparse.ArgumentParser(); ap.add_argument('glb'); ap.add_argument('prefix'); ap.add_argument('--lift', type=float, default=0.6)
o = ap.parse_args()
PEACH = np.array([236.0, 176.0, 146.0])
EYES = [np.array([0.018, 1.026, 0.092]), np.array([-0.028, 1.025, 0.092])]


def load(name):
    f = Path(f'textures/{o.prefix}_{name}.png'); bk = f.with_name(f.stem + '_prewarm.png')
    if not bk.exists() or os.environ.get('RESET') == '1':
        shutil.copyfile(f, bk)
    return f, np.asarray(Image.open(bk).convert('RGB'), float)


def skinlike(I):
    mx, mn = I.max(-1), I.min(-1); sat = (mx - mn) / np.maximum(mx, 1)
    r, g, b = I[..., 0], I[..., 1], I[..., 2]
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    return (hue > 8) & (hue < 40) & (sat > 0.18) & (sat < 0.72) & (mx > 90)


fh, H = load('head_basecolor'); fb, B = load('basecolor_graded')
ph, parth, _ = texel_parts(o.glb, 'PeasantDFHead', H.shape[0]); P = np.nan_to_num(ph)
pb, cb = texel_positions(o.glb, 'PeasantDF', B.shape[0])
cheek = (parth == 0) & (P[..., 1] > 1.0) & (P[..., 1] < 1.04) & (P[..., 2] > 0.07) & (np.abs(P[..., 0]) > 0.02) & (np.abs(P[..., 0]) < 0.05) & skinlike(H)
mc = np.median(H[cheek], 0)
G = np.sqrt(PEACH / mc)
hs = ndimage.gaussian_filter(((parth == 0) & skinlike(H)).astype(float), 1.0)
H2 = H * (1 + (G - 1) * hs[..., None])
bs = ndimage.gaussian_filter((cb & skinlike(B)).astype(float), 1.0)
B2 = B * (1 + (G - 1) * bs[..., None])
# eye sockets
lum = H2.mean(-1)
skin = (parth == 0)
lp = ndimage.gaussian_filter(lum * skin, 6) / np.maximum(ndimage.gaussian_filter(skin.astype(float), 6), 1e-3)
lc = float(np.median(lum[cheek]))
w = np.zeros(lum.shape)
for e in EYES:
    d = np.linalg.norm(P - e, axis=-1)
    ww = np.clip((0.023 - d) / 0.008, 0, 1) * (d > 0.0085) * ((P[..., 1] - e[1]) < 0.011) * skin
    w = np.maximum(w, ww)
w = ndimage.gaussian_filter(w, 1.5) * o.lift
gain = 1 + np.clip((lc - lp) / np.maximum(lp, 1), 0, 1.0) * w
H2 = H2 * gain[..., None]
Image.fromarray(np.uint8(np.clip(np.round(H2), 0, 255))).save(fh)
Image.fromarray(np.uint8(np.clip(np.round(B2), 0, 255))).save(fb)
fn = Path(f'textures/{o.prefix}_head_normal_1k.png'); bk = fn.with_name(fn.stem + '_prewarm.png')
if not bk.exists() or os.environ.get('RESET') == '1':
    shutil.copyfile(fn, bk)
Nm = np.asarray(Image.open(bk).convert('RGB'), float); n = Nm.shape[0]
wn = np.asarray(Image.fromarray(np.uint8(np.clip(w / max(o.lift, 1e-6), 0, 1) * 255)).resize((n, n), Image.BILINEAR), float) / 255 * 0.35
Nm = Nm * (1 - wn[..., None]) + np.array([128, 128, 255.0]) * wn[..., None]
Image.fromarray(np.uint8(np.round(Nm))).save(fn)
print('FACEWARM', o.prefix, 'cheek', mc.round(), 'gain', G.round(3), 'socket texels', int((w > 0.05).sum()))
