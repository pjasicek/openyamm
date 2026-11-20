#!/usr/bin/env python3
"""Neck pass paint: the welded throat tube (neck_weld.py) has its own UV strip in the free right-hand column of the body
atlas. That strip is filled by patch quilting from the body's own paint (no new art): red hide patches from the hide region
of the region mask, gunmetal patches from the steel region, each patch chosen among random candidates by the least
difference on its overlap with what is already laid, feathered. Where the skin round the hole is steel (the collar at the
nape and the sides) the strip takes the steel fill, where it is hide (the chest under the throat) the red fill, blended
smoothly round the neck. Both ends are then tone-matched (low frequencies only) to the paint they meet: the body skin at the
hole's rim and the head shell at the cut, so the seams carry no colour step and no smear.
The same patch choices fill the normal and ORM maps. Writes into the *_graded.png base (grade_regions.py then makes the final),
ldemon_normal_1k.png and ldemon_metal_rough_1k.png, always from the untouched copies in work/neck_in/.
Usage (project folder): neck_paint.py <weld dump npz> [seed]"""
import sys, json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import cKDTree
NPZ = sys.argv[1]; rng = np.random.default_rng(int(sys.argv[2]) if len(sys.argv) > 2 else 7)
S = 2048; C0, C1, R0, R1 = 1922, 2046, 28, 712          # target rectangle (2K pixels), strip plus gutter
P, O = 40, 12; K = 120
IN = 'work/neck_in/'
load = lambda f: np.asarray(Image.open(IN + f).convert('RGB'), np.float64) / 255
base = load('ldemon_basecolor_graded.png'); headb = load('ldemon_head_basecolor_graded.png')
nrm = np.asarray(Image.open(IN + 'ldemon_normal_1k.png').convert('RGB').resize((S, S), Image.BILINEAR), np.float64) / 255
orm = np.asarray(Image.open(IN + 'ldemon_metal_rough_1k.png').convert('RGB').resize((S, S), Image.BILINEAR), np.float64) / 255
mask = np.asarray(Image.open(IN + 'ldemon_region_mask.png').convert('RGB').resize((S, S), Image.BILINEAR), np.float64) / 255
d = np.load(NPZ); V, F, pa, hd, uvb, uvh, nk = d['V'], d['F'], d['part'], d['head'], d['uvb'], d['uvh'], d['neck']
body_f = (hd == 0) & (nk == 0); tube_f = nk == 1
occ = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(occ)
for f in np.nonzero(body_f)[0]: dr.polygon([(u * S, (1 - v) * S) for u, v in uvb[f]], fill=255)
occ = np.asarray(occ) > 0
hb, sb, db = (ndimage.uniform_filter(mask[..., i], 21) for i in range(3))
src = {'hide': ndimage.binary_erosion(occ & (hb > 0.3) & (sb < 0.12), iterations=3),
       'steel': ndimage.binary_erosion(occ & (sb > 0.55) & (hb < 0.1) & (db < 0.1), iterations=3)}
# hide only from the chest and belly front (the throat continues them), steel from anywhere on the body
fc_ = V[F].mean(1)
chest = Image.new('L', (S, S), 0); drc = ImageDraw.Draw(chest)
for f in np.nonzero(body_f & (pa[F[:, 0]] == 0) & (fc_[:, 1] < -0.25) & (fc_[:, 2] > -0.45) & (fc_[:, 2] < 0.4) & (np.abs(fc_[:, 0]) < 0.35))[0]:
    drc.polygon([(u * S, (1 - v) * S) for u, v in uvb[f]], fill=255)
