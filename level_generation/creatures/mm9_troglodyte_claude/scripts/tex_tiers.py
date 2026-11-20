"""Masks and ramps for tier A on the shared B set; tier C's head image and final images. Project folder. Needs tex_pipeline.py output."""
import sys, json, numpy as np
from pathlib import Path
from PIL import Image
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
sys.path.insert(0, 'scripts'); sys.path.insert(0, '../claude_shared')
import rast, region_variants as RV
T = Path('textures'); S = 2048
J = np.load('work/joined.npz'); U = np.load('work/uv.npz'); R = np.load('work/rasters.npz'); X = np.load('work/head_c_transfer.npz'); Pl = np.load('work/pools.npz')
co, part = J['co'], J['part']
def srgb(p): return np.asarray(Image.open(p).convert('RGB'), np.float32) / 255
def lin(c): return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)
def enc(c): c = np.clip(c, 0, 1); return np.where(c <= .0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - .055)
def save(a, p): Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype(np.uint8)).save(p)
def hsv(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0); r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360, sat, mx
def pad(img, cov):
    _, (iy, ix) = ndi.distance_transform_edt(~cov, return_indices=True); return img[iy, ix]
def soft(m, s=1.2): return np.clip(ndi.gaussian_filter(m.astype(np.float32), s) * 1.15, 0, 1)
Fb, Bb, Fh, Bh = R['Fb'], R['Bb'], R['Fh'], R['Bh']
Pb, mb = rast.positions(Fb, Bb, co[U['ob']]); Ph, mh = rast.positions(Fh, Bh, co[U['oh']])
ph = np.full((S, S), -1, np.int32); ph[mh] = part[U['oh']].max(1)[Fh[mh]]
Lw = np.array([.2126, .7152, .0722])
def rank(base_lum, core, pool):
    pl = lin(pool) @ Lw; pool = pool[np.argsort(pl)]
    # smooth so each level keeps one hue
    k = max(len(pool) // 40, 1); pool = np.stack([np.convolve(pool[:, c], np.ones(k) / k, mode='same') for c in range(3)], 1)[k:-k]
    o = np.argsort(base_lum[core]); out = np.zeros((core.sum(), 3), np.float32); out[o] = pool[(np.linspace(0, 1, core.sum()) * (len(pool) - 1)).astype(int)]
    return out
def softcap(c, t=.17, k=.4):
    '''pale throat and jaw: linear luminance over t is compressed, or the big chin glares against MM9's dark shelf'''
    l = lin(c); L = l @ Lw; L2 = np.where(L > t, t + (L - t) * k, L); return enc(l * (L2 / np.maximum(L, 1e-5))[..., None])
# ---- the skin pulled out to the neck ring has a smeared paint: low frequencies kept, the detail from a clean patch of the same atlas (same texel density)
def unsmear(img):
    up_ = J['co_up']; a3 = lambda P: np.linalg.norm(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]), axis=1)
    r = np.sqrt(a3(co[U['ob']]) / np.maximum(a3(up_[U['ob']]), 1e-9))
    rv = np.zeros((S, S), np.float32); rv[mb] = r[Fb[mb]]
    ring = co[J['ringcopy']]; d = np.full((S, S), 9., np.float32); d[mb] = cKDTree(ring).query(Pb[mb])[0]
    m = (rv > 1.55) & (d < .3)
    w = np.clip(ndi.gaussian_filter(m.astype(np.float32), 6) * 1.6, 0, 1) * mb
    # the largest clean square in the atlas
    clean = ndi.binary_erosion(mb & ~ndi.binary_dilation(m, iterations=8), iterations=4); dt = ndi.distance_transform_edt(clean); y, x = np.unravel_index(dt.argmax(), dt.shape); R = int(min(dt.max() * .7, 150))
    hp = img - np.stack([ndi.gaussian_filter(img[..., c], 7) for c in range(3)], -1)
    patch = hp[y - R:y + R, x - R:x + R]; tile = np.block([[patch[..., 0], patch[:, ::-1, 0]], [patch[::-1, :, 0], patch[::-1, ::-1, 0]]])
    tiles = np.stack([np.block([[patch[..., c], patch[:, ::-1, c]], [patch[::-1, :, c], patch[::-1, ::-1, c]]]) for c in range(3)], -1)
    ty, tx = np.mgrid[0:S, 0:S]; det = tiles[ty % tiles.shape[0], tx % tiles.shape[1]]
    lo = np.stack([ndi.gaussian_filter(img[..., c], 7) for c in range(3)], -1)
    print('unsmear texels', int(m.sum()), 'patch', x, y, R)
    return img * (1 - w[..., None]) + np.clip(lo + det, 0, 1) * w[..., None], w
