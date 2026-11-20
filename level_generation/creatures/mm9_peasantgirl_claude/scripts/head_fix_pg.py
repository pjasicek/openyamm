#!/usr/bin/env python3
"""Head paint fixes (PeasantGirl, after PeasantF5's head_fix.py) on textures/pg_head_<t>_sym.png -> pg_head_<t>_fix.png, per tier, by 3D
position (work/headmap.npz from headmap_pg.py):
- eyes: Meshy's eye paint (iris, lashes) is kept, but the front view sees the ball from 0.5 radii below its centre to 0.45 above (ray test);
  Meshy's iris fills that height, the white under it is the lower lid's inner rim painted white (a stare). The ball above U (0.30 radii) becomes the shadowed upper lid with a lash line, covering the top of the iris; the
  bottom below L the lower lid skin. Meshy's red-orange lid rims go toward the skin.
- mouth: the slit's inner faces (turned up or down) and the light specks Meshy painted in it (teeth) take a lip-shadow tone, so the closed
  mouth has one lip layer and no pale plate.
- gutters refilled from the nearest chart texel (sym_paint.py leaves the midline gutters unpadded: dark dots on the nose).
Args: <tier> [<tier>...] (g2 g3 g1e). Project folder."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ni
H = np.load('work/headmap.npz'); pos, nrm, face, cov = H['pos'], H['nrm'], H['face'], H['cov']
A = np.load('work/asm_frozen.npz'); D = np.load('work/uv.npz')
ac, at, acomp = A['co'], A['tri'], A['comp']; hk = [str(x) for x in A['names']].index('head')
par = np.arange(len(ac))
def find(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for a, b, c in at[acomp[at[:, 0]] == hk]:
    ra = find(a); par[find(b)] = ra; par[find(c)] = ra
hv = np.where(acomp == hk)[0]; roots = np.array([find(v) for v in hv]); big = np.bincount(roots).argmax()
eyev = np.zeros(len(ac), bool); eyev[hv[roots != big]] = True
eyef = eyev[D['orig'][D['tri'][:, 0]]]
EYE = cov & eyef[np.maximum(face, 0)]
ctr = {}
for sg in (1, -1):
    q = ac[eyev & (ac[:, 0] * sg > 0)]; c = q.mean(0); ctr[sg] = (c, float(np.linalg.norm(q - c, axis=1).mean()))
print('eyes', {k: (v[0].round(4).tolist(), round(v[1], 4)) for k, v in ctr.items()}, 'texels', int(EYE.sum()))
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
X, Y, Z = pos[..., 0], pos[..., 1], pos[..., 2]
# hair shell's open edges (asm), as a texel mask: hair texels within 1.2 cm of them
_hp = [str(x) for x in A['names']].index('hair'); _ht = at[acomp[at[:, 0]] == _hp]
_e = np.sort(np.vstack([_ht[:, [0, 1]], _ht[:, [1, 2]], _ht[:, [2, 0]]]), 1); _u, _c = np.unique(_e, axis=0, return_counts=True)
_bv = ac[np.unique(_u[_c == 1].ravel())]
from scipy.spatial import cKDTree as _KD
_hairf = (D['comp'][D['tri'][:, 0]] == _hp)
HB = np.zeros(cov.shape, bool); _m = cov & _hairf[np.maximum(face, 0)]
_d, _ = _KD(_bv).query(pos[_m]); _ii = np.argwhere(_m); HB[_ii[_d < 0.012, 0], _ii[_d < 0.012, 1]] = True
# chart-aware gutter padding (coordinator review, r14: pale tooth-like specks along the lip line). The lips and nose are cut into many small
# UV charts; their edge fragments sample texels just outside the polygon raster, which the old nearest-texel fill took from whichever chart
# was nearest in the atlas (often a skin chart 2 px away). Each chart now pads its own conservative ring (its triangles drawn with an
# outline) from its own nearest texel; the remaining gutter from the nearest texel overall.
from PIL import ImageDraw as _ID
_hf = np.where(D['mat'] == 1)[0]; _ht = D['tri'][_hf]; _par = np.arange(len(D['uv']))
def _fd(x):
    while _par[x] != x: _par[x] = _par[_par[x]]; x = _par[x]
    return x
for a_, b_, c_ in _ht:
    r_ = _fd(a_); _par[_fd(b_)] = r_; _par[_fd(c_)] = r_
_cid = np.array([_fd(t[0]) for t in _ht]); _uc, _cid = np.unique(_cid, return_inverse=True)
_SZ = cov.shape[0]
_lf = _ID.Draw(_imf := Image.new('I', (_SZ, _SZ), 0)); _lc = _ID.Draw(_imc := Image.new('I', (_SZ, _SZ), 0))
for k_, t_ in zip(_cid, _ht):
    pts = [(float(D['uv'][i, 0] * _SZ), float((1 - D['uv'][i, 1]) * _SZ)) for i in t_]
    _lc.polygon(pts, fill=int(k_) + 1, outline=int(k_) + 1)
for k_, t_ in zip(_cid, _ht):
    _lf.polygon([(float(D['uv'][i, 0] * _SZ), float((1 - D['uv'][i, 1]) * _SZ)) for i in t_], fill=int(k_) + 1)
LF = np.asarray(_imf); LC = np.ni_ = np.asarray(_imc)
LC = ni.grey_dilation(LC, size=3) * (LC == 0) + LC          # one more texel of ring
print('charts', len(_uc))
def chart_pad(img):
    out = img.copy()
    ring = (LC > 0) & (LF != LC)
    for k_ in np.unique(LC[ring]):
        m_ = LF == k_
        if not m_.any(): continue
        ys, xs = np.nonzero(m_ | (LC == k_)); y0, y1, x0, x1 = max(ys.min() - 2, 0), ys.max() + 3, max(xs.min() - 2, 0), xs.max() + 3
        sub = m_[y0:y1, x0:x1]; idx = ni.distance_transform_edt(~sub, return_distances=False, return_indices=True)
        rr = ring[y0:y1, x0:x1] & (LC[y0:y1, x0:x1] == k_)
        o_ = out[y0:y1, x0:x1]; o_[rr] = img[y0:y1, x0:x1][idx[0][rr], idx[1][rr]]
    filled = (LF > 0) | ring
    idx = ni.distance_transform_edt(~filled, return_distances=False, return_indices=True)
    return out[idx[0], idx[1]]
# protrusion of each head texel over a heavily smoothed head (the geometry's own nose / lips), from the asm head vertices
_hv2 = np.where((acomp == hk) & ~eyev)[0]; _ht2 = at[acomp[at[:, 0]] == hk]; _E = np.vstack([_ht2[:, [0, 1]], _ht2[:, [1, 2]], _ht2[:, [2, 0]]])
_S2 = ac.copy(); _dg = np.zeros(len(ac)); np.add.at(_dg, _E[:, 0], 1); np.add.at(_dg, _E[:, 1], 1)
for _ in range(40):
    _acc = np.zeros_like(_S2); np.add.at(_acc, _E[:, 0], _S2[_E[:, 1]]); np.add.at(_acc, _E[:, 1], _S2[_E[:, 0]])
    _S2 = np.where((_dg > 0)[:, None], 0.5 * _S2 + 0.5 * _acc / np.maximum(_dg, 1)[:, None], _S2)
_prot_v = (_S2[:, 1] - ac[:, 1])                       # forward protrusion (face looks to -y)
from scipy.spatial import cKDTree as _K4
_, _ni = _K4(ac[_hv2]).query(pos[cov]); PROT = np.zeros(cov.shape, np.float32); PROT[cov] = _prot_v[_hv2[_ni]]
import json as _js, os as _os2
BODY_NECK = _js.load(open('textures/body_neck.json')) if _os2.path.exists('textures/body_neck.json') else {}
FIXN = []
U, L = float(__import__('os').environ.get('EYE_U', '0.40')), float(__import__('os').environ.get('EYE_L', '-0.50'))
for t in sys.argv[1:]:
    im = np.asarray(Image.open(f'textures/pg_head_{t}_sym.png').convert('RGB'), np.float32)
    out = im.copy()
    skin_m = cov & ~EYE & (np.abs(np.abs(X) - 0.028) < 0.010) & (Z > 0.636) & (Z < 0.648) & (Y < -0.10)
    skin = np.median(im[skin_m], 0); print(t, 'cheek skin', skin.round(0), int(skin_m.sum()))
    for sg in (1, -1):
        c, r = ctr[sg]; m = EYE & (X * sg > 0)
        d = (pos[m] - c) / r; dx = d[:, 0] * sg; dz = d[:, 2]
        col = out[m]
        shade = 1 - 0.18 * np.exp(-((dz - (U - 0.06)) / 0.16) ** 2) * (dz < U)            # the lid's shadow on the ball
        col = col * shade[:, None]
        lash = np.exp(-((dz - (U - 0.01)) / 0.04) ** 2) * (1 - 0.5 * ss(np.abs(dx), 0.6, 1.0))
        col = col * (1 - 0.8 * lash)[:, None] + np.array([46, 30, 26.]) * (0.8 * lash)[:, None]
        up = ss(dz, U, U + 0.06); lo = ss(dz, L, L - 0.06)
        col = col * (1 - up)[:, None] + (skin * 0.55 + np.array([60, 40, 36.]) * 0.2) * up[:, None]
        # lower lid waterline: the lower lid's own skin under this eye (darker read as bags from above, lighter as a pale crescent)
        lid_m = cov & ~EYE & (X * sg > 0) & (np.abs(X - c[0]) < 0.008) & (Z < c[2] - 0.008) & (Z > c[2] - 0.016) & (Y < c[1])
        lidc = skin * 1.08          # user review r15: a sampled lid tone read as a dark wedge under each eye (the ball's lower half faces down: lighter paint)
        lo = ss(dz, L + 0.05, L - 0.10)
        col = col * (1 - lo)[:, None] + lidc * lo[:, None]
        out[m] = col
    rim = np.zeros_like(cov)
    for sg in (1, -1):
        c, r = ctr[sg]; dd = np.linalg.norm(pos - c, axis=2); rim |= cov & ~EYE & (dd < r + 0.006) & (X * sg > 0)
    hsv0 = np.asarray(Image.fromarray(np.clip(out, 0, 255).astype('u1')).convert('HSV'), np.float32) / 255
    sk_s = np.asarray(Image.fromarray(skin.astype('u1')[None, None]).convert('HSV'), np.float32)[0, 0, 1] / 255
    redrim = rim & ((hsv0[..., 0] * 360 < 22) | (hsv0[..., 0] * 360 > 340)) & (hsv0[..., 1] > sk_s + 0.06)
    rw = ni.gaussian_filter(redrim.astype(np.float32), 1.0)[..., None] * 0.7
    lum0 = out.mean(2, keepdims=True); out = out * (1 - rw) + skin * np.clip(lum0 / skin.mean(), 0.6, 1.1) * rw
    # the lower lid's inner rim (head shell round the bottom of the opening) was painted white: it read as white under the iris (a stare)
    wrim = np.zeros_like(cov)
    for sg in (1, -1):
        c, r = ctr[sg]; dd = np.linalg.norm(pos - c, axis=2); wrim |= cov & ~EYE & (dd < r + 0.008) & (X * sg > 0) & (Z < c[2] - 0.002)
    wsel = wrim & (hsv0[..., 1] < 0.24) & (hsv0[..., 2] > 0.55)
    ww = ni.gaussian_filter(ni.binary_dilation(wsel, iterations=1).astype(np.float32), 0.8)[..., None] * 0.9
    out = out * (1 - ww) + (skin * 0.92 + np.array([12, -4, -4.])) * ww
    print(t, 'white lower rim texels', int(wsel.sum()))
    # ---- mouth: inner faces of the slit and pale specks in it
    hsv = np.asarray(Image.fromarray(im.astype('u1')).convert('HSV'), np.float32) / 255
    h, s, v = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
    box = cov & ~EYE & (np.abs(X) < 0.026) & (Z > 0.617) & (Z < 0.633) & (Y < -0.10)
    lips = box & ((h < 14) | (h > 335)) & (s > 0.38)
    box_wide = cov & ~EYE & (np.abs(X) < 0.032) & (Z > 0.610) & (Z < 0.640) & (Y < -0.09)
    lipc = np.median(im[lips], 0) if lips.sum() > 20 else np.array([176, 72, 67.])
    inner = box & (np.abs(nrm[..., 2]) > 0.70) & (Y > -0.128) & (np.abs(Z - 0.625) < 0.005)
    lipd = ni.binary_dilation(lips, iterations=1) & box
    lipv = np.median(v[lips]) if lips.sum() > 20 else 0.7
    # lip specks (coordinator review 2026-11-02, r14: tooth-like dots along the lip line; an earlier speck pass that also took skin beside the
    # mouth corners painted dark wedges there): only inside the lips' own closed shape, light or desaturated texels take the plain lip
    # colour with the paint's broad shading; skin outside the lips is never touched
    lips_f = ni.binary_fill_holes(ni.binary_closing(lips, iterations=3)) & box
    pale = lips_f & ((v > lipv * 1.06) | (s < 0.40))
    lum_ = np.where(lips_f, im.mean(2), 0); lb_ = (ni.gaussian_filter(lum_, 4) / np.maximum(ni.gaussian_filter(lips_f.astype(np.float32), 4), 1e-3))[..., None]
    plain = lipc * np.clip(lb_ / max(float(np.median(im.mean(2)[lips])), 1), 0.8, 1.1)
    wp = (ni.gaussian_filter(pale.astype(np.float32), 0.7) * lips_f)[..., None] * 0.95
    out = out * (1 - wp) + plain * wp
    # the slit (Meshy's mouth is open a few mm): every texel inside the lips' x / z extent that lies recessed behind the lips' front surface
    # (more than 4 mm behind the frontmost surface in its own 1.5 mm x / z cell) is the inside of the mouth or the lips' inner faces, which caught the light
    # as pale specks: one lip-shadow tone. Nothing outside the lips' extent is painted (an earlier pass put dark wedges at the corners).
    xb = np.round(X / 0.0015).astype(int); zb = np.round(Z / 0.0015).astype(int); fr = {}
    mb = cov & ~EYE & (np.abs(X) < 0.03) & (Z > 0.60) & (Z < 0.65) & (Y < -0.09)
    for xx, zz, yy in zip(xb[mb], zb[mb], Y[mb]): fr[(xx, zz)] = min(fr.get((xx, zz), 9.0), yy)
    yfront = np.full(X.shape, -9.0); ii = np.argwhere(mb)
    for (r_, c_) in ii: yfront[r_, c_] = fr[(xb[r_, c_], zb[r_, c_])]
    zl = Z[lips_f]; xl = np.abs(X[lips_f]).max() if lips_f.any() else 0.0
    inner_l = mb & (np.abs(X) < xl - 0.002) & (Z > zl.min()) & (Z < zl.max()) & (Y > yfront + 0.004)
    wi_ = ni.gaussian_filter(inner_l.astype(np.float32), 0.7)[..., None] * 0.92
    out = out * (1 - wi_) + (lipc * 0.5) * wi_
    sl = inner_l
    cav = pale | inner_l
    print(t, 'red rim', int(redrim.sum()), 'lips', int(lips.sum()), 'mouth slit', int(cav.sum()), 'lip colour', lipc.round(0))
    # hairline arc (coordinator review 2026-11-02 of the boys, "dark line across the head"): where the hair shell's front edge lies on the
    # scalp cap Meshy painted a dark band (g3 / g1e read as a hairband at 128 px): hair texels within 1.2 cm of the shell's open edges,
    # above the brows, take the luminance of their neighbourhood (a dark band only is lifted, never darkened)
    lum_o = out.mean(2); big = ni.gaussian_filter(np.where(cov, lum_o, 0), 10) / np.maximum(ni.gaussian_filter(cov.astype(np.float32), 10), 1e-3)
    band = cov & HB & (Z > 0.69)
    gain = np.clip(big / np.maximum(lum_o, 1), 1.0, 1.7) * band
    gw = ni.gaussian_filter(band.astype(np.float32), 1.5)
    g_ = 1 + (np.where(band, gain, 1) - 1) * gw
    out = np.clip(out * g_[..., None], 0, 255)
    print(t, 'hairline band texels', int(band.sum()), 'mean gain', round(float(gain[band].mean()), 2) if band.any() else 0)
    # neck (coordinator review): Meshy painted the dress neckline as brown blobs on the head's neck strip above the level seam (a dotted
    # line under the chin at 128 px) and the mirror left a dark tick at the chin's midline: the neck under the jaw and the chin's underside
    # take the girl's chin skin with only broad shading
    chin_m = cov & ~EYE & (np.abs(X) < 0.016) & (Z > 0.596) & (Z < 0.610) & (Y < -0.105)
    chin_skin = np.median(im[chin_m], 0) if chin_m.sum() > 20 else skin
    hd = cov & ~EYE & ~_hairf[np.maximum(face, 0)]          # head skin faces only (hair hangs beside the neck)
    lum1 = np.where(hd, out.mean(2), 0); lb1 = (ni.gaussian_filter(lum1, 6) / np.maximum(ni.gaussian_filter(hd.astype(np.float32), 6), 1e-3))[..., None] + 1
    neck = hd & (Z < 0.598) & (Y < 0.02)
    nw_ = (ni.gaussian_filter(neck.astype(np.float32), 2.0) * hd)[..., None]
    out = out * (1 - nw_) + chin_skin * np.clip(lb1 / max(float(chin_skin.mean()), 1), 0.82, 1.05) * nw_
    mid = cov & ~EYE & (np.abs(X) < 0.003) & (Z > 0.572) & (Z < 0.615) & (Y < -0.05)
    mw = ni.gaussian_filter(mid.astype(np.float32), 1.0)[..., None] * 0.9
    out = out * (1 - mw) + ni.gaussian_filter(out, (3, 3, 0)) * mw
    # sockets (coordinator review: eyes dark and sunken at 128 px): the skin round each lid opening (not the ball) lifted, most at the rim
    sock = np.zeros(cov.shape, np.float32)
    for sg in (1, -1):
        c, r = ctr[sg]; dd = np.linalg.norm(pos - c, axis=2)
        sock = np.maximum(sock, (cov & ~EYE & (X * sg > 0) & (Y < c[1])) * (1 - ss(dd, r + 0.002, r + 0.012)))
    out = np.clip(out * (1 + 0.16 * sock[..., None]), 0, 255)
    print(t, 'neck texels', int(neck.sum()), 'chin skin', chin_skin.round(0), 'socket lift texels', int((sock > 0.1).sum()))
    # ---- user review r15 (viewer front close-up, g2)
    # nose: the paint's alae are wider than the geometry's nose (a lighter 'ghost nose' outline either side). Texels near the nose that
    # do not protrude from the face (protrusion < 1.6 mm over a heavily smoothed head surface) take the smooth skin of their surroundings
    fz = cov & ~EYE & (np.abs(X) < 0.026) & (Z > 0.636) & (Z < 0.668) & (Y < -0.09)     # above the upper lip
    pro = PROT
    ghost = fz & (pro < 0.0016) & (np.abs(X) > 0.004)
    keep_ = cov & ~EYE & ~ghost & ~(fz & (pro >= 0.0016))
    sk_ = np.where(keep_[..., None], out, 0); wk_ = ni.gaussian_filter(keep_.astype(np.float32), 9)[..., None]
    smooth_skin = ni.gaussian_filter(sk_, (9, 9, 0)) / np.maximum(wk_, 1e-3)
    lumo = out.mean(2, keepdims=True); lbo = ni.gaussian_filter(lumo, (9, 9, 0)) + 1
    detail = np.clip(lumo / lbo, 0.9, 1.1)
    gw = (ni.gaussian_filter(ghost.astype(np.float32), 1.5) * fz)[..., None]
    out = out * (1 - gw) + smooth_skin * detail * gw
    # lips: the dark outline and dark corners (lipstick-like) softened to a natural lip edge
    ring = ni.binary_dilation(lips_f, iterations=4) & ~ni.binary_erosion(lips_f, iterations=1) & box_wide
    lum2 = out.mean(2); dark = ring & (lum2 < 0.9 * np.median(lum2[lips_f]))
    edgec = lipc * 0.55 + skin * 0.45
    dw = (ni.gaussian_filter(dark.astype(np.float32), 1.2) * ring)[..., None] * 0.85
    out = out * (1 - dw) + edgec * np.clip(lum2[..., None] / max(float(np.median(lum2[ring])), 1), 0.85, 1.05) * dw
    # chin: the dark dot at the chin's lowest point
    # small dark blobs on the lower face (the chin's lowest point, the lip corners, a speck beside the upper lip): texels darker than 0.8 x
    # their smooth surroundings outside the lips take the surroundings (shadows wider than ~4 mm stay)
    lf_ = np.where(cov & ~EYE, out.mean(2), 0); wf_ = ni.gaussian_filter((cov & ~EYE).astype(np.float32), 5)
    loc_ = ni.gaussian_filter(lf_, 5) / np.maximum(wf_, 1e-3)
    blob = cov & ~EYE & (np.abs(X) < 0.036) & (Z > 0.572) & (Z < 0.640) & (Y < -0.06) & ~ni.binary_dilation(lips_f, iterations=4) \
        & (out.mean(2) < np.where(PROT >= 0.0016, 0.80, 0.88) * loc_)
    redish = ((h < 20) | (h > 330)) & (s > 0.30)                 # lip-red texels (the lower lip reaches below the lips box) are never blobs
    blob &= ~ni.binary_dilation(redish & (np.abs(X) < 0.03) & (Z > 0.60) & (Z < 0.64), iterations=3)
    blob = ni.binary_dilation(blob, iterations=1) & cov
    surr = ni.gaussian_filter(np.where((cov & ~blob)[..., None], out, 0), (5, 5, 0)) / np.maximum(ni.gaussian_filter((cov & ~blob).astype(np.float32), 5), 1e-3)[..., None]
    cdw = (ni.gaussian_filter(blob.astype(np.float32), 0.8) * cov)[..., None]
    out = out * (1 - cdw) + surr * cdw
    chin_d = blob
    # nose base (user review r15/r16: brown blotches round the nostrils): on the geometry's nose below the tip every texel is at least
    # 0.66 x its smooth surroundings (the nostril holes keep a soft shadow, the spread brown goes)
    # the nose base below the tip takes the nose's own smooth skin; two soft nostril shadows only on down-facing texels
    nbase = cov & ~EYE & (PROT >= 0.0008) & (np.abs(X) < 0.021) & (Z > 0.6345) & (Z < 0.650) & (Y < -0.10) & ~ni.binary_dilation(lips_f, iterations=6)   # the nose only, never the upper lip
    nsrc = cov & ~EYE & (PROT >= 0.0016) & (np.abs(X) < 0.012) & (Z > 0.642) & (Z < 0.665)
    nskin = np.median(out[nsrc], 0) if nsrc.sum() > 20 else skin
    lumn = out.mean(2, keepdims=True); lbn = ni.gaussian_filter(lumn, (6, 6, 0)) + 1
    nostril = nbase & (nrm[..., 2] < -0.45) & (np.abs(X) > 0.003) & (np.abs(X) < 0.013)
    tgt = nskin * np.clip(lumn / lbn, 0.92, 1.06)
    tgt = np.where(nostril[..., None], tgt * 0.72, tgt)
    bw_ = (ni.gaussian_filter(nbase.astype(np.float32), 1.2) * cov)[..., None]
    out = out * (1 - bw_) + tgt * bw_
    # neck seam: the head's neck within 2.5 cm of the level seam blends toward the body's skin tone at the seam (BODY_NECK, the tier's ramped
    # body skin, measured by tiers_pg.py), fully at the seam
    if t in BODY_NECK:
        nb = cov & ~EYE & ~_hairf[np.maximum(face, 0)] & (Z < 0.5703 + 0.025)
        nwt = ((1 - ss(Z, 0.5703, 0.5703 + 0.025)) * nb)[..., None]
        bc = np.array(BODY_NECK[t]); lum3 = out.mean(2, keepdims=True); lb3 = ni.gaussian_filter(lum3, (8, 8, 0)) + 1
        out = out * (1 - nwt) + bc * np.clip(lum3 / lb3, 0.92, 1.06) * nwt
    # coordinator review r20: a dark diamond between the brows / top of the bridge, a dark stripe in the chin dimple under the lower lip,
    # and light specks on the neck under the jaw: texels darker (or, on the neck, lighter) than their smooth surroundings take the
    # surroundings' colour with their own fine detail
    lf2 = np.where(cov & ~EYE, out.mean(2), 0); wf2 = ni.gaussian_filter((cov & ~EYE).astype(np.float32), 7)
    loc2 = ni.gaussian_filter(lf2, 7) / np.maximum(wf2, 1e-3)
    brow = cov & ~EYE & (np.abs(X) < 0.022) & (Z > 0.672) & (Z < 0.712) & (Y < -0.09) & ~_hairf[np.maximum(face, 0)]
    dimple = cov & ~EYE & (np.abs(X) < 0.010) & (Z > 0.607) & (Z < 0.6175) & (Y < -0.09) & ~lips_f
    dsoft = (1 - ss(np.abs(X), 0.006, 0.010)) * ss(Z, 0.607, 0.610) * (1 - ss(Z, 0.6165, 0.6178))     # feathered: no box edge
    neckz = cov & ~EYE & (Z > 0.5703) & (Z < 0.598) & (Y < 0.02) & ~_hairf[np.maximum(face, 0)]
    lum4 = out.mean(2)
    fix2 = (brow | dimple) & (lum4 < 0.95 * loc2)                # the neck pass took colour across chart edges (a dark triangle, r21): dropped
    fix2 = ni.binary_dilation(fix2, iterations=1) & (brow | dimple)
    ok2 = cov & ~EYE & ~fix2
    surr2 = ni.gaussian_filter(np.where(ok2[..., None], out, 0), (6, 6, 0)) / np.maximum(ni.gaussian_filter(ok2.astype(np.float32), 6), 1e-3)[..., None]
    det2 = np.clip(lum4 / np.maximum(ni.gaussian_filter(lum4, 2), 1), 0.96, 1.04)[..., None]
    w2_ = (ni.gaussian_filter(fix2.astype(np.float32), 1.0) * (brow | dimple) * np.where(dimple, dsoft, 1.0))[..., None]
    out = out * (1 - w2_) + surr2 * det2 * w2_
    # the dimple's V under the lower lip faces down (the lip's underside): lit from above it shades dark, so its paint is lifted up to 1.35x
    dv = dimple & (nrm[..., 2] < -0.15)
    gl_ = np.where(dv, 1 + 0.25 * np.clip(-nrm[..., 2], 0, 1) * dsoft, 1.0); gl_ = ni.gaussian_filter(gl_, 1.5)
    out = np.clip(out * gl_[..., None], 0, 255)
    FIXN.append(fix2)
    print(t, 'ghost-nose texels', int(ghost.sum()), 'dark lip edge', int(dark.sum()), 'chin dot', int(chin_d.sum()))
    out = chart_pad(out)
    Image.fromarray(np.clip(out, 0, 255).astype('u1')).save(f'textures/pg_head_{t}_fix.png')
# head normal maps flattened on the eyeballs, round the lid opening and on the mouth: Meshy's normal map carried its own eye and lip
# relief (in the viewer a dark crescent under each eye and white all round the iris, where the flat paint reads calm)
FLAT = np.zeros(cov.shape, np.float32)
for sg in (1, -1):
    c, r = ctr[sg]; dd = np.linalg.norm(pos - c, axis=2); FLAT = np.maximum(FLAT, (cov & (dd < r + 0.009)).astype(np.float32))
FLAT = np.maximum(FLAT, (cov & (np.abs(X) < 0.028) & (Z > 0.614) & (Z < 0.636) & (Y < -0.10)).astype(np.float32))
FLAT = np.maximum(FLAT, (cov & (Z < 0.5703 + 0.02)).astype(np.float32))     # the neck band above the seam (user review r15: shading step)
for _f2 in FIXN: FLAT = np.maximum(FLAT, ni.binary_dilation(_f2, iterations=3).astype(np.float32))   # their normal-map relief too
FLAT = ni.gaussian_filter(FLAT, 1.5)
for t in sys.argv[1:]:
    src = f'textures/pg_head_{t}_normal.png'
    if not __import__('os').path.exists(src): continue
    NM = np.asarray(Image.open(src).convert('RGB'), np.float32)
    F_ = ni.zoom(FLAT, NM.shape[0] / FLAT.shape[0], order=1)[..., None] if NM.shape[0] != FLAT.shape[0] else FLAT[..., None]
    Image.fromarray(np.clip(NM * (1 - F_) + np.array([128, 128, 255.]) * F_, 0, 255).astype('u1')).save(f'textures/pg_head_{t}_normal_fix.png')
print('normal flattened texels', int((FLAT > 0.5).sum()))
print('HEADFIX')
