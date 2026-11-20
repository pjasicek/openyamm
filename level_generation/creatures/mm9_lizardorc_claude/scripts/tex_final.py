"""Final shared set and tiers. Head brought to the body's level per class, seam band harmonised on both sides of the neck, region masks (R hide, G steel, B leather) and tier ramps. A is the paint (MM9's look, its ramps dropped at runtime); B and C are ramps on the same images. Project folder."""
import sys, json, numpy as np
from pathlib import Path
from PIL import Image
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
sys.path.insert(0, 'scripts'); sys.path.insert(0, '../claude_shared')
import rast, region_variants as RV, headfr as H
from classes import classes, hsv
T = Path('textures'); S = 2048
J = np.load('work/joined.npz'); U = np.load('work/uv.npz'); co, part = J['co'], J['part']
def srgb(p): return np.asarray(Image.open(p).convert('RGB'), np.float32) / 255
def save(a, p): Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype(np.uint8)).save(p)
def lin(c): return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)
def enc(c): c = np.clip(c, 0, 1); return np.where(c <= .0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - .055)
def pad(img, cov):
    _, (iy, ix) = ndi.distance_transform_edt(~cov, return_indices=True); return img[iy, ix]
Fb, Bb = rast.raster(U['ub'], S); Fh, Bh = rast.raster(U['uh'], S)
Pb, mb = rast.positions(Fb, Bb, co[U['ob']]); Ph, mh = rast.positions(Fh, Bh, co[U['oh']])
ph = np.full((S, S), -1, np.int32); ph[mh] = part[U['oh']].max(1)[Fh[mh]]
Bbody = srgb(T / 'body_basecolor_graded.png'); Bhead = srgb(T / 'head_basecolor_graded.png')
# head level: per class against the body (the head's AO and the mouth's dark paint pulled it under)
hib, stb, leb, *_ = classes(Bbody); hih, sth, leh, *_ = classes(Bhead)
hib &= mb; stb &= mb; hih &= mh; sth &= mh
gain_h = (lin(Bbody[hib]).mean(0) / lin(Bhead[hih]).mean(0)); gain_s = lin(Bbody[stb]).mean(0) / lin(Bhead[sth]).mean(0)
print('class gain head hide', gain_h.round(2), 'steel', gain_s.round(2))
k = float(sys.argv[1]) if len(sys.argv) > 1 else .75
sf = lambda m: np.clip(ndi.gaussian_filter(m.astype(np.float32), 2.) * 1.1, 0, 1)[..., None]
Bh_l = lin(Bhead); Bh_l = Bh_l * (1 + sf(hih) * (gain_h ** k - 1)) ; Bh_l = Bh_l * (1 + sf(sth) * (gain_s ** k - 1))
Bhead1 = enc(Bh_l)
# seam band
ring = co[J['ringcopy']]; cen = ring.mean(0); n = H.PLANE_N; u_ = np.array([1., 0, 0]); v_ = np.cross(n, u_)
def theta(P): q = P - cen; return np.arctan2(q @ v_, q @ u_)
tree = cKDTree(ring)
db = np.full((S, S), 9., np.float32); db[mb] = tree.query(Pb[mb])[0]; dh = np.full((S, S), 9., np.float32); dh[mh & (ph == 1)] = tree.query(Ph[mh & (ph == 1)])[0]
tb = np.zeros((S, S), np.float32); tb[mb] = theta(Pb[mb]); th = np.zeros((S, S), np.float32); th[mh] = theta(Ph[mh])
gr = np.linspace(-np.pi, np.pi, 33); mb_ = np.zeros((32, 3)); mh_ = np.zeros((32, 3))
for i in range(32):
    a = (db < .05) & (tb >= gr[i]) & (tb < gr[i + 1]); b = (dh < .05) & (th >= gr[i]) & (th < gr[i + 1])
    mb_[i] = lin(Bbody[a]).mean(0) if a.sum() > 20 else np.nan; mh_[i] = lin(Bhead1[b]).mean(0) if b.sum() > 20 else np.nan
