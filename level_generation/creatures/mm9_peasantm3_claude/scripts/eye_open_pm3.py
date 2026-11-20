#!/usr/bin/env python3
"""Calm, open eyes for tier A (orchestrator review 2026-11-02: "A glares - heavy lowered brows pressing on the eyes, a
squinting intense look"; MM9's A is calm and open-eyed). The eyes are paint on the filled sockets (eye_fill.py), so the fix
is a paint warp, sampled on the face surface itself: every head texel of the front face near an eye takes the paint of the
surface point at (x, z - D) (rest pose, Blender axes: x across, z up; the front of the face is a height field over x, z):
  eye opening   D = (z - ZE) * (1 - 1/K) * w_eye   (the painted opening, iris and lids scaled K about the iris line; w_eye
                1 inside an ellipse of AX x AZ round the eye, smooth to 0 at 1.7x)
  brows         D = LIFT * w_brow                   (the brow paint moves LIFT up; w_brow a smooth bump from 4 mm to 32 mm
                above the iris line, peak at 15 mm, over |x - XE| < 3.2 cm)
then the upper-lid crease (2-11 mm above the iris line) is lightened toward the cheek tone by CREASE (it read as a dark
lowered lid). Iris centres measured on the A paint (blue texels): L x -0.0326, R x 0.0228, z 0.810.
Usage (project folder): eye_open_pm3.py <export glb> <prefix> [K 1.35] [LIFT 0.003] [CREASE 0.35] [BROW_LIGHT 0.35] [LIFT_IN 0.004]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
glb, prefix = sys.argv[1], sys.argv[2]
K = float(sys.argv[3]) if len(sys.argv) > 3 else 1.35
LIFT = float(sys.argv[4]) if len(sys.argv) > 4 else 0.003
CREASE = float(sys.argv[5]) if len(sys.argv) > 5 else 0.35
LIFT_IN = float(sys.argv[7]) if len(sys.argv) > 7 else 0.004
EYES = [(-0.0326, 0.810), (0.0228, 0.810)]
AX, AZ, FLOOR = 0.017, 0.0085, 0.855
f = Path(f'textures/{prefix}_head_basecolor.png')
img = np.asarray(Image.open(f).convert('RGB'), float)
N = img.shape[0]
pos, cov = texel_positions(glb, 'PeasantM3Head', N)
bx = np.nan_to_num(pos[..., 0]); by = -np.nan_to_num(pos[..., 2]); bz = np.nan_to_num(pos[..., 1]) - FLOOR
front = cov & (by < -0.025) & (bz > 0.76) & (bz < 0.87) & (np.abs(bx) < 0.075)
src_idx = np.nonzero(front)
tree = cKDTree(np.column_stack([bx[front], bz[front]]))


def sst(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


D = np.zeros(img.shape[:2])
crease = np.zeros(img.shape[:2])
for xe, ze in EYES:
    r = np.sqrt(((bx - xe) / AX) ** 2 + ((bz - ze) / AZ) ** 2)
    w_eye = 1 - sst((r - 1.0) / 0.7)
    D += (bz - ze) * (1 - 1 / K) * w_eye
    up = bz - ze
    w_b = np.where(up < 0.015, sst((up - 0.004) / 0.011), 1 - sst((up - 0.015) / 0.017))
    w_b *= 1 - sst((np.abs(bx - xe) - 0.022) / 0.010)
    D += LIFT * w_b
    # r2c: the inner brow ends dipped toward the nose (a frown): an extra lift growing toward the inner end
    sgn = np.sign(-0.005 - xe)
    w_in = w_b * sst(sgn * (bx - xe) / 0.018)
    D += LIFT_IN * w_in
    w_c = sst((up - 0.002) / 0.003) * (1 - sst((up - 0.013) / 0.004)) * (1 - sst((np.abs(bx - xe) - 0.017) / 0.006))   # r2d: up to the lifted brow (a darker under-brow band read as a second brow)
    crease = np.maximum(crease, w_c)
tgt = front & ((np.abs(D) > 1e-5) | (crease > 0))
ty, tx = np.nonzero(tgt)
_, k = tree.query(np.column_stack([bx[tgt], bz[tgt] - D[tgt]]))
out = img.copy()
out[ty, tx] = img[src_idx[0][k], src_idx[1][k]]
# crease: toward the cheek skin at the texel's own detail
cheek = cov & (bz > 0.775) & (bz < 0.79) & (np.abs(bx) > 0.03) & (np.abs(bx) < 0.055) & (by < -0.04)
ref = np.median(img[cheek], 0)
lum = out @ [0.299, 0.587, 0.114]
det = (lum / np.maximum(ndimage.gaussian_filter(lum, 3), 1))[..., None]
cw = (CREASE * crease * front)[..., None]
out = out * (1 - cw) + np.clip(ref * det, 0, 255) * cw
# r2b: the brows lighter (blond: MM9's A has light golden brows; the paint's dark heavy brows pressed on the eyes) and the
# reddish lower-lid rims moved to the cheek hue at their own brightness (the boys' face_paint_fix.py step 5)
BROW_LIGHT = float(sys.argv[6]) if len(sys.argv) > 6 else 0.35
brow = np.zeros(img.shape[:2]); lowlid = np.zeros(img.shape[:2])
for xe, ze in EYES:
    up = bz - ze
    wb = sst((up - 0.006) / 0.004) * (1 - sst((up - 0.022) / 0.006)) * (1 - sst((np.abs(bx - xe) - 0.022) / 0.008))
    brow = np.maximum(brow, wb)
    r = np.sqrt(((bx - xe) / 0.02) ** 2 + ((bz - ze + 0.004) / 0.008) ** 2)
    lowlid = np.maximum(lowlid, (1 - sst((r - 1.0) / 0.5)) * (bz < ze - 0.001))
lum = out @ [0.299, 0.587, 0.114]
dark = np.clip((ref @ [0.299, 0.587, 0.114] * 0.75 - lum) / 40, 0, 1)
gb = np.array([196.0, 160.0, 96.0])            # light golden brow at the paint's own strand detail
bw = (BROW_LIGHT * brow * dark * front)[..., None]
out = out * (1 - bw) + np.clip(gb * det, 0, 255) * bw
rg = out[..., 0] / np.maximum(out[..., 1], 1)
red = np.clip((rg - ref[0] / ref[1] * 1.08) / 0.2, 0, 1) * lowlid * front
lum = out @ [0.299, 0.587, 0.114]
tone = ref * (lum / max(ref @ [0.299, 0.587, 0.114], 1))[..., None]
out = out * (1 - 0.75 * red[..., None]) + tone * 0.75 * red[..., None]
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(f)
print('EYE_OPEN', prefix, 'texels', int(tgt.sum()), 'max shift mm %.1f' % (np.abs(D[tgt]).max() * 1000), 'cheek ref', ref.round())
