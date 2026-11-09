"""Textures from the paints: seam harmonised B set, tier C images, tier A pattern (from the projected purple masters), region masks and ramps. Project folder. Writes textures/*."""
import sys, json, numpy as np
from pathlib import Path
from PIL import Image
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
sys.path.insert(0, 'scripts'); sys.path.insert(0, '../claude_shared')
import rast, project_master as PM, region_variants as RV
Image.MAX_IMAGE_PIXELS = None
T = Path('textures'); S = 2048
J = np.load('work/joined.npz'); U = np.load('work/uv.npz'); C = np.load('work/cutoff.npz'); Um = np.load('work/upload_maps.npz')
co, up, part, nb = J['co'], J['co_up'], J['part'], int(J['nb'])
def srgb(p): return np.asarray(Image.open(p).convert('RGB'), np.float32) / 255
def save(a, p): Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype(np.uint8)).save(p)
def lin(c): return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)
def enc(c): c = np.clip(c, 0, 1); return np.where(c <= .0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - .055)
Lw = np.array([.2126, .7152, .0722])
def hsv(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0); r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360, sat, mx
def pad(img, cov):
    _, (iy, ix) = ndi.distance_transform_edt(~cov, return_indices=True); return img[iy, ix]
# texel rasters
Fb, Bb = rast.raster(U['ub'], S); Fh, Bh = rast.raster(U['uh'], S)
Pb, mb = rast.positions(Fb, Bb, co[U['ob']]); Ph, mh = rast.positions(Fh, Bh, co[U['oh']])
Pbu, _ = rast.positions(Fb, Bb, up[U['ob']]); Phu, _ = rast.positions(Fh, Bh, up[U['oh']])
fnu = np.cross(up[U['ob']][:, 1] - up[U['ob']][:, 0], up[U['ob']][:, 2] - up[U['ob']][:, 0]); fnu /= np.maximum(np.linalg.norm(fnu, axis=1, keepdims=True), 1e-12)
partv = part[U['oh']].max(1)      # per head face
ph = np.full((S, S), -1, np.int32); ph[mh] = partv[Fh[mh]]
np.savez('work/rasters.npz', Fb=Fb, Bb=Bb, Fh=Fh, Bh=Bh)
# --- B set: seam band
Bbody = srgb(T / 'body_b_basecolor_graded.png'); Bhead = srgb(T / 'head_b_basecolor_graded.png')
ring = co[J['ringcopy']]; cen = ring.mean(0); A_ = np.radians(25.8); n = np.array([0, -np.sin(A_), np.cos(A_)]); u_ = np.array([1., 0, 0]); v_ = np.cross(n, u_)
def theta(P): q = P - cen; return np.arctan2(q @ v_, q @ u_)
tree = cKDTree(ring)
db = np.full((S, S), 9., np.float32); db[mb] = tree.query(Pb[mb])[0]; dh = np.full((S, S), 9., np.float32); dh[mh & (ph == 1)] = tree.query(Ph[mh & (ph == 1)])[0]
tb = np.zeros((S, S), np.float32); tb[mb] = theta(Pb[mb]); th = np.zeros((S, S), np.float32); th[mh] = theta(Ph[mh])
gr = np.linspace(-np.pi, np.pi, 49); mb_ = np.zeros((48, 3)); mh_ = np.zeros((48, 3))
for i in range(48):
    a = (db < .05) & (tb >= gr[i]) & (tb < gr[i + 1]); b = (dh < .05) & (th >= gr[i]) & (th < gr[i + 1])
    mb_[i] = lin(Bbody[a]).mean(0) if a.sum() > 20 else np.nan; mh_[i] = lin(Bhead[b]).mean(0) if b.sum() > 20 else np.nan
