#!/usr/bin/env python3
"""Texture quality pass (2026-10-30): the wing base colour and wing alpha re-projected from the HD top view into the
wing_uv_v2.py layout (no Meshy job; the paint is the same top view as v1).

Source: references_hd/05_wings_top.png, wing pixels dilated over the background exactly as prep_wings.py (nearest wing
colour), enlarged x4 twice: Real-ESRGAN x4plus (tools/upscaling/realesrgan-ncnn-vulkan; crisp veins) and Lanczos
(keeps the membrane's fine mottling, which ESRGAN smooths). The mix is the ESRGAN image plus DETAIL x the Lanczos
image's band above a 1.5-source-px Gaussian, i.e. ESRGAN edges with the original fine grain.
Each texel of the new 1K layout belongs to its wing piece (gutters to the nearest piece) and samples the source
through that piece's affine map (work/wing_uv_v2.json), so gutters hold the true continuation of the paint.

Writes textures/dfly_wing_basecolor_src_v2.png and work/wing_alpha_v2.png (compose_dfly.py inputs).
Usage: compose_wing_v2.py [--detail 0.6] [--esrgan <x4 png>] (the ESRGAN result is cached in work/wing_top_esrgan_x4.png)
"""
import argparse, json, subprocess
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
REPO = HERE.parents[2]
ap = argparse.ArgumentParser()
ap.add_argument('--detail', type=float, default=0.6)
ap.add_argument('--layout', default='work/wing_uv_v2.json')
ap.add_argument('--uvs', default='work/wing_uv_v2.npz')
ap.add_argument('--out', default='textures/dfly_wing_basecolor_src_v2.png')
ap.add_argument('--alpha-out', default='work/wing_alpha_v2.png')
args = ap.parse_args()
lay = json.load(open(HERE / args.layout))
S = lay['size']
prof = json.load(open(HERE / 'work' / 'wing_profiles.json'))

# ---- dilated top view (prep_wings.py's wing mask: alpha without the body column)
im = np.array(Image.open(HERE / 'references_hd' / '05_wings_top.png').convert('RGBA')).astype(np.float32)
alpha = im[..., 3] > 128
lower = alpha[700:880]
cols = np.nonzero(lower.any(0))[0]
cx = (cols.min() + cols.max()) / 2.0
body_half = 0.5 * (cols.max() - cols.min()) + 14
wing = alpha.copy()
wing[:, int(cx - body_half):int(cx + body_half) + 1] = False
_, (iy, ix) = ndimage.distance_transform_edt(~wing, return_indices=True)
dil = im[..., :3][iy, ix]
W = HERE / 'work'
dil_png = W / 'wing_top_dilated.png'
esr_png = W / 'wing_top_esrgan_x4.png'
if not esr_png.exists():
    Image.fromarray(dil.clip(0, 255).astype(np.uint8)).save(dil_png)
    subprocess.run([str(REPO / 'tools/upscaling/realesrgan-ncnn-vulkan'), '-i', str(dil_png), '-o', str(esr_png),
                    '-n', 'realesrgan-x4plus', '-s', '4', '-m', str(REPO / 'tools/upscaling/models')], check=True,
                   capture_output=True)
esr = np.asarray(Image.open(esr_png).convert('RGB'), np.float32)
lan = np.asarray(Image.fromarray(dil.clip(0, 255).astype(np.uint8)).resize(esr.shape[1::-1], Image.LANCZOS),
                 np.float32)
band = lan - ndimage.gaussian_filter(lan, (6, 6, 0))          # 1.5 source px at x4
src = np.clip(esr + args.detail * band, 0, 255)
wing4 = np.asarray(Image.fromarray((wing * 255).astype(np.uint8)).resize(esr.shape[1::-1], Image.BILINEAR),
                   np.float32) / 255

# ---- piece per texel (top faces rasterised; gutters to the nearest piece)
d = np.load(HERE / args.uvs)
uv, piece, top = d['uv'], d['piece'], d['top']
label = np.full((S, S), -1, np.int32)
for t, p in zip(uv[top] * S, piece[top]):
    x0, x1 = max(int(np.floor(t[:, 0].min())), 0), min(int(np.ceil(t[:, 0].max())), S - 1)
    y0, y1 = max(int(np.floor(t[:, 1].min())), 0), min(int(np.ceil(t[:, 1].max())), S - 1)
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    a, b, c = t
    w0 = (b[0] - a[0]) * (gy - a[1]) - (b[1] - a[1]) * (gx - a[0])
    w1 = (c[0] - b[0]) * (gy - b[1]) - (c[1] - b[1]) * (gx - b[0])
    w2 = (a[0] - c[0]) * (gy - c[1]) - (a[1] - c[1]) * (gx - c[0])
    inside = ((w0 >= 0) & (w1 >= 0) & (w2 >= 0)) | ((w0 <= 0) & (w1 <= 0) & (w2 <= 0))
    yy, xx = np.nonzero(inside)
    label[S - 1 - (yy + y0), xx + x0] = p                        # image rows run top-down, v up
covered = label >= 0
_, (ly, lx) = ndimage.distance_transform_edt(~covered, return_indices=True)
label = label[ly, lx]

rows, cols_ = np.mgrid[0:S, 0:S]
u = (cols_ + 0.5) / S
v = 1.0 - (rows + 0.5) / S
px = np.zeros((S, S, 2))
for p, rec in lay['affine_uv_to_image'].items():
    Q = np.array(rec['matrix'])
    m = label == int(p)
    px[m] = np.c_[u[m], v[m], np.ones(m.sum())] @ Q
# v1 sampled the image at continuous coordinate = pixel index; x4 continuous 4c -> array index 4c - 0.5
ci = [px[..., 1] * 4 - 0.5, px[..., 0] * 4 - 0.5]
out = np.stack([ndimage.map_coordinates(src[..., k], ci, order=3, mode='nearest') for k in range(3)], -1)
a = ndimage.map_coordinates(wing4, ci, order=1, mode='nearest')
Image.fromarray(out.clip(0, 255).round().astype(np.uint8)).save(HERE / args.out)
Image.fromarray((a.clip(0, 1) * 255).round().astype(np.uint8)).save(HERE / args.alpha_out)
print('WING_V2', json.dumps({'size': S, 'covered_pct': round(100 * float(covered.mean()), 1), 'detail': args.detail,
                             'pieces': len(lay['affine_uv_to_image'])}))
