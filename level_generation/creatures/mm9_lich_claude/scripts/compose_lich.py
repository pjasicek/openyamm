#!/usr/bin/env python3
"""Body and skull texture sets from the 4K Meshy paints on our UVs (colour downsampled once to 2K, normal, roughness to 1K,
padded into the gutters), linings filled from the outer paint and darkened. Writes textures/lich_* (body) and
textures/lich_head_*, class maps, and the skull's eye mask. Run from the project folder."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
LINING_DARK = 0.3
d = np.load('work/uv_v1.npz')
part, fid, idx, uv, hu, co = d['part'], d['fid'], d['idx'], d['uv'], d['hu'], d['co']
T = Path('textures'); J = Path('meshy/retexture_v1'); H = Path('meshy/head_retexture_v1')
head = part == 30; line = np.isin(part, (40, 41, 42))


def coverage(tris, size):
    im = Image.new('L', (size, size), 0); dr = ImageDraw.Draw(im)
    for t in tris:
        dr.polygon([(float(u * size), float(v * size)) for u, v in t], fill=255)
    return np.asarray(im) > 0


def pad(img, cov):
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    return img[iy, ix]


def decrack(im, tris, cov, thresh=0.022):
    """Meshy's paint leaves hair-thin pale cracks along triangle edges inside the charts (lines straight across the cloth
    and hood). Texels on a triangle edge that stand out from their neighbours off the edge take the neighbours' colour."""
    n = im.shape[0]
    m = Image.new('L', (n, n), 0); dr = ImageDraw.Draw(m)
    for t in tris:
        p = [(float(u * n), float(v * n)) for u, v in t]
        dr.line(p + p[:1], fill=255, width=7)
    edge = (np.asarray(m) > 0) & cov
    a = np.asarray(im, np.float32) / 255
    if a.ndim == 2:
        a = a[..., None]
    keep = (~edge).astype(np.float32)
    w = ndimage.gaussian_filter(keep, 3.5)
    near = np.stack([ndimage.gaussian_filter(a[..., c] * keep, 3.5) for c in range(a.shape[2])], -1) / np.maximum(w, 1e-3)[..., None]
    dev = (a - near).max(2)                                 # pale cracks only: never touch dark weave
    fix = edge & (dev > thresh)
    print('decrack', im.shape, 'edge texels', int(edge.sum()), 'fixed', int(fix.sum()))
    a[fix] = near[fix]
    out = (a.clip(0, 1) * 255 + 0.5).astype(np.uint8)
    return out[..., 0] if np.asarray(im).ndim == 2 else out


def load(job, name, mode, size, tris=None, erode=3):
    """Meshy's gutters hold pale streaks: at 4K the texels inside the eroded charts are padded outward first, then the
    map is downsampled once, so chart borders never sample the gutter (the pale lines along the seams)."""
    im = np.asarray(Image.open(job / f'texture_urls_0_{name}.png').convert(mode))
    if tris is not None:
        cov = ndimage.binary_erosion(coverage(tris, im.shape[0]), iterations=erode)
        im = pad(im, cov)
        im = decrack(im, tris, cov)
    return np.asarray(Image.fromarray(im).resize((size, size), Image.LANCZOS))


body_faces = ~line
# glTF UVs: v from the image top (the raster above uses v * size as the row); Blender's are flipped
def flip(u):
    o = u.copy(); o[..., 1] = 1 - o[..., 1]; return o


uvt = flip(uv); hut = flip(hu)
c2, c1 = coverage(uvt[body_faces & ~head], 2048), coverage(uvt[body_faces & ~head], 1024)
bt = uvt[body_faces & ~head]
base = load(J, 'base_color', 'RGB', 2048, bt).copy()
nrm = load(J, 'normal', 'RGB', 1024, bt).copy()
rough = load(J, 'roughness', 'L', 1024, bt).astype(np.float32) / 255
# neck in the hood: Meshy painted the master's rust collar bright; it sits in shadow
neck = coverage(uvt[part == 12], 2048)
base[neck] = (base[neck] * np.array([0.42, 0.26, 0.26])).astype(np.uint8)
# bandages and bone: the masters read lighter than MM9's skin; bring them closer
for parts, gain in (((1,), 0.8), ((3, 10), 0.84)):
    c = coverage(uvt[np.isin(part, parts)], 2048)
    base[c] = (base[c] * gain).astype(np.uint8)
