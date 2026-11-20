#!/usr/bin/env python3
"""Shared texture set of the MM9 cat (CLAUDE_CREATURE_TEXTURES.md, one MM9 skin: no tiers, no region mask). Usage: compose_cat.py

Inputs: meshy/cat_retexture_v1 and meshy/cat_head_retexture_v1 (the second paints only the head islands of the same
layout, from the head masters), textures/cat_ao_2k.png, work/uv3d_cat.npz (dump_uv3d.py).
Outputs in textures/: cat_basecolor.png (2K; graded separately by grade_basecolor.py), cat_normal_1k.png,
cat_metal_rough_1k.png (R AO, G roughness, B metallic 0), cat_material_classes.png.
The head paint replaces the body paint over the head islands, faded in by the head weight so the neck has no seam, its
colour gain matched to the body in the fade band. The eye spheres take a procedural iris and slit pupil.
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
T = HERE / 'textures'
MB = HERE / 'meshy' / 'cat_retexture_v1'
MH = HERE / 'meshy' / 'cat_head_retexture_v1'
HEADPAINT = MH.exists()
ss = lambda a, b, x: (lambda t: t * t * (3 - 2 * t))(np.clip((x - a) / (b - a), 0, 1))


def ALPHA(hw, xyz, hf, piece):
    return np.where(hf, ss(0.3, 0.92, hw), 0.0).astype(np.float32)


EYES = json.load(open(HERE / 'work' / 'graft_v1.json'))['eyes']
EYES = [(e['centre'], e['radius']) for e in EYES]


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


d = np.load(HERE / 'work' / 'uv3d_cat.npz')
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
    gj = json.load(open(HERE / 'work' / 'graft_v1.json'))
    C = np.array(gj['cut_at'])
    U = np.array([0.0, -0.72, 0.694])
    dn = (xyz - C) @ U
    srcm = hf & ~piece
    sy, sx = np.nonzero(srcm)
    tree = cKDTree(xyz[sy, sx])
    want = cov & ~piece & (dn > -0.004)
    fill = want & ~hf
    wy, wx = np.nonzero(fill)
    near = np.ones((S, S), np.float32)
    if len(wy):
        q = xyz[wy, wx]
        d0, n0 = tree.query(q, workers=8)
        d1, n1 = tree.query(q * np.array([-1, 1, 1]), workers=8)
        use_m = d1 < d0
        ni = np.where(use_m, n1, n0); dist = np.minimum(d0, d1)
        # blurred head colour plus the body paint's fur grain: a nearest copy of the head paint gives stair steps of tan dots
        ws_ = ndimage.gaussian_filter(srcm.astype(np.float32), 8) + 1e-4
        hb_low = np.stack([ndimage.gaussian_filter(hb[..., c] * srcm, 8) for c in range(3)], -1) / ws_[..., None]
        grain = base - np.stack([ndimage.gaussian_filter(base[..., c], 3) for c in range(3)], -1)
        hb[wy, wx] = hb_low[sy[ni], sx[ni]]
        fw_ = ndimage.gaussian_filter(fill.astype(np.float32), 4) + 1e-4
        soft = np.stack([ndimage.gaussian_filter(hb[..., c] * fill, 4) for c in range(3)], -1) / fw_[..., None]
        hb[wy, wx] = soft[wy, wx] + grain[wy, wx]
        hn[wy, wx] = nrm[wy, wx]
        hr[wy, wx] = rough[wy, wx]
        near[wy, wx] = 1 - ss(0.003, 0.012, dist)
    rep['head_fill_texels'] = int(fill.sum())
    # the head paint fades in over 3.8 cm from the graft plane along the neck (the head and body views draw the fur apart)
    alpha = np.where(want, ss(-0.004, 0.034, dn), 0.0).astype(np.float32) * near
    band = want & (dn > -0.004) & (dn < 0.03) & (xyz[..., 1] > -0.17)
    gain = np.median(base[band], 0) / np.maximum(np.median(hb[band], 0), 1e-3) if band.sum() > 100 else np.ones(3)
    gain = np.clip(gain, 0.9, 1.15)
    rep['head_gain'] = np.round(gain, 3).tolist()
    # the head fur takes the body fur's tone (the white blaze and muzzle keep theirs)
    lum = hb @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    k = (0.5 * (1 - ss(0.4, 0.8, lum)))[..., None]
    hb2 = hb * (1 + (gain[None, None] - 1) * k)
    base = base * (1 - alpha[..., None]) + hb2 * alpha[..., None]
    rough = rough * (1 - alpha) + hr * alpha
    nrm = nrm * (1 - alpha[..., None]) + hn * alpha[..., None]
    # tone levelling across the chart seams of the head and upper neck: the low-pass colour just inside each island is
    # compared with the matching 3D point on the neighbouring island, half the difference goes in on each side and fades
    # out over 40 px, so the chart borders stop reading as patches and the fur grain is untouched
    lab_, n_lab = ndimage.label(cov)
    ins_ = ndimage.binary_erosion(cov, iterations=4)
    w5_ = ndimage.gaussian_filter(ins_.astype(np.float32), 5) + 1e-4
    low_ = np.stack([ndimage.gaussian_filter(base[..., c] * ins_, 5) for c in range(3)], -1) / w5_[..., None]
    ring = ins_ & ~ndimage.binary_erosion(cov, iterations=7) & (dn > -0.05) & ~piece
    ry, rx = np.nonzero(ring)
    rt = cKDTree(xyz[ry, rx])
    rd, rn = rt.query(xyz[ry, rx], k=96, workers=8)
    rl = lab_[ry, rx]
    other = rl[rn] != rl[:, None]
    first_ = other.argmax(1)
    idx_ = np.arange(len(ry))
    ok_ = other[idx_, first_] & (rd[idx_, first_] < 0.008)
    off_ = np.zeros((S, S, 3), np.float32)
    have = np.zeros((S, S), bool)
    off_[ry[ok_], rx[ok_]] = np.clip(0.5 * (low_[ry[rn[idx_, first_]], rx[rn[idx_, first_]]] - low_[ry, rx]), -0.35, 0.35)[ok_]
    have[ry[ok_], rx[ok_]] = True
    for i_, sl_ in enumerate(ndimage.find_objects(lab_), 1):
        h_ = have[sl_] & (lab_[sl_] == i_)
        if not h_.any():
            continue
        isl = lab_[sl_] == i_
        w_ = ndimage.gaussian_filter(h_.astype(np.float32), 6) + 1e-5
        o_ = np.stack([ndimage.gaussian_filter(off_[sl_][..., c] * h_, 6) for c in range(3)], -1) / w_[..., None]
        fade = 1 - ss(0.0, 40.0, ndimage.distance_transform_edt(~h_).astype(np.float32))
        fade = fade * ss(-0.05, -0.02, dn[sl_])
        base[sl_][isl & ~piece[sl_]] += (o_ * fade[..., None])[isl & ~piece[sl_]]
    base = np.clip(base, 0, 1)
    rep['seam_level_texels'] = int(ok_.sum())
ao = load(T / 'cat_ao_2k.png', S, 'L')
classes = np.zeros((S, S), np.uint8)
classes[cov] = 2                     # fur
# eyes are the two sphere pieces: a procedural iris (yellow-green, vertical slit pupil) unless the paint holds one
eyes = piece.copy()
E = EYES
for c, r_ in E:
    c = np.array(c)
    m = eyes & ((xyz - c)[..., 0] * c[0] >= 0) & (np.linalg.norm(xyz - c, axis=-1) < r_ * 1.2)
    ax = np.array([np.sign(c[0]) * 0.42, -0.9, 0.0]); ax /= np.linalg.norm(ax)
    v = (xyz[m] - c) / r_
    cosv = v @ ax
    side = np.cross(ax, [0, 0, 1.0]); side /= np.linalg.norm(side)
    upv = np.cross(side, ax)
    u_, w_ = v @ side, v @ upv
    rr = np.sqrt(u_ ** 2 + w_ ** 2)
    iris = np.array([0.72, 0.66, 0.22])[None] * (0.72 + 0.5 * rr[:, None]) * (1 - 0.35 * ss(0.62, 0.8, rr)[:, None])
    pupil = (np.abs(u_) < 0.13 * (1 - 0.5 * np.clip(np.abs(w_) / 0.75, 0, 1))) & (np.abs(w_) < 0.72)
    col = iris.copy()
    col[pupil] = (0.02, 0.02, 0.02)
    col[rr > 0.82] = (0.05, 0.04, 0.03)
    spec = (((u_ + 0.28) ** 2 + (w_ - 0.32) ** 2) < 0.018)
    col[spec] = (0.95, 0.95, 0.92)
    base[m] = np.where((cosv > 0)[:, None], col, base[m] * 0.2)
rough = np.where(eyes, 0.2, np.clip(rough, 0.72, 0.92))
classes[eyes] = 6

# Meshy painted a one-texel white line across the left hip (atlas y = 1.0958 x + 0.957, x 886..1016): only those texels
# are replaced, each by the fur 6 px to the side of the line, so the fur grain survives
yy_, xx_ = np.mgrid[0:S, 0:S]
dist_ = (1.0958 * xx_ + 0.957 - yy_) / np.hypot(1.0958, 1.0)
line = (np.abs(dist_) < 2.5) & (xx_ >= 886) & (xx_ <= 1016)
rows_, cols_ = np.nonzero(line)
for sign_ in (1, -1):
    r2_ = np.clip((rows_ - sign_ * 6 / np.hypot(1.0958, 1.0)).round().astype(int), 0, S - 1)
    c2_ = np.clip((cols_ + sign_ * 6 * 1.0958 / np.hypot(1.0958, 1.0)).round().astype(int), 0, S - 1)
    ok_ = cov[r2_, c2_] & ~line[r2_, c2_]
    base[rows_[ok_], cols_[ok_]] = base[r2_[ok_], c2_[ok_]]
    rows_, cols_ = rows_[~ok_], cols_[~ok_]
rep['scratch_texels'] = int(line.sum())
# Meshy paints a thin pale rim along some island borders: the outer 3 px of every island are replaced
core = ndimage.binary_erosion(cov, iterations=3) | piece
base_p = pad(base, core)
# the rim takes the fur mirrored across the island's core edge: padding or blurring it left a smooth strip along every seam
rim_ = cov & ~core
_, (iy_, ix_) = ndimage.distance_transform_edt(~core, return_indices=True)
ry_, rx_ = np.nonzero(rim_)
my_ = np.clip(2 * iy_[ry_, rx_] - ry_, 0, S - 1)
mx_ = np.clip(2 * ix_[ry_, rx_] - rx_, 0, S - 1)
ok_ = core[my_, mx_]
base_p[ry_[ok_], rx_[ok_]] = base[my_[ok_], mx_[ok_]]
rep['rim_mirrored'] = int(ok_.sum())
nrm = pad(nrm, core)
save(base_p, T / 'cat_basecolor.png')
save(pad(nrm, cov)[::1], T / 'cat_normal_2k.png')
Image.open(T / 'cat_normal_2k.png').resize((1024, 1024), Image.LANCZOS).save(T / 'cat_normal_1k.png')
r2 = pad(rough, cov)
r1 = np.asarray(Image.fromarray((r2 * 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS), np.float32) / 255
a1 = np.asarray(Image.fromarray((ao * 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS), np.uint8)
Image.merge('RGB', [Image.fromarray(a1), Image.fromarray((r1 * 255).astype(np.uint8)), Image.new('L', (1024, 1024), 0)]).save(T / 'cat_metal_rough_1k.png')
Image.fromarray(classes).resize((1024, 1024), Image.NEAREST).save(T / 'cat_material_classes.png')
rep['classes'] = {int(k): int((classes == k).sum()) for k in np.unique(classes)}
json.dump(rep, open(HERE / 'work' / 'compose.json', 'w'), indent=1)
print('COMPOSED', json.dumps(rep))
