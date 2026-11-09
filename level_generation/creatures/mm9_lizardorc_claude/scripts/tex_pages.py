"""Final body pages and head. Body: 4K paint graded at 4K, charts copied 1:1 (no resample) to two 2K pages (repage.py); normal and ORM copied the same way, then 1K. Head: level per class, the neck band fades into the body's own paint mirrored across the ring, so colour and scale pattern carry across. Region masks and ramps as tex_final.py. Project folder."""
import sys, json, numpy as np
from pathlib import Path
from PIL import Image
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
sys.path.insert(0, 'scripts'); sys.path.insert(0, '../claude_shared')
import rast, region_variants as RV, headfr as H
from classes import classes, hsv
Image.MAX_IMAGE_PIXELS = None
T = Path('textures'); S = 2048; C = 4
J = np.load('work/joined.npz'); U = np.load('work/uv.npz'); Pg = np.load('work/pages.npz', allow_pickle=True); co, part = J['co'], J['part']
ub2, page, own, moves, masks = Pg['ub2'], Pg['page'], Pg['own'], Pg['moves'], Pg['masks']
def srgb(p): return np.asarray(Image.open(p).convert('RGB'), np.float32) / 255
def save(a, p): Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype(np.uint8)).save(p)
def lin(c): return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)
def enc(c): c = np.clip(c, 0, 1); return np.where(c <= .0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - .055)
def pad(img, cov):
    _, (iy, ix) = ndi.distance_transform_edt(~cov, return_indices=True); return img[iy, ix]
def paste(src, ch):
    out = [np.zeros((S, S, ch), np.uint8) for _ in range(2)]; cov = [np.zeros((S, S), bool) for _ in range(2)]
    for c, p, dy, dx, my, mx, gh, gw in moves:
        g = masks[c]
        for gy, gx in np.argwhere(g):
            y0 = (my + gy) * C; x0 = (mx + gx) * C; yd, xd = y0 + dy, x0 + dx
            out[p][yd:yd + C, xd:xd + C] = src[y0:y0 + C, x0:x0 + C]; cov[p][yd:yd + C, xd:xd + C] = True
    return [pad(o, c_) for o, c_ in zip(out, cov)], cov
