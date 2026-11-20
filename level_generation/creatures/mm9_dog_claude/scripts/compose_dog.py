#!/usr/bin/env python3
"""Shared texture set of the MM9 dog (CLAUDE_CREATURE_TEXTURES.md, one MM9 skin: no tiers, no region mask). Usage: compose_dog.py

Inputs: meshy/dog_retexture_v1 and meshy/dog_head_retexture_v1 (the second paints only the head islands of the same
layout, from the head masters), textures/dog_ao_2k.png, work/uv3d_dog.npz (dump_uv3d.py).
Outputs in textures/: dog_basecolor.png (2K; graded separately by grade_basecolor.py), dog_normal_1k.png,
dog_metal_rough_1k.png (R AO, G roughness, B metallic 0), dog_material_classes.png.
The head paint replaces the body paint over the head islands, faded in by the head weight so the neck has no seam, its
colour gain matched to the body in the fade band. The mouth interior (no master shows it) is painted per texel by position and the baked AO: palate with ridges, floor, a dark throat, tongue with a groove, ivory teeth.
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
T = HERE / 'textures'
MB = HERE / 'meshy' / 'dog_retexture_v1'
MH = HERE / 'meshy' / 'dog_head_retexture_v1'
HEADPAINT = MH.exists()
ss = lambda a, b, x: (lambda t: t * t * (3 - 2 * t))(np.clip((x - a) / (b - a), 0, 1))


def ALPHA(hw, xyz, hf, piece):
    return np.where(hf, ss(0.3, 0.92, hw), 0.0).astype(np.float32)


def raster(d, size):
    """Per texel: triangle index and the interpolated 3D position and head weight."""
    uv = d['uv'] * size
    tri = np.full((size, size), -1, np.int32)
    xyz = np.zeros((size, size, 3), np.float32)
    head = np.zeros((size, size), np.float32)
    for t in range(len(uv)):
        p = uv[t]
        x0, x1 = max(int(np.floor(p[:, 0].min())), 0), min(int(np.ceil(p[:, 0].max())), size - 1)
        y0, y1 = max(int(np.floor(p[:, 1].min())), 0), min(int(np.ceil(p[:, 1].max())), size - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = p
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        l3 = 1 - l1 - l2
        inside = (l1 >= -1e-4) & (l2 >= -1e-4) & (l3 >= -1e-4)
        if not inside.any():
            continue
        iy, ix = np.nonzero(inside)
        rows, cols = size - 1 - (iy + y0), ix + x0
        tri[rows, cols] = t
        L = np.stack([l1[inside], l2[inside], l3[inside]], 1)
        xyz[rows, cols] = L @ d['xyz'][t]
        head[rows, cols] = L @ d['head'][t]
    return tri, xyz, head


def load(path, size, mode='RGB'):
    im = Image.open(path).convert(mode)
    if im.width != size:
        im = im.resize((size, size), Image.LANCZOS)
    return np.asarray(im, np.float32) / 255


def pad(img, covered):
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]


def save(a, path):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)


d = np.load(HERE / 'work' / 'uv3d_dog.npz')
S = 2048
tri, xyz, hw = raster(d, S)
cov = tri >= 0
ti = np.maximum(tri, 0)
part = np.where(cov, d['part'][ti], -1)
hf = cov & (d['headface'][ti] == 1)
piece = cov & (part % 10 == 2)
base = load(MB / 'texture_urls_0_base_color.png', S)
rough = load(MB / 'texture_urls_0_roughness.png', S, 'L')
nrm = load(MB / 'texture_urls_0_normal.png', S)
alpha = np.zeros((S, S), np.float32)
rep = {}
if HEADPAINT:
    hb = load(MH / 'texture_urls_0_base_color.png', S)
    hn = load(MH / 'texture_urls_0_normal.png', S)
    hr = load(MH / 'texture_urls_0_roughness.png', S, 'L')
    # the head paint covers the head islands; head texels on other islands take the nearest head-island texel (same side
    # or mirrored across the midline), fading to the body paint where none is close
    from scipy.spatial import cKDTree
    srcm = hf & ~piece
    sy, sx = np.nonzero(srcm)
    tree = cKDTree(xyz[sy, sx])
    want = cov & ~piece & (hw > 0.25)
    fill = want & ~hf
    wy, wx = np.nonzero(fill)
    q = xyz[wy, wx]
    d0, n0 = tree.query(q, workers=8)
    qm = q * np.array([-1, 1, 1])
    d1, n1 = tree.query(qm, workers=8)
    use_m = d1 < d0
    ni = np.where(use_m, n1, n0); dist = np.minimum(d0, d1)
    for arr in (hb, hn, hr):
        arr[wy, wx] = arr[sy[ni], sx[ni]]
    hn[wy[use_m], wx[use_m], 0] = 1 - hn[wy[use_m], wx[use_m], 0]
    near = np.ones((S, S), np.float32)
    near[wy, wx] = 1 - ss(0.008, 0.024, dist)
    rep['head_fill_texels'] = int(fill.sum()); rep['head_fill_dist_p99'] = round(float(np.percentile(dist, 99)), 4)
    alpha = np.where(want, ss(0.3, 0.92, hw), 0.0).astype(np.float32) * near
    band = want & (alpha > 0.15) & (alpha < 0.75) & (xyz[..., 1] > -0.36)
    gain = np.median(base[band], 0) / np.maximum(np.median(hb[band], 0), 1e-3) if band.sum() > 100 else np.ones(3)
    gain = np.clip(gain, 0.75, 1.3)
    rep['head_gain'] = np.round(gain, 3).tolist()
    hb2 = hb * (gain[None, None] * (1 - alpha[..., None]) + alpha[..., None])
    base = base * (1 - alpha[..., None]) + hb2 * alpha[..., None]
    rough = rough * (1 - alpha) + hr * alpha
    nrm = nrm * (1 - alpha[..., None]) + hn * alpha[..., None]
ao = load(T / 'dog_ao_2k.png', S, 'L')
classes = np.zeros((S, S), np.uint8)
classes[cov] = 2                     # fur
# mouth: the pocket is dark in the bake; teeth and tongue are the small pieces in the mouth, eyes the pieces above it
f = 0.7475 + 0.03 * (xyz[..., 1] + 0.5)
box = cov & (np.abs(xyz[..., 0]) < 0.095) & (xyz[..., 2] > 0.705) & (xyz[..., 2] < 0.80) & (xyz[..., 1] < -0.352)
pocket = box & ~piece & (ao < 0.42)
pocket = ndimage.binary_opening(pocket, iterations=2)
t_ = json.load(open(HERE / 'work' / 'teeth_v2.json'))['patch']
tongue = piece & (xyz[..., 2] < 0.8) & (xyz[..., 2] > 0.7) & (np.abs(xyz[..., 0]) < 0.0235)
eyes = piece & (xyz[..., 2] >= 0.8)
# eye spheres: a procedural brown iris, round pupil and catchlight (the views disagree on the two eyes)
for sign in (-1, 1):
    m = eyes & (xyz[..., 0] * sign > 0)
    c = np.array([xyz[m][:, 0].mean(), xyz[m][:, 1].mean(), xyz[m][:, 2].mean()])
    v = (xyz[m] - c) / max(np.linalg.norm(xyz[m] - c, axis=1).max(), 1e-6)
    ax = np.array([sign * 0.55, -0.82, 0.12]); ax /= np.linalg.norm(ax)
    side = np.cross(ax, [0, 0, 1.0]); side /= np.linalg.norm(side)
    upv = np.cross(side, ax)
    u_, w_ = v @ side, v @ upv
    rr = np.sqrt(u_ ** 2 + w_ ** 2)
    col = np.array([0.30, 0.16, 0.07])[None] * (0.7 + 0.6 * rr[:, None])
    col[rr < 0.42] = (0.015, 0.012, 0.01)
    col[rr > 0.85] = (0.03, 0.02, 0.015)
    col[((u_ + sign * 0.25) ** 2 + (w_ - 0.3) ** 2) < 0.02] = (0.9, 0.9, 0.88)
    col[(v @ ax) < 0] = (0.05, 0.03, 0.02)
    base[m] = col
claws = piece & (xyz[..., 2] <= 0.7)
base[claws] = base[claws] * 0.45 + 0.02
y, z = xyz[..., 1], xyz[..., 2]
up = z > f
pal = np.array([0.46, 0.22, 0.24])[None, None] * (0.8 + 0.2 * np.sin(y * 420))[..., None] * up[..., None] + \
    np.array([0.52, 0.27, 0.29])[None, None] * (~up)[..., None]
throat = ss(-0.40, -0.365, y)
pal = pal * (1 - 0.82 * throat[..., None])
m = np.asarray(Image.fromarray((pocket * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.0)), np.float32)[..., None] / 255
base = base * (1 - m) + pal * m
gr = 1 - 0.35 * np.exp(-(xyz[..., 0] / 0.003) ** 2)
base[tongue] = (np.array([0.78, 0.42, 0.45])[None] * gr[tongue][:, None])
# the teeth share one ivory patch: darker at the gum, bright at the tip
pu0, pv0, pd = t_
px0, px1 = int(pu0 * S), int((pu0 + pd) * S) + 2
py1, py0 = S - int(pv0 * S), S - int((pv0 + pd) * S) - 2
ramp = np.linspace(1.0, 0.72, py1 - py0)[:, None, None]
base[py0:py1, px0:px1] = np.array([0.95, 0.91, 0.80])[None, None] * ramp
teeth = np.zeros((S, S), bool); teeth[py0:py1, px0:px1] = True
cov = cov | teeth
rough = np.where(pocket | tongue, 0.42, rough)
rough = np.where(teeth, 0.35, rough)
rough = np.where(eyes, 0.2, rough)
rough = np.where(cov & ~(pocket | tongue | teeth | eyes), np.clip(rough, 0.72, 0.92), rough)
classes[pocket | tongue] = 7
classes[teeth] = 5
classes[eyes] = 6
classes[claws] = 4

base_p = pad(base, cov)
save(base_p, T / 'dog_basecolor.png')
save(pad(nrm, cov)[::1], T / 'dog_normal_2k.png')
Image.open(T / 'dog_normal_2k.png').resize((1024, 1024), Image.LANCZOS).save(T / 'dog_normal_1k.png')
r2 = pad(rough, cov)
r1 = np.asarray(Image.fromarray((r2 * 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS), np.float32) / 255
a1 = np.asarray(Image.fromarray((ao * 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS), np.uint8)
Image.merge('RGB', [Image.fromarray(a1), Image.fromarray((r1 * 255).astype(np.uint8)), Image.new('L', (1024, 1024), 0)]).save(T / 'dog_metal_rough_1k.png')
Image.fromarray(classes).resize((1024, 1024), Image.NEAREST).save(T / 'dog_material_classes.png')
rep['classes'] = {int(k): int((classes == k).sum()) for k in np.unique(classes)}
json.dump(rep, open(HERE / 'work' / 'compose.json', 'w'), indent=1)
print('COMPOSED', json.dumps(rep))