# ---- body regions on the B image
Bb_0 = srgb(T / 'body_b_final.png'); Bb_, wsm = unsmear(Bb_0); save(Bb_, T / 'body_b_final2.png'); h, s, v = hsv(Bb_)
fg = json.load(open('work/fingers.json')); tips = np.array([fg[f][3] for f in fg]); tips = np.vstack([tips, tips * [-1, 1, 1]])
d_tip = np.full((S, S), 9., np.float32); d_tip[mb] = cKDTree(tips).query(Pb[mb])[0]
feet = np.zeros((S, S), bool); feet[mb] = Pb[mb][:, 1] < -.5
band = (h > 15) & (h < 45) & (s > .3) & (v < .38) & (np.abs(d_tip - .4) < .3) & False
from_ankle = np.full((S, S), 0., np.float32)
Fi = json.load(open('work/fit.json'))['tgt']; an = np.array(Fi['an']); from_ankle[mb] = np.linalg.norm(np.c_[np.abs(Pb[mb][:, 0]), Pb[mb][:, 1:]] - an, axis=1)
claw = ((d_tip < .06) | (feet & (from_ankle > .30) & (h > 8) & (h < 42) & (s > .4))) & mb & (s > .3)
# only on the hands' and feet's own faces: in the bind the fingertips hang beside the calf
lab = J['lab']; nb = int(J['nb']); facelab = np.array([np.bincount(lab[f[f < nb]], minlength=10).argmax() if (f < nb).any() else 0 for f in U['ob']]); fl = np.load('work/finger_labels.npy'); fl = np.r_[fl, np.zeros(len(co) - len(fl), int)]
okf = (fl[U['ob']].max(1) > 0) | (facelab == 9)
okt = np.zeros((S, S), bool); okt[mb] = okf[Fb[mb]]
claw = ndi.binary_closing(claw & okt, iterations=2) & mb
w_claw = soft(claw)
vein = np.asarray(Image.open('work/_veinb.png').convert('L'), np.float32) / 255
lab_, nl = ndi.label(vein > .35); sz = ndi.sum(vein > .35, lab_, np.arange(1, nl + 1)); keep = np.isin(lab_, 1 + np.where(sz >= 60)[0])     # ribs, not speckle
vein = vein * ndi.binary_dilation(keep, iterations=2)
vein = np.clip(ndi.gaussian_filter(vein, .7) * 1.4, 0, 1) * (1 - w_claw)
hide = np.clip(mb.astype(np.float32) - w_claw, 0, 1)
hide = pad(hide, mb); vein = pad(vein, mb); w_c = pad(w_claw, mb)
RV.write_mask([hide, vein, w_c], T / 'trog_region_mask.png')
lb = RV.luminance(Bb_); core = (hide > .9) & mb
ta = Bb_.copy(); ta[core] = rank(lb, core, enc(np.clip(lin(Pl['hide']) * np.array([1.05, .92, 1.6]) * 1.5, 0, 1))); fit_h, r1 = RV.fit_ramps(Bb_, {'trog_a': ta, 'trog_b': Bb_, 'trog_c': Bb_}, hide)
tv = Bb_.copy(); c2 = (vein > .8) & mb
if c2.sum() > 200:
    tv[c2] = rank(lb, c2, enc(np.clip(lin(Pl['vein']) * np.array([.95, .95, 1.15]), 0, 1)))
