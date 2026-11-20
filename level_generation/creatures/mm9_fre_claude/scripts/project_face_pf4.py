#!/usr/bin/env python3
"""PF3 copy of project_face_pf1.py (2026-11-02): the veil and braids neither occlude the front z-buffer nor take the repaint (they keep
their own paint); HAIRWIN=1 (tier B) widens the window over the head shell's hair (|x| < 9.8 cm, up to 1.82 m), whose dark repaint
replaces tier A's blonde.
Project a repainted flat front face render back onto the head set (face fix 2026-11-02, after mm9_peasantm1_claude/scripts/project_face.py;
orchestrator review: swollen pout, chin smudge, staring eyes, tier A not elderly). view_uvtex.py rendered the unlit front orthographic
view of work/uv_tex2.npz (Blender frame, camera from -y, centre x CX, z CZ, ORTHO wide, R px); Codex repainted the face (references_face/).
Every head texel whose rest point is visible from the front (z-buffer over all triangles, 2 mm) takes the repaint's colour at its
projected pixel, weighted by the face window (|x| < 7 cm, 1.495-1.690 m over the soles, 6 mm ramps) times a facing ramp.
Also, for the shared head set: the normal map flattened by the same window x 0.85 (Meshy's relief of the old lips and eyes) and fully
inside the ear zone beside the cheeks (a corrupt normal there drew a grey speck at the hood edge).
Args: <tier> <repaint png> <in base png> <out base png> [--normal <in normal> <out normal>]   (project folder)"""
import sys, os
import numpy as np
from PIL import Image
from scipy import ndimage
t, paint, src, dst = sys.argv[1:5]
CX, CZ, ORTHO = 0.0, 0.6703, 0.26; Z0 = -0.9297
D = np.load('work/uv_tex2.npz'); co, tri, uv, mat = D['co'], D['tri'], D['uv'], D['mat']
img = np.asarray(Image.open(paint).convert('RGB'), float); R = img.shape[0]
assert img.shape[0] == img.shape[1] == 1254, img.shape
# front z-buffer: depth = -y (the camera looks along +y)
Zb = np.full((R, R), -1e9)
px_v = ((co[:, 0] - CX) / ORTHO + 0.5) * R; py_v = (0.5 - (co[:, 2] - CZ) / ORTHO) * R; dz_v = -co[:, 1]
_nm = [str(n) for n in D['names']]; _zk = ~np.isin(D['comp'][tri[:, 0]], [_nm.index(n) for n in ('veil', 'braids') if n in _nm])
for f in tri[_zk]:
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
win = ramp(zs, 1.495, 1.501) * (1 - ramp(zs, 1.684, 1.690)) * (1 - ramp(np.abs(x), 0.064, 0.070))
_part = np.where(fid >= 0, D['comp'][tri[np.maximum(fid, 0), 0]], -1)
_okp = np.isin(_part, [_nm.index(n) for n in ('head', 'scarf') if n in _nm])
if __import__('os').environ.get('HAIRWIN'):
    win = np.maximum(win, ramp(zs, 1.60, 1.62) * (1 - ramp(zs, 1.80, 1.82)) * (1 - ramp(np.abs(x), 0.092, 0.098)) * (_part == _nm.index('head')))
