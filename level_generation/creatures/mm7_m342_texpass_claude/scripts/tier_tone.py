"""Tier colours as the engine shows them (region ramps applied to the base colour), installed against the texture pass,
per ramp region (dress, hair) at the same surface points (the installed maps carried onto the layout by
resample_approved.py): area-weighted mean sRGB and luminance sd. Usage: tier_tone.py <after glb>"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb import Glb  # noqa: E402
from viewer_variants import bake  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
S = 2048
r = np.load(HERE / 'work' / 'approved_fine_raster2048.npz')
cov = r['tri_id'] >= 0
lay = np.load(HERE / 'work' / 'uv_cc4_fine.npz')
uv, xyz = lay['uv'], lay['xyz']
a3 = np.linalg.norm(np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]), axis=1) / 2
a2 = np.abs((uv[:, 1, 0] - uv[:, 0, 0]) * (uv[:, 2, 1] - uv[:, 0, 1])
            - (uv[:, 2, 0] - uv[:, 0, 0]) * (uv[:, 1, 1] - uv[:, 0, 1])) / 2
w = np.zeros((S, S))
w[cov] = (a3 / np.maximum(a2, 1e-12))[r['tri_id'][cov]]
legs = np.load(HERE / 'textures' / 'm342_tp_classes.npz')['legs']
amask_img = Image.open(HERE / 'work' / 'approved_fine_region_mask.png')


def channels(img):
    # each channel on its own: an RGBA resize premultiplies alpha (zero here)
    return np.stack([np.asarray(ch.resize((S, S), Image.BILINEAR), np.float32)
                     for ch in img.convert('RGBA').split()], -1) / 255


amask = channels(amask_img)
appr_base = Image.open(HERE / 'work' / 'approved_fine_basecolor.png').convert('RGB')
g = Glb(sys.argv[1])
m0 = g.doc['materials'][0]
new_base = g.image(g.doc['textures'][m0['pbrMetallicRoughness']['baseColorTexture']['index']]['source']).convert('RGB')
new_mask_img = g.image(g.doc['textures'][m0['extras']['openyamm_region_mask']['index']]['source'])
nmask = channels(new_mask_img)
L = np.array([0.2126, 0.7152, 0.0722])
for mi in range(9):
    ramps = g.doc['materials'][mi]['extras']['openyamm_region_ramps']
    A = bake(appr_base, amask_img, ramps).astype(np.float32)
    B = bake(new_base, new_mask_img, ramps).astype(np.float32)
    row = []
    for k, region in enumerate(('dress', 'hair')):
        sa = cov & ~legs & (amask[..., k] > 0.5)
        sb = cov & ~legs & (nmask[..., k] > 0.5)
        ma = [round(float(np.average(A[sa, c], weights=w[sa]))) for c in range(3)]
        mb = [round(float(np.average(B[sb, c], weights=w[sb]))) for c in range(3)]
        sda = float(np.sqrt(np.cov(A[sa] @ L, aweights=w[sa])))
        sdb = float(np.sqrt(np.cov(B[sb] @ L, aweights=w[sb])))
        row.append(f'{region} {ma}->{mb} sd {sda:.1f}->{sdb:.1f}')
    print(g.doc['materials'][mi]['name'], ' | '.join(row))
