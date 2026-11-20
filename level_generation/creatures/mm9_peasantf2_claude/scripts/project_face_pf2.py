#!/usr/bin/env python3
"""PF2 (F2 framing and landmarks; copy of mm9_peasantf7_claude/scripts/project_face_pf7.py, reduced from mm9_peasantf1_claude/scripts/project_face_pf1.py, F7 framing; no normal flattening, no ear/eye-ledge steps). Project a repainted flat front face render back onto the head set (face fix 2026-11-02, after mm9_peasantm1_claude/scripts/project_face.py;
orchestrator review: swollen pout, chin smudge, staring eyes, tier A not elderly). view_uvtex.py rendered the unlit front orthographic
view of work/uv_tex2.npz (Blender frame, camera from -y, centre x CX, z CZ, ORTHO wide, R px); Codex repainted the face (references_face/).
Every head texel whose rest point is visible from the front (z-buffer over all triangles, 2 mm) takes the repaint's colour at its
projected pixel, weighted by the face window (|x| < 7 cm, 1.495-1.690 m over the soles, 6 mm ramps) times a facing ramp.
Also, for the shared head set: the normal map flattened by the same window x 0.85 (Meshy's relief of the old lips and eyes) and fully
inside the ear zone beside the cheeks (a corrupt normal there drew a grey speck at the hood edge).
Args: <tier> <repaint png> <in base png> <out base png> [--normal <in normal> <out normal>]   (project folder)"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
t, paint, src, dst = sys.argv[1:5]
import os
CX, CZ, ORTHO = 0.0, 0.668, 0.24; Z0 = -0.9297
D = np.load('work/uv_tex2.npz'); co, tri, uv, mat = D['co'], D['tri'], D['uv'], D['mat']
img = np.asarray(Image.open(paint).convert('RGB'), float); R = img.shape[0]
assert img.shape[0] == img.shape[1] == 1254, img.shape
# front z-buffer: depth = -y (the camera looks along +y)
Zb = np.full((R, R), -1e9)
px_v = ((co[:, 0] - CX) / ORTHO + 0.5) * R; py_v = (0.5 - (co[:, 2] - CZ) / ORTHO) * R; dz_v = -co[:, 1]
for f in tri:
    x, y, z = px_v[f], py_v[f], dz_v[f]
    x0, x1 = int(max(np.floor(x.min()), 0)), int(min(np.ceil(x.max()), R - 1)); y0, y1 = int(max(np.floor(y.min()), 0)), int(min(np.ceil(y.max()), R - 1))
    if x1 < x0 or y1 < y0: continue
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
    if abs(d) < 1e-12: continue
    a = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / d; b = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / d
    c = 1 - a - b; m = (a >= 0) & (b >= 0) & (c >= 0); zz = a * z[0] + b * z[1] + c * z[2]
    sub = Zb[y0:y1 + 1, x0:x1 + 1]; upd = m & (zz > sub); sub[upd] = zz[upd]
# head texels: position and normal
fn_ = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]])
key = np.round(co, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
Nv = np.zeros((inv.max() + 1, 3)); [np.add.at(Nv, inv[tri[:, k]], fn_) for k in range(3)]; Nv = Nv[inv]; Nv /= np.maximum(np.linalg.norm(Nv, axis=1, keepdims=True), 1e-12)
base = np.asarray(Image.open(src).convert('RGB'), float); N = base.shape[0]
pos = np.full((N, N, 3), np.nan); nor = np.zeros((N, N, 3)); fid = np.full((N, N), -1)
for f in np.where(mat == 1)[0]:
    q = uv[tri[f]] * [N, -N] + [0, N]
    x0, y0 = np.maximum(np.floor(q.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int), N - 1)
    if x1 < x0 or y1 < y0: continue
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    T_ = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
    if abs(np.linalg.det(T_)) < 1e-12: continue
    l = np.linalg.solve(T_, (np.c_[gx.ravel(), gy.ravel()] - q[2]).T).T; L3 = np.c_[l, 1 - l.sum(1)]; ins = (L3 >= -1e-3).all(1)
    if ins.any():
        yy, xx = (gy.ravel()[ins] - 0.5).astype(int), (gx.ravel()[ins] - 0.5).astype(int)
        pos[yy, xx] = L3[ins] @ co[tri[f]]; nor[yy, xx] = L3[ins] @ Nv[tri[f]]; fid[yy, xx] = f
cov = ~np.isnan(pos[..., 0]); x, y, z = (np.nan_to_num(pos[..., i]) for i in range(3)); zs = z - Z0
nor /= np.maximum(np.linalg.norm(nor, axis=-1, keepdims=True), 1e-9); facing = np.clip(-nor[..., 1], 0, 1)
px = ((x - CX) / ORTHO + 0.5) * R; py = (0.5 - (z - CZ) / ORTHO) * R
ix = np.clip(px.astype(int), 0, R - 1); iy = np.clip(py.astype(int), 0, R - 1)
visible = cov & (-y > Zb[iy, ix] - 0.002) & (px >= 0) & (px < R) & (py >= 0) & (py < R)
def ramp(v, a, b): return np.clip((v - a) / (b - a), 0, 1)
Z_BOX = (1.540, 1.590)
W_LO, W_HI, W_X = 1.507, 1.690, float(os.environ.get('WIN_X', '0.056'))
win = ramp(zs, W_LO, W_LO + 0.006) * (1 - ramp(zs, W_HI - 0.006, W_HI)) * (1 - ramp(np.abs(x), W_X - 0.006, W_X))
neckx = (1 - ramp(zs, 1.512, 1.524)) * (1 - ramp(-y, 0.060, 0.072))
w = win * ramp(facing, -0.02, 0.12) * visible * (1 - neckx)
w = np.maximum(w, ndimage.grey_dilation(w, size=5) * win * (1 - neckx) * cov)
_hk = int(list(map(str, D['names'])).index('head')); part = np.where(fid >= 0, D['comp'][tri[np.maximum(fid, 0), 0]], -1)
mbox = ramp(zs, 1.535, 1.539) * (1 - ramp(zs, 1.570, 1.574)) * (1 - ramp(np.abs(x), 0.028, 0.032)) * (y < -0.05) * cov * (part == _hk)
w = np.maximum(w, mbox)
w = ndimage.gaussian_filter(w * cov, 2.0) / np.maximum(ndimage.gaussian_filter(cov.astype(float), 2.0), 1e-6) * cov
fx, fy = np.clip(px - 0.5, 0, R - 1.001), np.clip(py - 0.5, 0, R - 1.001)
x0, y0 = fx.astype(int), fy.astype(int); ax, ay = (fx - x0)[..., None], (fy - y0)[..., None]
samp = img[y0, x0] * (1 - ax) * (1 - ay) + img[y0, x0 + 1] * ax * (1 - ay) + img[y0 + 1, x0] * (1 - ax) * ay + img[y0 + 1, x0 + 1] * ax * ay
ring = cov & (w > 0.25) & (w < 0.85) & (part == _hk)
g_ = np.clip(np.median(base[ring], 0) / np.maximum(np.median(samp[ring], 0), 1), 0.8, 1.25) if ring.sum() > 50 else np.ones(3)
samp = np.clip(samp * g_, 0, 255); print('EDGE gains', np.round(g_, 3).tolist(), 'ring texels', int(ring.sum()))
out = base * (1 - w[..., None]) + samp * w[..., None]
from scipy.spatial import cKDTree
# the nose underside (faces turned down, seen edge-on from the front: the projection stretches the repaint's nostrils over them): the
# nearest well-projected nose texels' colour, a step darker; the geometry's own notches shade the nostrils
nzn = np.nan_to_num(nor[..., 2])
und = cov & (part == _hk) & (nzn < -0.30) & (np.abs(x) < 0.017) & (zs > 1.561) & (zs < 1.586) & (y < -0.083)
good = cov & (part == _hk) & (w > 0.9) & (nzn > -0.1) & (np.abs(x) < 0.02) & (zs > 1.571) & (zs < 1.605) & (y < -0.088)
if und.any() and good.any():
    side_ = cov & (part == _hk) & (w > 0.9) & (np.abs(x) > 0.018) & (np.abs(x) < 0.03) & (zs > Z_BOX[0] + 0.02) & (zs < Z_BOX[1] + 0.01) & (y < -0.07)
    ref_ = np.median(out[side_], 0) if side_.sum() > 20 else np.median(out[good], 0)
    out[und] = ref_ * float(os.environ.get('UNDER_DARK', '1.15'))
print('NOSE underside texels', int(und.sum()))
# nose/philtrum box: texels the projection did not reach (hidden from the front: the closed mouth's inner faces, the underside's back) take
# the colour of the nearest well-projected texels in 3D
box_ = cov & (part == _hk) & (np.abs(x) < 0.022) & (zs > Z_BOX[0]) & (zs < Z_BOX[1]) & (y < -0.075)
need_ = box_ & (w < 0.6) & ~und; good_ = cov & (part == _hk) & (w > 0.9) & (np.abs(x) < 0.03) & (zs > Z_BOX[0] - 0.01) & (zs < Z_BOX[1] + 0.01) & (nzn > -0.2)
if need_.any() and good_.any():
    dd, ii = cKDTree(pos[good_]).query(pos[need_], k=6); out[need_] = out[good_][ii].mean(1)
print('BOX filled', int(need_.sum()))
# off-hue texels in the nose/mouth box (olive specks in the lip corners, an orange tick under the columella): nearest normal-hued box texels
_hs = np.asarray(Image.fromarray(np.uint8(np.clip(out, 0, 255))).convert('HSV'), float) / 255; _h, _s = _hs[..., 0] * 360, _hs[..., 1]
odd_ = box_ & (((_h > 32) & (_h < 300)) | (_s > 0.62)) & (os.environ.get('ODD', '0') == '1')
odd_ = ndimage.binary_dilation(odd_, iterations=1) & box_
okb_ = box_ & ~odd_
if odd_.any() and okb_.any():
    dd, ii = cKDTree(pos[okb_]).query(pos[odd_], k=6); out[odd_] = out[okb_][ii].mean(1)
print('ODD hue texels', int(odd_.sum()))
_c = co[tri]; _ar = np.linalg.norm(np.cross(_c[:, 1] - _c[:, 0], _c[:, 2] - _c[:, 0]), axis=1)
fin = (np.abs(_c[:, :, 0]) < 1e-6).all(1) & (_ar > 1e-10) & (mat == 1)
ft = (fid >= 0) & fin[np.maximum(fid, 0)]
ok = cov & ~ft & (np.abs(x) < 0.02) & (np.abs(x) > 0.0004)
if ft.any() and ok.any():
    kd = cKDTree(pos[ok]); dd, ii = kd.query(pos[ft], k=6); out[ft] = out[ok][ii].mean(1)
print('FIN texels recoloured', int(ft.sum()))
# faces whose UV footprint is under ~2 texels (the closed mouth's slit, collapsed fins) are missed by the rasteriser and showed whatever lay at
# their UV point (olive and orange specks on the lip line): their UV vertices and centroid take the nearest well-projected texel's colour
fh = np.where(mat == 1)[0]; q3 = uv[tri[fh]] * N
ua = np.abs((q3[:, 1, 0] - q3[:, 0, 0]) * (q3[:, 2, 1] - q3[:, 0, 1]) - (q3[:, 2, 0] - q3[:, 0, 0]) * (q3[:, 1, 1] - q3[:, 0, 1])) / 2
tiny = fh[ua < 2.0]; okp = cov & (w > 0.9) & (part == _hk)
if len(tiny) and okp.any():
    kdp = cKDTree(pos[okp]); cols_ = out[okp]; nt = 0
    for f in tiny:
        c3 = co[tri[f]].mean(0); _, j = kdp.query(c3, k=4); col = cols_[j].mean(0)
        for uu in list(uv[tri[f]]) + [uv[tri[f]].mean(0)]:
            px_, py_ = int(uu[0] * N), int((1 - uu[1]) * N)
            for dy_ in (-1, 0, 1):
                for dx_ in (-1, 0, 1):
                    yy_, xx_ = min(max(py_ + dy_, 0), N - 1), min(max(px_ + dx_, 0), N - 1)
                    if fid[yy_, xx_] < 0 or fid[yy_, xx_] == f: out[yy_, xx_] = col; nt += 1
    print('TINY faces', len(tiny), 'texels set', nt)
# per face in the nose/mouth box: the colour at its UV centroid vs the colour expected at its 3D position (nearest well-projected texels); a
# face that differs by more than FACE_TOL has its whole UV triangle (dilated 1 px) refilled (faces whose texels the projection never reached)
from PIL import ImageDraw as _IDraw
fcen = co[tri].mean(1); bx = np.where((mat == 1) & (np.abs(fcen[:, 0]) < 0.03) & (fcen[:, 2] - Z0 > Z_BOX[0] - 0.005) & (fcen[:, 2] - Z0 < Z_BOX[1] + 0.005) & (fcen[:, 1] < -0.06))[0]
kdp2 = cKDTree(pos[okp]); cols2 = out[okp]; FT = float(os.environ.get('FACE_TOL', '45')); nfix = 0
for f in bx:
    _, j = kdp2.query(fcen[f], k=6); exp_ = cols2[j].mean(0)
    uc = uv[tri[f]].mean(0); dev = np.abs(out[min(int((1 - uc[1]) * N), N - 1), min(int(uc[0] * N), N - 1)] - exp_).sum()
    if dev > FT:
        m_ = _IDraw.Image.new('L', (N, N), 0); _IDraw.Draw(m_).polygon([(float(uv[i, 0] * N), float((1 - uv[i, 1]) * N)) for i in tri[f]], fill=255, outline=255)
        mm_ = ndimage.binary_dilation(np.asarray(m_) > 0, iterations=1); out[mm_] = exp_; nfix += 1
print('FACES refilled', nfix, 'of', len(bx))
# face-based nose underside and columella base: whole UV triangles (dilated 1 px) on one nose-skin colour (the texel-wise underside mask left a
# jagged patch, and thin faces at the columella base kept stray texels: a pale speck in close-ups)
fnz = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]]); fnz = fnz[:, 2] / np.maximum(np.linalg.norm(fnz, axis=1), 1e-12)
NB_ = tuple(float(v) for v in os.environ.get('NOSE_BOX', '0.022,1.572,1.592,-0.081').split(','))
undf = bx[(np.abs(fcen[bx, 0]) < NB_[0]) & (fcen[bx, 2] - Z0 > NB_[1]) & (fcen[bx, 2] - Z0 < NB_[2]) & (fcen[bx, 1] < NB_[3]) & (fnz[bx] < -0.25)]
CB_ = tuple(float(v) for v in os.environ.get('COL_BOX', '0.008,1.569,1.580,-0.090').split(','))
colf = bx[(np.abs(fcen[bx, 0]) < CB_[0]) & (fcen[bx, 2] - Z0 > CB_[1]) & (fcen[bx, 2] - Z0 < CB_[2]) & (fcen[bx, 1] < CB_[3])]
side2 = cov & (part == _hk) & (w > 0.9) & (np.abs(x) > 0.018) & (np.abs(x) < 0.03) & (zs > NB_[1]) & (zs < NB_[2] + 0.01) & (y < -0.07)
nsk_ = np.median(out[side2], 0) if side2.sum() > 20 else np.median(out[okp], 0)
mk_ = _IDraw.Image.new('L', (N, N), 0); dr_ = _IDraw.Draw(mk_); mk2_ = _IDraw.Image.new('L', (N, N), 0); dr2_ = _IDraw.Draw(mk2_)
for f in undf: dr_.polygon([(float(uv[i, 0] * N), float((1 - uv[i, 1]) * N)) for i in tri[f]], fill=255, outline=255)
for f in colf: dr2_.polygon([(float(uv[i, 0] * N), float((1 - uv[i, 1]) * N)) for i in tri[f]], fill=255, outline=255)
m1_ = ndimage.binary_dilation(np.asarray(mk_) > 0, iterations=1); m2_ = ndimage.binary_dilation(np.asarray(mk2_) > 0, iterations=1)
fillc = np.zeros_like(out); fillc[m1_] = np.clip(nsk_ * float(os.environ.get('UNDER_LIFT', '1.06')), 0, 255); fillc[m2_ & ~m1_] = nsk_
a_ = np.clip(ndimage.gaussian_filter((m1_ | m2_).astype(float), 1.5) * 1.4, 0, 1) * cov; a_[m1_ | m2_] = np.maximum(a_[m1_ | m2_], 0.85)
src_ = ndimage.distance_transform_edt(~(m1_ | m2_), return_indices=True)[1]; fillc = fillc[src_[0], src_[1]]
out = out * (1 - a_[..., None]) + fillc * a_[..., None]
print('NOSE faces underside', len(undf), 'columella', len(colf), 'skin', np.round(nsk_).tolist())
# the head normal map on those faces only (Meshy's normals there are corrupt: jagged shading edges and a blue-white speck in lit close-ups,
# unchanged by any paint): neutral (128,128,255). The rest of the nose and mouth relief is untouched.
if '--normal' in sys.argv:
    i_ = sys.argv.index('--normal'); nin, nout = sys.argv[i_ + 1:i_ + 3]
    if not __import__('os').path.exists(nout) or True:
        nm_ = np.asarray(Image.open(nin).convert('RGB'), float); M_ = nm_.shape[0]
        mm_ = np.asarray(Image.fromarray(np.uint8((m1_ | m2_) * 255)).resize((M_, M_), Image.NEAREST)) > 0
        mm_ = ndimage.binary_dilation(mm_, iterations=1); nm_[mm_] = (128, 128, 255)
        Image.fromarray(np.uint8(nm_)).save(nout); print('NORMAL patch neutral texels', int(mm_.sum()))
near = ndimage.binary_dilation(w > 0.02, iterations=8) & ~cov
_, (jy, jx) = ndimage.distance_transform_edt(~cov, return_indices=True); out[near] = out[jy[near], jx[near]]
Image.fromarray(np.uint8(np.clip(out + 0.5, 0, 255))).save(dst)
print('PROJECT_FACE', t, 'texels', int((w > 0.5).sum()), 'visible', int(visible.sum()))