win = win * _okp
# the nose (nose fix 2026-11-02): no longer excluded. The earlier pass kept Meshy's first paint on the front of the nose tip (the repaint's
# nostrils fell there): that left a paint boundary round the alae, a pale stripe up the bridge and the old nostrils above our nose's own
# shaded underside (the user's "double textures"). The repaint is now fitted to the geometry's nose first (scripts/warp_nose_pf1.py), so
# the whole nose takes it; the zone below only drives the normal-map flattening.
nose = ramp(zs, 1.568, 1.574) * (1 - ramp(zs, 1.640, 1.648)) * (1 - ramp(np.abs(x), 0.026, 0.032))
neckx = (1 - ramp(zs, 1.535, 1.547)) * (1 - ramp(-y, 0.064, 0.076))     # the neck behind the jaw line keeps head_fix_pf1.py's even skin
w = win * ramp(facing, -0.02, 0.12) * visible * (1 - neckx)
# texels on triangle edges can miss the z-buffer test (rasterisation): they kept the old paint as thin lines. Grown by 2 px over the
# window's covered texels (a hidden texel next to a visible one takes the repaint too; nothing shows it).
w = np.maximum(w, ndimage.grey_dilation(w, size=5) * win * (1 - neckx) * cov)
# the mouth box (lips, the cavity tweak_pf1.py closed flush, the philtrum): every texel takes the repaint, visible or not, so no sliver of
# the old lip paint or the dark slit line shows between the lips
mbox = ramp(zs, 1.532, 1.536) * (1 - ramp(zs, 1.584, 1.588)) * (1 - ramp(np.abs(x), 0.030, 0.034)) * (y < -0.05) * cov * _okp
w = np.maximum(w, mbox)
w = ndimage.gaussian_filter(w * cov, 1.0) / np.maximum(ndimage.gaussian_filter(cov.astype(float), 1.0), 1e-6) * cov * _okp      # normalised: the island edges are not half-weighted (they kept the old paint as lines)
fx, fy = np.clip(px - 0.5, 0, R - 1.001), np.clip(py - 0.5, 0, R - 1.001)
x0, y0 = fx.astype(int), fy.astype(int); ax, ay = (fx - x0)[..., None], (fy - y0)[..., None]
samp = img[y0, x0] * (1 - ax) * (1 - ay) + img[y0, x0 + 1] * ax * (1 - ay) + img[y0 + 1, x0] * (1 - ax) * ay + img[y0 + 1, x0 + 1] * ax * ay
out = base * (1 - w[..., None]) + samp * w[..., None]
# the nose's underside (nose fix 2026-11-02): a facet facing forward and down that the engine already shades dark under light from above;
# the repaint's baked nostril shadows on it doubled that into a brown smudge. It takes plain skin albedo (the nose front's, a little warmer)
# with two soft dark nostrils where the geometry's nostril recesses are (x +-6.5 mm, 9 mm behind the tip), a skin columella between them.
nzn = np.nan_to_num(nor[..., 2])
und = cov * ramp(-nzn, 0.22, 0.42) * (1 - ramp(np.abs(x), 0.012, 0.016)) * ramp(zs, 1.568, 1.572) * (1 - ramp(zs, 1.602, 1.607)) \
    * ramp(-y, 0.110, 0.114)
front_n = cov & (np.abs(x) < 0.012) & (zs > 1.595) & (zs < 1.625) & (np.nan_to_num(nor[..., 1]) < -0.75)
skin_n = np.median(out[front_n], 0) * np.array([1.10, 1.04, 1.00])      # PF4 review: the underside faces down and shades dark; painted a step lighter
dn = ((np.abs(x) - 0.0065) / 0.0034) ** 2 + ((y + 0.1295) / 0.0046) ** 2
nk = np.clip((1.0 - dn) / 0.55, 0, 1); nk = nk * nk * (3 - 2 * nk)
ucol = skin_n * (1 - nk[..., None]) + np.array([160.0, 104, 92]) * nk[..., None] * 0.5 + skin_n * 0.5 * nk[..., None]      # PF3: softer nostrils (read as dark holes from the front)
und = ndimage.gaussian_filter(und, 1.0)
# NOSEKEEP (PF4 v2 faces, 2026-11-02): the v2 repaint was painted on a render of our own nose, so its nose already sits on the geometry;
# the plain underside plate drew a paler outlined patch from the front (a ghost nose). It keeps the repaint's nose: no plate, and pass 3
# only lifts texels darker than 0.80 of the nose skin (the dark nostril blob)
NOSEKEEP = bool(os.environ.get('NOSEKEEP'))
if NOSEKEEP: und = und * 0
out = out * (1 - und[..., None]) + ucol * und[..., None]
# pass 3 (user: "nose tip and nostrils read as a dark brown dirty patch"): every nose texel (tip, alae, underside) darker than 0.86 of the
# nose's own skin takes that skin with its fine detail; nostrils only where the surface faces straight down (the geometry's real nostril
# floor), soft and small
nose3 = cov * (1 - ramp(np.abs(x), 0.017, 0.022)) * ramp(zs, 1.560, 1.566) * (1 - ramp(zs, 1.612, 1.620)) * ramp(-y, 0.100, 0.106)
_lm3 = out @ np.array([0.2126, 0.7152, 0.0722]); _sk3 = float(np.median(_lm3[(nose3 > 0.9) & (np.nan_to_num(nor[..., 1]) < -0.6)]))
_dk3 = np.clip(((0.80 if NOSEKEEP else 0.95) * _sk3 - _lm3) / (0.15 * _sk3), 0, 1) * nose3
_det3 = (_lm3 - ndimage.gaussian_filter(_lm3, 1.5))[..., None]
out = out * (1 - _dk3[..., None]) + np.clip(skin_n / ([1.10, 1.04, 1.00] if NOSEKEEP else 1) * (0.85 if NOSEKEEP else 1) + _det3 * 0.5, 0, 255) * _dk3[..., None]
_down = ramp(-nzn, 0.70, 0.85) * nose3 * (1 - ramp(np.abs(x), 0.011, 0.014)) * ramp(np.abs(x), 0.002, 0.004)
_down = ndimage.gaussian_filter(_down, 1.0)
out = out * (1 - 0.18 * _down[..., None]) + np.array([150.0, 92, 80]) * 0.18 * _down[..., None]      # PF4: small soft nostril shadows
print('NOSE pass3 cleaned', int((_dk3 > 0.3).sum()), 'nostril texels', int((_down > 0.3).sum()))
print('NOSE underside texels', int((und > 0.5).sum()), 'skin', np.round(skin_n).tolist())
# midline fins (nose fix 2026-11-02): faces lying in the x = 0 plane (the sliver snap made them, in coincident mirrored pairs) are seen
# edge-on from the front, so their texels missed the repaint's colour and drew as a thin pale line down the nose in perspective close-ups.
# Their texels take the colour of the nearest ordinary face texels in 3D.
_c = co[tri]; _ar = np.linalg.norm(np.cross(_c[:, 1] - _c[:, 0], _c[:, 2] - _c[:, 0]), axis=1)
fin = (np.abs(_c[:, :, 0]) < 1e-6).all(1) & (_ar > 1e-10) & (mat == 1)
ft = (fid >= 0) & fin[np.maximum(fid, 0)]
ok = cov & ~ft & (np.abs(x) < 0.02) & (np.abs(x) > 0.0004)
if ft.any() and ok.any():
    from scipy.spatial import cKDTree
    kd = cKDTree(pos[ok]); dd, ii = kd.query(pos[ft], k=6)
    out[ft] = out[ok][ii].mean(1)
