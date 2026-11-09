#!/usr/bin/env python3
"""The Dread's head and the eye glow mask, from the skull paint (no third paid paint). MM9's skin C/D sits between the woman and the clean skull: rotting flesh still on the bone, dull eyes. Here: the skull stained brown, the woman's skin showing through in patches on cheeks and jaw, green eyes turned rust.
Writes textures/banshee_head_b_graded.png, banshee_eye_mask.png. Run from the project folder."""
import numpy as np
from PIL import Image
from scipy import ndimage
c = np.asarray(Image.open('textures/banshee_head_c_graded.png').convert('RGB'), np.float32) / 255
a = np.asarray(Image.open('textures/banshee_head_a_graded.png').convert('RGB'), np.float32) / 255
# per identity paint inside the head, in UV space: the mouth cavity's walls dark on every tier, tongue blood-dark; on the skulls the eyeballs repainted (no view shows them cleanly): black, a green iris round the pole, a dark pupil
D = np.load('work/uv_v1.npz')
idx, co, uvc = D['Head_idx'], D['Head_co'], D['Head_uv']
hp = D['Head_hpart']
tag = hp[idx].max(1) * (hp[idx].min(1) == hp[idx].max(1))
P = co[idx]
fn = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
import sys
sys.path.insert(0, 'scripts')
import interior
shellf = np.where(np.isin(hp[idx], [0, 5]).all(1))[0]
cavity = np.zeros(len(idx), bool)
cavity[shellf] = interior.interior_faces(P[shellf])
C = np.array([0, -0.292, 0.513]); R_ = np.array([0.056, 0.072, 0.060]) * 1.12
cen = P.mean(1); toC = C - cen; toC /= np.maximum(np.linalg.norm(toC, axis=1, keepdims=True), 1e-9)
fu = fn / np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
extra = np.isin(hp[idx], [0, 5]).all(1) & (np.sum(((cen - C) / R_) ** 2, axis=1) < 1) & (np.sum(fu * toC, axis=1) > 0.1)
# only the mouth is painted dark: rays from the neck hit the jaw and from under the hair cap's rim hit the shoulder of the head
cavity = np.isin(hp[idx], [0, 5]).all(1) & (np.sum(((cen - C) / (R_ * 1.12)) ** 2, axis=1) < 1) & (np.sum(fu * toC, axis=1) > 0.1) & (cen[:, 2] > 0.476) & (cen[:, 1] < -0.235) & (np.abs(cen[:, 0]) < 0.05)      # not the crease under the jaw, nor the outer crease behind the mouth corner
print('INTERIOR faces', int(cavity.sum()))
# the notch between chin and throat: Meshy painted its crease brown, and the jaw opens it. Neck colour there
notch = np.isin(hp[idx], [0, 5]).all(1) & (cen[:, 1] > -0.285) & (cen[:, 1] < -0.175) & (cen[:, 2] > 0.435) & (cen[:, 2] < 0.49) & ~cavity
zipf = (hp[idx].min(1) == 0) & (hp[idx].max(1) == 5)        # the strip that stitches the head's ring to the neck
notch = notch | zipf
neckf = hp[idx].min(1) == 5
SIZE = c.shape[0]
uvp = uvc * SIZE; uvp[..., 1] = SIZE - uvp[..., 1]
EYES = {}
for sgn in (-1, 1):
    m_ = (hp == 1) & (np.sign(co[:, 0]) == sgn)
    EYES[sgn] = co[m_].mean(0)
pos = np.zeros(c.shape, np.float32); kind = np.zeros(c.shape[:2], np.int8)
for i in range(len(P)):
    if not (cavity[i] or notch[i] or tag[i] in (1, 2, 3, 4)):
        continue
    a_, b_, c_ = uvp[i]
    x0, x1 = int(min(a_[0], b_[0], c_[0])) - 1, int(max(a_[0], b_[0], c_[0])) + 2
    y0, y1 = int(min(a_[1], b_[1], c_[1])) - 1, int(max(a_[1], b_[1], c_[1])) + 2
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, SIZE)) + .5, np.arange(max(y0, 0), min(y1, SIZE)) + .5)
    if xs.size == 0:
        continue
    d = (b_[1] - c_[1]) * (a_[0] - c_[0]) + (c_[0] - b_[0]) * (a_[1] - c_[1])
    if abs(d) < 1e-9:
        continue
    l0 = ((b_[1] - c_[1]) * (xs - c_[0]) + (c_[0] - b_[0]) * (ys - c_[1])) / d
    l1 = ((c_[1] - a_[1]) * (xs - c_[0]) + (a_[0] - c_[0]) * (ys - c_[1])) / d
    l2 = 1 - l0 - l1
    ok = (l0 > -0.05) & (l1 > -0.05) & (l2 > -0.05)
    yy, xx = ys[ok].astype(int), xs[ok].astype(int)
    w = np.stack([l0[ok], l1[ok], l2[ok]], 1)
    pos[yy, xx] = w @ P[i]
    kind[yy, xx] = 1 if cavity[i] else 2 if tag[i] == 2 else 3 if tag[i] == 1 else 4 if tag[i] in (3, 4) else 5
