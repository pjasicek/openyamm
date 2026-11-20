#!/usr/bin/env python3
"""Paint fixes for the r27 head repaint (fresh 4K Meshy paint on the final mouth geometry; the coordinator: re-apply only the paint fixes,
no geometry moves after the paint). textures/pg_head_<t>_sym.png -> pg_head_<t>_fix.png, _normal.png -> _normal_fix.png
(work/headmap_final.npz from headmap_final_pg.py: the layout of work/uv.npz on the final, painted geometry).
- Nostrils: the nose underside takes the nose's own skin with two small soft nostril shadows on the geometry's openings; the down-facing
  underside is lifted against the top light.
- Neck: the head's neck within 2.5 cm of the level seam blends to the tier's ramped body skin (textures/body_neck.json from tiers_pg.py).
- Hairline: the band under the hair's front edge (face chart / scalp chart border) takes the skin carried up from below and the hair-root
  colour in the last 5 mm, so the charts' triangle border does not show.
- Seam halos (3 px along chart borders) and thin pale lines (white top-hat, under ~4 px) on the skin, as for the r24 paint.
- Normal map flattened on the face skin (85 %), the nose underside and the neck; gutters padded per UV chart.
Args: <tier> [<tier>...]. Project folder."""
import sys, json, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ni
H = np.load('work/headmap_final.npz'); pos, nrm, face, cov = H['pos'], H['nrm'], H['face'], H['cov']
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
under = SKIN & (np.abs(X) < 0.017) & (Z > 0.6345) & (Z < 0.646) & (Y < -0.104) & ((nrm[..., 2] < -0.35) | (nrm[..., 1] > -0.5))   # underside and the nostril cavity walls
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
    # ---- neck blend to the body skin at the seam
    if t in BODY_NECK:
        nb = SKIN & (Z < 0.5703 + 0.025); nwt = ((1 - ss(Z, 0.5703, 0.5703 + 0.025)) * nb)[..., None]
        bc = np.array(BODY_NECK[t]); l3 = out.mean(2, keepdims=True); lb3 = ni.gaussian_filter(l3, (8, 8, 0)) + 1
        out = out * (1 - nwt) + bc * np.clip(l3 / lb3, 0.94, 1.05) * nwt
    # ---- the nose underside faces down: the viewer's top light shades it into a brown triangle under the tip; its paint (not the two
    # nostril shadows) is lifted up to 1.6x by how much it faces down
    dn = under & (sh < 0.35) & (nrm[..., 2] < -0.4)      # r28: only the truly down-facing underside (a pale rectangle on the philtrum top)
    gl = ni.gaussian_filter(np.where(dn, 1 + 0.6 * np.clip(-nrm[..., 2], 0, 1), 1.0), 2.0)
    gl = np.minimum(gl, 250.0 / np.maximum(out.max(2), 1))      # hue kept
    out = out * gl[..., None]
    # (r27: Meshy's fresh paint drew pale strands across the forehead and fringe again; the same two r24 clean-ups)
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
    lines = SKIN & (th > 4) & ~ni.binary_dilation(EYE, iterations=4) & ~((np.abs(X) < 0.03) & (Z > 0.612) & (Z < 0.640) & (Y < -0.09))   # not the lips
    lines = ni.binary_dilation(lines, iterations=1) & SKIN
    op = np.stack([ni.grey_opening(out[..., c], size=(5, 5)) for c in range(3)], -1)
    out[lines] = 0.3 * out[lines] + 0.7 * np.maximum(op[lines], 0)
    # ---- r28 (user review r27, g2: "fix this patch please - on the upper lip": a pale, blurry, roughly rectangular patch between the nose
    # and the mouth with hard side edges at the mouth corners; the unlit render shows it in Meshy's paint, a whitish band over the upper
    # lip with a duller philtrum, the clay render shows nothing): the r26 muzzle fill, on this paint. The lips (rosy: red hue, saturation
    # over 0.30, closed and filled) keep their paint; everything else in the ellipse takes the cheeks' tone.
    lipm = SKIN & (np.abs(X) < 0.032) & (Z > 0.612) & (Z < 0.636) & (Y < -0.095)
    hsv = np.asarray(Image.fromarray(np.clip(out, 0, 255).astype('u1')).convert('HSV'), np.float32) / 255
    lips = lipm & (((hsv[..., 0] * 360 < 15) | (hsv[..., 0] * 360 > 335)) & (hsv[..., 1] > 0.30))
    lipsf = ni.binary_fill_holes(ni.binary_closing(lips, iterations=3)) & lipm
    inner = np.zeros(cov.shape, bool)
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
    print(t, 'r28 muzzle texels', int(ell.sum()), 'lips', int(lipsf.sum()))
    # the whitish band over the upper lip (Meshy painted the former slit pocket's faces, now on the lip line, pale, with notched ends at the
    # corners): texels on the front between the line and 7 mm above it, lighter than the front-view colour field round them, take that
    # field (built from the not-pale texels, 1.5 mm blur, holes filled from their neighbours), with the paint's fine detail
    bandz = SKIN & (np.abs(X) < 0.027) & (Z > 0.6262) & (Z < 0.6345) & (Y < -0.10)
    gx2 = np.clip(((X + 0.08) / 0.0005).astype(int), 0, 319); gz2 = np.clip(((Z - 0.55) / 0.0005).astype(int), 0, 279)
    fr2 = SKIN & (Y < -0.06) & (nrm[..., 1] < -0.2)
    def field(okm, sg):
        a = np.zeros((280, 320, 3)); n = np.zeros((280, 320))
        np.add.at(a, (gz2[okm], gx2[okm]), out[okm]); np.add.at(n, (gz2[okm], gx2[okm]), 1)
        return ni.gaussian_filter(a, (sg, sg, 0)) / np.maximum(ni.gaussian_filter(n, sg), 1e-9)[..., None]
    F1 = field(fr2 & ~bandz, 6)[gz2, gx2]
    pale = bandz & (out.mean(2) > 1.04 * F1.mean(2))
    pale = ni.binary_dilation(pale, iterations=2) & bandz
    F2 = field(fr2 & ~pale, 3)[gz2, gx2]
    l10 = out.mean(2, keepdims=True); d10 = np.clip(l10 / (ni.gaussian_filter(l10, (1.5, 1.5, 0)) + 1), 0.97, 1.03)
    pw = (ni.gaussian_filter(pale.astype(np.float32), 1.5) * bandz)[..., None]
    out = out * (1 - pw) + F2 * d10 * pw
    print(t, 'upper lip pale band texels', int(pale.sum()))
    # under the lower lip: fine vertical grey streaks (Meshy's paint on the faces the r26 sculpt brought forward) take the colour field
    # round them, without the paint's fine detail; the lower lip (rosy, as above) is kept
    hsv4 = np.asarray(Image.fromarray(np.clip(out, 0, 255).astype('u1')).convert('HSV'), np.float32) / 255
    rosy = (((hsv4[..., 0] * 360 < 12) | (hsv4[..., 0] * 360 > 335)) & (hsv4[..., 1] > 0.38))
    rosy = ni.binary_closing(rosy, iterations=2)
    under_lip = SKIN & (np.abs(X) < 0.025) & (Z > 0.6085) & (Z < 0.6235) & (Y < -0.10) & ~ni.binary_dilation(rosy & (Z > 0.617), iterations=2)
    F3 = field(fr2 & ~under_lip, 4)[gz2, gx2]
    uw = (ni.gaussian_filter(under_lip.astype(np.float32), 2.0) * under_lip)[..., None]
    out = out * (1 - uw) + F3 * uw
    print(t, 'under-lip streak texels', int(under_lip.sum()))
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
    out = chart_pad(out)
    Image.fromarray(np.clip(out, 0, 255).astype('u1')).save(f'textures/pg_head_{t}_fix.png')
    FLAT = np.maximum(FLAT, under.astype(np.float32))
    print(t, 'nose skin', nskin.round(0))
FLAT = np.maximum(FLAT, (cov & ~HAIR & (Z < 0.5703 + 0.02)).astype(np.float32))
FLAT = ni.gaussian_filter(ni.binary_dilation(FLAT > 0.5, iterations=2).astype(np.float32), 1.5)
# the whole face skin: Meshy's normal map drew light ridges up the bridge and down the chin's midline in the viewer (its relief is not the
# geometry's); the skin keeps 15 % of it
FLAT = np.maximum(FLAT, 0.85 * ni.gaussian_filter(SKIN.astype(np.float32), 2.0))
for t in sys.argv[1:]:
    NM = np.asarray(Image.open(f'textures/pg_head_{t}_normal.png').convert('RGB'), np.float32)
    F_ = ni.zoom(FLAT, NM.shape[0] / FLAT.shape[0], order=1)[..., None] if NM.shape[0] != FLAT.shape[0] else FLAT[..., None]
    Image.fromarray(np.clip(NM * (1 - F_) + np.array([128, 128, 255.]) * F_, 0, 255).astype('u1')).save(f'textures/pg_head_{t}_normal_fix.png')
print('HEADFIX3')