print('FIN texels recoloured', int(ft.sum()), 'faces', int(fin.sum()))
# under each eye (r23, coordinator review: "pale jagged crescent under each lower lid"). tweak_pf1.py moves the eyeball's lower part back
# behind a smooth lid curve; the socket pocket's walls seen there kept Meshy's dark old paint (the projection does not reach them). Head
# texels round each eye that the projection reached less than half take the colour of the nearest well-projected texels in 3D, a step
# darker (a lid shadow); then head texels 2.5 to 10 mm below the ball centre lighter than 90 % of the cheek's luminance are scaled to it
# (the repaint's pale lower-lid rim, on a margin that faces up into the light).
from scipy.spatial import cKDTree as _KD
_S = np.load('work/asm_frozen.npz'); _ku_ = np.round(_S['co'], 5); _uu_, _iv_ = np.unique(_ku_, axis=0, return_inverse=True); _iv_ = _iv_.ravel()
_tu_ = _iv_[_S['tri']]; _pr_ = np.arange(len(_uu_))
def _fr(a):
    while _pr_[a] != a: _pr_[a] = _pr_[_pr_[a]]; a = _pr_[a]
    return a
for _a, _b, _c in _tu_: _r = _fr(_a); _pr_[_fr(_b)] = _r; _pr_[_fr(_c)] = _r
_rt_ = np.array([_fr(i) for i in range(len(_uu_))]); _small = (np.bincount(_rt_)[_rt_] < 400)[_iv_]
_isball = (fid >= 0) & _small[D['orig'][tri[np.maximum(fid, 0), 0]]]
for _sg in (1, -1):
    _dx = x - _sg * 0.0287; _dz = zs - 1.6136
    _zone = cov & (np.abs(_dx) < 0.016) & (np.abs(_dz) < 0.014) & (y < -0.07)
    _need = _zone & (w < 0.5); _good = _zone & (w > 0.9) & (y < -0.095)
    if _need.any() and _good.any():
        _dd, _ii = _KD(pos[_good]).query(pos[_need], k=6); out[_need] = out[_good][_ii].mean(1) * 0.78
    _ck = cov & (y < -0.09) & (np.abs(_dx) < 0.012) & (_dz < -0.011) & (_dz > -0.016)
    _band = cov & (w > 0.5) & (y < -0.09) & (np.abs(_dx) < 0.013) & (_dz < -0.0025) & (_dz > -0.010)
    if _band.any() and _ck.any():
        _lm = out @ np.array([0.2126, 0.7152, 0.0722]); _cl = 0.9 * float(np.median(_lm[_ck]))      # the lid margin faces up into the light
        _kb = ndimage.gaussian_filter(_band.astype(float), 1.5) * cov
        _sc = np.clip(_cl / np.maximum(ndimage.gaussian_filter(_lm, 2.0), 1), 0.75, 1.0)
        out = out * (1 - _kb[..., None] * (1 - _sc[..., None]))
    # the lid margin: Meshy's lower lid ends in a scalloped ledge just in front of the ball's lower part (the "pale jagged crescent": lit
    # from above and painted with the repaint's pale rim). Its texels (head shell, not the ball, within 1.8 of the ball's ellipsoid below
    # its centre, facing up: it is lit full by a light from above) take at most 92 % of the cheek's luminance (build_glb_pf.py relaxes its normals), so the ledge reads as the lid's
    # shadowed edge rather than a light band
    _ebv = (_dx / 0.0114) ** 2 + ((y + 0.0990) / 0.0089) ** 2 + (_dz / 0.0121) ** 2
    _tt = 1 - (_dx / 0.0114) ** 2 - (_dz / 0.0121) ** 2
    _up = cov & ~_isball & (_tt > -0.5) & (_dz < -0.001) & (y < -0.093) & (np.nan_to_num(nor[..., 2]) > 0.25)
    _lab, _nl = ndimage.label(_up)                    # keep the ledge (its UV islands touch the ball's band), drop stray cheek facets
    if _nl:
        _sz = ndimage.sum(np.ones_like(_dz), _lab, index=np.arange(1, _nl + 1)); _mz = ndimage.mean(_ebv, _lab, index=np.arange(1, _nl + 1))
        print('EYE ledge islands', [(int(a), round(float(b), 2)) for a, b in zip(_sz, _mz)])
        _keep = np.zeros(_nl + 1, bool); _keep[1:] = _mz < float(__import__('os').environ.get('LEDGE_EBV', '2.2')); _up = _keep[_lab]
    if _up.any() and _ck.any():
        _lm = out @ np.array([0.2126, 0.7152, 0.0722]); _tl = 0.92 * float(np.median(_lm[_ck]))
        _ku = np.clip(ndimage.gaussian_filter(ndimage.binary_dilation(_up, iterations=1).astype(float), 0.6) * 2.0, 0, 1) * (cov & ~_isball)
        _su = np.clip(_tl / np.maximum(_lm, 1), 0.5, 1.0)
        out = out * (1 - _ku[..., None] * (1 - _su[..., None]))
    print('EYE lower lid', _sg, 'pocket texels filled', int(_need.sum()), 'band', int(_band.sum()), 'margin', int(_up.sum()) if _ck.any() else 0)