g4 = np.asarray(Image.open(T / 'body4k_basecolor_graded.png').convert('RGB'))
col, cov = paste(g4, 3)
nm4 = np.asarray(Image.open('meshy/retex_body/texture_urls_0_normal.png').convert('RGB').resize((4096, 4096), Image.BILINEAR)); nrm, _ = paste(nm4, 3)
ro4 = np.asarray(Image.open('meshy/retex_body/texture_urls_0_roughness.png').convert('L').resize((4096, 4096), Image.BILINEAR))[..., None]; ro, _ = paste(ro4, 1)
ao4 = np.asarray(Image.open(T / 'body_ao_2k.png').convert('L').resize((4096, 4096), Image.BILINEAR))[..., None]; ao, _ = paste(ao4, 1)
body = [c.astype(np.float32) / 255 for c in col]
for p in range(2):
    Image.fromarray(nrm[p]).resize((1024, 1024), Image.LANCZOS).save(T / f'body{p}_normal_1k.png')
    r = np.maximum(ro[p][..., 0].astype(np.float32) / 255, .5); o = Image.fromarray(ao[p][..., 0]).resize((1024, 1024), Image.LANCZOS); r = Image.fromarray((r * 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS)
    Image.merge('RGB', [o, r, Image.new('L', (1024, 1024), 0)]).save(T / f'body{p}_metal_rough_1k.png')
# rasters
Fp = []; Pp = []; Mp = []; fid = []
for p in range(2):
    ids = np.where(own & (page == p))[0]; F, B = rast.raster(ub2[ids], S); Q, m = rast.positions(F, B, co[U['ob'][ids]]); Fp.append(F); Pp.append(Q); Mp.append(m); fid.append(ids)
Fh, Bh = rast.raster(U['uh'], S); Ph, mh = rast.positions(Fh, Bh, co[U['oh']])
ph = np.full((S, S), -1, np.int32); ph[mh] = part[U['oh']].max(1)[Fh[mh]]
Bhead = srgb(T / 'head_basecolor_graded.png')
hb = np.vstack([b[m] for b, m in zip(body, Mp)]); hib, stb, *_ = classes(hb); hih, sth, *_ = classes(Bhead); hih &= mh; sth &= mh
gain_h = lin(hb[hib]).mean(0) / lin(Bhead[hih]).mean(0); gain_s = lin(hb[stb]).mean(0) / lin(Bhead[sth]).mean(0)
print('class gain', gain_h.round(2), gain_s.round(2))
sf = lambda m: np.clip(ndi.gaussian_filter(m.astype(np.float32), 2.) * 1.1, 0, 1)[..., None]
kg = .75; Bl = lin(Bhead); Bl = Bl * (1 + sf(hih) * (gain_h ** kg - 1)); Bl = Bl * (1 + sf(sth) * (gain_s ** kg - 1)); head = enc(Bl)
# neck band: head paint fades into the body's paint mirrored across the ring
ring = co[J['ringcopy']]; cen = ring.mean(0); n = H.PLANE_N; v_ = np.cross(n, [1., 0, 0]); tree = cKDTree(ring)
def th(Pq): q = Pq - cen; return np.arctan2(q @ v_, np.abs(q[:, 0]))
pts = []; cols = []
for p in range(2):
    m = Mp[p].copy(); m[Mp[p]] &= part[U['ob'][fid[p]]].max(1)[Fp[p][Mp[p]]] == 0
    d = tree.query(Pp[p][m])[0]; k = d < .13
    pts.append(np.c_[th(Pp[p][m][k]) * .12, d[k]]); cols.append(body[p][m][k])
pts = np.vstack(pts); cols = np.vstack(cols); tb = cKDTree(pts)
band = mh & (ph == 1); dh = np.full((S, S), 9., np.float32); dh[band] = tree.query(Ph[band])[0]
above = np.zeros((S, S), bool); above[band] = ((Ph[band] - H.PLANE_P) @ n) < .13
sel = band & (dh < .115) & above
Q = np.c_[th(Ph[sel]) * .12, dh[sel] * .7]; dd, nn = tb.query(Q, k=12)
# run 2: one nearest body texel per head texel repeated each body texel along the band's length (vertical streaks under the jaw, the pale
# patch seen from below in Hit2): the mean of the 12 nearest, weighted by inverse distance
iw = 1 / np.maximum(dd, 1e-4); iw /= iw.sum(1, keepdims=True); cm = np.einsum('nk,nkc->nc', iw, lin(cols[nn])); dd = dd[:, 0]
x = np.clip(dh[sel] / .115, 0, 1); w = (1 - x * x * (3 - 2 * x))[:, None]
head2 = head.copy(); head2[sel] = enc(lin(head[sel]) * (1 - w) + cm * w)
print('neck texels', int(sel.sum()), 'lookup max', round(float(dd.max()), 3))
# run 2, pale streaks under the chin: the long fan triangles of the throat (join_liz.py) smear their texels into streaks. Their texels take the mean
# colour of the head's other texels within 1.5 cm in 3D, so they read as smooth hide.
fo_ = U['oh']; jk_ = J['jawk']; P3 = co[fo_]; cf = P3.mean(1); e_ = np.linalg.norm(P3[:, [1, 2, 0]] - P3, axis=2); ar_ = np.linalg.norm(np.cross(P3[:, 1] - P3[:, 0], P3[:, 2] - P3[:, 0]), axis=1) / 2
elong = e_.max(1) ** 2 / np.maximum(2 * ar_, 1e-9)
zf = (np.abs(cf[:, 0]) < .10) & (cf[:, 1] > .55) & (cf[:, 1] < .665) & (cf[:, 2] > .05) & (cf[:, 2] < .21) & (elong > 4) & (jk_[fo_].min(1) < .9)     # the throat behind the jaw, with the folded fan at the back of the jaw underside (jaw weight up to .82)
hh_, ss_, _ = hsv(head2); sl = mh & zf[np.maximum(Fh, 0)]; near_ = mh & ~sl & (np.abs(Ph[..., 0]) < .16) & (Ph[..., 1] > .52) & (Ph[..., 1] < .70) & (Ph[..., 2] > .0) & (hh_ > 40) & (hh_ < 160)      # hide only: no mouth red
# (a flat median colour there kept the slivers' streaky relief in the normal map and read as a pale square from below, coordinator on r16 mouth
# Hit2): the slivers instead take the body throat's own scale paint just above the plate, front-projected and mirror-tiled in height, blended
# over 4 texels at the edges, and their relief is flattened.
import plate_fix as _pf
_pv = []
for p in range(2):
    a = np.full(Mp[p].shape, -1, np.int32); a[Mp[p]] = part[U['ob'][fid[p]]].max(1)[Fp[p][Mp[p]]]; _pv.append(a)
_gt = _pf.grid(body, Pp, [(_pv[p] >= 0) & (_pv[p] != 11) & (Pp[p][..., 2] > 0) for p in range(2)])
_w = np.clip(ndi.gaussian_filter(sl.astype(np.float32), 2.) * 1.6, 0, 1) * mh
_k = _w > .01; _q = Ph[_k]; _ys = .535 + np.abs(((_q[:, 1] - .535) / .06 + 1) % 2 - 1) * .06
_gtb = ndi.gaussian_filter(_gt, (9, 9, 0))      # low-passed: a sliver smears each texel along its length, so the scale detail would come back as streaks
head2[_k] = head2[_k] * (1 - _w[_k, None]) + _pf.look(_gtb, np.minimum(np.abs(_q[:, 0]), .05), _ys) * _w[_k, None]
_src = T / 'head_normal_1k_src.png'
if not _src.exists(): Image.open(T / 'head_normal_1k.png').save(_src)
_n = np.asarray(Image.open(_src).convert('RGB'), np.float32); _wn = np.asarray(Image.fromarray((_w * 255).astype(np.uint8)).resize(_n.shape[:2][::-1], Image.BILINEAR), np.float32)[..., None] / 255
Image.fromarray((_n * (1 - _wn) + np.array([128, 128, 255.]) * _wn).astype(np.uint8)).save(T / 'head_normal_1k.png')
print('throat sliver faces', int(zf.sum()), 'texels', int(sl.sum()), 'blended', int(_k.sum()))
# run 2, third request: jaw underside and throat from one paint source (throat_paint.py); strip and chin faces in their own cells
import os, throat_paint as TP
_us, _uch, _cf = TP.cells(J); _cuv = np.vstack([_us, _uch]); Fc, Bc = rast.raster(_cuv, S); Pc, mc = rast.positions(Fc, Bc, co[_cf]); mc &= ~mh
def _fn(F_, faces, m_):
    q = co[faces]; n_ = np.cross(q[:, 1] - q[:, 0], q[:, 2] - q[:, 0]); n_ /= np.maximum(np.linalg.norm(n_, axis=1, keepdims=True), 1e-12)
    N_ = np.zeros((S, S, 3), np.float32); N_[m_] = n_[F_[m_]]; return N_
Nh = _fn(Fh, U['oh'], mh); Nc = _fn(Fc, _cf, mc)
# cell texels first take the paint round them by 3D position (head skin and body hide, inverse-distance mean of 8)
_src_p = np.vstack([Ph[mh & (ph == 1)]] + [Pp[p][Mp[p]] for p in range(2)]); _src_c = np.vstack([head2[mh & (ph == 1)]] + [body[p][Mp[p]] for p in range(2)])
_d, _i = cKDTree(_src_p).query(Pc[mc], k=8); _w = 1 / np.maximum(_d, 1e-4); _w /= _w.sum(1, keepdims=True); head2[mc] = np.einsum('nk,nkc->nc', _w, _src_c[_i])
PhA = np.where(mc[..., None], Pc, Ph); mA = mh | mc; NA = np.where(mc[..., None], Nc, Nh)
phA = np.where(mc, 1, ph)
surfs = [dict(img=head2, P=PhA, N=NA, m=mA, prt=phA, paint=(phA == 1))]
for p in range(2):
    pv_ = np.full((S, S), -1, np.int32); pv_[Mp[p]] = part[U['ob'][fid[p]]].max(1)[Fp[p][Mp[p]]]
    _N = np.zeros((S, S, 3), np.float32); q = co[U['ob'][fid[p]]]; n_ = np.cross(q[:, 1] - q[:, 0], q[:, 2] - q[:, 0]); n_ /= np.maximum(np.linalg.norm(n_, axis=1, keepdims=True), 1e-12); _N[Mp[p]] = n_[Fp[p][Mp[p]]]
    surfs.append(dict(img=body[p], P=Pp[p], N=_N, m=Mp[p], prt=pv_, paint=np.zeros((S, S), bool)))
_mode = os.environ.get('THROAT_MODE', 'apply' if (TP.TD / 'throat_below_edit.png').exists() else 'render')
TP.use('below'); Wt = TP.run(surfs, _mode)[0]
# second view from the front for the throat just over the neck ring (edge-on from below): head texels the first view left, and the body's
# hide just under the ring (its Meshy paint smeared there); painted only where the first view did not
if _mode == 'apply' or os.environ.get('THROAT_FRONT') == 'render':
    _ring = cKDTree(co[J['ringcopy']])
    surfs[0]['prior'] = np.clip(Wt, 0, 1); surfs[0]['paint'] = (phA == 1) & (PhA[..., 1] < .655) & (PhA[..., 2] < .22)
    for k_ in (1, 2):
        s_ = surfs[k_]; dd_ = np.full((S, S), 9.); dd_[s_['m']] = _ring.query(s_['P'][s_['m']])[0]
        s_['paint'] = (s_['prt'] == 0) & (dd_ < .05) & (s_['P'][..., 2] > -.02); s_['prior'] = np.zeros((S, S), np.float32)
    TP.use('front'); _m2 = 'render' if os.environ.get('THROAT_FRONT') == 'render' or not (TP.TD / 'throat_front_edit.png').exists() else 'apply'
    W2 = TP.run(surfs, _m2); Wt = np.maximum(Wt, W2[0]) if _m2 == 'apply' else Wt
    if _m2 == 'apply':
        for k_ in (1, 2): Wf_body = W2[k_]          # body pages: relief faded below with plate_fix weights
        _W2b = [W2[1], W2[2]]
    TP.use('below')
# the cells: pad each cell square with its nearest painted texel (no bleed at mip levels)
_cellsq = np.zeros((S, S), bool)
for x0, y0, x1, y1 in TP.FREE: _cellsq[y0:y1, x0:x1] = True
_, (_a, _b) = ndi.distance_transform_edt(~mc, return_indices=True); _fill = _cellsq & ~mc & ~mh; head2[_fill] = head2[_a[_fill], _b[_fill]]
if _mode == 'apply':
    _nm = np.asarray(Image.open(T / 'head_normal_1k.png').convert('RGB'), np.float32) / 255 * 2 - 1; _ln = TP.lum_normal(head2)
    _wt = np.maximum(Wt, (mc | _fill).astype(np.float32)); _w1 = np.asarray(Image.fromarray((np.clip(_wt, 0, 1) * 255).astype(np.uint8)).resize((1024, 1024), Image.BILINEAR), np.float32)[..., None] / 255
    _n2 = _nm * (1 - _w1) + _ln * _w1; _n2 /= np.maximum(np.linalg.norm(_n2, axis=2, keepdims=True), 1e-6)
    Image.fromarray(((_n2 * .5 + .5) * 255 + .5).astype(np.uint8)).save(T / 'head_normal_1k.png')
mh = mh | mc | _fill; ph = np.where(mc | _fill, 1, ph)
import plate_fix
Wf = plate_fix.apply(body, Pp, Mp, Fp, fid, U['ob'], part)
for p in range(2):
    n_ = np.asarray(Image.open(T / f'body{p}_normal_1k.png').convert('RGB'), np.float32); w_ = np.asarray(Image.fromarray((Wf[p] * 255).astype(np.uint8)).resize((1024, 1024), Image.BILINEAR), np.float32)[..., None] / 255 * .75
    Image.fromarray((n_ * (1 - w_) + np.array([128, 128, 255.]) * w_).astype(np.uint8)).save(T / f'body{p}_normal_1k.png')
if '_W2b' in globals():      # body texels repainted by the front view: relief from the new paint
    for p in range(2):
        _n = np.asarray(Image.open(T / f'body{p}_normal_1k.png').convert('RGB'), np.float32) / 255 * 2 - 1; _l = TP.lum_normal(body[p])
        _w = np.asarray(Image.fromarray((np.clip(_W2b[p], 0, 1) * 255).astype(np.uint8)).resize((1024, 1024), Image.BILINEAR), np.float32)[..., None] / 255
        _n = _n * (1 - _w) + _l * _w; _n /= np.maximum(np.linalg.norm(_n, axis=2, keepdims=True), 1e-6)
        Image.fromarray(((_n * .5 + .5) * 255 + .5).astype(np.uint8)).save(T / f'body{p}_normal_1k.png')
for p in range(2): save(body[p], T / f'body{p}_final.png')
save(head2, T / 'head_final.png')
def soft(m, s=1.2): return np.clip(ndi.gaussian_filter(m.astype(np.float32), s) * 1.1, 0, 1)
def regions(img, cv, out=None):
    hi, st, le, hh, sa, va = classes(img); claw = (hh > 28) & (hh < 62) & (sa > .10) & (sa < .42) & (va > .42); st = st & ~claw
    if out is not None: hi = hi & ~out; st = st & ~out; le = le & ~out
    return [pad(soft(ndi.binary_closing(m & cv, iterations=1)), cv) for m in (hi, st, le)]
def rotate(rgb, deg, sat=1., val=1.):
    hh, ss, vv = hsv(rgb); hh = (hh + deg) % 360; ss = np.clip(ss * sat, 0, 1); vv = vv * val
    c = vv * ss; x = c * (1 - np.abs(((hh / 60) % 2) - 1)); m = vv - c; i = (hh // 60).astype(int) % 6; z = np.zeros_like(c)
    r = np.choose(i, [c, x, z, z, x, c]); g = np.choose(i, [x, c, c, x, z, z]); b = np.choose(i, [z, z, x, c, c, x]); return np.stack([r + m, g + m, b + m], -1)
def tint(rgb, c_, val): L = rgb @ np.array([.2126, .7152, .0722]); return np.clip(L[..., None] * np.array(c_) * val, 0, 1)
TIERS = {'liz_b': dict(hide=(62, .9, .78), steel=((.72, .78, .92), .72), lea=(-12, .9, .7)), 'liz_c': dict(hide=(-52, 1.05, .92), steel=((1.05, .86, .58), .9), lea=(200, .75, .75))}
VS = ['liz_a', 'liz_b', 'liz_c']; mats = []
out_h = np.isin(ph, [3, 4, 7]) | (ph == -1); hu, sa, va = hsv(head2); red = ((hu < 28) | (hu > 335)) & (sa > .45)
rh = regions(head2, mh, out_h | red); rh[2] = np.zeros_like(rh[2])
for base, r_, prefix, mask in ((body[0], regions(body[0], cov[0]), 'Liz', 'liz_body0_mask.png'), (body[1], regions(body[1], cov[1]), 'LizB', 'liz_body1_mask.png'), (head2, rh, 'LizHead', 'liz_head_mask.png')):
    RV.write_mask(r_, T / mask, 1024); ramps = {v: [] for v in VS}
    for reg, w_ in zip(('hide', 'steel', 'lea'), r_):
        if w_.max() < .01: continue
        tg = {'liz_a': base}
        for v, t in TIERS.items(): tg[v] = tint(base, *t['steel']) if reg == 'steel' else rotate(base, *t[reg])
        rp, err = RV.fit_ramps(base, tg, w_)
        for v in VS: ramps[v].append(rp[v])
    mats.append({'base': prefix, 'prefix': prefix, 'mask': mask, 'ramps': ramps})
json.dump({'variants': VS, 'materials': mats}, open(T / 'liz_ramps.json', 'w')); print('RAMPS written')
# chest plate: where its hide starts, per |x|
