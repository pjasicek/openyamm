#!/usr/bin/env python3
"""PF3 copy of head_fix_pf1.py (2026-11-02): F3 has no standing collar (a low neckline: the neck is skin down into the body's
chest skin), so the collar recolours are off; the ear zone also takes the white veil paint Meshy put on the pressed-in ears to skin.
Head paint fixes per tier (after sym_paint): Meshy painted broad dark crimson lips beyond the lip shells, a dark smudge under the lower
lip on the chin, the reference's orange bodice straps on the collar of the head set, and very white sclera (a staring look).
- texels of the lip shells: halfway to a natural rose, luminance detail kept;
- face-shell texels round the mouth and on the chin that are redder or darker than the skin round them: the surrounding skin (normalised
  convolution of the clean skin texels), the paint's fine luminance kept;
- orange texels on the neck/collar of the head set: the collar cream round them;
- sclera (eyeball shells, pale texels) 15 % darker.
Args: <in png> <out png> [preview png]   (project folder; positions from work/uv.npz, rest pose)"""
import sys, os
FRESH = bool(os.environ.get('FRESH'))      # pass 5: a fresh Meshy head paint fitted to the current (closed-mouth) geometry: mouth, lips, lip line, teeth and sclera left as painted
import numpy as np
from PIL import Image
from scipy import ndimage as ni
SRC, DST = sys.argv[1:3]; PREV = sys.argv[3] if len(sys.argv) > 3 else None
D = np.load('work/uv.npz'); co, tri, uv, mat, comp = D['co'], D['tri'], D['uv'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
Z0 = -0.9297; S = 1024
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32) / 255
hf = np.where(mat == 1)[0]
# connected pieces of the head part (welded by position): face shell, eyes, lips
key = np.round(co, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
par = np.arange(inv.max() + 1)
def f(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for t in tri[hf]:
    a = f(inv[t[0]]); par[f(inv[t[1]])] = a; par[f(inv[t[2]])] = a
root = np.array([f(inv[t[0]]) for t in tri[hf]])
cen = co[tri[hf]].mean(1); kind = np.zeros(len(hf), int)       # 0 shell/hood, 1 lips, 2 eyes
for r in np.unique(root):
    m = root == r; n = m.sum(); c = cen[m].mean(0)
    if n < 400 and abs(c[0]) < 0.03 and 1.52 < c[2] - Z0 < 1.59: kind[m] = 1
    elif n < 400 and 0.015 < abs(c[0]) < 0.05 and 1.58 < c[2] - Z0 < 1.65: kind[m] = 2
print('pieces', {k: int((kind == k).sum()) for k in (0, 1, 2)})
# raster: piece kind, part, 3D position per texel
K = np.full((S, S), -1, int); PART = np.full((S, S), -1, int); POS = np.zeros((S, S, 3))
for j, fi in enumerate(hf):
    q = uv[tri[fi]] * [S, -S] + [0, S]; x0, y0 = np.floor(q.min(0)).astype(int); x1, y1 = np.ceil(q.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1 + 1, S)), np.arange(max(y0, 0), min(y1 + 1, S)))
    pts = np.c_[xs.ravel() + 0.5, ys.ravel() + 0.5]
    T_ = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
    if abs(np.linalg.det(T_)) < 1e-12: continue
    l = np.linalg.solve(T_, (pts - q[2]).T).T; l3 = np.c_[l, 1 - l.sum(1)]; ok = (l3 > -0.01).all(1)
    yy, xx = pts[ok, 1].astype(int), pts[ok, 0].astype(int)
    K[yy, xx] = kind[j]; PART[yy, xx] = comp[tri[fi][0]]; POS[yy, xx] = l3[ok] @ co[tri[fi]]