# the hood's crown over the old skull: Meshy painted a dark scab where the skull poked through; filled from the cloth around it
from scipy.spatial import cKDTree
sk = co[np.unique(idx[head])]
hood_f = np.nonzero((part == 2) & (co[idx][:, :, 2].min(1) > 1.42))[0]
near = np.array([cKDTree(sk).query(co[idx[f]].mean(0))[0] < 0.016 for f in hood_f])
print('hood faces over the skull', int(near.sum()))
big = coverage(uvt[hood_f[near]], 2048)
hood = coverage(uvt[hood_f], 2048)
_mx = base.max(2) / 255.0; _s = (_mx - base.min(2) / 255.0) / np.maximum(_mx, 1e-3)
_p = ndimage.binary_opening(hood & (_mx > 0.34) & (_s < 0.62), iterations=2)
_l, _n = ndimage.label(_p)
if _n:
    _z = ndimage.sum(_p, _l, range(1, _n + 1))
    big |= np.isin(_l, 1 + np.nonzero(_z > 60)[0])
big = ndimage.binary_dilation(big, iterations=10) & hood
# the AO was baked with the crown through the hood: a dark oval round the contact, gone with the same fill
_ao = np.asarray(Image.open('textures/lich_ao.png').convert('L'), np.float32)
if big.any():
    src = hood & ~big
    _k = src.astype(np.float32); _w = np.maximum(ndimage.gaussian_filter(_k, 24), 1e-3)
    _f = ndimage.gaussian_filter(_ao * _k, 24) / _w
    _a = np.clip(ndimage.gaussian_filter(big.astype(np.float32), 5), 0, 1)
    _ao = _ao * (1 - _a) + _f * _a
    Image.fromarray(_ao.clip(0, 255).astype(np.uint8)).save('textures/lich_ao_final.png')
    ks = src.astype(np.float32); ws = np.maximum(ndimage.gaussian_filter(ks, 24), 1e-3)
    fill = np.stack([ndimage.gaussian_filter(base[..., c].astype(np.float32) * ks, 24) / ws for c in range(3)], -1)
    grain = base.astype(np.float32) - ndimage.gaussian_filter(base.astype(np.float32), (6, 6, 0))
    ys, xs = np.nonzero(big)
    # weave from cloth of the same chart beside the patch
    far = np.nonzero(src)
    k = np.random.default_rng(3).integers(0, len(far[0]), 1)
    g = grain[(far[0][(np.arange(len(ys)) * 7) % len(far[0])]), (far[1][(np.arange(len(ys)) * 7) % len(far[0])])]
    gx = grain[np.clip(ys + 140, 0, 2047), np.clip(xs + 60, 0, 2047)]
    w = np.clip(ndimage.gaussian_filter(big.astype(np.float32), 4), 0, 1)[ys, xs][:, None]
    base[ys, xs] = np.clip(base[ys, xs] * (1 - w) + (fill[ys, xs] + np.clip(gx, -24, 24)) * w, 0, 255).astype(np.uint8)
# what decrack left: pale strokes on the cloth, long and thin, off the triangle edges by a few texels, found by their shape
clothm = coverage(uvt[np.isin(part, (2, 8))], 2048)
lumb = base.astype(np.float32) @ np.array([0.3, 0.59, 0.11]) / 255
th = lumb - ndimage.median_filter(lumb, size=11)
cand = (th > 0.014) & ndimage.binary_erosion(clothm, iterations=1)
lab, n = ndimage.label(cand, structure=np.ones((3, 3)))
strokes = np.zeros(n + 1, bool)
sz = ndimage.sum(cand, lab, range(1, n + 1))
for i, o in enumerate(ndimage.find_objects(lab)):
    ext = max(o[0].stop - o[0].start, o[1].stop - o[1].start)
    if ext >= 11 and sz[i] / ext < 3.0:
        strokes[i + 1] = True