src["hide"] &= np.asarray(chest) > 0
for k in src: src[k][:, C0 - 8:] = False
def corners(m):
    """top-left corners of P x P windows fully inside m"""
    Sa = np.pad(m.astype(np.int32).cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    full = Sa[P:, P:] - Sa[:-P, P:] - Sa[P:, :-P] + Sa[:-P, :-P] == P * P
    return np.argwhere(full)
cand = {k: corners(m) for k, m in src.items()}
# rank the windows at their centre: crisp (Meshy's stretched charts and the gutter fill are smooth), round detail (not
# streaks), and for hide the chest's own dark red rather than the orange speckle bands; keep the best KEEP share
KEEP = 0.35
lum = base @ np.array([0.3, 0.59, 0.11]); det = ndimage.uniform_filter(np.abs(ndimage.laplace(ndimage.gaussian_filter(lum, 0.7))), 25)
gl = ndimage.gaussian_filter(lum, 1.0); Ix, Iy = ndimage.sobel(gl, 1), ndimage.sobel(gl, 0)
Jxx, Jyy, Jxy = (ndimage.uniform_filter(a, 31) for a in (Ix * Ix, Iy * Iy, Ix * Iy))
aniso = np.sqrt((Jxx - Jyy) ** 2 + 4 * Jxy ** 2) / np.maximum(Jxx + Jyy, 1e-9)
lowc = ndimage.uniform_filter(base, (41, 41, 1))
rank = lambda x: np.argsort(np.argsort(x))
for k in cand:
    c = cand[k] + P // 2; score = rank(-det[c[:, 0], c[:, 1]]) + rank(aniso[c[:, 0], c[:, 1]])
    if k == 'hide':
        col = lowc[c[:, 0], c[:, 1]]; score = score + rank(np.linalg.norm(col - np.median(col, 0), axis=1))
    cand[k] = cand[k][score <= np.percentile(score, KEEP * 100)]
print('PAINT source windows', {k: len(v) for k, v in cand.items()})
H, Wd = R1 - R0, C1 - C0
def window(kind, y, x):
    """a P x P source window; hide windows turn a quarter (the chest's scale rows run round the body, the strip's x runs up the
    throat), their tangent-space normals turned with them"""
    w = stack[y:y + P, x:x + P].copy()
    if kind == 'hide':
        w = np.rot90(w, 1).copy(); nx, ny = w[..., 3] * 2 - 1, w[..., 4] * 2 - 1
        w[..., 3], w[..., 4] = (-ny + 1) / 2, (nx + 1) / 2
    return w
stack = np.dstack([base, nrm, orm])
EXT = 90
def quilt(kind, Wq=None):
    Wq = Wq or Wd
    out = np.zeros((H, Wq, 9)); wsum = np.zeros((H, Wq))
    ramp = np.minimum(np.arange(P) + 1, O) / O; ramp = np.minimum(ramp, ramp[::-1]); A2 = np.minimum.outer(ramp, ramp)
    for r in range(0, H, P - O):
        for c in range(0, Wq, P - O):
            h, w = min(P, H - r), min(P, Wq - c)
            cs = cand[kind][rng.integers(0, len(cand[kind]), K)]
            have = wsum[r:r + h, c:c + w] > 0
            best, bi = 1e18, 0
            if have.any():
                cur = out[r:r + h, c:c + w, :3] / np.maximum(wsum[r:r + h, c:c + w, None], 1e-9)
                for i, (y, x) in enumerate(cs):
                    e = (((window(kind, y, x)[:h, :w, :3] - cur) ** 2).sum(2) * have).sum()
                    if e < best: best, bi = e, i
            y, x = cs[bi]; a = np.where(have, A2[:h, :w], 1.0)
            out[r:r + h, c:c + w] += window(kind, y, x)[:h, :w] * a[..., None]; wsum[r:r + h, c:c + w] += a
    return out / np.maximum(wsum[..., None], 1e-9)
hide_ext = quilt('hide', Wd + EXT); fills = {'hide': hide_ext[:, :Wd].copy(), 'steel': quilt('steel')}
# per strip row: is the skin at the hole's rim steel or hide there? (tube faces at the body end -> nearest old skin face)
tc = V[F].mean(1); bt = cKDTree(tc[body_f & (pa[F[:, 0]] == 0)]); bidx = np.nonzero(body_f & (pa[F[:, 0]] == 0))[0]
ht = cKDTree(tc[hd == 1]); hidx = np.nonzero(hd == 1)[0]
blur = ndimage.uniform_filter(base, (15, 15, 1)); hblur = ndimage.uniform_filter(headb, (15, 15, 1))
def texel(img, uv): return img[np.clip(((1 - uv[:, 1]) * img.shape[0]).astype(int), 0, img.shape[0] - 1), np.clip((uv[:, 0] * img.shape[1]).astype(int), 0, img.shape[1] - 1)]
tf = np.nonzero(tube_f)[0]; tuv = uvb[tf] * S
acc = {k: [[] for _ in range(H)] for k in ('b', 'h', 's', 'e')}
rowof = np.clip((S - tuv[:, :, 1].mean(1) - R0).astype(int), 0, H - 1)
for k, f in enumerate(tf): acc['e'][rowof[k]].append(tuv[k, :, 0].max() - C0)
def rowfield(lst, dim):
    a = np.full((H, dim), np.nan)
    for i, l in enumerate(lst):
        if l: a[i] = np.mean(l, 0)
    ok = ~np.isnan(a[:, 0]); idx = np.arange(H)
    for c in range(dim): a[:, c] = np.interp(idx, idx[ok], a[ok, c])
    return ndimage.gaussian_filter1d(a, 12, axis=0, mode='nearest')
Ex = rowfield([[max(l)] if l else [] for l in acc['e']], 1)[:, 0]
for k, f in enumerate(tf):
    xs = tuv[k, :, 0]; row = rowof[k]
    if xs.min() < 1932 + 6:                                  # at the body end: the old skin next to it
        _, j = bt.query(tc[f], k=3); fj = bidx[j]
        acc['b'][row].append(texel(blur, uvb[fj].mean(1)).mean(0))
        g = texel(mask, uvb[fj].mean(1)); acc['s'][row].append(float(g[:, 2].mean() - g[:, 0].mean()))
    if xs.max() - C0 > Ex[row] - 6:                          # at the head end: the head shell next to it
        _, j = ht.query(tc[f], k=3); fj = hidx[j]
        acc['h'][row].append(texel(hblur, uvh[fj].mean(1)).mean(0))
B_ = rowfield(acc['b'], 3); Hh = rowfield(acc['h'], 3)
St = rowfield([[np.mean(l)] if l else [] for l in acc['s']], 1)[:, 0]
# steel share by the angle round the neck (row -> tube faces' angle), not by the rim colour (shards alternate there):
# the throat (within RED_DEG of straight down) red, the sides and the nape gunmetal like MM9's collar
RED_DEG, BLEND_DEG = 60.0, 25.0
angrow = [[] for _ in range(H)]
for k, f in enumerate(tf): angrow[rowof[k]].append(np.degrees(np.arctan2(tc[f, 2] - 0.61, tc[f, 0])))
def angd(a): return np.abs(((np.array(a) + 90 + 180) % 360) - 180)        # distance from straight down
Ad = rowfield([[angd(np.mean(l))] if l else [] for l in angrow], 1)[:, 0]
st = np.clip((Ad - RED_DEG) / BLEND_DEG, 0, 1); st = st * st * (3 - 2 * st)
fill = fills['hide'] * (1 - st[:, None, None]) + fills['steel'] * st[:, None, None]
# tone match at both ends: low frequencies of the fill moved to the neighbour's mean over ~20 px
low = ndimage.gaussian_filter(fill[..., :3], (10, 10, 0))
xx = np.arange(Wd)[None, :] + C0 - 1932
wb = np.clip(1 - xx / 22.0, 0, 1); wb = wb * wb * (3 - 2 * wb)
we = np.clip(1 - (Ex[:, None] - xx) / 22.0, 0, 1); we = we * we * (3 - 2 * we)
corr = (B_[:, None, :] - low) * wb[..., None] + (Hh[:, None, :] - low) * we[..., None] * (1 - wb[..., None])
fill[..., :3] = np.clip(fill[..., :3] + corr, 0, 1)
# head rim (the neck_rim.py approach, without the smear): head-shell texels of the throat (outer surface, facing down or out,
# within RIM_FAR of the tube, where the tube is red) take the same quilted paint, continued past the tube's head end by
# their distance from it, so the paint runs across the material seam; faded out from RIM_NEAR to RIM_FAR
RIM_NEAR, RIM_FAR = 0.04, 0.12
hcorr = (Hh - ndimage.gaussian_filter(hide_ext[..., :3], (10, 10, 0))[np.arange(H), np.clip(Ex.astype(int), 0, Wd + EXT - 1)])
vt = hide_ext[..., :3] + hcorr[:, None, :]
Ht = headb.shape[0]; hout = headb.copy(); hw = np.zeros(headb.shape[:2])
tube_tri = V[F[tf]]; ttree = cKDTree(tube_tri.mean(1))
cand_f = np.nonzero((hd == 1) & (pa[F[:, 0]] == 10))[0]
cand_f = cand_f[ttree.query(tc[cand_f])[0] < RIM_FAR + 0.03]
nrm_f = np.cross(V[F[cand_f, 1]] - V[F[cand_f, 0]], V[F[cand_f, 2]] - V[F[cand_f, 0]]); nrm_f /= np.linalg.norm(nrm_f, axis=1, keepdims=True) + 1e-12
rad = tc[cand_f] - np.c_[np.zeros(len(cand_f)), tc[cand_f, 1], np.full(len(cand_f), 0.58)]
outer = ((nrm_f * rad).sum(1) > 0) & (nrm_f[:, 2] < 0.4)
painted = 0
for f in cand_f[outer]:
    U = uvh[f] * Ht; U[:, 1] = Ht - U[:, 1]; X3 = V[F[f]]
    x0, x1 = int(np.floor(U[:, 0].min())), int(np.ceil(U[:, 0].max())); y0, y1 = int(np.floor(U[:, 1].min())), int(np.ceil(U[:, 1].max()))
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    T = np.array([[U[1, 0] - U[0, 0], U[2, 0] - U[0, 0]], [U[1, 1] - U[0, 1], U[2, 1] - U[0, 1]]])
    if abs(np.linalg.det(T)) < 1e-9: continue
    ab = np.linalg.solve(T, np.vstack([gx.ravel() - U[0, 0], gy.ravel() - U[0, 1]]))
    inside = (ab[0] >= -0.02) & (ab[1] >= -0.02) & (ab.sum(0) <= 1.02)
    if not inside.any(): continue
    a_, b_ = ab[0][inside], ab[1][inside]; px = gx.ravel()[inside].astype(int); py = gy.ravel()[inside].astype(int)
    ok = (px >= 0) & (px < Ht) & (py >= 0) & (py < Ht); a_, b_, px, py = a_[ok], b_[ok], px[ok], py[ok]
    P3 = X3[0] + np.outer(a_, X3[1] - X3[0]) + np.outer(b_, X3[2] - X3[0])
    dist, j = ttree.query(P3); tfj = tf[j]
    tuvj = uvb[tfj].mean(1) * S; row = np.clip((S - tuvj[:, 1] - R0).astype(int), 0, H - 1)
    xv = np.clip(Ex[row] + dist * 414.0, 0, Wd + EXT - 1)
    w = np.clip((RIM_FAR - dist) / (RIM_FAR - RIM_NEAR), 0, 1); w = w * w * (3 - 2 * w) * (1 - st[row])
    col = vt[row, xv.astype(int)]
    keep = w > hw[py, px]
    hw[py[keep], px[keep]] = w[keep]; hout[py[keep], px[keep]] = headb[py[keep], px[keep]] * (1 - w[keep, None]) + col[keep] * w[keep, None]
    painted += int(keep.sum())
print('PAINT head rim texels', painted, 'faces', int(outer.sum()))
Image.fromarray((np.clip(hout, 0, 1) * 255 + 0.5).astype(np.uint8)).save('textures/ldemon_head_basecolor_graded.png')
print('PAINT rows', H, 'steel share mean %.2f' % st.mean(), 'body-end mean', B_.mean(0).round(3), 'head-end mean', Hh.mean(0).round(3))
out = base.copy(); out[R0:R1, C0:C1] = fill[..., :3]
Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save('textures/ldemon_basecolor_graded.png')
for name, sl in (('ldemon_normal_1k.png', slice(3, 6)), ('ldemon_metal_rough_1k.png', slice(6, 9))):
    full = np.asarray(Image.open(IN + name).convert('RGB'), np.float64) / 255
    big = (nrm if 'normal' in name else orm).copy(); big[R0:R1, C0:C1] = fill[..., sl]
    small = np.asarray(Image.fromarray((big * 255 + 0.5).astype(np.uint8)).resize((1024, 1024), Image.BOX), np.float64) / 255
    full[R0 // 2:R1 // 2, C0 // 2:C1 // 2] = small[R0 // 2:R1 // 2, C0 // 2:C1 // 2]
    Image.fromarray((full * 255 + 0.5).astype(np.uint8)).save('textures/' + name)
Image.fromarray((fill[..., :3] * 255 + 0.5).astype(np.uint8)).save('work/neck/strip_paint.png')
json.dump({'steel_rows': st.round(3).tolist()}, open('work/neck/strip_paint.json', 'w'))
print('PAINT written')
