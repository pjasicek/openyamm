#!/usr/bin/env python3
"""Head paint fixes for the fresh 4K head repaint (r24: paint-over masters on the one-chart face layout of uv_head_pg.py). Light touch:
the paint is clean; only marks that do not follow the geometry are repaired, each from the skin's own blurred colour with its fine detail.
textures/pg_head_<t>_sym.png -> pg_head_<t>_fix.png, pg_head_<t>_normal.png -> pg_head_<t>_normal_fix.png (work/headmap.npz from
headmap_pg.py, current layout work/uv.npz).
- Nostrils (user, viewer from below: brown smears that do not follow the nostrils): the nose underside takes the nose's own skin, and two
  small soft nostril shadows sit on the geometry's nostril openings (the most recessed down-facing texels of each side, found on the mesh);
  dark brown paint on the front of the nose tip is cleaned.
- Small dark marks: the chin dimple under the lower lip, the chin tip. Small light marks: the top of the bridge, pale hair strands painted
  on the forehead skin under the fringe.
- Neck: the head's neck within 2.5 cm of the level seam blends to the tier's ramped body skin (textures/body_neck.json from tiers_pg.py);
  the normal map is flattened there, on the nose underside and on the cleaned marks.
- Gutters padded per UV chart.
Args: <tier> [<tier>...]. Project folder."""
import sys, json, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ni
H = np.load('work/headmap.npz'); pos, nrm, face, cov = H['pos'], H['nrm'], H['face'], H['cov']
D = np.load('work/uv.npz'); pn = [str(x) for x in D['names']]
X, Y, Z = pos[..., 0], pos[..., 1], pos[..., 2]
fcomp = D['comp'][D['tri'][:, 0]]
HAIR = cov & np.isin(fcomp[np.maximum(face, 0)], [pn.index(x) for x in ('hair', 'ears') if x in pn])
# eyeballs: the head part's small components, by mesh connectivity of the current layout's head faces
hk = pn.index('head'); fh = np.where((D['mat'] == 1) & (fcomp == hk))[0]
par = {}
def fd(x):
    while par.setdefault(x, x) != x: par[x] = par[par[x]]; x = par[x]
    return x
O = D['orig']
for f in fh:
    a, b, c = O[D['tri'][f]]; r = fd(a); par[fd(b)] = r; par[fd(c)] = r
roots = {f: fd(O[D['tri'][f][0]]) for f in fh}
from collections import Counter
big = Counter(roots.values()).most_common(1)[0][0]
eyef = np.zeros(len(D['tri']), bool)
for f in fh: eyef[f] = roots[f] != big
EYE = cov & eyef[np.maximum(face, 0)]
SKIN = cov & ~EYE & ~HAIR
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
BODY_NECK = json.load(open('textures/body_neck.json')) if os.path.exists('textures/body_neck.json') else {}
# per-chart padding
S = cov.shape[0]; ht = D['tri'][D['mat'] == 1]; uvv = D['uv']
pr = np.arange(len(uvv))
def f2(x):
    while pr[x] != x: pr[x] = pr[pr[x]]; x = pr[x]
    return x
for a, b, c in ht:
    r = f2(a); pr[f2(b)] = r; pr[f2(c)] = r
cid = np.unique([f2(t[0]) for t in ht], return_inverse=True)[1]
imf = Image.new('I', (S, S), 0); imc = Image.new('I', (S, S), 0); df = ImageDraw.Draw(imf); dc = ImageDraw.Draw(imc)
for k, t in zip(cid, ht):
    pts = [(float(uvv[i, 0] * S), float((1 - uvv[i, 1]) * S)) for i in t]
    dc.polygon(pts, fill=int(k) + 1, outline=int(k) + 1); df.polygon(pts, fill=int(k) + 1)
LF = np.asarray(imf); LC = np.asarray(imc); LC = ni.grey_dilation(LC, size=3) * (LC == 0) + LC
def chart_pad(img):
    out = img.copy(); ring = (LC > 0) & (LF != LC)
    for k in np.unique(LC[ring]):
        m = LF == k
        if not m.any(): continue
        ys, xs = np.nonzero(m | (LC == k)); y0, y1, x0, x1 = max(ys.min() - 2, 0), ys.max() + 3, max(xs.min() - 2, 0), xs.max() + 3
        idx = ni.distance_transform_edt(~m[y0:y1, x0:x1], return_distances=False, return_indices=True)
        rr = ring[y0:y1, x0:x1] & (LC[y0:y1, x0:x1] == k); o_ = out[y0:y1, x0:x1]; o_[rr] = img[y0:y1, x0:x1][idx[0][rr], idx[1][rr]]
    filled = (LF > 0) | ring; idx = ni.distance_transform_edt(~filled, return_distances=False, return_indices=True)
    return out[idx[0], idx[1]]