stroke = ndimage.binary_dilation(strokes[lab], iterations=2) & clothm
print('strokes', int(strokes.sum()), 'texels', int(stroke.sum()))
keep = (~stroke).astype(np.float32)
w = np.maximum(ndimage.gaussian_filter(keep, 3), 1e-3)
fill = np.stack([ndimage.gaussian_filter(base[..., c].astype(np.float32) * keep, 3) / w for c in range(3)], -1)
base[stroke] = fill[stroke].clip(0, 255).astype(np.uint8)
# linings: each texel takes the outer face's colour at the same barycentric point, darkened
lm = np.nonzero(line)[0]
out = base.astype(np.float32)
lcov = np.zeros((2048, 2048), bool)
for f in lm:
    of = int(fid[f])
    pl = co[idx[f]]; po = co[idx[of]]
    order = [int(np.argmin(np.linalg.norm(po - p, axis=1))) for p in pl]
    tl = uvt[f] * 2048; to = uvt[of][order] * 2048
    lo = np.floor(tl.min(0)).astype(int) - 1; hi = np.ceil(tl.max(0)).astype(int) + 2
    xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], 2048)), np.arange(max(lo[1], 0), min(hi[1], 2048)))
    if xs.size == 0:
        continue
    p = np.stack([xs + 0.5, ys + 0.5], -1)
    m = np.array([tl[1] - tl[0], tl[2] - tl[0]]).T
    if abs(np.linalg.det(m)) < 1e-9:
        continue
    st = (p - tl[0]) @ np.linalg.inv(m).T
    ok = (st[..., 0] >= -0.03) & (st[..., 1] >= -0.03) & (st.sum(-1) <= 1.06)
    w = st[ok]
    q = to[0] + w[:, :1] * (to[1] - to[0]) + w[:, 1:2] * (to[2] - to[0])
    qi = np.clip(q.astype(int), 0, 2047)
    out[ys[ok], xs[ok]] = base[qi[:, 1], qi[:, 0]] * LINING_DARK
    lcov[ys[ok], xs[ok]] = True
base = out.clip(0, 255).astype(np.uint8)
cov2 = c2 | lcov
lc1 = np.asarray(Image.fromarray(lcov.astype(np.uint8) * 255).resize((1024, 1024), Image.BILINEAR)) > 127
nrm[lc1] = (128, 128, 255); rough[lc1] = 0.97
cov1 = c1 | lc1
Image.fromarray(pad(base, cov2)).save(T / 'lich_basecolor.png')
Image.fromarray(pad(nrm, cov1)).save(T / 'lich_normal_1k.png')
ao = np.asarray(Image.open('textures/lich_ao_final.png').convert('L').resize((1024, 1024), Image.LANCZOS))
r8 = pad((rough * 255).astype(np.uint8), cov1)
Image.merge('RGB', [Image.fromarray(pad(ao, cov1)), Image.fromarray(r8), Image.new('L', (1024, 1024), 0)]).save(T / 'lich_metal_rough_1k.png')
cover = np.zeros((1024, 1024), np.uint8)
# per-part id map (1K) for masks and classes
pm = Image.new('I', (1024, 1024), 0); dr = ImageDraw.Draw(pm)
for f in np.nonzero(~head)[0]:
    dr.polygon([(float(u * 1024), float(v * 1024)) for u, v in uvt[f]], fill=int(part[f]) + 1)
pm = np.asarray(pm).astype(np.int32) - 1
np.save('work/part_map_1k.npy', pm)
# skull set
hc2 = coverage(hut[head], 2048); hc1 = coverage(hut[head], 1024)
ht = hut[head]
hb = load(H, 'base_color', 'RGB', 2048, ht)
Image.fromarray(pad(hb, hc2)).save(T / 'lich_head_basecolor.png')
Image.fromarray(pad(load(H, 'normal', 'RGB', 1024, ht), hc1)).save(T / 'lich_head_normal_1k.png')
hr = np.maximum(load(H, 'roughness', 'L', 1024, ht), 190)
hao = np.asarray(Image.open('textures/lich_head_ao.png').convert('L').resize((1024, 1024), Image.LANCZOS))
Image.merge('RGB', [Image.fromarray(pad(hao, hc1)), Image.fromarray(pad(hr.astype(np.uint8), hc1)), Image.new('L', (1024, 1024), 0)]).save(T / 'lich_head_metal_rough_1k.png')
print('COMPOSE', 'body %.1f%%' % (100 * cov2.mean()), 'skull %.1f%%' % (100 * hc2.mean()))