fit_v, r2 = RV.fit_ramps(Bb_, {'trog_a': tv, 'trog_b': Bb_, 'trog_c': Bb_}, np.where(vein > .8, 1., 0.))
tc = Bb_.copy(); c3 = (w_c > .9) & mb
s_ = np.clip((lin(Bb_[c3]) @ Lw) / .25, 0, 1)[:, None]; tc[c3] = np.array([.05, .16, .19]) * (1 - s_) + np.array([.66, .82, .84]) * s_
fit_c, r3 = RV.fit_ramps(Bb_, {'trog_a': tc, 'trog_b': Bb_, 'trog_c': Bb_}, w_c)
print('body', r1, r2, r3)
# ---- head regions
PH = enc(np.clip(lin(Pl['hide']) * np.array([1.05, .92, 1.6]) * 2.1, 0, 1))        # the violet of MM9's skin, brighter than the master's grey lights
PV = enc(np.clip(lin(Pl['vein']) * np.array([.95, .95, 1.15]), 0, 1))
Hb = srgb(T / 'head_b_final.png'); h, s, v = hsv(Hb)
skin = mh & (ph == 1)
red = skin & ((h < 12) | (h > 340)) & (s > .45)
Phu, _ = rast.positions(Fh, Bh, J['co_up'][U['oh']])
box = (np.abs(Phu[..., 0]) < .19) & (Phu[..., 1] > -.25) & (Phu[..., 1] < .0) & (Phu[..., 2] > -.22) & (Phu[..., 2] < .3) & mh
tongue = skin & box & (h >= 7) & (h < 40) & (s > .5) & (v > .5)
print('tongue texels', int(tongue.sum()), 'box', int((box & skin).sum()))
red = ndi.binary_opening(ndi.binary_closing(red, iterations=2), iterations=1); tongue = ndi.binary_opening(tongue, iterations=2)
lining = red | tongue
teeth = mh & ((ph == 3) | (ph == 4))
eye = mh & (ph == 6)
w_l, w_t = soft(lining), soft(teeth, .8)
vh = np.asarray(Image.open('work/_veinh.png').convert('L'), np.float32) / 255
Xz = np.zeros((S, S), np.float32); Xz[mh] = Ph[mh][:, 1]
dome = np.clip((Xz - .30) / .05, 0, 1) * (ph == 1)
lab_, nl = ndi.label(vh > .35); sz = ndi.sum(vh > .35, lab_, np.arange(1, nl + 1)); keep = np.isin(lab_, 1 + np.where(sz >= 60)[0])
vh = vh * ndi.binary_dilation(keep, iterations=2)
vh = np.clip(ndi.gaussian_filter(vh, .7) * 1.4, 0, 1) * dome * (1 - w_l)
vh = np.maximum(vh, soft(eye, .8))       # tier A is blind: a milky patch of the rib colour where the others have eyes
hideh = np.clip((skin).astype(np.float32) - w_l, 0, 1)
hideh, vh, w_l2, w_t2 = pad(hideh, mh), pad(vh, mh), pad(w_l, mh), pad(w_t, mh)
RV.write_mask([hideh, vh, w_l2, w_t2], T / 'trog_head_region_mask.png')
lh = RV.luminance(Hb); core = (hideh > .9) & mh
ta = Hb.copy(); ta[core] = softcap(rank(lh, core, PH), .2, .45); fh1, r4 = RV.fit_ramps(Hb, {'trog_a': ta, 'trog_b': Hb, 'trog_c': Hb}, hideh)
tv = Hb.copy(); c2 = (vh > .8) & mh; tv[c2] = rank(lh, c2, PV); fh2, r5 = RV.fit_ramps(Hb, {'trog_a': tv, 'trog_b': Hb, 'trog_c': Hb}, np.where(vh > .8, 1., 0.))
tl = Hb.copy(); c3 = (w_l2 > .9) & mh; s_ = np.clip((lin(Hb[c3]) @ Lw) / .5, 0, 1)[:, None] ** .8; tl[c3] = np.array([.02, .13, .17]) * (1 - s_) + np.array([.28, .72, .78]) * s_
fh3, r6 = RV.fit_ramps(Hb, {'trog_a': tl, 'trog_b': Hb, 'trog_c': Hb}, w_l2)
tt = Hb.copy(); c4 = (w_t2 > .9) & mh; s_ = np.clip((lin(Hb[c4]) @ Lw) / .7, 0, 1)[:, None]; tt[c4] = np.array([.25, .36, .42]) * (1 - s_) + np.array([.82, .92, .96]) * s_
fh4, r7 = RV.fit_ramps(Hb, {'trog_a': tt, 'trog_b': Hb, 'trog_c': Hb}, w_t2)
print('head', r4, r5, r6, r7)
ram = {'variants': ['trog_a', 'trog_b', 'trog_c'], 'materials': [
    {'base': 'Trog', 'prefix': 'Trog', 'mask': 'trog_region_mask.png', 'ramps': {k: [fit_h[k], fit_v[k], fit_c[k]] for k in ('trog_a', 'trog_b', 'trog_c')}},
    {'base': 'TrogHead', 'prefix': 'TrogHead', 'mask': 'trog_head_region_mask.png', 'ramps': {k: [fh1[k], fh2[k], fh3[k], fh4[k]] for k in ('trog_a', 'trog_b', 'trog_c')}}]}