def surround(img, ok, r):
    w = ni.gaussian_filter(ok.astype(np.float32), r)[..., None]
    return ni.gaussian_filter(np.where(ok[..., None], img, 0), (r, r, 0)) / np.maximum(w, 1e-3)
# nostril openings on the mesh (asm positions of the head shell): per side, the down-facing nose-underside texels' most recessed part
under = SKIN & (np.abs(X) < 0.017) & (Z > 0.624) & (Z < 0.646) & (Y < -0.104) & ((nrm[..., 2] < -0.35) | (nrm[..., 1] > -0.5))   # underside and the nostril cavity walls
NOST = {}
for sg in (1, -1):
    m = under & (X * sg > 0.002)
    if m.sum() < 20: continue
    yv = Y[m]; lo_, hi_ = np.percentile(yv, [35, 75]); sel = m & (Y >= lo_) & (Y <= hi_) & (np.abs(X) > 0.004) & (np.abs(X) < 0.011)   # the opening: mid-depth, between columella and ala
    NOST[sg] = np.array([X[sel].mean(), Y[sel].mean(), Z[sel].mean()])
print('nostril centres', {k: v.round(4).tolist() for k, v in NOST.items()}, 'underside texels', int(under.sum()))
FLAT = np.zeros(cov.shape, np.float32)
for t in sys.argv[1:]:
    im = np.asarray(Image.open(f'textures/pg_head_{t}_sym.png').convert('RGB'), np.float32); out = im.copy()
    lum = out.mean(2)
    # ---- nose underside and nostrils
    nfront = SKIN & (np.abs(X) < 0.010) & (Z > 0.646) & (Z < 0.668) & (Y < -0.11)
    nskin = np.median(out[nfront], 0)
    tgt = np.repeat(nskin[None, None], S, 0).repeat(S, 1)
    sh = np.zeros(cov.shape, np.float32)
    for sg, c in NOST.items():
        d = np.sqrt(((X - c[0]) / 0.0016) ** 2 + ((Y - c[1]) / 0.0022) ** 2 + ((Z - c[2]) / 0.0016) ** 2)   # r25: smaller
        sh = np.maximum(sh, np.exp(-d ** 2) * (X * sg > 0))
    tgt = tgt * (1 - 0.42 * sh[..., None])
    nw = (ni.gaussian_filter(under.astype(np.float32), 1.2) * SKIN)[..., None]
    out = out * (1 - nw) + tgt * nw
    # dark brown paint on the front of the nose tip / alae
    loc = surround(out, SKIN, 6); lum = out.mean(2)
    ntip = SKIN & (np.abs(X) < 0.018) & (Z > 0.630) & (Z < 0.652) & (Y < -0.10) & ~under & (lum < 0.88 * loc.mean(2))
    # small dark marks: chin dimple under the lower lip, chin tip
    dark = SKIN & (np.abs(X) < 0.012) & (((Z > 0.600) & (Z < 0.6185)) | ((Z > 0.578) & (Z < 0.600))) & (Y < -0.07) & (lum < 0.92 * loc.mean(2))
    # small light marks: top of the bridge, pale strands on the forehead skin
    light = SKIN & (((np.abs(X) < 0.012) & (Z > 0.670) & (Z < 0.712)) | ((np.abs(X) < 0.06) & (Z > 0.700) & (Z < 0.76) & (Y < -0.05))) \
        & (lum > 1.06 * loc.mean(2))
    fix = ni.binary_dilation(ntip | dark | light, iterations=1) & SKIN
    sur = surround(out, SKIN & ~fix, 5)
    det = np.clip(lum / np.maximum(ni.gaussian_filter(lum, 1.5), 1), 0.97, 1.03)[..., None]
    fw = (ni.gaussian_filter(fix.astype(np.float32), 0.8) * SKIN)[..., None]
    out = out * (1 - fw) + sur * det * fw
    # ---- mouth: the dark brown slit and dark corners (lipstick-like) -> a soft lip shadow on the closed line, skin at the corners
    lipm = SKIN & (np.abs(X) < 0.032) & (Z > 0.612) & (Z < 0.636) & (Y < -0.095)
    hsv = np.asarray(Image.fromarray(np.clip(out, 0, 255).astype('u1')).convert('HSV'), np.float32) / 255
    lips = lipm & (((hsv[..., 0] * 360 < 15) | (hsv[..., 0] * 360 > 335)) & (hsv[..., 1] > 0.30))
    lipc = np.median(out[lips], 0) if lips.sum() > 30 else np.array([200, 110, 100.])
    l5 = out.mean(2); loc5 = surround(out, SKIN, 5).mean(2)
    darkm = lipm & (l5 < 0.86 * loc5)
    corner = darkm & (np.abs(X) > 0.015)
    slit = darkm & ~corner
    sk5 = surround(out, SKIN & ~darkm, 4)
    cw_ = (ni.gaussian_filter(corner.astype(np.float32), 1.0) * SKIN)[..., None]
    out = out * (1 - cw_) + sk5 * cw_                               # r25: the corners take the skin (a pursed mouth before)
    # r25: the corner notches keep a grey cast below the 0.86 threshold (viewer: dark wedges) -> lifted to the surrounding skin as well
    l6 = out.mean(2); ax = np.abs(X)
    cz = SKIN & (ax > 0.012) & (ax < 0.028) & (Z > 0.614) & (Z < 0.636) & (Y < -0.09) & (l6 < 0.97 * loc5)
    sk6 = surround(out, SKIN & ~cz & ~darkm, 5)
    cw2 = (ni.gaussian_filter(cz.astype(np.float32), 1.2) * SKIN * ss(ax, 0.010, 0.014))[..., None] * 0.9
    out = out * (1 - cw2) + sk6 * cw2
    print(t, 'mouth corner notches', int(cz.sum()))
    fade = (1 - ss(np.abs(X), 0.008, 0.017))[..., None]             # the slit line fades out toward the corners
    sw_ = (ni.gaussian_filter(slit.astype(np.float32), 0.8) * SKIN)[..., None] * 0.8
    slitc = lipc * 0.68 * fade + (sk5 * 0.95) * (1 - fade)
    out = out * (1 - sw_) + slitc * sw_
    print(t, 'mouth dark slit', int(slit.sum()), 'corners', int(corner.sum()))
    # ---- r25 (coordinator: r24 reads pale and blank): a soft cheek blush per girl, lips a little rosier (no outline)
    BL = {'g2': 0.30, 'g3': 0.16, 'g1e': 0.20}.get(t, 0.18)
    blush = np.zeros(cov.shape, np.float32)
    for sg in (1, -1):
        dd = ((X - 0.036 * sg) / 0.016) ** 2 + ((Z - 0.640) / 0.013) ** 2
        blush = np.maximum(blush, np.exp(-dd) * (X * sg > 0))
    blush *= SKIN & (Y < -0.06)
    rose = np.array([228, 120, 112.]) * np.clip(out.mean(2, keepdims=True) / max(float(np.median(out[SKIN].mean(1))), 1), 0.85, 1.1)
    bw = (blush * BL)[..., None]
    out = out * (1 - bw) + (out * 0.5 + rose * 0.5) * bw
    lipsf = ni.binary_fill_holes(ni.binary_closing(lips, iterations=3)) & lipm
    lw = (ni.gaussian_filter(lipsf.astype(np.float32), 1.2) * SKIN)[..., None] * 0.35
    rosy = np.array([214, 112, 108.]) * np.clip(out.mean(2, keepdims=True) / max(float(np.median(out[lips].mean(1))), 1), 0.85, 1.12)
    out = out * (1 - lw) + rosy * lw
    # earlobe specks: dark dots on the ears / beside the jaw
    loc6 = surround(out, SKIN, 5).mean(2); l6 = out.mean(2)
    ear = SKIN & (np.abs(X) > 0.050) & (np.abs(X) < 0.110) & (Z > 0.595) & (Z < 0.680) & (Y < 0.04) & (l6 < 0.90 * loc6)   # r25: to the lobe
    # forehead midline stitches (between and above the brows)
    th2 = l6 - ni.grey_opening(l6, size=(5, 5))
    stitch = SKIN & (np.abs(X) < 0.012) & (Z > 0.665) & (Z < 0.78) & (Y < -0.04) & ((th2 > 3) | (l6 > 1.04 * loc6) | (l6 < 0.95 * loc6))
    fix6 = ni.binary_dilation(ear | stitch, iterations=1) & SKIN
    sur6 = surround(out, SKIN & ~fix6, 5)
    w6 = (ni.gaussian_filter(fix6.astype(np.float32), 0.8) * SKIN)[..., None]
    out = out * (1 - w6) + sur6 * w6
    # the midline itself: sym_paint keeps the faces crossing x = 0 and mirrors their neighbours, so the paint steps along the midline in a
    # stitch-like row (forehead, bridge, chin): a 4 mm band takes the skin's 4 px blur with a little of its own detail
    mband = SKIN & (np.abs(X) < 0.004) & (Y < -0.04) & (((Z > 0.665) & (Z < 0.79)) | ((Z > 0.572) & (Z < 0.616)))
    mw = (ni.gaussian_filter(mband.astype(np.float32), 1.5) * SKIN * (1 - ss(np.abs(X), 0.0025, 0.004)))[..., None] * 0.85
    mb = surround(out, SKIN, 4)
    out = out * (1 - mw) + mb * mw
    print(t, 'blush', BL, 'earlobe specks', int(ear.sum()), 'forehead midline', int(stitch.sum()))
    # ---- neck blend to the body skin at the seam
    if t in BODY_NECK:
        nb = SKIN & (Z < 0.5703 + 0.025); nwt = ((1 - ss(Z, 0.5703, 0.5703 + 0.025)) * nb)[..., None]
        bc = np.array(BODY_NECK[t]); l3 = out.mean(2, keepdims=True); lb3 = ni.gaussian_filter(l3, (8, 8, 0)) + 1
        out = out * (1 - nwt) + bc * np.clip(l3 / lb3, 0.94, 1.05) * nwt
    # ---- the nose underside faces down: the viewer's top light shades it into a brown triangle under the tip; its paint (not the two
    # nostril shadows) is lifted up to 1.4x by how much it faces down
    dn = under & (sh < 0.35)
    gl = np.where(dn, 1 + 0.6 * np.clip(-nrm[..., 2], 0, 1), 1.0)
    # the chin dimple's V under the lower lip faces down too (a dark dot in front views)
    dimv = SKIN & (np.abs(X) < 0.010) & (Z > 0.604) & (Z < 0.6175) & (Y < -0.09) & (nrm[..., 2] < -0.15)
    dsoft = (1 - ss(np.abs(X), 0.005, 0.010)) * ss(Z, 0.604, 0.608) * (1 - ss(Z, 0.614, 0.6178))      # feathered (no box edge)
    gl = ni.gaussian_filter(gl, 2.0)      # r26: the chin dimple is smoothed out of the mesh (tweak_pg.py), its lift (a light blob) dropped
    gl = np.minimum(gl, 250.0 / np.maximum(out.max(2), 1))      # hue kept: a channel clipping at 255 turned the lifted chin yellow-green
    out = out * gl[..., None]
    # ---- seam halos: Meshy paints a pale line along chart borders (the face chart's cuts from the eye openings ran as light lines up the
    # bridge): skin texels within 3 px of a chart border take the texel 3 px inside
    bord = (LF != ni.grey_dilation(LF, size=3)) | (LF != ni.grey_erosion(LF, size=3))
    dist = ni.distance_transform_edt(~bord)
    near = (dist < 3.5) & (LF > 0)
    idx = ni.distance_transform_edt(near | (LF == 0), return_distances=False, return_indices=True)
    halo = near & ni.binary_dilation(SKIN, iterations=2)
    out[halo] = out[idx[0][halo], idx[1][halo]]
    # ---- thin pale lines Meshy painted along the face chart's cuts (inner eye corners up across the brows, down the sides of the bridge):
    # a white top-hat on the luminance finds lines under ~4 px wide; they take the grey-opened colour round them
    lumt = out.mean(2)
    th = lumt - ni.grey_opening(lumt, size=(5, 5))
    lines = SKIN & (th > 7) & ~ni.binary_dilation(EYE, iterations=4) & ~(np.abs(X) < 0.03) * 0 | False
    lines = SKIN & (th > 4) & ~ni.binary_dilation(EYE, iterations=4) & ~(lipm if 'lipm' in dir() else np.zeros_like(SKIN))
    lines = ni.binary_dilation(lines, iterations=1) & SKIN
    op = np.stack([ni.grey_opening(out[..., c], size=(5, 5)) for c in range(3)], -1)
    out[lines] = 0.3 * out[lines] + 0.7 * np.maximum(op[lines], 0)
    print(t, 'thin pale line texels', int(lines.sum()))
    # ---- r26 (user review r25: "whats wrong with the mouth?"): a lighter oval round the mouth with an edge (Meshy's paint: a duller,
    # browner disc from under the nose to the chin, ringed by the cheeks' blush), the slit's inner faces showing as dark corner wedges and
    # white specks. (1) The mouth's inner faces (more than 2.5 mm behind the face's front at their place) take the soft slit colour.
    mb_ = SKIN & (np.abs(X) < 0.036) & (Z > 0.600) & (Z < 0.642) & (Y < -0.06)
    from scipy.spatial import cKDTree as _KD
    _r, _c = np.where(mb_); _xz = np.stack([X[_r, _c], Z[_r, _c]], 1); _kd = _KD(_xz)
    _ym = np.array([Y[_r, _c][j].min() for j in _kd.query_ball_point(_xz, 0.002)])
    _beh = np.zeros(cov.shape, np.float32); _beh[_r, _c] = Y[_r, _c] - _ym
    inner = (_beh > 0.0025) & (Z > 0.621) & (Z < 0.634) & (np.abs(X) < 0.026)          # the slit only (the lower lip's underside is skin)
    sk8 = surround(out, SKIN & ~inner & ~lipsf, 5)
    slit_c = lipc * 0.88 * (1 - ss(np.abs(X), 0.004, 0.014))[..., None] + sk8 * ss(np.abs(X), 0.004, 0.014)[..., None]   # a soft rose line, skin by the corners
    out[inner] = slit_c[inner]
    # pale specks along the lips' meeting line (Meshy's teeth / highlight paint on the lips' inner edges) take the lip colour round them
    hsv3 = np.asarray(Image.fromarray(np.clip(out, 0, 255).astype('u1')).convert('HSV'), np.float32) / 255
    lipc_loc = surround(out, lipsf & ~inner, 4)
    pale = lipsf & (np.abs(Z - 0.6275) < 0.0045) & (out.mean(2) > 1.06 * lipc_loc.mean(2)) & (hsv3[..., 1] < 0.42)
    pale = ni.binary_dilation(pale, iterations=1) & lipsf
    out[pale] = lipc_loc[pale]
    print(t, 'lip pale specks', int(pale.sum()))
    # (2) the oval: Meshy painted a duller, browner disc round the mouth with a visible rim (not in the shading: the unlit render shows
    # it). In the front view (x, z on a 0.5 mm grid) the skin's colour field (2 mm blur, lips, slit and nostrils left out) is replaced
    # inside an ellipse a little wider than the disc by a harmonic fill from the field round it; each texel there is scaled by fill /
    # field, so the rim and the disc's tone go and the paint's detail stays. The lips keep their paint.
    import scipy.sparse as _sp, scipy.sparse.linalg as _spl
    lipk = ni.binary_dilation(lipsf, iterations=1)
    gx = np.clip(((X + 0.08) / 0.0005).astype(int), 0, 319); gz = np.clip(((Z - 0.55) / 0.0005).astype(int), 0, 279)
    srcf = SKIN & (Y < -0.05) & (nrm[..., 1] < -0.3) & ~lipk & ~inner & ~under
    gs = np.zeros((280, 320, 3)); gn = np.zeros((280, 320))
    np.add.at(gs, (gz[srcf], gx[srcf]), out[srcf]); np.add.at(gn, (gz[srcf], gx[srcf]), 1)
    Lg = ni.gaussian_filter(gs, (4, 4, 0)) / np.maximum(ni.gaussian_filter(gn, 4), 1e-9)[..., None]
    Lg = np.where((ni.gaussian_filter(gn, 4) > 1e-3)[..., None], Lg, ni.gaussian_filter(gs, (16, 16, 0)) / np.maximum(ni.gaussian_filter(gn, 16), 1e-9)[..., None])
    xx = np.arange(320) * 0.0005 - 0.08; zz = np.arange(280) * 0.0005 + 0.55
    EG = (xx[None, :] / 0.044) ** 2 + ((zz[:, None] - 0.6185) / 0.028) ** 2
    reg = (EG < 1.0) & ~((np.abs(xx[None, :]) < 0.021) & (zz[:, None] > 0.6395))     # not the nose
    idx = -np.ones(reg.shape, int); idx[reg] = np.arange(reg.sum())
    rows, cols, vals = [], [], []; rhs = np.zeros((reg.sum(), 3))
    for dz_, dx_ in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nb = np.roll(np.roll(idx, -dz_, 0), -dx_, 1); nbv = np.roll(np.roll(Lg, -dz_, 0), -dx_, 1)
        r_ = idx[reg]; n_ = nb[reg]
        inn = n_ >= 0
        rows += [r_[inn]]; cols += [n_[inn]]; vals += [-np.ones(inn.sum())]
        rhs[~inn] += nbv[reg][~inn]
    nr = reg.sum()
    A_ = _sp.csr_matrix((np.concatenate(vals + [4 * np.ones(nr)]), (np.concatenate(rows + [np.arange(nr)]), np.concatenate(cols + [np.arange(nr)]))), shape=(nr, nr))
    Fg = Lg.copy()
    for k in range(3): Fg[..., k][reg] = _spl.spsolve(A_.tocsc(), rhs[:, k])
    ratio = np.clip(Fg / np.maximum(Lg, 1), 0.7, 1.4)
    regw = ni.gaussian_filter(reg.astype(np.float32), 2)
    rt = 1 + (ratio[gz, gx] - 1) * regw[gz, gx][..., None]
    aw = (SKIN & (Y < -0.05) & ~under)[..., None] * (1 - ni.gaussian_filter(lipk.astype(np.float32), 1.5))[..., None]
    out = out * (1 + (rt - 1) * aw)
    ell = reg[gz, gx] & SKIN
    # the rim's thin darker line (narrower than the 2 mm field): a dark top-hat inside the ellipse, filled from the closing
    lm = out.mean(2)
    cl = np.stack([ni.grey_closing(out[..., c], size=(7, 7)) for c in range(3)], -1)
    dth = cl.mean(2) - lm
    ell2 = SKIN & (((X / 0.052) ** 2 + ((Z - 0.6185) / 0.033) ** 2) < 1.0) & ~((np.abs(X) < 0.021) & (Z > 0.6395))
    rim = ell2 & (Y < -0.05) & ~ni.binary_dilation(lipk | inner, iterations=3) & ~under & (dth > 2.5)
    rim = ni.binary_dilation(rim, iterations=1) & ell2 & ~lipk & ~inner
    rw = (ni.gaussian_filter(rim.astype(np.float32), 0.8) * ell2)[..., None]
    out = out * (1 - rw) + cl * rw
    print(t, 'muzzle rim texels', int(rim.sum()))
    print(t, 'mouth inner texels', int(inner.sum()), 'muzzle texels', int(ell.sum()))
    # ---- r26 hairline (user review r25: a sawtooth across the top of the forehead): the head shell's face chart (skin) meets its scalp
    # chart (hair colour) along a zig-zag of triangle edges just under the hair shell's front edge; a soft band about that edge (Zh(x),
    # from the hair shell's open front edge) takes a skin -> hair-root gradient by height, with the paint's fine detail, so the charts'
    # border no longer shows
    Zh = np.interp(np.abs(X), [0, 0.030, 0.044, 0.052, 0.058, 0.062, 0.065, 0.080], [0.760, 0.760, 0.756, 0.750, 0.722, 0.705, 0.690, 0.680])
    hz = Z - Zh
    hfront = SKIN & (Y < -0.03) & (np.abs(X) < 0.068)
    Cs = np.median(out[hfront & (hz > -0.036) & (hz < -0.028) & (np.abs(X) < 0.04)], 0)
    Ch = np.median(out[hfront & (hz > 0.006) & (hz < 0.020) & (np.abs(X) < 0.04)], 0)
    tg = ss(hz, -0.005, 0.002)[..., None]                               # skin up to 5 mm under the hair's edge, then the roots
    # the skin below the band, carried up into it in the front view (x, z on a 0.5 mm grid), so both charts get the same colour
    src = hfront & (hz > -0.045) & (hz < -0.028) & (nrm[..., 1] < -0.3)
    hgx = np.clip(((X + 0.08) / 0.0005).astype(int), 0, 319); hgz = np.clip(((Z - 0.66) / 0.0005).astype(int), 0, 279)
    hs = np.zeros((280, 320, 3)); hn = np.zeros((280, 320))
    np.add.at(hs, (hgz[src], hgx[src]), out[src]); np.add.at(hn, (hgz[src], hgx[src]), 1)
    Sg = ni.gaussian_filter(hs, (14, 14, 0)) / np.maximum(ni.gaussian_filter(hn, 14), 1e-9)[..., None]
    Cs = Sg[hgz, hgx]
    gc = Cs * (1 - tg) + Ch * tg
    l9 = out.mean(2, keepdims=True); d9 = np.clip(l9 / (ni.gaussian_filter(l9, (1.5, 1.5, 0)) + 1), 0.97, 1.03)
    hw = (hfront * ss(hz, -0.031, -0.026) * (1 - ss(hz, 0.005, 0.009)))[..., None]   # the scalp chart's teeth reach 2.4 cm under the edge
    out = out * (1 - hw) + gc * d9 * hw
    print(t, 'hairline band', int((hw[..., 0] > 0.5).sum()), 'hair root', Ch.round(0).tolist())
    # r25 earlobes (coordinator: dark specks beside the jaw in front views): the head side under the hair, where the lobe stubs poke out,
    # was painted a darker orange-brown; it takes the jaw's skin with its own fine detail
    ax_ = np.abs(X)
    sidew = SKIN * np.clip((ax_ - 0.054) / 0.008, 0, 1) * np.clip((Y + 0.040) / 0.010, 0, 1) * np.clip((0.035 - Y) / 0.01, 0, 1) \
        * np.clip((Z - 0.590) / 0.008, 0, 1) * np.clip((0.695 - Z) / 0.008, 0, 1)
    jaw = SKIN & (ax_ > 0.045) & (ax_ < 0.058) & (Y < -0.03) & (Z > 0.60) & (Z < 0.66)
    jc = np.median(out[jaw], 0)
    l7 = out.mean(2, keepdims=True); d7 = np.clip(l7 / (ni.gaussian_filter(l7, (3, 3, 0)) + 1), 0.95, 1.05)
    sw7 = sidew[..., None]
    out = out * (1 - sw7) + jc * d7 * sw7
    print(t, 'head side under the hair', int((sidew > 0.5).sum()), 'jaw skin', jc.round(0).tolist())
    out = chart_pad(out)
    Image.fromarray(np.clip(out, 0, 255).astype('u1')).save(f'textures/pg_head_{t}_fix.png')
    FLAT = np.maximum(FLAT, np.maximum(fix, under).astype(np.float32))
    print(t, 'nose skin', nskin.round(0), 'tip', int(ntip.sum()), 'dark', int(dark.sum()), 'light', int(light.sum()))
FLAT = np.maximum(FLAT, (cov & ~HAIR & (Z < 0.5703 + 0.02)).astype(np.float32))
FLAT = ni.gaussian_filter(ni.binary_dilation(FLAT > 0.5, iterations=2).astype(np.float32), 1.5)
# the whole face skin: Meshy's normal map drew light ridges up the bridge and down the chin's midline in the viewer (its relief is not the
# geometry's); the skin keeps 15 % of it
FLAT = np.maximum(FLAT, 0.85 * ni.gaussian_filter(SKIN.astype(np.float32), 2.0))
for t in sys.argv[1:]:
    NM = np.asarray(Image.open(f'textures/pg_head_{t}_normal.png').convert('RGB'), np.float32)
    F_ = ni.zoom(FLAT, NM.shape[0] / FLAT.shape[0], order=1)[..., None] if NM.shape[0] != FLAT.shape[0] else FLAT[..., None]
    Image.fromarray(np.clip(NM * (1 - F_) + np.array([128, 128, 255.]) * F_, 0, 255).astype('u1')).save(f'textures/pg_head_{t}_normal_fix.png')
print('HEADFIX2')