# the clamped ear plates (nose fix 2026-11-02, the ear-area sweep): the head faces pressed flat beside each cheek at the hood's edge
# (tweak_pf1.py clamps them to |x| 6.3 cm) kept Meshy's ear paint: a paler patch outlined in the hood's orange, seen from the side and 3/4.
# The outline texels (the hood's orange or white) take the nearest other plate texel's colour (UV space); the plate's skin-like
# texels (head part, |x| > 5.9 cm, below the hairline) are toned toward the cheek in front of it by per-channel gains held to +-10 % and shaded by EAR_SHADE.
EAR_SHADE = 0.90      # the plate sits in the hood edge's shadow; lit flat-on it otherwise read as a pale patch
_hk = int(list(map(str, D['names'])).index('head')); part = np.where(fid >= 0, D['comp'][tri[np.maximum(fid, 0), 0]], -1)
_hsv = np.asarray(Image.fromarray(np.uint8(np.clip(out, 0, 255))).convert('HSV'), float) / 255
plate = cov & (part == _hk) & (zs > 1.535) & (zs < 1.612) & (y > -0.070) & (y < 0.015)
kpl = np.clip((np.abs(x) - 0.056) / 0.003, 0, 1) * plate
orange = plate & (np.abs(x) > 0.054) & (((_hsv[..., 0] * 360 > 27) & (_hsv[..., 1] > 0.45)) | ((_hsv[..., 1] < 0.16) & (_hsv[..., 2] > 0.62)))   # hood orange / hood white
orange = ndimage.binary_dilation(orange, iterations=1) & plate
src = plate & ~orange & (np.abs(x) > 0.054)
if orange.any() and src.any():
    _, (jy, jx) = ndimage.distance_transform_edt(~src, return_indices=True); out[orange] = out[jy[orange], jx[orange]]