x, y, z = POS[..., 0], POS[..., 1], POS[..., 2] - Z0
hsv = np.asarray(Image.fromarray((im * 255).astype('u1')).convert('HSV'), np.float32) / 255
hue, sat, val = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
lum = im @ np.array([0.2126, 0.7152, 0.0722])
detail = lum - ni.gaussian_filter(lum, 2.0)
def fill(src_mask, sigma):
    w = ni.gaussian_filter(src_mask.astype(np.float32), sigma)
    c = np.stack([ni.gaussian_filter(im[..., k] * src_mask, sigma) for k in range(3)], -1)
    c = c / np.maximum(w, 1e-4)[..., None]
    fb = np.median(im[src_mask], 0) if src_mask.any() else np.array([0.8, 0.6, 0.5])
    a = np.clip(w / 0.08, 0, 1)[..., None]                     # far from any clean texel (other UV islands): the class median
    return c * a + fb * (1 - a), w
out = im.copy(); head_id = names.index('head')
shell = (K == 0) & (PART == head_id)
# colour classes by nearest reference (sRGB): skin from the forehead, crimson lip paint, orange bodice, cream collar
fore = shell & (np.abs(x) < 0.03) & (z > 1.63) & (z < 1.67) & (y < -0.09)
SKIN = np.median(im[fore], 0); LIP = np.array([0.50, 0.08, 0.09]); ORA = np.array([0.80, 0.32, 0.08]); CRE = np.array([0.84, 0.80, 0.70])
print('skin ref', np.round(SKIN * 255).tolist())
REF = np.stack([SKIN, LIP, ORA, CRE]); dist = ((im[..., None, :] - REF) ** 2).sum(-1); cls = dist.argmin(-1)
# ---- mouth and chin on the face shell: lip-red paint off the lip shells, and the dark smudge under the lower lip
zone = shell & (np.abs(x) < 0.045) & (y < -0.06) & (z > 1.49) & (z < 1.585)
skin_ok = shell & (cls == 0)
sk, wk = fill(skin_ok & (np.abs(x) < 0.07) & (z > 1.46) & (z < 1.64), 6.0)
skl = sk @ np.array([0.2126, 0.7152, 0.0722])
LZ = float(__import__('os').environ.get('LIP_Z', '1.552')); E2_ = shell & (y < -0.05) & ((x / 0.024) ** 2 + ((z - LZ) / np.where(z > LZ, 0.0115, 0.0085)) ** 2 < 1); E = shell & (y < -0.05) & ((x / 0.027) ** 2 + ((z - LZ) / 0.017) ** 2 < 1)      # the sculpted lips
chin = zone & (np.abs(x) < 0.03) & (z < 1.540) & ~E
bad = zone & ~E2_ & ((cls == 1) | (lum < skl * 0.62)) | chin & (lum < skl * 0.80)
bad = ni.binary_dilation(bad, iterations=1) & zone & ~ni.binary_erosion(E2_, iterations=2)
soft_bad = np.clip(ni.gaussian_filter(bad.astype(np.float32), 1.0) * 1.6, 0, 1) * zone
rep = np.clip(sk + detail[..., None] * 0.6, 0, 1)
if not FRESH: out = out * (1 - soft_bad[..., None]) + rep * soft_bad[..., None]
print('mouth/chin texels replaced', int(bad.sum()))
# ---- the lips: recess of every mouth texel behind the front-most surface at its x (2 mm bins): the front is lip, the recess the slit and
# the mouth cavity behind it. Meshy painted crimson lips round a pale open-mouth band; repainted as closed rose lips over a dark line.
BS = 0.0015; xb = np.clip(((x + 0.03) / BS).astype(int), 0, 39); zb = np.clip(((z - LZ + 0.03) / BS).astype(int), 0, 39)
F = np.full((40, 40), np.nan)
for i_, j_, yv in zip(xb[E], zb[E], y[E]):
    if not (F[i_, j_] <= yv): F[i_, j_] = yv
