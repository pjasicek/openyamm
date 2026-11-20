"""1K head maps (head half of the merged atlas) for the face retexture of the reduced Mep, in head_uv.py's layout:
- turban faces: the installed maps copied per triangle from their installed UVs (bilinear); tangent-space normals
  rotated by each triangle's UV-frame change (polar part of new <- old), so the turban looks as installed;
- the ears: installed texels as for the turban (Meshy painted them as grey cloth); Meshy's skin wedge in the white
  head band (above z 1.576 m) takes the nearest white band texel;
- rest of the face part (skin, eyes, brows, beard, neck cloth): Meshy head_retexture_r62. Classes by the new colour:
  skin (warm brown), white (beard, brows, cloth), other (eyes, mouth, nostrils). White is quantile-matched per
  channel to the installed white texels; skin luminance half quantile-matched, half mean-shifted (chroma kept), so the
  tier ramps (mask A skin, B coat) see similar values without the installed dark veins;
  mask, specular (R) and roughness (G) take the installed medians of the class;
- normal convention measured (Meshy returns +y down), metallic 0.
Writes textures/mep_head_{basecolor,metal_rough,normal,region_mask}.png, review/head_regions.png, work/compose_head.json."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P = Path(__file__).resolve().parents[1]; ROOT = P.parents[2]; N = 1024; X0 = 1056
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
sys.path.insert(0, str(ROOT / 'tools')); from normal_map_convention import measure  # noqa: E402
M = P / 'meshy/head_retexture_r62'; T = P / 'textures'; T.mkdir(exist_ok=True)


def raster(uv):
    """per texel (rows top-down): triangle index and barycentrics of UV triangles (uv: T x 3 x 2 in 0..1)"""
    tri = np.full((N, N), -1, np.int32); bary = np.zeros((N, N, 3), np.float32)
    for i, t in enumerate(uv * N):
        lo = np.maximum(0, np.floor(t.min(0)).astype(int)); hi = np.minimum(N - 1, np.ceil(t.max(0)).astype(int))
        m = np.column_stack([t[1] - t[0], t[2] - t[0]])
        if hi[0] < lo[0] or hi[1] < lo[1] or abs(np.linalg.det(m)) < 1e-12:
            continue
        xx, yy = np.meshgrid(np.arange(lo[0], hi[0] + 1) + .5, np.arange(lo[1], hi[1] + 1) + .5)
        w = (np.stack([xx, yy], -1) - t[0]) @ np.linalg.inv(m).T; w0 = 1 - w.sum(-1)
        inside = (w[..., 0] >= -.02) & (w[..., 1] >= -.02) & (w0 >= -.02)
        rows = N - 1 - (yy[inside] - .5).astype(int); cols = (xx[inside] - .5).astype(int)
        tri[rows, cols] = i; bary[rows, cols] = np.stack([w0[inside], w[inside, 0], w[inside, 1]], -1)
    return tri, bary


def bilinear(img, x, y):
    x = np.clip(x - .5, 0, img.shape[1] - 1.001); y = np.clip(y - .5, 0, img.shape[0] - 1.001)
    x0, y0 = x.astype(int), y.astype(int); fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
            + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


def pad(a, c):
    return a[tuple(ndimage.distance_transform_edt(~c, return_distances=False, return_indices=True))]


def save(a, p, mode='RGB'):
    Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255 + .5), mode).save(p, optimize=True)


def meshy(suffix):
    return np.asarray(Image.open(M / f'texture_urls_0_{suffix}.png').convert('RGB').resize((N, N), Image.LANCZOS), float) / 255


inst = {k: np.asarray(Image.open(P / f'work/inst_{k}.png').convert('RGBA' if k == 'mask' else 'RGB'), float) / 255
        for k in ('base', 'mr', 'normal', 'mask')}
d = np.load(P / 'work/head_uv.npz'); new, old, face = d['uv'], d['old'], d['face']
# 'turban' triangles (pale blue in the installed colour) whose installed mask is partly skin are forehead faces under
# the band: they take the Meshy texels like the face (Meshy painted every head face), or they stand out as skin wedges
B12 = np.random.default_rng(1).dirichlet((1, 1, 1), 12)
sp = np.einsum('sk,tkc->tsc', B12, old)
skin_a = inst['mask'][np.clip(((1 - sp[..., 1]) * N).astype(int), 0, N - 1), np.clip((X0 + sp[..., 0] * N).astype(int), 0, 2079), 3].mean(1)
forehead = ~face & (skin_a > .2)
face = face | forehead
# the ears keep the installed texels (Meshy painted them as grey cloth); the white head band (per texel: the long
# glabella triangles also hold the brows) is repaired below
c = d['pos'].mean(1); zmax = d['pos'][..., 2].max(1)
band = face & (zmax > 1.574)  # triangles reaching the band (some also hold the brows): per texel below
ears = face & (np.abs(c[:, 0]) > .045) & (c[:, 2] > 1.52) & (c[:, 2] < 1.59) & (c[:, 1] > -.015)
copy = ~face | ears
tri, bary = raster(new); cov = tri >= 0; t = np.maximum(tri, 0)
tz = (bary * d['pos'][t][..., 2]).sum(-1); tx = (bary * d['pos'][t][..., 0]).sum(-1)  # texel height and side
wedge = tz > 1.576  # the band starts right above the brows (installed); Meshy ran skin up into it
fpart = cov & ~copy[t]; turban = cov & ~fpart; bandreg = (band[t] & wedge)[fpart]
report = {'forehead_triangles': int(forehead.sum()), 'band_triangles': int(band.sum()), 'ear_triangles': int(ears.sum()), 'covered': int(cov.sum()), 'face_texels': int(fpart.sum()), 'turban_texels': int(turban.sum())}

# installed texels: the old layout of the same triangles, in atlas pixels (rows top-down)
ouv = (np.einsum('rk,rkc->rc', bary[turban], old[t[turban]]))
ox, oy = X0 + ouv[:, 0] * N, (1 - ouv[:, 1]) * N
out = {k: np.zeros((N, N, inst[k].shape[2])) for k in inst}
for k in inst:
    out[k][turban] = bilinear(inst[k], ox, oy)
# normals: rotate xy from the old to the new UV frame (u right, v up; glTF +y up)
jn = np.stack([new[:, 1] - new[:, 0], new[:, 2] - new[:, 0]], -1); jo = np.stack([old[:, 1] - old[:, 0], old[:, 2] - old[:, 0]], -1)
L = jn @ np.linalg.pinv(jo)  # maps old UV vectors to new ones (columns = edge vectors)
U, _, Vt = np.linalg.svd(L); Rot = U @ Vt
n = out['normal'][turban] * 2 - 1
n[:, :2] = np.einsum('nij,nj->ni', Rot[t[turban]], n[:, :2])
out['normal'][turban] = (n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-8) + 1) / 2
report['turban_mirrored_triangles'] = int((np.linalg.det(Rot) < 0).sum())

# installed face-part texels (old layout) for the class references
otri, obary = raster(old); ofp = (otri >= 0) & face[np.maximum(otri, 0)]
ob = inst['base'][:, X0:][ofp]; om = inst['mask'][:, X0:][ofp]; omr = inst['mr'][:, X0:][ofp]


def classes(rgb):
    r, g, b = rgb[:, 0] * 255, rgb[:, 1] * 255, rgb[:, 2] * 255
    lum = R.luminance(rgb); chroma = rgb.max(1) - rgb.min(1)
    skin = ((r - b) > 30) & (r > 60) & (chroma > .12)
    white = ~skin & (lum > .45) & (chroma < .14)
    return skin, white


base = meshy('base_color')[fpart]
sk, wh = classes(base); osk, owh = classes(ob)
# Meshy's skin wedge in the white head band: those texels take the nearest white band texel of the same chart area
from scipy.spatial import cKDTree  # noqa: E402
rc = np.argwhere(fpart); fix = bandreg & ~wh; src_ = np.where(bandreg & wh)[0]
base[fix] = base[src_[cKDTree(rc[src_]).query(rc[fix])[1]]]; wh[fix] = True; sk[fix] = False
report['band_fixed_texels'] = int(fix.sum())
lum = lambda a: a @ np.array([.2126, .7152, .0722]); q = np.linspace(0, 1, 101)
# white (beard, brows, cloth): per-channel quantiles of the installed white texels
for c_ in range(3):
    base[wh, c_] = np.interp(base[wh, c_], np.quantile(base[wh, c_], q), np.quantile(ob[owh, c_], q))
# skin: luminance only (the tier ramp colours skin by luminance), half quantile match, half mean and Meshy's own
# spread, so the face is as dark as installed without its dark veins; chroma kept
ln, lo_ = lum(base[sk]), lum(ob[osk])
target = .5 * np.interp(ln, np.quantile(ln, q), np.quantile(lo_, q)) + .5 * (lo_.mean() + ln - ln.mean())
base[sk] = np.clip(base[sk] * (target / np.maximum(ln, 1e-4))[:, None], 0, 1)
for name, m, om_ in (('skin', sk, osk), ('white', wh, owh)):
    report[f'{name}_texels'] = int(m.sum())
    report[f'{name}_lum_mean_std_new_installed'] = [round(float(lum(base[m]).mean()), 3), round(float(lum(base[m]).std()), 3),
                                                   round(float(lum(ob[om_]).mean()), 3), round(float(lum(ob[om_]).std()), 3)]
out['base'][fpart] = base
mask = np.zeros((len(base), 4)); mrv = np.zeros((len(base), 3))
for m, om_ in ((sk, osk), (wh, owh), (~sk & ~wh, ~osk & ~owh)):
    mask[m] = np.median(om[om_], 0); mrv[m] = np.median(omr[om_], 0)
mrv[:, 2] = 0
out['mask'][fpart] = mask; out['mr'][fpart] = mrv
report['class_mask'] = {k: np.round(np.median(om[o], 0), 3).tolist() for k, o in (('skin', osk), ('white', owh))}

nm = meshy('normal'); score = measure(np.uint8(nm * 255 + .5)); assert abs(score) > .15, score
if score < 0:
    nm[..., 1] = 1 - nm[..., 1]
out['normal'][fpart] = nm[fpart]; report['normal_correlation'] = round(float(score), 3)

# soft mask edges inside the face part only (classes meet there); then pad everything into empty space
for c in range(4):
    sm = ndimage.gaussian_filter(np.where(fpart, out['mask'][..., c], 0), .6) / np.maximum(ndimage.gaussian_filter(fpart.astype(float), .6), 1e-3)
    out['mask'][..., c] = np.where(fpart, sm, out['mask'][..., c])
save(pad(out['base'], cov), T / 'mep_head_basecolor.png'); save(pad(out['normal'], cov), T / 'mep_head_normal.png')
save(pad(out['mr'], cov), T / 'mep_head_metal_rough.png'); save(pad(out['mask'], cov), T / 'mep_head_region_mask.png', 'RGBA')
ov = out['base'] * .4
ov[fpart] = np.where(sk[:, None], [.95, .55, .1], np.where(wh[:, None], [1, 1, 1], [.1, .9, .1]))
(P / 'review').mkdir(exist_ok=True); save(ov, P / 'review/head_regions.png')
(P / 'work/compose_head.json').write_text(json.dumps(report, indent=1)); print(json.dumps(report))