# the stitch strip's triangles are thin in UV and can miss every texel centre: drawn as strokes
from PIL import ImageDraw
stroke = Image.new('L', (SIZE, SIZE), 0); dr_ = ImageDraw.Draw(stroke)
for i in np.where(zipf)[0]:
    pts = [tuple(p_) for p_ in uvp[i].tolist()]
    dr_.polygon(pts, fill=255); dr_.line(pts + pts[:1], fill=255, width=4)
kind[(np.asarray(stroke) > 0) & (kind == 0)] = 5
eye = kind == 3
m = np.zeros(c.shape[:2], np.float32)
if eye.any():
    for sgn, ec in EYES.items():
        sel = eye & (np.sign(pos[..., 0]) == sgn)
        rr = np.hypot(pos[..., 0] - ec[0], pos[..., 2] - ec[2]) / 0.0135
        iris = np.clip((1.0 - rr) * 6, 0, 1) * (pos[..., 1] < ec[1])
        pupil = np.clip((0.3 - rr) * 12, 0, 1)
        e = iris * (1 - pupil)
        m[sel] = e[sel]
nuv = uvp[neckf].mean(1).astype(int).clip(0, SIZE - 1)
for name, img in (('a', a), ('c', c)):
    nc = np.median(img[nuv[:, 1], nuv[:, 0]], axis=0)
    if (kind == 5).any():
        l_ = img[kind == 5].mean(1, keepdims=True)
        img[kind == 5] = nc * (0.92 + 0.16 * np.clip(l_ / max(float(l_.mean()), 1e-3), 0, 1.4) / 1.4)
    img[kind == 1] = np.array([0.1, 0.03, 0.03], np.float32) * (0.5 + 0.5 * img[kind == 1].mean(1, keepdims=True))
    img[kind == 2] = np.array([0.2, 0.05, 0.05], np.float32) * (0.6 + 0.8 * img[kind == 2].mean(1, keepdims=True))
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)).save(f'textures/banshee_head_{name}_graded.png')
# teeth: the woman's paint in ivory (the repaint's mouth is black)
c[kind == 4] = (a[kind == 4].mean(1, keepdims=True) * np.array([0.98, 0.92, 0.78], np.float32))
gree = np.array([0.25, 0.95, 0.35], np.float32)
c[eye] = (0.015 + m[eye, None] * gree)
Image.fromarray((np.clip(c, 0, 1) * 255 + 0.5).astype(np.uint8)).save('textures/banshee_head_c_graded.png')
green = eye & (m > 0.3)
m = ndimage.gaussian_filter(m, 0.7) * eye
Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).save('textures/banshee_eye_mask.png')
# stain and flesh by noise in 3D, so they run across UV seams
allf = np.where(np.isin(hp[idx], [0, 5]).all(1))[0]
posm = np.zeros(c.shape, np.float32); cov = np.zeros(c.shape[:2], bool)
for i in allf:
    a_, b_, c_ = uvp[i]
    x0, x1 = int(min(a_[0], b_[0], c_[0])) - 1, int(max(a_[0], b_[0], c_[0])) + 2
    y0, y1 = int(min(a_[1], b_[1], c_[1])) - 1, int(max(a_[1], b_[1], c_[1])) + 2
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, SIZE)) + .5, np.arange(max(y0, 0), min(y1, SIZE)) + .5)
    if xs.size == 0:
        continue
    d = (b_[1] - c_[1]) * (a_[0] - c_[0]) + (c_[0] - b_[0]) * (a_[1] - c_[1])
    if abs(d) < 1e-9:
        continue
    l0 = ((b_[1] - c_[1]) * (xs - c_[0]) + (c_[0] - b_[0]) * (ys - c_[1])) / d
    l1 = ((c_[1] - a_[1]) * (xs - c_[0]) + (a_[0] - c_[0]) * (ys - c_[1])) / d
    l2 = 1 - l0 - l1
    ok = (l0 > -0.05) & (l1 > -0.05) & (l2 > -0.05)
    yy, xx = ys[ok].astype(int), xs[ok].astype(int)
    w = np.stack([l0[ok], l1[ok], l2[ok]], 1)
    posm[yy, xx] = w @ P[i]; cov[yy, xx] = True
_, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
posm = posm[iy, ix]
# ---- the neck join, per paint: the loft and its stitch strip take a smooth colour read in 3D from the neck itself, keep their fine detail, and fade at the bottom into the torso's own colour at the ring (the saw-teeth were a seam between two paints)
from PIL import ImageDraw as _D
neckf_all = hp[idx].max(1) == 5
ms = Image.new('L', (SIZE, SIZE), 0); dd_ = _D.Draw(ms)
for i in np.where(neckf_all)[0]:
    pts = [tuple(p_) for p_ in uvp[i].tolist()]
    dd_.polygon(pts, fill=255); dd_.line(pts + pts[:1], fill=255, width=3)
zone = (np.asarray(ms) > 0) | (kind == 5)
zone &= (kind != 1) & (kind != 2) & (kind != 3) & (kind != 4) | (kind == 5)
tc = np.array([0, -0.153, 0.488]); hc = np.array([0, -0.189, 0.531])
axn = hc - tc; Ln = float(np.linalg.norm(axn)); axn = axn / Ln
tn = np.clip(((posm - tc) @ axn) / (Ln + 0.03), 0, 1)
az = np.arctan2(posm[..., 0], -(posm[..., 1] + 0.17))
# torso colour round the ring
B_ = np.load('work/uv_v1.npz')
bi, bc_, bu = B_['Body_idx'], B_['Body_co'], B_['Body_uv'].copy(); bu[..., 1] = 1 - bu[..., 1]
cb = bc_[bi].mean(1)
dr = (cb - np.array([0, -0.13, 0.505])) @ (np.array([0, -0.6, 0.8]))
near = (dr > -0.03) & (np.abs(cb[:, 0]) < 0.2) & (B_['Body_part'] == 0)
body = np.asarray(Image.open('textures/banshee_basecolor_graded.png').convert('RGB'), np.float32) / 255
sx = (bu[near].mean(1) * 2048).astype(int).clip(0, 2047)
cs = body[sx[:, 1], sx[:, 0]]
azb = np.arctan2(cb[near, 0], -(cb[near, 1] + 0.17))
Bins = 48
num = np.zeros((Bins, 3)); cnt = np.zeros(Bins)
ib = ((azb + np.pi) / (2 * np.pi) * Bins).astype(int) % Bins
np.add.at(num, ib, cs); np.add.at(cnt, ib, 1)
ringc = np.stack([ndimage.gaussian_filter1d(num[:, c], 3, mode='wrap') / np.maximum(ndimage.gaussian_filter1d(cnt, 3, mode='wrap'), 1e-3) for c in range(3)], 1)
rc = ringc[np.clip(((az + np.pi) / (2 * np.pi) * Bins).astype(int), 0, Bins - 1)]
Zs = zone.astype(np.float32)
print('RINGC', np.round(ringc[::8], 2).tolist())
_m5 = Image.new('L', (SIZE, SIZE), 0); _d5 = _D.Draw(_m5)
for i in np.where(hp[idx].min(1) == 5)[0]:
    _d5.polygon([tuple(p_) for p_ in uvp[i].tolist()], fill=255)