Ff = np.where(np.isnan(F), np.nanmax(F), F)
Fs = ni.gaussian_filter(Ff, 2.0); groove = (Ff - Fs) > 0.0022
recess = y - Ff[xb, zb]
hidden = E & (recess > 0.002)
E2 = E & ((x / 0.024) ** 2 + ((z - LZ) / np.where(z > LZ, 0.0115, 0.0085)) ** 2 < 1)
# the cavity is closed flush by tweak_pf1.py: lips and closed cavity become one rose lip surface, the lip line drawn at the slit's height
lips = E2 & ~hidden
rose = np.array([0.64, 0.31, 0.30]); lm = max(float(np.median(lum[lips])), 1e-3)
sh_ = np.where(hidden, 0.92, np.clip(lum / lm, 0.72, 1.25))
tgt = rose * np.where(hidden, ni.gaussian_filter(sh_, 1.0), sh_)[..., None]
allm = E2 | hidden
kl = np.clip(ni.gaussian_filter(allm.astype(np.float32), 1.2) * 1.2, 0, 1)[..., None] * E[..., None]
if not FRESH: out = out * (1 - kl) + np.clip(tgt, 0, 1) * kl
hc = hidden & (np.abs(x) < 0.006)
zl = float(np.median(z[hc])) if hc.any() else LZ
zline = zl + 4.0 * x ** 2                      # a slight upward curve to the corners (the smile)
line = allm & (np.abs(z - zline) < 0.0010) & (np.abs(x) < 0.022)
kl2 = np.clip(ni.gaussian_filter(line.astype(np.float32), 0.8), 0, 1)[..., None]
if not FRESH: out = out * (1 - kl2) + np.array([0.30, 0.10, 0.10]) * kl2
print('lip texels', int(lips.sum()), 'line texels', int(line.sum()), 'lip line z', round(zl, 4))
# ---- round the pressed-in ears (head and hood faces interleave at the hood's edge; Meshy's paint there is right except for grey specks of
# shadow): grey low-saturation texels below the hairline take the nearest good texel's colour
zone_e = (K == 0) & (np.abs(x) > 0.058) & (np.abs(x) < 0.095) & (z > 1.54) & (z < 1.592) & (y > -0.065) & (y < 0.01)
grey = zone_e & (sat < 0.20) & (val < 0.70) | (zone_e & (PART == head_id) & (sat < 0.20) & (val >= 0.70))      # PF3: white veil paint on the ears
grey = ni.binary_dilation(grey, iterations=1) & zone_e
if grey.any():
    good = (K >= 0) & ~grey; ii = ni.distance_transform_edt(~good, return_distances=False, return_indices=True)
    out[grey] = out[ii[0][grey], ii[1][grey]]
print('ear-zone grey texels', int(grey.sum()))
# ---- the teeth pieces behind the mouth slit: dark mouth interior, so the slit reads as the line between closed lips
teeth = K == 1
if not FRESH: out[teeth] = np.array([0.22, 0.07, 0.07]) * np.clip(lum[teeth] / max(float(lum[teeth].mean()), 1e-3), 0.6, 1.3)[:, None]
# ---- collar: orange straps painted on the neck of the head set
neck = shell & (z < 1.505)
orange = neck & (cls == 2)
orange = np.zeros_like(neck)      # PF3: no orange straps
cream_ok = neck & (cls == 3)
cr, wc = fill(cream_ok, 8.0)
ko = np.clip(ni.gaussian_filter(orange.astype(np.float32), 1.0) * 1.5, 0, 1) * neck
out = out * (1 - ko[..., None]) + np.clip(cr + detail[..., None] * 0.6, 0, 1) * ko[..., None]
print('collar texels recoloured', int(orange.sum()))
# the head set's neck is skin down to the seam: the reference's collar, painted here in jagged cream teeth, belongs to the body's standing
# collar, whose top is then the clean slanted neck cut (assemble_pf1.py)
neckc = neck & ((cls == 3) | orange | (sat < 0.24) | ((y > -0.01) & (hue < 30) & (sat > 0.45))) & (z < 1.50)
neckc = ni.binary_dilation(neckc, iterations=2) & neck
nsk, _ = fill(neck & (cls == 0) & ~neckc, 10.0)
kn = np.clip(ni.gaussian_filter(neckc.astype(np.float32), 1.0) * 1.5, 0, 1)[..., None] * neck[..., None]
out = out * (1 - kn) + np.clip(nsk + detail[..., None] * 0.2, 0, 1) * kn
print('neck cream texels to skin', int(neckc.sum()))
# the collar line: head faces at the shoulder/neck junction outside the bisected neck band carry the head material below the neck cut
# in jagged spikes (seen from 3/4 and behind). Head texels within 5 mm above the cut plane (assemble_pf1.py: front 1.44, back 1.48 m), or
# below 1.50 m outside the neck radius, take the body collar's cream (median of the body paint's collar texels), so the skin/collar line
# is the smooth plane, not the triangle edges.
pnv = np.array([0, -0.04, 0.16]); pnv /= np.linalg.norm(pnv); sp = (y - (-0.10)) * pnv[1] + (z - 1.44) * pnv[2]
rad = np.hypot(x, y + 0.01)
collar = np.zeros_like(shell)      # PF3: no collar (low neckline)
if collar.any():
    bt = np.asarray(Image.open('textures/pf_body_tone.png').convert('RGB'), np.float32) / 255
    bh = np.asarray(Image.fromarray((bt * 255).astype('u1')).convert('HSV'), np.float32) / 255
    cream = np.median(bt[(bh[..., 1] < 0.2) & (bh[..., 2] > 0.75)], 0)
    kc = np.clip(ni.gaussian_filter(collar.astype(np.float32), 1.2) * 1.4, 0, 1)[..., None] * shell[..., None]
    out = out * (1 - kc) + np.clip(cream + detail[..., None] * 0.4, 0, 1) * kc