ratio = np.nan_to_num((mb_ @ [.2126, .7152, .0722]) / np.maximum(mh_ @ [.2126, .7152, .0722], 1e-4), nan=1.); ratio = np.clip(ratio, .6, 1.5)[:, None].repeat(3, 1)
for _ in range(4): ratio = .25 * np.roll(ratio, 1, 0) + .5 * ratio + .25 * np.roll(ratio, -1, 0)
print('seam ratio', ratio.mean(0).round(3), ratio.min(0).round(3), ratio.max(0).round(3))
def gain(t): return np.stack([np.interp(t, (gr[:-1] + gr[1:]) / 2, ratio[:, c], period=2 * np.pi) for c in range(3)], -1)
def fall(d, R): x = np.clip(d / R, 0, 1); return (1 - x * x * (3 - 2 * x))
Gb = gain(tb); Gh = gain(th)
body = enc(lin(Bbody) * np.exp(-.5 * np.log(Gb) * fall(db, .09)[..., None]))
head = enc(lin(Bhead1) * np.exp(.5 * np.log(Gh) * fall(dh, .09)[..., None]))
save(body, T / 'body_final.png'); save(head, T / 'head_final.png')
# masks
def soft(m, s=1.2): return np.clip(ndi.gaussian_filter(m.astype(np.float32), s) * 1.1, 0, 1)
def regions(img, cov, extra_out=None):
    hi, st, le, hh, sa, va = classes(img)
    claw = (hh > 28) & (hh < 62) & (sa > .10) & (sa < .42) & (va > .42)
    st = st & ~claw
    if extra_out is not None: hi &= ~extra_out; st &= ~extra_out; le &= ~extra_out
    # every texel of an island into its nearest class by a small closing, the gutters by padding
    r = []
    for m in (hi, st, le):
        m = ndi.binary_closing(m & cov, iterations=1); r.append(pad(soft(m), cov))
    return r
rb = regions(body, mb)
out_h = np.isin(ph, [3, 4, 7]) | (ph == -1)
hu, sa, va = hsv(head); red = ((hu < 28) | (hu > 335)) & (sa > .45)
rh = regions(head, mh, out_h | red)
rh[2] = np.zeros_like(rh[2])
RV.write_mask(rb, T / 'liz_body_mask.png', 1024); RV.write_mask(rh, T / 'liz_head_mask.png', 1024)
# tier targets on the same images
def rotate(rgb, deg, sat=1., val=1.):
    hh, ss, vv = hsv(rgb); hh = (hh + deg) % 360; ss = np.clip(ss * sat, 0, 1); vv = vv * val
    c = vv * ss; x = c * (1 - np.abs(((hh / 60) % 2) - 1)); m = vv - c; i = (hh // 60).astype(int) % 6
    z = np.zeros_like(c); r = np.choose(i, [c, x, z, z, x, c]); g = np.choose(i, [x, c, c, x, z, z]); b = np.choose(i, [z, z, x, c, c, x])
    return np.stack([r + m, g + m, b + m], -1)
def tint(rgb, col, val):
    L = rgb @ np.array([.2126, .7152, .0722]); return np.clip(L[..., None] * np.array(col) * val, 0, 1)
TIERS = {'liz_b': dict(hide=(62, .9, .78), steel=((.72, .78, .92), .72), lea=(-12, .9, .7)), 'liz_c': dict(hide=(-52, 1.05, .92), steel=((1.05, .86, .58), .9), lea=(200, .75, .75))}
VS = ['liz_a', 'liz_b', 'liz_c']
mats = []
for nm, base, r_, prefix, mask in (('body', body, rb, 'Liz', 'liz_body_mask.png'), ('head', head, rh, 'LizHead', 'liz_head_mask.png')):
    ramps = {v: [] for v in VS}
    for reg, w in zip(('hide', 'steel', 'lea'), r_):
        if w.max() < .01:
            continue
        tg = {'liz_a': base}
        for v, t in TIERS.items():
            if reg == 'steel': tg[v] = tint(base, *t['steel'])
            else: tg[v] = rotate(base, *t[reg])
        rp, err = RV.fit_ramps(base, tg, w)
        print(nm, reg, json.dumps(err)[:160])
        for v in VS: ramps[v].append(rp[v])
    mats.append({'base': prefix, 'prefix': prefix, 'mask': mask, 'ramps': ramps})
json.dump({'variants': VS, 'materials': mats}, open(T / 'liz_ramps.json', 'w'))
print('RAMPS written')