ratio = np.nan_to_num(mb_ / np.maximum(mh_, 1e-4), nan=1.); ratio = np.clip(ratio, .5, 2.)
for _ in range(6): ratio = .25 * np.roll(ratio, 1, 0) + .5 * ratio + .25 * np.roll(ratio, -1, 0)
print('seam ratio', ratio.mean(0).round(3), ratio.min(0).round(3), ratio.max(0).round(3))
def gain(t): return np.stack([np.interp(t, (gr[:-1] + gr[1:]) / 2, ratio[:, c], period=2 * np.pi) for c in range(3)], -1)
def fall(d, R): x = np.clip(d / R, 0, 1); return (1 - x * x * (3 - 2 * x))
Gb = gain(tb); Gh = gain(th)
Bbody2 = enc(lin(Bbody) * Gb ** (-.5 * fall(db, .10))[..., None].repeat(1, -1) if False else lin(Bbody) * np.exp(-.5 * np.log(Gb) * fall(db, .10)[..., None]))
Bhead2 = enc(lin(Bhead) * np.exp(.5 * np.log(Gh) * fall(dh, .10)[..., None]))
save(Bbody2, T / 'body_b_final.png'); save(Bhead2, T / 'head_b_final.png')
# --- C set: crops of the combined paint
pc = Image.open('meshy/body_c/texture_urls_0_base_color.png').convert('RGB'); H = pc.size[0]; S1, S2 = float(Um['S1']), float(Um['S2'])
box_b = (0, int(round(H * (1 - S1))), int(round(H * S1)), H)
box_c = (int(round(H * S1)), int(round(H * (1 - S2))), int(round(H * (S1 + S2))), H)
cb = pc.crop(box_b).resize((S, S), Image.LANCZOS); Cc = pc.crop(box_c)
nc = Image.open('meshy/body_c/texture_urls_0_normal.png').convert('RGB')
pad_b = pad(np.asarray(cb, np.float32) / 255, mb)
ao = np.asarray(Image.open(T / 'body_ao.png').convert('L').resize((S, S), Image.LANCZOS), np.float32) / 255
save(pad_b, T / 'body_c_raw.png')
save(pad(np.asarray(nc.crop(box_b).resize((1024, 1024), Image.LANCZOS), np.float32) / 255, ndi.zoom(mb, .5, order=0)), T / 'body_c_normal_1k.png')
Cc = np.asarray(Cc, np.float32) / 255
# head C: leather from the cut-off piece, hide from a ramp of B
cc, ct = C['co'], C['tri']
Uc = U['uc']; oc = U['oc']; cen_c = cc[oc].mean(1)
from detached_parts_audit import closest_on_triangles
tc = cKDTree(cen_c)
hid = mh & (ph == 1)
ptsH = Ph[hid]; A3, B3, C3 = cc[oc][:, 0], cc[oc][:, 1], cc[oc][:, 2]
def nearest_map(pts, batch=200000, k=10):
    fi = np.zeros(len(pts), int); bar = np.zeros((len(pts), 3), np.float32)
    for i in range(0, len(pts), batch):
        q = pts[i:i + batch]; _, nn = tc.query(q, k=k)
        rp = np.repeat(q, k, 0); cp, _ = closest_on_triangles(rp, A3[nn.ravel()], B3[nn.ravel()], C3[nn.ravel()])
        d = np.linalg.norm(rp - cp, axis=1).reshape(nn.shape); best = d.argmin(1); r = np.arange(len(q)); f = nn[r, best]; c = cp.reshape(*nn.shape, 3)[r, best]
        e1, e2 = B3[f] - A3[f], C3[f] - A3[f]; w = c - A3[f]
        d00, d01, d11 = (e1 * e1).sum(1), (e1 * e2).sum(1), (e2 * e2).sum(1); d20, d21 = (w * e1).sum(1), (w * e2).sum(1); den = np.maximum(d00 * d11 - d01 * d01, 1e-12)
        v = (d11 * d20 - d01 * d21) / den; w_ = (d00 * d21 - d01 * d20) / den
        fi[i:i + batch] = f; bar[i:i + batch] = np.c_[1 - v - w_, v, w_]
    return fi, bar
