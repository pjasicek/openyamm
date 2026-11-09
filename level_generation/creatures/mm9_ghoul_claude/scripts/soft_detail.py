#!/usr/bin/env python3
"""Second pass of the body look, at 4K in the old layout, without a repaint (the new 2K atlas is one resample of this, repack_maps.py):
- tone toward MM9's darker hide; refill faces no master showed (pale armpits); the pale stick on the chest (Codex's reading of MM9's small stitched gash) painted out;
- the 1.2-9 px pebble band cut (the 'lizard' look);
- arm and shin banding and the pale knee and hip patches flattened by a surface field: a smoothed per-vertex colour (no UV seams) pulled toward MM9's olive, and the texel multiplied by target/field, so all fine detail stays; wounds, wrist wraps and the shin bone are left out; a faint olive mottle added.
Writes textures/zombie4k_final.png, zombie_final_old2k.png, zombie_torso_b_basecolor_final.png, zombie_head_basecolor_final.png, normal softs, work/dark_uv.json."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, 'scripts')
import project_lib as PL
import project_lib_v as PV
from soft_detail_tone import tone
Image.MAX_IMAGE_PIXELS = None
TX = Path('textures')
F = np.load('work/faces.npz')
gauss = lambda a, s: np.stack([ndimage.gaussian_filter(a[..., c], s) for c in range(a.shape[2])], -1)


def hsv(rgb):
    mx, mn = rgb.max(2), rgb.min(2); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360, sat, mx


def soften(im, k, sc):
    lo = gauss(im, 9 * sc); mid = gauss(im, 1.2 * sc)
    return lo + (mid - lo) * k + (im - mid) * 0.7


def flatten_normal(a, k=0.5):
    n = a.copy(); n[..., :2] *= k; return n / np.maximum(np.linalg.norm(n, axis=2, keepdims=True), 1e-6)


# ---------- body at 4K (old layout)
base = np.asarray(Image.open(TX / 'zombie4k_basecolor_graded.png').convert('RGB'), np.float32) / 255
S = base.shape[0]; SC = S / 2048
nb = F['head'] == 0                          # the whole old atlas: limbs and tier A's torso
uv, co = F['uvb'][nb], F['co'][nb]; parts = F['part'][nb]
pos, nor, cov, bar, fid = PL.raster(uv, co, S)
ptex = parts[fid]
# pale faces no master showed
h, s, v = hsv(base)
pale = ndimage.binary_opening((s < 0.2) & (v > 0.42) & cov & (ptex != 4), iterations=2)
lab, n = ndimage.label(pale)
big = np.isin(lab, 1 + np.nonzero(ndimage.sum(pale, lab, range(1, n + 1)) > 1200)[0]) if n else pale
# the stick: long pale mark on the right chest
L = base.mean(2); lf = ndimage.gaussian_filter(L, 40)
box = (pos[..., 0] < 0.0) & (pos[..., 0] > -0.2) & (pos[..., 2] > 0.5) & (pos[..., 2] < 0.75) & (pos[..., 1] < 0.03) & cov
stick = ndimage.binary_opening(((L - lf) > 0.16) & box, iterations=1)
lab, n = ndimage.label(stick); sz = ndimage.sum(stick, lab, range(1, n + 1)) if n else []
print('STICK comps', n, sorted(np.round(sz, 0))[-4:] if n else None)
if n:
    for c in np.nonzero(np.array(sz) > 150)[0][:4]:
        m = lab == c + 1; print('  at', pos[m].mean(0).round(3), 'ext', np.ptp(pos[m], 0).round(3), int(m.sum()))
stick = np.isin(lab, 1 + np.nonzero(np.array(sz) > 150)[0]) if n else stick
fill = ndimage.binary_dilation(big | stick, iterations=int(5 * SC))
print('FILL texels', int(fill.sum()))
_, (iy, ix) = ndimage.distance_transform_edt(fill, return_indices=True)
fc = gauss(base[iy, ix], 8 * SC)
# a smooth refill read as a flat patch in the pebbled skin: the skin's own detail is tiled back in, from the largest clean square of skin
good = cov & ~fill & (s > 0.3) & (v > 0.35) & (ptex == 0)
N = int(256 * SC / 2) * 2
ii = ndimage.uniform_filter(good.astype(np.float32), N)
cy, cx = np.unravel_index(np.argmax(ii), ii.shape)
print('DETAIL patch', cy, cx, round(float(ii[cy, cx]), 3))
y0, x0 = max(cy - N // 2, 0), max(cx - N // 2, 0)
det = (base - gauss(base, 6 * SC))[y0:y0 + N, x0:x0 + N]
det = np.concatenate([det, det[::-1]], 0); det = np.concatenate([det, det[:, ::-1]], 1)
yy, xx = np.mgrid[0:S, 0:S]
fd = det[yy % det.shape[0], xx % det.shape[1]]
w = ndimage.gaussian_filter(fill.astype(np.float32), 2 * SC)[..., None]
base = base * (1 - w) + (fc + fd) * w
im = tone(soften(base, 0.4, SC))
# surface field
tri = PV.weld(co); nv = tri.max() + 1
blur = gauss(im, 5 * SC)
vc = PV.per_vertex(PL.sample(blur, uv.reshape(1, -1, 2))[0].reshape(-1, 3, 3), tri, nv)
vpos = PV.per_vertex(co, tri, nv)
vf = PV.smooth(vc, tri, nv, 7)
field = np.maximum(PV.texel(vf, tri, bar, fid), 1e-3)
h, s, v = hsv(field)
red = np.clip(((h < 20) | (h > 335)) * (s - 0.5) / 0.15, 0, 1)
skin = np.clip((h - 30) / 8, 0, 1) * np.clip((v - 0.14) / 0.08, 0, 1)
OLIVE = np.array([112, 100, 58], np.float32) / 255
# trousers and wraps keep their own brown: the target is a much smoother field of themselves
vt = PV.smooth(vc, tri, nv, 60)
far = np.maximum(PV.texel(vt, tri, bar, fid), 1e-3)
k_skin = 0.72; k_cloth = 0.5
wr = np.minimum(np.linalg.norm(pos - np.array([0.631, -0.146, 0.661]), axis=2), np.linalg.norm(pos - np.array([-0.631, -0.146, 0.661]), axis=2))
wrist = np.clip((wr - 0.05) / 0.05, 0, 1)            # the wrist wraps stay
keep = (1 - red) * wrist * (ptex != 4)
target = field * (1 - (k_skin * skin * keep)[..., None]) + OLIVE * (k_skin * skin * keep)[..., None]
target = target * (1 - (k_cloth * (1 - skin) * keep)[..., None]) + far * (k_cloth * (1 - skin) * keep)[..., None]
rng = np.random.default_rng(9)
mot = PV.smooth(rng.normal(size=(nv, 1)), tri, nv, 12); mot /= mot.std()
mt = PV.texel(mot, tri, bar, fid)[..., 0] * skin * keep
gain = target / field
out = im * gain
out[..., 0] *= 1 - 0.016 * mt; out[..., 1] *= 1 + 0.014 * mt; out[..., 2] *= 1 - 0.022 * mt
out = out * cov[..., None] + im * (~cov)[..., None]
_, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
out = np.clip(out[iy, ix], 0, 1)
Image.fromarray((out * 255 + 0.5).astype('u1')).save(TX / 'zombie4k_final.png')
Image.fromarray((out * 255 + 0.5).astype('u1')).resize((2048, 2048), Image.LANCZOS).save(TX / 'zombie_final_old2k.png')
print('BODY done')
# ---------- vest: same soften and tone; the linen stays
b = np.asarray(Image.open(TX / 'zombie_torso_b_basecolor_graded.png').convert('RGB'), np.float32) / 255
Image.fromarray((np.clip(tone(soften(b, 0.35, 1.0)), 0, 1) * 255 + 0.5).astype('u1')).save(TX / 'zombie_torso_b_basecolor_final.png')
for nm in ('zombie_torso_b_normal_1k',):
    n = np.asarray(Image.open(TX / f'{nm}.png').convert('RGB'), np.float32) / 127.5 - 1
    Image.fromarray(((flatten_normal(n) + 1) * 127.5 + 0.5).astype('u1')).save(TX / 'zombie_torso_b_normal_soft.png')
# ---------- head: tone; the neck led to the body's colour
hb = tone(np.asarray(Image.open(TX / 'zombie_head_basecolor_graded.png').convert('RGB'), np.float32) / 255)
nh = F['head'] > 0
ph, _, ch, _, _ = PL.raster(F['uvh'][nh], F['co'][nh], 2048)
bb = np.asarray(Image.open(TX / 'zombie_final_old2k.png').convert('RGB'), np.float32) / 255
n2 = (F['head'] == 0) & (F['part'] == 0)
pb, _, cb, _, _ = PL.raster(F['uvb'][n2], F['co'][n2], 2048)
zb = cb & (pb[..., 2] > 0.72) & (pb[..., 2] < 0.79) & (np.abs(pb[..., 0]) < 0.14)
zh = ch & (ph[..., 2] > 0.80) & (ph[..., 2] < 0.835) & (np.abs(ph[..., 0]) < 0.05)
gain = bb[zb].mean(0) / np.maximum(hb[zh].mean(0), 1e-3)
gain = np.clip(gain, 0.8, 1.35)
print('NECK gain', gain.round(3))
w = np.clip((0.875 - ph[..., 2]) / 0.05, 0, 1); w = ndimage.gaussian_filter(w * w * (3 - 2 * w) * ch, 2)[..., None]
hb = hb * (1 - w) + np.clip(hb * gain, 0, 1) * w
Image.fromarray((hb * 255 + 0.5).astype('u1')).save(TX / 'zombie_head_basecolor_final.png')
L = ndimage.gaussian_filter(hb.mean(2), 5); inner = ndimage.binary_erosion(ch, iterations=8)
L[~inner] = 9; y, x = np.unravel_index(np.argmin(L), L.shape)
json.dump({'u': (x + 0.5) / 2048, 'v': 1 - (y + 0.5) / 2048}, open('work/dark_uv.json', 'w'))
print('SOFT done')