skin_pl = plate & (kpl > 0.99) & ~orange & (_hsv[..., 0] * 360 < 27) & (_hsv[..., 1] > 0.25) & (_hsv[..., 1] < 0.6) & (_hsv[..., 2] > 0.55)
chk = cov & (part == _hk) & (np.abs(x) > 0.040) & (np.abs(x) < 0.050) & (zs > 1.545) & (zs < 1.605) & (y < -0.03)
if skin_pl.sum() > 50 and chk.any():
    g = np.clip(np.median(out[chk], 0) / np.maximum(np.median(out[skin_pl], 0), 1), 0.9, 1.1)
    kk = (kpl * ~orange)[..., None]
    out = out * (1 - kk) + np.clip(out * g * EAR_SHADE, 0, 255) * kk
    print('EAR plate gains', np.round(g, 3).tolist(), 'skin texels', int(skin_pl.sum()), 'orange', int(orange.sum()))
# PF3: the ear plates still read as a paler, pinker rectangle beside each cheek under the veil's edge: the plate's skin texels take the
# cheek's colour in front of it outright (its fine detail kept), a step darker (the veil edge's shadow)
if skin_pl.sum() > 50 and chk.any():
    _lmo = out @ np.array([0.2126, 0.7152, 0.0722]); _det = (_lmo - ndimage.gaussian_filter(_lmo, 3.0))[..., None]
    _pl = (plate & (np.abs(x) > 0.054) & ~orange).astype(float)
    _kp = np.clip(ndimage.gaussian_filter(_pl, 1.5) * 1.3, 0, 1)[..., None] * plate[..., None]
    # the colour of the nearest skin texels in 3D outside the plate (cheek in front, jaw below), so there is no flat block
    from scipy.spatial import cKDTree as _K2
    _ring = cov & (part == _hk) & ~plate & (np.abs(x) > 0.035) & (zs > 1.50) & (zs < 1.63) & (y < 0.02)
    _rh = np.asarray(Image.fromarray(np.uint8(np.clip(out, 0, 255))).convert('HSV'), float) / 255
    _ring &= (_rh[..., 0] * 360 < 35) & (_rh[..., 1] > 0.15) & (_rh[..., 2] > 0.35)
    _tgt = plate & (_kp[..., 0] > 0.01)
    if _ring.any() and _tgt.any():
        _bl = ndimage.gaussian_filter(out, (4, 4, 0))
        _d, _i = _K2(pos[_ring]).query(pos[_tgt], k=12); _w = 1 / np.maximum(_d, 1e-3)
        _cc = (_bl[_ring][_i] * _w[..., None]).sum(1) / _w.sum(1)[:, None]
        _new = out.copy(); _new[_tgt] = _cc * 0.97 + _det[_tgt] * 0.6
        out = out * (1 - _kp) + np.clip(_new, 0, 255) * _kp
    print('EAR plate set to its surrounding skin', int(_pl.sum()))
near = ndimage.binary_dilation(w > 0.02, iterations=8) & ~cov      # gutters only (cov = every head-set face)
_, (jy, jx) = ndimage.distance_transform_edt(~cov, return_indices=True); out[near] = out[jy[near], jx[near]]
Image.fromarray(np.uint8(np.clip(out + 0.5, 0, 255))).save(dst)
print('PROJECT_FACE', t, 'texels', int((w > 0.5).sum()), 'visible', int(visible.sum()))
if '--normal' in sys.argv:
    i = sys.argv.index('--normal'); nsrc, ndst = sys.argv[i + 1:i + 3]
    nm = np.asarray(Image.open(nsrc).convert('RGB'), float); M = nm.shape[0]
    ear = cov & (np.abs(x) > 0.052) & (zs > 1.53) & (zs < 1.625) & (y > -0.075) & (y < 0.02)
    # fully flat on the nose and the mouth box (Meshy's relief there is of its own paint: the old nostrils on the tip, the open mouth)
    wn = np.clip(np.maximum(w * 0.85, np.maximum(nose, mbox) * win) + ndimage.gaussian_filter(ear.astype(float), 1.5), 0, 1)
    # pass 2: the chin and jaw below the lips fully flat too (Meshy's relief of its open mouth and chin met the flattened mouth box in a
    # hard diagonal edge on the chin under a light from above)
    jaw_ = (cov & (zs < 1.548) & (y < -0.02)).astype(float)
    wn = np.clip(np.maximum(wn, ndimage.gaussian_filter(jaw_, 3.0) * 1.5), 0, 1)
    w1 = np.asarray(Image.fromarray(np.uint8(wn * 255)).resize((M, M), Image.BILINEAR), float)[..., None] / 255
    nm = nm * (1 - w1) + np.array([128, 128, 255.0]) * w1
    Image.fromarray(np.uint8(np.clip(nm, 0, 255))).save(ndst); print('NORMAL flattened', ndst)
