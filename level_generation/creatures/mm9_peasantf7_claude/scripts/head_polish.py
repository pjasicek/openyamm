#!/usr/bin/env python3
"""Head paint polish per tier (after project_face_pf6.py), by 3D position from work/headmap.npz:
  rim   - the hair shell's rim strip (shell edge to 2 mm inside the skull: faces with a vertex behind the skull surface) was painted as a dark
          line along the hairline and the bob's edge; its texels take the nearest shell texels' colour in 3D;
  neck  - the neck's sides below the jaw carried Meshy's grey shadow paint (a darker patch in profile): the neck (head shell below the jaw,
          outside the face window) is pulled to the front-of-neck skin colour at low frequency, keeping its fine detail.
Args: <in png> <out png>   (project folder)"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ni
from scipy.spatial import cKDTree
SRC, DST = sys.argv[1:3]
H = np.load('work/headmap.npz'); pos, cov, face, nrm = H['pos'], H['cov'], H['face'], H['nrm']
D = np.load('work/uv.npz'); co, tri, comp, orig = D['co'], D['tri'], D['comp'], D['orig']; names = [str(x) for x in D['names']]
A = np.load('work/asm_f6.npz'); aco, atri, acomp = A['co'], A['tri'], A['comp']
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32); out = im.copy()
X, Y, Z = pos[..., 0], pos[..., 1], pos[..., 2]
fc = np.full(cov.shape, -1); fc[cov] = comp[tri[face[cov], 0]]
# ---- rim: hair asm vertices behind the skull surface
hk, sk = names.index('hair'), names.index('head')
sv = np.where(acomp == sk)[0]; st = atri[acomp[atri[:, 0]] == sk]
fn = np.cross(aco[st[:, 1]] - aco[st[:, 0]], aco[st[:, 2]] - aco[st[:, 0]]); N = np.zeros_like(aco)
for c in range(3): np.add.at(N, st[:, c], fn)
N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
hv = np.where(acomp == hk)[0]
# make_f6_geom.py appends the hair shell first, then one inner rim vertex per boundary vertex (2 mm inside the skull): the last NB hair
# vertices, NB = the shell patch's boundary vertex count (shell faces = all hair faces with no inner vertex)
inner = np.zeros(len(aco), bool)
_ht = atri[acomp[atri[:, 0]] == hk]; _vt = np.zeros(len(aco), int); np.add.at(_vt, _ht.ravel(), 1)
_e = np.sort(np.vstack([_ht[:, [0, 1]], _ht[:, [1, 2]], _ht[:, [2, 0]]]), axis=1); _u, _c = np.unique(_e, axis=0, return_counts=True)
NB = int(np.unique(_u[_c == 1]).size) if False else None
# rim strip faces are the last 2*68 hair faces; their vertices that are not shared with any shell-only face are the inner ones
shell_faces = _ht[:-136]; sv_ = set(np.unique(shell_faces).tolist())
for v in np.unique(_ht[-136:]):
    if v not in sv_: inner[v] = True
rimf = (comp[tri[:, 0]] == hk) & inner[orig[tri]].any(1)
rim = cov & rimf[np.maximum(face, 0)] & (face >= 0) & (Z > 0.75) & (np.abs(X) < 0.07)      # the dark arc over the forehead only (the side rims show the curtain's own strands)
good = cov & (fc == hk) & ~rim
dd, nn = cKDTree(pos[good]).query(pos[rim], k=24); w_ = 1 / np.maximum(dd, 1e-3)
out[rim] = (out[good][nn] * w_[..., None]).sum(1) / w_.sum(1)[:, None]      # a soft, slightly shaded hair tone, no stretched strands
# ---- crown front edge (party view arc): the skull texels just in front of the shell's forehead edge carry Meshy's dark band (the old
# bob's front edge shadow, painted on the skull). Skull texels over the forehead within EW of the shell boundary take the shell's own hair
# colour (3D nearest shell texels), keeping their strand detail, fading out over EW toward the fringe
shellm = cov & (fc == hk) & ~rim
bvx = aco[np.where(inner)[0]]
fr = cov & (fc == sk) & (Z > 0.72) & (Y < -0.02) & (np.abs(X) < 0.07)
fy, fx = np.nonzero(fr); db_ = cKDTree(bvx).query(pos[fy, fx])[0]
EW = 0.014; sel = db_ < EW; ty, tx = fy[sel], fx[sel]
sy, sx = np.nonzero(shellm); _, nn_ = cKDTree(pos[sy, sx]).query(pos[ty, tx], k=12)
scol = out[sy, sx][nn_].mean(1)
w_ = np.clip(1 - db_[sel] / EW, 0, 1)[:, None] ** 0.6
L_ = out[ty, tx].mean(1, keepdims=True); Lb = ni.gaussian_filter(out.mean(2), 3)[ty, tx][:, None] + 1
out[ty, tx] = out[ty, tx] * (1 - w_) + np.clip(scol * np.clip(L_ / Lb, 0.85, 1.15), 0, 255) * w_
print('crown edge texels', int(sel.sum()))
# ---- ears: plain skin (now fully clear of the close cap, their paint showed hair strands on the back and the cup): the cheek's skin colour
# with the paint's fine luminance detail (clipped), a little rosier in the cup, a touch darker toward the root
ek = names.index('ears'); ear = cov & (fc == ek)
cheek = cov & (fc == sk) & (np.abs(np.abs(X) - 0.05) < 0.012) & (Z > 0.60) & (Z < 0.635) & (Y < -0.07)
sref = np.median(out[cheek], 0) * 0.4 + np.array([223, 146, 96.]) * 0.6      # toward the neck skin (the cheek reference is shaded)
lum = out.mean(2); lb = ni.gaussian_filter(lum, 4) + 1; det = np.clip(lum / lb, 0.9, 1.08)
root = np.clip((np.abs(X) - 0.066) / 0.05, 0, 1)
ecol = sref[None, None, :] * det[..., None] * (0.86 + 0.14 * root)[..., None] * np.array([1.0, 0.96, 0.95])
out[ear] = ecol[ear]
# ---- mouth and chin (coordinator review r13): pale specks in the lip slit and a small dark V under the lower lip (F5's chin facet,
# geometry kept). Slit texels (lip box, faces turned away from the front) take a soft lip-shadow tone; pale outliers in the lower face
# (3D-neighbour median + 14) take the neighbour median; the chin facet's down-facing texels are lifted a little
nr = H['nrm']
lipbox = cov & (fc == sk) & (np.abs(X) < 0.024) & (Z > 0.596) & (Z < 0.614) & (Y < -0.10)
front_lip = lipbox & (nr[..., 1] < -0.75)
lipc = np.median(out[front_lip], 0)
# slit: the faces inside the lip line (turned away from the front, also behind the lips) take the colour of the nearest front-facing
# lip texels in 3D (no fixed tone: a flat tone drew stitches along the line); gold specks (the old slit fill) the same
slit = cov & (fc == sk) & (np.abs(X) < 0.022) & (Z > 0.598) & (Z < 0.612) & (Y < -0.09) & (nr[..., 1] > -0.55)
hsv_ = np.asarray(Image.fromarray(np.clip(out, 0, 255).astype('u1')).convert('HSV'), np.float32) / 255
gold = cov & (fc == sk) & (np.abs(X) < 0.022) & (Z > 0.596) & (Z < 0.614) & (Y < -0.09) & (hsv_[..., 0] * 360 > 34) & (hsv_[..., 0] * 360 < 62) & (hsv_[..., 1] > 0.35)
odd = slit | gold
src = front_lip & ~odd
sy, sx = np.nonzero(src); oy, ox = np.nonzero(odd)
if len(sy) and len(oy):
    _, nn_ = cKDTree(pos[sy, sx]).query(pos[oy, ox], k=8); out[oy, ox] = np.median(out[sy, sx][nn_], axis=1)
fz = cov & (fc == sk) & (np.abs(X) < 0.06) & (Z > 0.56) & (Z < 0.70) & (Y < -0.06)
fy, fx = np.nonzero(fz); _, nn = cKDTree(pos[fy, fx]).query(pos[fy, fx], k=16)
Lf = out[fy, fx].mean(1); med = np.median(Lf[nn], axis=1); pl = Lf > med + 14
out[fy[pl], fx[pl]] = np.median(out[fy, fx][nn[pl]], axis=1)
# the V under the lower lip: a small notch in F5's geometry at the midline whose down-facing facets shade dark; a soft 3D-weighted lift
cwf = np.exp(-((X / 0.006) ** 2 + ((Z - 0.590) / 0.006) ** 2)) * np.clip((-nr[..., 2] - 0.2) / 0.3, 0, 1) * (cov & (fc == sk) & (Y < -0.09))
chin = cwf > 0.2
out = out * (1 + 0.16 * cwf)[..., None]
print('mouth slit texels', int(slit.sum()), 'odd lip', int(odd.sum()), 'pale specks', int(pl.sum()), 'chin facet', int(chin.sum()), 'lip', lipc.round(0).tolist())
# ---- neck: low-frequency colour pulled to the front-of-neck skin
neck = cov & (fc == sk) & (Z > 0.50) & ((Z < 0.585) | ((Z < 0.63) & (Y > -0.05)))      # the neck and the skin behind the jaw
front = neck & (np.abs(X) < 0.03) & (Y < -0.04)
ref = np.median(out[front], 0)
idx = ni.distance_transform_edt(~neck, return_distances=False, return_indices=True)
filled = out[idx[0], idx[1]]
low = np.stack([ni.gaussian_filter(filled[..., c], 12) for c in range(3)], -1)
gain = np.clip(ref / np.maximum(low, 1), 0.6, 1.6)
k = np.clip(ni.gaussian_filter(neck.astype(np.float32), 3), 0, 1)[..., None] * (1 - np.clip(ni.gaussian_filter(front.astype(np.float32), 6), 0, 1))[..., None]
out = out * (1 - k) + np.clip(out * gain, 0, 255) * k
idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True); out = out[idx[0], idx[1]]
Image.fromarray(np.clip(out + .5, 0, 255).astype('u1')).save(DST)
print('POLISH', SRC, 'ear texels', int(ear.sum()), 'skin', sref.round(0).tolist(), 'rim texels', int(rim.sum()), 'neck texels', int(neck.sum()), 'neck ref', ref.round(0).tolist())