json.dump(ram, open(T / 'trog_ramps.json', 'w'))
# ---- tier C head: hide from a rank onto the C body's own hide, leather from the transfer, mouth lining red-brown, tongue green, eyes steel
Cb = srgb(T / 'body_c_graded.png')
hb, sb, vb = hsv(Cb)
# MM9's Gnoll is dark under the leather: the hide goes down, the leather a little
leather = (hb > 8) & (hb < 45) & (sb > .36)
leather = ndi.binary_opening(ndi.binary_closing(leather, iterations=2), iterations=2)
wl = np.clip(ndi.gaussian_filter(leather.astype(np.float32), 2), 0, 1)[..., None]
Cb2 = enc(lin(Cb) * (np.array([.42, .46, .40]) * (1 - wl) + np.array([.62, .58, .55]) * wl))
Cb2, _ = unsmear(Cb2)
save(pad(Cb2, mb), T / 'body_c_final.png')
hideC = mb & (sb < .3) & (Pb[..., 1] > -.5) & (Pb[..., 1] < .3)
pool = Cb2[hideC][::11]
Hc = Hb.copy(); core = skin & ~lining
Hc[core] = softcap(rank(lh, core, pool), .1, .4)
lw = X['lw']; Tr = X['Trans']
Hc = Hc * (1 - lw[..., None]) + Tr * lw[..., None]
c = lining & ~tongue; s_ = np.clip((lin(Hb[c]) @ Lw) / .35, 0, 1)[:, None]; Hc[c] = np.array([.26, .10, .05]) * (1 - s_) + np.array([.78, .46, .26]) * s_
c = tongue; s_ = np.clip((lin(Hb[c]) @ Lw) / .5, 0, 1)[:, None]; Hc[c] = np.array([.13, .30, .04]) * (1 - s_) + np.array([.60, .86, .20]) * s_
c = eye; s_ = np.clip((lin(Hb[c]) @ Lw) / .6, 0, 1)[:, None]; dk = lin(Hb[c]) @ Lw < .02
Hc[c] = np.array([.16, .19, .25]) * (1 - s_) + np.array([.78, .83, .90]) * s_; Hc[c] = np.where(dk[:, None], Hb[c], Hc[c])
c = teeth; Hc[c] = enc(lin(Hb[c]) * np.array([.95, .98, .62]))
Hc = pad(Hc, mh)
save(Hc, T / 'head_c_final.png')
nb_ = srgb(T / 'head_b_normal_1k.png'); lw1 = ndi.zoom(lw, .5, order=1)[..., None]; nf = nb_ * (1 - .75 * lw1) + np.array([.5, .5, 1.]) * .75 * lw1
save(nf, T / 'head_c_normal_1k.png')
print('tiers done')