print('collar-line texels', int(collar.sum()))
# the neck between the jaw and the collar line: one even skin (a translucent ghost of the reference's collar, its V slit and folds, stayed
# under the earlier fills): the jaw's skin colour, a trace of fine detail, eased in below 1.51 m
jawm = shell & (z > 1.505) & (z < 1.53) & (np.abs(x) < 0.05) & (y < -0.04) & (cls == 0)
if jawm.any():
    jaw = np.median(im[jawm], 0)
    import re as _re, os as _os
    _m = _re.search(r'pf_head_([ab])_', SRC); _fp = f'references_face_f3/out_face_{_m.group(1)}_aligned.png' if _m else ''
    if _fp and _os.path.exists(_fp):      # the skin of the repainted chin (projected later), so face and neck are one tone
        jaw = np.asarray(Image.open(_fp).convert('RGB'), np.float32)[985:1010, 580:680].reshape(-1, 3).mean(0) / 255
    under = np.clip((-0.07 - y) / 0.012, 0, 1)                               # 0 on the neck behind the jaw line, 1 on the chin's front
    kn2 = np.maximum(1 - np.clip((z - 1.492) / 0.018, 0, 1), (1 - under) * (1 - np.clip((z - 1.535) / 0.012, 0, 1))) * shell * ~collar * (np.abs(x) < 0.075)
    kn2 = np.clip(ni.gaussian_filter(kn2.astype(np.float32), 1.0), 0, 1)[..., None] * shell[..., None] * (~collar)[..., None]
    # PF3: no collar: the neck runs into the body's chest skin (low neckline), so the fill eases from the chin's tone at the jaw to the
    # body paint's chest skin at the seam (median of the body tone at dress faces just below the front of the neck, 1.38-1.43 m)
    _bt = np.asarray(Image.open('textures/pf_body_tone.png').convert('RGB'), np.float32) / 255; _B = _bt.shape[0]
    _bf = np.where(mat == 0)[0]; _c3 = co[tri[_bf]].mean(1); _zz = _c3[:, 2] - Z0
    _sel = _bf[(np.abs(_c3[:, 0]) < 0.04) & (_zz > 1.38) & (_zz < 1.43) & (_c3[:, 1] < -0.05)]
    _uvc = uv[tri[_sel]].mean(1); _px = np.clip((_uvc[:, 0] * _B).astype(int), 0, _B - 1); _py = np.clip(((1 - _uvc[:, 1]) * _B).astype(int), 0, _B - 1)
    _samp = _bt[_py, _px]; _h = np.asarray(Image.fromarray((_samp[None] * 255).astype('u1')).convert('HSV'), np.float32)[0] / 255
    _skin = _samp[(_h[:, 0] * 360 < 40) & (_h[:, 1] > 0.2) & (_h[:, 1] < 0.6) & (_h[:, 2] > 0.5)]
    chest = np.median(_skin, 0) if len(_skin) > 5 else jaw
    tg = np.clip((1.505 - z) / 0.06, 0, 1)[..., None]; tg = tg * tg * (3 - 2 * tg)
    col = jaw * 0.98 * (1 - tg) + chest * tg
    out = out * (1 - kn2) + np.clip(col + detail[..., None] * 0.35, 0, 1) * kn2
    print('PF3 neck to chest', np.round(chest * 255).tolist(), 'from', len(_skin), 'body texels')
    print('neck skin', np.round(jaw * 255).tolist())