idx, bar = nearest_map(ptsH)
uvq = (Uc[idx] * bar[..., None]).sum(1)
Hc = Cc.shape[0]
xs = np.clip(uvq[:, 0] * (Hc - 1), 0, Hc - 1); ys = np.clip((1 - uvq[:, 1]) * (Hc - 1), 0, Hc - 1)
samp = np.stack([ndi.map_coordinates(Cc[..., k], [ys, xs], order=1) for k in range(3)], 1)
Trans = np.zeros((S, S, 3), np.float32); Trans[hid] = samp
hu, sa, va = hsv(Trans)
lea = (hu > 8) & (hu < 42) & (sa > .42) & hid
lea = ndi.binary_opening(ndi.binary_closing(lea, iterations=3), iterations=2)
# leather belongs on the top and back of the dome only
top = np.zeros((S, S), bool); top[hid] = (Ph[hid][:, 1] > .42) | (Ph[hid][:, 2] < .05)
lea &= top
lw = np.clip(ndi.gaussian_filter(lea.astype(np.float32), 2.0) * 1.15, 0, 1) * hid
np.savez('work/head_c_transfer.npz', Trans=Trans, lw=lw)
save(lw, 'work/_lw.png'); save(Trans, 'work/_trans.png')
print('C done, leather texels', int(lea.sum()))
# --- tier A pattern: pale ribs of the purple masters as a mask
Path('work/tierA_v').mkdir(exist_ok=True)
pool_a = []
for nm in ('01_front', '02_back', '03_left', '04_right'):
    im = np.asarray(Image.open(f'references_hd/tierA/{nm}.png').convert('RGBA'), np.float32) / 255
    L = im[..., :3] @ Lw; a = im[..., 3] > .5
    Lb = ndi.gaussian_filter(L * a, 11) / np.maximum(ndi.gaussian_filter(a.astype(np.float32), 11), .05)
    D = L - Lb
    v = np.clip((D - .05) / .12, 0, 1) * np.clip((L - .42) / .15, 0, 1) * a
    Image.fromarray((np.dstack([v, v, v, im[..., 3]]) * 255).astype(np.uint8)).save(f'work/tierA_v/{nm}.png')
    pool_a.append((im[a][:, :3], v[a]))
Pl = np.vstack([p[0] for p in pool_a]); Vl = np.concatenate([p[1] for p in pool_a])
pool_hide = Pl[Vl < .05]; pool_vein = Pl[Vl > .6]
# body mesh for the depth test: upload pose incl. the cut-off head
mv = np.vstack([up[:nb], C['co_up']]); mt = np.vstack([J['tri'][J['mat'] == 0][np.all(J['tri'][J['mat'] == 0] < nb, 1)], C['tri'] + nb])
nu = np.zeros((S, S, 3), np.float32); nu[mb] = fnu[Fb[mb]]
ptsB = Pbu[mb]; rgbv, wt = PM.project(ptsB, nu[mb], mv, mt, 'work/tierA_v')
vein_b = np.zeros((S, S), np.float32); vein_b[mb] = rgbv[:, 0] * (wt > 1e-3)
save(vein_b, 'work/_veinb.png')
# head: through the cut-off skin
cup = C['co_up'][oc]; Pcu = (cup[idx] * bar[..., None]).sum(1); ncu = np.cross(cup[:, 1] - cup[:, 0], cup[:, 2] - cup[:, 0]); ncu /= np.maximum(np.linalg.norm(ncu, axis=1, keepdims=True), 1e-12)
rgbh, wth = PM.project(Pcu, ncu[idx], mv, mt, 'work/tierA_v')
vein_h = np.zeros((S, S), np.float32); vein_h[hid] = rgbh[:, 0] * (wth > 1e-3)
save(vein_h, 'work/_veinh.png')
np.savez('work/pools.npz', hide=pool_hide[::37], vein=pool_vein[::7])
print('tier A masks', vein_b.mean(), vein_h.mean())