hp5m = np.asarray(_m5)
aref = a.copy()
# the hair as a whole mass, strands and all, with a smooth edge: the accepted hairline must survive the neck fade
hairm = (aref.mean(2) < 0.64) & (aref[..., 0] - aref[..., 2] > 0.26) & (kind == 0) & (posm[..., 1] > -0.27)
hairm = ndimage.binary_opening(ndimage.binary_closing(hairm, iterations=3), iterations=2)
_lab, _n = ndimage.label(hairm)
_sz = ndimage.sum(hairm, _lab, np.arange(1, _n + 1))
hairm = np.isin(_lab, 1 + np.where(_sz > 2500)[0])
hairm = ndimage.gaussian_filter(hairm.astype(np.float32), 4) > 0.5
# ... but not the stump around the head's ring: the brown crease and fringe Meshy painted there touch the hair and would count as hair, all round the throat
_n = np.array([0, 0.68, -0.73]); _s = np.array([0, 0.73, 0.68])
_q = (posm - np.array([0, -0.198, 0.523]))
_el = np.sqrt((_q[..., 0] / 0.05) ** 2 + ((_q @ _s) / 0.084) ** 2)
hairm &= ~((_q @ _n > -0.02) & (_el < 1.18))
hairs = np.clip(ndimage.gaussian_filter(ndimage.binary_dilation(hairm, iterations=2).astype(np.float32), 1.5) * 1.3, 0, 1)
for name, img in (('a', a), ('c', c)):
    wz = np.maximum(ndimage.gaussian_filter(Zs, 5), 1e-3)
    blur = np.stack([ndimage.gaussian_filter(img[..., k] * Zs, 5) / wz for k in range(3)], -1)
    detail = np.ones(img.shape[:2] + (1,), np.float32)      # no fine paint on the join: its stitch triangles have no UV area, so they would read a stray texel
    # the smooth colour: mean by height along the neck and azimuth
    grid = np.zeros((10, 24, 3)); gn = np.zeros((10, 24))
    it = np.clip((tn * 9.99).astype(int), 0, 9); ia = np.clip(((az + np.pi) / (2 * np.pi) * 24).astype(int), 0, 23)
    src = zone & (kind != 5) & (img.mean(2) > 0.25)
    np.add.at(grid, (it[src], ia[src]), img[src]); np.add.at(gn, (it[src], ia[src]), 1)
    if name == 'c':
        src = src & (np.abs(img - aref).sum(2) > 0.12)          # under the jaw no view saw the neck, and the skull paint fell back on the woman's: only what the repaint covered
    # the neck takes the skin just above the join, under the jaw and cheek, so the two read as one surface
    dn0 = (posm - np.array([0, -0.2, 0.52])) @ np.array([0, 0.68, -0.73])
    band = cov & (kind == 0) & ~hairm & (dn0 > -0.09) & (dn0 < -0.05) & (posm[..., 1] < -0.17)
    if name == 'c':
        band &= np.abs(img - aref).sum(2) > 0.12
    glob = np.median(img[band], axis=0) if band.sum() > 200 else np.median(img[src], axis=0)
    grid = np.broadcast_to(glob[None, None], grid.shape).copy()      # one colour: any variation stretches into stripes when the neck is thrown back
    F = grid[it, ia]
    F = ndimage.gaussian_filter(F, (3, 3, 0)) * 0.0 + F
    col = F * detail ** 0.8
    k_ = (1 - np.clip(tn / 0.5, 0, 1)) ** 1.5
    rc_ = np.maximum(rc, glob * 0.75)        # the ring's colour, never a dark texel of Meshy's collar
    col = col * (1 - k_[..., None]) + (rc_ * detail ** 0.5) * k_[..., None]
    dn = (posm - np.array([0, -0.2, 0.52])) @ np.array([0, 0.68, -0.73])
    w3 = np.clip((dn + 0.05) / 0.035, 0, 1); w3 = w3 * w3 * (3 - 2 * w3)           # up the stump the smooth colour fades into the paint by height, not at a chart's edge
    wy = 1 - np.clip((-0.262 - posm[..., 1]) / 0.035, 0, 1); wy = wy * wy * (3 - 2 * wy)      # the chin and jawbone keep their paint
    wz_ = 1 - np.clip((posm[..., 2] - 0.59) / 0.04, 0, 1)                          # the plane rises to the crown at the back: only the stump
    skin = (cov & ((kind == 0) | (kind == 5))).astype(np.float32)                  # per texel, by 3D height alone: no triangle of a zone's edge can show
    _ds = np.clip((_q @ _n + 0.03) / 0.015, 0, 1) * (1 - np.clip((_el - 1.05) / 0.2, 0, 1))      # the stump around the ring: all neck, whatever Meshy painted
    wm = (skin * np.maximum(np.maximum(w3 * wy * wz_ * (1 - hairs), (hp5m > 0) * 1.0), _ds * _ds * (3 - 2 * _ds)))[..., None]      # never over her hair
    img[:] = img * (1 - wm) + col * wm
    # the last dark slivers of Meshy's crease under the jaw, at the chin end of the fade: replaced by the skin around them
    reg = (cov & ((kind == 0) | (kind == 5)) & (posm[..., 1] > -0.31) & (posm[..., 1] < -0.22) & (posm[..., 2] < 0.50) & (dn > -0.045)).astype(np.float32)
    lum = img.mean(2); gr = np.maximum(ndimage.gaussian_filter(reg, 8), 1e-3)
    dark = (reg > 0) & (lum < 0.8 * ndimage.gaussian_filter(lum * reg, 8) / gr)
    good = reg * (1 - ndimage.binary_dilation(dark, iterations=2)); gg = np.maximum(ndimage.gaussian_filter(good, 8), 1e-3)
    fill = np.stack([ndimage.gaussian_filter(img[..., k] * good, 8) / gg for k in range(3)], -1)
    dm = np.clip(ndimage.gaussian_filter(ndimage.binary_dilation(dark, iterations=2).astype(np.float32), 1.0) * 1.5, 0, 1)[..., None]
    img[:] = img * (1 - dm) + fill * dm
    print('SLIVERS', name, int(dark.sum()))
    # the stitch strip's triangles have no UV area and no texel position of their own: each drawn in the smooth colour at its 3D centre
    pil = Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)); dz = _D.Draw(pil)
    for i in np.where(zipf)[0]:
        tv = np.clip(((cen[i] - tc) @ axn) / (Ln + 0.03), 0, 1); av = np.arctan2(cen[i, 0], -(cen[i, 1] + 0.17))
        cc = grid[min(int(tv * 9.99), 9), min(int((av + np.pi) / (2 * np.pi) * 24), 23)]
        fillc = tuple(int(np.clip(x, 0, 1) * 255 + 0.5) for x in cc)
        pts = [tuple(p_) for p_ in uvp[i].tolist()]
        dz.polygon(pts, fill=fillc); dz.line(pts + pts[:1], fill=fillc, width=5)
    img[:] = np.asarray(pil, np.float32) / 255
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)).save(f'textures/banshee_head_{name}_graded.png')
# the same triangles sample the normal map at a point: flat there, or the stretched strip shades in stripes
nm_ = np.array(Image.open('textures/banshee_head_normal_1k.png').convert('RGB'))
zz = ndimage.binary_dilation(zone, iterations=2)
nm_[zz] = (128, 128, 255)
Image.fromarray(nm_).save('textures/banshee_head_normal_1k.png')
# neck alpha: opaque at the head, the torso's own at the ring
naf = 0.72 + 0.28 * np.clip(tn / 0.4, 0, 1)        # rig_fix.py maps the stitch strip onto a face in the upper neck, which is opaque here
alpha_im = Image.fromarray(((np.where(zone, naf, 1.0)) * 255).astype(np.uint8))
alpha_im.save('textures/banshee_neck_alpha.png')
rng = np.random.default_rng(3)