# ---- eyelid rims (TOWNSFOLK_BRIEF "Eyes and brows": no heavy red rims): reddish texels round each eye toward the skin round them
for sg in (1, -1):
    e_ = (K == 2) & (np.sign(x) == sg)
    if not e_.any(): continue
    ec = np.array([np.median(x[e_]), np.median(y[e_]), np.median(z[e_])])
    dd_ = np.sqrt((x - ec[0]) ** 2 + (y - ec[1]) ** 2 + (z - ec[2]) ** 2)
    rim = shell & (dd_ < 0.016) & (((hue < 20) | (hue > 330)) & (sat > 0.30))
    kr = np.clip(ni.gaussian_filter(rim.astype(np.float32), 0.8) * 1.3, 0, 1)[..., None] * 0.7 * shell[..., None]
    out = out * (1 - kr) + np.clip(sk + detail[..., None] * 0.7, 0, 1) * kr
    print('eye rim texels', sg, int(rim.sum()))
# ---- sclera
scl = (K == 2) & (sat < 0.30) & (val > 0.50)
if not FRESH: out[scl] *= 0.85
# the eyeballs' upper third darkened (the lid's shadow): the round painted sclera read as a stare
eyes = K == 2
for sg in (1, -1):
    e_ = eyes & (np.sign(x) == sg)
    if e_.any():
        zc = np.median(z[e_]); zr = np.percentile(z[e_], 95) - zc
        k_ = np.clip((z - zc) / max(zr, 1e-4), 0, 1) * e_
        if not FRESH: out *= (1 - 0.45 * k_)[..., None]
print('sclera texels', int(scl.sum()))
# ---- PF3: the veil's lower tip hangs below the head masters' frame; Meshy painted bodice red and lacing there. Saturated or dark texels on
# the veil and hood take the nearest clean linen texel's colour (UV space), the linen's fine detail kept
if 'veil' in names and not FRESH:
    lin_ = np.isin(PART, [names.index('veil'), names.index('scarf')])
    _o = np.clip(out, 0, 1); _h = np.asarray(Image.fromarray((_o * 255).astype('u1')).convert('HSV'), np.float32) / 255
    dirt = lin_ & ((_h[..., 1] > 0.28) | (_h[..., 2] < 0.45))
    dirt = ni.binary_dilation(dirt, iterations=2) & lin_
    clean = lin_ & ~dirt
    if dirt.any() and clean.any():
        _, (jy, jx) = ni.distance_transform_edt(~clean, return_indices=True)
        out[dirt] = np.clip(out[jy[dirt], jx[dirt]] + detail[dirt][:, None] * 0.5, 0, 1)
    print('veil dirt texels', int(dirt.sum()))
# gutters keep the padded neighbour colour
cov = K >= 0; idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True); out = out[idx[0], idx[1]]
Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save(DST)
if PREV:
    pv = (im * 0.5 * 255).astype('u1'); pv[bad] = (255, 0, 255); pv[orange] = (255, 160, 0); pv[lips] = (255, 0, 0); pv[scl] = (0, 255, 255)
    Image.fromarray(pv).save(PREV)
print('HEADFIX', DST)
