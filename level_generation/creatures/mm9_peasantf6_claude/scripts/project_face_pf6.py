#!/usr/bin/env python3
"""PeasantF6 copy of PeasantF5's project_face_pf5.py (uv.npz, asm_f6.npz, window |x| < WINX, default 7 cm: the hair at the temples is repainted too); originally a PeasantF5 copy of mm9_peasantf1_claude/scripts/project_face_pf1.py (camera centre z 0.64, window from the chin to the top of the coif
opening so the hair inside the coif is repainted too). Project a repainted flat front face render back onto the head set (face fix 2026-11-02, after mm9_peasantm1_claude/scripts/project_face.py;
orchestrator review: swollen pout, chin smudge, staring eyes, tier A not elderly). view_uvtex.py rendered the unlit front orthographic
view of work/uv.npz (Blender frame, camera from -y, centre x CX, z CZ, ORTHO wide, R px); Codex repainted the face (references_face/).
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
CX, CZ, ORTHO = 0.0, 0.64, 0.26; Z0 = -0.9297
D = np.load('work/uv.npz'); co, tri, uv, mat = D['co'], D['tri'], D['uv'], D['mat']
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
visible = cov & (-y > Zb[iy, ix] - float(__import__('os').environ.get('ZTOL', '0.004'))) & (px >= 0) & (px < R) & (py >= 0) & (py < R)
def ramp(v, a, b): return np.clip((v - a) / (b - a), 0, 1)
WX = float(__import__('os').environ.get('WINX', '0.062')); WZ = float(__import__('os').environ.get('WINZ', '1.700'))
# PeasantF6: wide soft edges (a 7 mm ramp left a lighter plate on the neck's sides and a line across the forehead)
win = ramp(zs, 1.478, 1.512) * (1 - ramp(zs, WZ - 0.02, WZ)) * (1 - ramp(np.abs(x), WX - 0.022, WX))
# the hair shell and the braid keep their own paint (Codex's hair at the temples came out paler than the shell's)
_hair = np.isin(D['comp'][tri[np.maximum(fid, 0), 0]], [[str(n) for n in D['names']].index(k) for k in ('hair', 'braid', 'ears')]) & (fid >= 0)
win = win * ~_hair
# the nose keeps the earlier paint: the repaint's nostrils and highlights fall on the front of our nose tip (a dark pig-nose patch)
nose = np.zeros_like(zs) if not __import__('os').environ.get('KEEP_NOSE') else ramp(zs, 1.548, 1.554) * (1 - ramp(zs, 1.596, 1.604)) * (1 - ramp(np.abs(x), 0.020, 0.026)) * (1 - ramp(y, -0.112, -0.106))
w = win * ramp(facing, 0.05, 0.25) * visible * (1 - nose)
w = ndimage.gaussian_filter(w, 1.0) * cov
fx, fy = np.clip(px - 0.5, 0, R - 1.001), np.clip(py - 0.5, 0, R - 1.001)
x0, y0 = fx.astype(int), fy.astype(int); ax, ay = (fx - x0)[..., None], (fy - y0)[..., None]
samp = img[y0, x0] * (1 - ax) * (1 - ay) + img[y0, x0 + 1] * ax * (1 - ay) + img[y0 + 1, x0] * (1 - ax) * ay + img[y0 + 1, x0 + 1] * ax * ay
out = base * (1 - w[..., None]) + samp * w[..., None]
# PeasantF5: texels inside the window the projection only partly reached (eye sockets, the upper eyeball under the lid, the nose's underside,
# the mouth's inner lips: they face up or down) take the colour of the nearest well-projected texels in 3D, so no old paint (the procedural lid
# shadow, Meshy's dark nostrils) survives; on the eyeballs fully (their lid-covered parts), elsewhere by how little the projection reached. Then every gutter is padded (an 8 px pad left light cracks at chart seams).
from scipy.spatial import cKDTree
H_ = np.load('work/headmap.npz'); eye_ = np.zeros(cov.shape, bool)
A_ = np.load('work/asm_f6.npz'); ac_, at_, acp_ = A_['co'], A_['tri'], A_['comp']; hk_ = [str(v) for v in A_['names']].index('head')
par_ = np.arange(len(ac_))
def _f(q):
    while par_[q] != q: par_[q] = par_[par_[q]]; q = par_[q]
    return q
for a_, b_, c_ in at_[acp_[at_[:, 0]] == hk_]:
    r_ = _f(a_); par_[_f(b_)] = r_; par_[_f(c_)] = r_
hv_ = np.where(acp_ == hk_)[0]; rt_ = np.array([_f(v) for v in hv_]); big_ = np.bincount(rt_).argmax()
ev_ = np.zeros(len(ac_), bool); ev_[hv_[rt_ != big_]] = True
eyef_ = ev_[D['orig'][tri[:, 0]]]; F_ = H_['face']; eye_ = H_['cov'] & eyef_[np.maximum(F_, 0)]
good = cov & (w > 0.85)
need = cov & (win > 0.5) & (w < 0.85) & ((nor[..., 1] < -0.15) | eye_)      # PeasantF6: front-facing only (the neck sides took a light plate)
kd_ = cKDTree(pos[good]); dd_, nn_ = kd_.query(pos[need], k=6); wt_ = 1 / np.maximum(dd_, 2e-4)
gcol = out[good]; fillc = (gcol[nn_] * wt_[..., None]).sum(1) / wt_.sum(1)[:, None]
blend = np.where(eye_[need], 1.0, 1 - w[need] / 0.85)[:, None] * (dd_[:, 0] < 0.012)[:, None]
out[need] = out[need] * (1 - blend) + fillc * blend
print('FILLED', int(need.sum()), 'texels (eyeballs', int(eye_.sum()), ')')
# lift where the geometry turns away from a light above the face (the viewer's and the game's key light): Meshy's nose underside and the lid
# crease under each brow stayed dark even with clean paint (a dark nostril triangle, a band over the eyes)
nz_ = nor[..., 2]; zz_ = z
under = cov & (np.abs(x) < 0.022) & (zz_ > 0.616) & (zz_ < 0.632) & (y < -0.105) & (nz_ < -0.2)
crs = cov & (np.abs(np.abs(x) - 0.0266) < 0.02) & (zz_ > 0.666) & (zz_ < 0.682) & (y < -0.085) & ~eye_
# nose fix 2026-11-02: the nose underside is no longer lifted (the +30 % drew a pale ring round a blotchy brown fill of nearest texels: the
# user's "something wrong on her nose"); it is repainted below as plain skin with two nostrils
lift = 1 + float(__import__('os').environ.get('CREASE_LIFT', '0.0')) * ndimage.gaussian_filter(crs.astype(float), 2.0)      # PeasantF6: off (it drew a light box round each brow)
out = np.clip(out * lift[..., None], 0, 255); print('LIFT nose underside', int(under.sum()), 'crease', int(crs.sum()))
# nose underside (nose fix 2026-11-02, as mm9_peasantf1_claude/scripts/project_face_pf1.py): a facet facing forward and down that the
# engine shades dark under light from above. Plain skin albedo (the nose front's, a little warmer) with two soft dark nostrils at the
# geometry's nostril recesses (x +-6 mm, 7 mm behind the tip), a skin columella between them.
def ramp_(v, a, b): return np.clip((v - a) / (b - a), 0, 1)
und = cov * ramp_(-nor[..., 2], 0.22, 0.42) * (1 - ramp_(np.abs(x), 0.0115, 0.0155)) * ramp_(zs, 1.548, 1.552) * (1 - ramp_(zs, 1.586, 1.591)) \
    * ramp_(-y, 0.112, 0.116)
front_n = cov & (np.abs(x) < 0.012) & (zs > 1.577) & (zs < 1.607) & (nor[..., 1] < -0.75)
skin_n = np.median(out[front_n], 0) * np.array([1.08, 1.0, 0.96])      # a touch lighter than F1's: F5's underside is larger and shades darker
dn = ((np.abs(x) - 0.0060) / 0.0017) ** 2 + ((y + 0.1300) / 0.0025) ** 2
nk = np.clip((1.0 - dn) / 0.8, 0, 1); nk = nk * nk * (3 - 2 * nk) * ramp_(-nor[..., 2], 0.55, 0.75)      # only where it faces down (not on the ala's side: a dot from 3/4)
# the columella between the nostrils faces straight down and sits in the deepest shadow: its skin a little lighter (bounce light), eased out
cb = np.exp(-((x / 0.0050) ** 2 + ((y + 0.131) / 0.007) ** 2))
# r19 (coordinator: "nostrils read as a dark brown blotch"): smaller, and a cool shadow, the skin darkened and a little desaturated, not brown
_ns = skin_n * float(__import__('os').environ.get('NOSTRIL', '0.70')); _ns = _ns * 0.75 + _ns.mean() * 0.25      # PeasantF6 (coordinator: nostrils slightly dark): softer, 0.70
ucol = np.clip(skin_n * (1 + 0.16 * cb[..., None]), 0, 255) * (1 - nk[..., None]) + _ns * nk[..., None]
und = ndimage.gaussian_filter(und, 1.0)
out = out * (1 - und[..., None]) + ucol * und[..., None]
print('NOSE underside texels', int((und > 0.5).sum()), 'skin', np.round(skin_n).tolist())
# midline fins (faces in the x = 0 plane, left by the sliver snap; tweak_pf.py makes most degenerate): texels take the nearest ordinary
# face texels' colour in 3D, so no edge-on texel shows as a pale line down the face
_c = co[tri]; _ar = np.linalg.norm(np.cross(_c[:, 1] - _c[:, 0], _c[:, 2] - _c[:, 0]), axis=1)
fin = (np.abs(_c[:, :, 0]) < 1e-6).all(1) & (_ar > 1e-10) & (mat == 1)
ft = (fid >= 0) & fin[np.maximum(fid, 0)]
ok = cov & ~ft & (np.abs(x) < 0.02) & (np.abs(x) > 0.0004)
if ft.any() and ok.any():
    _dd, _ii = cKDTree(pos[ok]).query(pos[ft], k=6); out[ft] = out[ok][_ii].mean(1)
print('FIN texels recoloured', int(ft.sum()))
_, (jy, jx) = ndimage.distance_transform_edt(~cov, return_indices=True); out[~cov] = out[jy[~cov], jx[~cov]]
Image.fromarray(np.uint8(np.clip(out + 0.5, 0, 255))).save(dst)
print('PROJECT_FACE', t, 'texels', int((w > 0.5).sum()), 'visible', int(visible.sum()))
if '--normal' in sys.argv:
    i = sys.argv.index('--normal'); nsrc, ndst = sys.argv[i + 1:i + 3]
    nm = np.asarray(Image.open(nsrc).convert('RGB'), float); M = nm.shape[0]
    ear = np.zeros_like(cov)          # PeasantF5: no pressed-in ear plates (F1 flattened its ear zone here)
    # fully flat on the nose and the mouth (Meshy's relief there is of its own paint: ringed nostrils, the open mouth)
    nm_box = cov & (np.abs(x) < 0.032) & (zs > 1.505) & (zs < 1.625)
    wn = np.clip(w * 0.85, 0, 1)      # PeasantF6: the window only (its soft edges); the hard nose/mouth box drew a light box round the brows
    w1 = np.asarray(Image.fromarray(np.uint8(wn * 255)).resize((M, M), Image.BILINEAR), float)[..., None] / 255
    nm = nm * (1 - w1) + np.array([128, 128, 255.0]) * w1
    Image.fromarray(np.uint8(np.clip(nm, 0, 255))).save(ndst); print('NORMAL flattened', ndst)