def noise3(scale, oct=7):
    out = np.zeros(c.shape[:2], np.float32)
    for k in range(oct):
        v = rng.normal(size=3); v /= np.linalg.norm(v)
        f = scale * (1 + 0.6 * k)
        out += np.sin(posm @ (v * f) + rng.uniform(0, 6.28))
    return out / np.sqrt(oct / 2)


n1 = noise3(26.0); n2 = noise3(70.0)
stain = 0.5 + 0.22 * n1 + 0.1 * n2
out = c * (np.array([0.96, 0.82, 0.66])[None, None] * (0.78 + 0.3 * np.clip(stain, 0, 1))[..., None])
# flesh in patches: where the two paints are both skin (not hair: a is red-brown strands there, c is straw), not on the neck's seam-rich charts below the jaw
skin_a = (a[..., 0] > 0.55) & (a[..., 1] > 0.4) & (a[..., 2] > 0.3) & (posm[..., 2] > 0.47)
k = np.clip((n1 * 0.6 + n2 * 0.35 - 0.1), 0, 1) * ndimage.gaussian_filter(skin_a.astype(np.float32), 3)
k = np.clip(k * 1.1, 0, 0.7)[..., None]
out = out * (1 - k) + (a * np.array([0.82, 0.74, 0.66])[None, None]) * k
# eyes: rust
gray = c @ np.array([0.2, 0.7, 0.1])
rust = np.stack([gray * 1.5, gray * 0.55, gray * 0.28], -1)
out = out * (1 - m[..., None]) + rust * m[..., None]
out[kind == 3] = (0.015 + m[kind == 3, None] * np.array([0.95, 0.38, 0.1], np.float32))
out[kind == 4] = c[kind == 4]
# the middle tier's stains and rust stop at the neck join too: the loft and the stump are one even colour, as on the other two
wn = np.maximum(ndimage.gaussian_filter((hp5m > 0).astype(np.float32), 3), _ds * _ds * (3 - 2 * _ds)) * (cov & ((kind == 0) | (kind == 5)))
out = out * (1 - wn[..., None]) + np.median(out[wn > 0.9], axis=0) * wn[..., None]
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save('textures/banshee_head_b_graded.png')
print('HEADB eye texels', int(green.sum()))
