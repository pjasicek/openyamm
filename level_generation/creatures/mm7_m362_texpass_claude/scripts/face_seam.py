"""Skin colour as the engine shows it (region ramps applied per skin, viewer_variants.bake) at the same surface points,
in zones of the face and across the head/body neck crossfade. Zones are rest-pose positions of the texels of the
paid layout (textures/m362_tp_texels.npz); skin-piece texels outside the hair region count. Every skin is clean shaven
since the "No beard" follow-up, so every zone counts on every skin (the installed state: its beard box included).
Reports the mean sRGB colour per zone and CIE76 dE against the cheeks.

Usage: face_seam.py <glb with the ramps> <basecolor png> <region mask png> [json out]
For the installed state: face_seam.py work/before_texpass/mm7_m362.glb work/approved_fine_basecolor.png
work/approved_fine_region_mask.png (the installed maps carried onto the same surface points)."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb import Glb  # noqa: E402
from viewer_variants import bake  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
X0 = -0.0058
g = Glb(sys.argv[1])
base = Image.open(sys.argv[2]).convert('RGB')
mask_img = Image.open(sys.argv[3])
d = np.load(HERE / 'textures' / 'm362_tp_texels.npz')
P = d['P'].astype(np.float32)
piece = d['piece']
S = P.shape[0]
if base.size != (S, S):
    base = base.resize((S, S), Image.Resampling.BILINEAR)
m = np.stack([np.asarray(c.resize((S, S), Image.Resampling.BILINEAR), np.float32) / 255
              for c in mask_img.convert('RGBA').split()], -1)
y, z, dx = P[..., 1], P[..., 2], np.abs(P[..., 0] - X0)
jaw = 1.478 + np.clip(0.03 - z, 0, None) * 0.4
skin = (piece == 0)
ZONES = {
    'forehead': skin & (y > 1.585) & (y < 1.600) & (dx < 0.03) & (z > 0.03),
    'cheeks': skin & (y > 1.525) & (y < 1.548) & (dx > 0.026) & (dx < 0.046) & (z > 0.015),
    'nose': skin & (y > 1.528) & (y < 1.550) & (dx < 0.008) & (z > 0.05),
    'upper lip': skin & (y > 1.5165) & (y < 1.5210) & (dx < 0.012) & (z > 0.046) & (z < 0.054),
    'mouth corners': skin & (y > 1.500) & (y < 1.520) & (dx > 0.026) & (dx < 0.036) & (z > 0.025),
    'chin': skin & (y > 1.482) & (y < 1.500) & (dx < 0.018) & (z > 0.035),
    'jaw sides': skin & (y > 1.490) & (y < 1.515) & (dx > 0.038) & (z > -0.02) & (z < 0.02),
    'neck above seam': skin & (y > jaw + 0.012) & (y < jaw + 0.022) & (z < 0.0),
    'neck below seam': skin & (y > jaw - 0.016) & (y < jaw - 0.006) & (z < 0.0),
    'throat': skin & (y > 1.43) & (y < 1.46) & (z > 0.0) & (dx < 0.03),
}


def lab(rgb):
    c = rgb / 255
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    xyz = c @ np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]).T
    xyz /= np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


out = {}
for mi, mat in enumerate(g.doc['materials']):
    if '_LOD' in mat['name']:
        continue
    ramps = mat['extras']['openyamm_region_ramps']
    eng = bake(base, mask_img, ramps).astype(np.float32)
    clear = m[..., 1] < 0.05
    row = {}
    for name, sel in ZONES.items():
        sel = sel & clear
        if sel.sum() < 30:
            row[name] = None
            continue
        row[name] = np.round(eng[sel].mean(0), 1).tolist()
    ref = lab(np.array(row['cheeks']))
    de = {k: (round(float(np.linalg.norm(lab(np.array(v)) - ref)), 1) if v else None) for k, v in row.items()}
    seam = round(float(np.linalg.norm(lab(np.array(row['neck above seam'])) - lab(np.array(row['neck below seam'])))),
                 1)
    out[mat['name']] = {'mean_srgb': row, 'dE_vs_cheeks': de, 'dE_neck_seam': seam}
    print(f"{mat['name']}: neck seam dE {seam:5.1f} | " + ', '.join(f'{k} {v}' for k, v in de.items() if v is not None))
if len(sys.argv) > 4:
    json.dump(out, open(sys.argv[4], 'w'), indent=1)
