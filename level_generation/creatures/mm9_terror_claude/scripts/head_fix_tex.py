#!/usr/bin/env python3
"""Carry the Meshy retexture maps over to the head_fix.py layout (uv_v2) and paint the mouth cavity.
Usage: head_fix_tex.py terror   (after head_fix.py and dump_uv3d.py on uv_v2.blend; before compose.py)

Inputs: meshy/<body>_retexture_v1 maps (old layout), work/head_fix.json, work/head_fix_cover.npy (old-layout faces
per texel).
Outputs: work/retexture_v2/texture_urls_0_{base_color,normal,roughness}.png (2K, new layout); compose.py reads them
instead of the Meshy folder when they exist.

- Squeeze: every kept island moved from v to v * vscale; texels are resampled the same way (bilinear).
- Relocated faces: each new texel maps through its face's barycentric coordinates to the old texel. Texels the old
  layout painted twice (and the rest of those faces, whose Meshy paint is a dark smear: hidden from every view) are
  repainted from the clean surface around them in 3D (local mean plus mirrored skin detail; see the refill below). A face turned by 90 degrees
  in UV gets its normal-map vectors turned with it.
- Cavity (one rectangle: u around the mouth from the bottom middle, v from the lip loop to the throat): flesh painted
  from the Meshy mouth's own colours (the replaced cavity faces' texels, ordered by luminance), with gums at the lip
  loop, palate ridges on the roof, a tongue-bed groove on the floor, folds at the corners, darkening toward the
  throat; the throat cap is near black. Normal: a small height field (ridges, gums, grain); roughness wet.
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

BODY = sys.argv[1]
HERE = Path(__file__).resolve().parent.parent
M = HERE / 'meshy' / f'{BODY}_retexture_v1'
OUT = HERE / 'work' / 'retexture_v2'
R = json.load(open(HERE / 'work' / 'head_fix.json'))
VS = R['vscale']
S = 2048
W = np.array([0.2126, 0.7152, 0.0722])
rng = np.random.default_rng(11)


def load(name):
    return np.asarray(Image.open(M / f'texture_urls_0_{name}.png').convert('RGB'), np.float32) / 255


old = {k: load(k) for k in ('base_color', 'normal', 'roughness')}


def sample(img, x, y):
    """Bilinear sample at pixel-centre coordinates (x right, y down)."""
    return np.stack([ndimage.map_coordinates(img[..., c], [y, x], order=1, mode='nearest')
                     for c in range(img.shape[-1])], -1)


# ---------------------------------------------------------------- squeeze
new = {k: np.zeros_like(v) for k, v in old.items()}
rows = np.arange(S)
vprime = 1 - (rows + 0.5) / S
keep = vprime <= VS
yy, xx = np.meshgrid(rows[keep], np.arange(S), indexing='ij')
v_old = vprime[keep][:, None] / VS * np.ones((1, S))
y_old = (1 - v_old) * S - 0.5
for k in old:
    new[k][rows[keep]] = sample(old[k], xx.astype(np.float64), y_old)


# ---------------------------------------------------------------- relocated faces
def tri_texels(p, eps=-0.02):
    """Texel centres inside a triangle given in pixel coords (x right, y down); returns rows, cols, barycentrics."""
    x0, x1 = max(int(np.floor(p[:, 0].min())) - 1, 0), min(int(np.ceil(p[:, 0].max())) + 1, S - 1)
    y0, y1 = max(int(np.floor(p[:, 1].min())) - 1, 0), min(int(np.ceil(p[:, 1].max())) + 1, S - 1)
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
    a, b, c = p
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-12:
        return None
    l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
    l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
    l3 = 1 - l1 - l2
    ins = (l1 >= eps) & (l2 >= eps) & (l3 >= eps)
    iy, ix = np.nonzero(ins)
    return iy + y0, ix + x0, np.stack([l1[ins], l2[ins], l3[ins]], 1)


def px(uv):
    uv = np.asarray(uv, np.float64)
    return np.stack([uv[..., 0] * S, (1 - uv[..., 1]) * S], -1)


# Every texel of a relocated face is repainted: its old texels were shared with another face (the green tentacle-tip
# skin inside the blue belly), and the rest of these faces (crotch and inner thighs, hidden from every reference
# view) carry a dark Meshy smear.
fill_rc, fill_xyz, fill_n = [], [], []
for e in R['relocated']:
    xyz = np.array(e['xyz'])
    hit = tri_texels(px(e['uv_new']))
    if hit is None:
        continue
    iy, ix, bc = hit
    nrm = np.cross(xyz[1] - xyz[0], xyz[2] - xyz[0])
    fill_rc.append(np.stack([iy, ix], 1))
    fill_xyz.append(bc @ xyz)
    fill_n.append(np.repeat((nrm / (np.linalg.norm(nrm) + 1e-12))[None], len(iy), 0))
fill_rc = np.concatenate(fill_rc)
fill_xyz = np.concatenate(fill_xyz)
fill_n = np.concatenate(fill_n)
fill_mask = np.zeros((S, S), bool)
fill_mask[fill_rc[:, 0], fill_rc[:, 1]] = True
# the source: clean texels of the new layout (outside the band), their 3D positions from the uv3d dump
d = np.load(HERE / 'work' / f'uv3d_{BODY}.npz')
pool_rc, pool_xyz, pool_n = [], [], []
valid_new = np.zeros((S, S), bool)
for t in range(len(d['uv'])):
    if d['uv'][t].mean(0)[1] > VS:
        continue
    hit = tri_texels(px(d['uv'][t]), 0.0)
    if hit is None:
        continue
    iy, ix, bc = hit
    valid_new[iy, ix] = True
    pool_rc.append(np.stack([iy[::2], ix[::2]], 1))
    pool_xyz.append(bc[::2] @ d['xyz'][t])
    pool_n.append(np.repeat(d['normal'][t][None], len(iy[::2]), 0))
pool_rc, pool_xyz, pool_n = np.concatenate(pool_rc), np.concatenate(pool_xyz), np.concatenate(pool_n)
dist, idx = cKDTree(pool_xyz).query(fill_xyz, k=24)
wgt = np.where((pool_n[idx] * fill_n[:, None]).sum(-1) > 0.3, 1 / (dist + 0.004) ** 2, 0)
wgt[wgt.sum(1) == 0] = 1
wgt /= wgt.sum(1, keepdims=True)

# Refill: the local colour is the inverse-distance mean of the clean surface around the hole in 3D (blurred clean
# texels, same side); the fine detail is the high-pass of a clean square of skin next to it, mirrored over the hole
# (a scale pattern without streaks). The normal map takes the local mean only.


def norm_blur(img, mask, sigma):
    m = ndimage.gaussian_filter(mask.astype(np.float32), sigma)
    return np.stack([ndimage.gaussian_filter(img[..., c] * mask, sigma) for c in range(3)], -1) / \
        np.maximum(m, 1e-4)[..., None], m


lab, _ = ndimage.label(fill_mask)
reg_of = lab[fill_rc[:, 0], fill_rc[:, 1]]
valid_new &= ~fill_mask
inside_new = ndimage.distance_transform_edt(valid_new)
kd_pool = cKDTree(pool_xyz)
hp_new, low3d = {}, {}
for k in old:
    lowmap, _ = norm_blur(new[k], valid_new, 4)
    hp_new[k] = np.where(valid_new[..., None], new[k] - lowmap, 0)
    low3d[k] = (lowmap[pool_rc[idx][..., 0], pool_rc[idx][..., 1]] * wgt[..., None]).sum(1)
vals = {k: low3d[k].copy() for k in old}
regions = np.unique(reg_of)
for r in regions:
    m = reg_of == r
    # detail tile: a clean square of the new layout around the clean surface point nearest the hole in 3D (the
    # same skin, already squeezed like its neighbours), mirrored over the hole in its own texel coordinates
    _, j = kd_pool.query(fill_xyz[m].mean(0))
    cy, cx = pool_rc[j]
    win = inside_new[max(cy - 40, 0):cy + 41, max(cx - 40, 0):cx + 41]
    oy, ox = np.unravel_index(np.argmax(np.minimum(win, 12)), win.shape)
    cy, cx = max(cy - 40, 0) + oy, max(cx - 40, 0) + ox
    h = int(max(min(inside_new[cy, cx], 12), 2))
    rel = fill_rc[m] - fill_rc[m].mean(0)
    ty = np.abs((rel[:, 0] + 2 * h) % (4 * h) - 2 * h) - h      # mirrored repeat in [-h, h]
    tx = np.abs((rel[:, 1] + 2 * h) % (4 * h) - 2 * h) - h
    sy, sx = np.clip(cy + ty, 0, S - 1), np.clip(cx + tx, 0, S - 1)
    for k in ('base_color', 'roughness'):
        vals[k][m] += np.stack([ndimage.map_coordinates(hp_new[k][..., c], [sy, sx], order=1, mode='nearest')
                                for c in range(3)], -1)
for k in old:
    new[k][fill_rc[:, 0], fill_rc[:, 1]] = np.clip(vals[k], 0, 1)
nl = len(regions)
report = {'repainted_texels': int(len(fill_rc)), 'repainted_regions': int(nl)}

# ---------------------------------------------------------------- cavity paint
cav = R['cavity']
x0c, y0c, x1c, y1c = cav['uv_rect']
cav_uv = np.array(R['cavity_old_uv']).reshape(-1, 3, 2)
samp = []
for tri in cav_uv:
    hit = tri_texels(px(tri), 0.0)
    if hit is not None:
        samp.append(old['base_color'][hit[0], hit[1]])
samp = np.concatenate(samp)
h_red = (samp[:, 0] > samp[:, 1] * 1.25) & (samp[:, 0] > 0.12)
pal = samp[h_red]
pal = pal[np.argsort(pal @ W)]
ramp = np.array([pal[int(q * (len(pal) - 1))] for q in np.linspace(0.03, 0.97, 64)])
ramp = ndimage.uniform_filter1d(ramp, 5, axis=0)
rough_cav = float(np.median(np.concatenate([old['roughness'][tri_texels(px(t), 0.0)[0], tri_texels(px(t), 0.0)[1], 1]
                                            for t in cav_uv if tri_texels(px(t), 0.0) is not None])))


def value_noise(h, w, cell, seed):
    g = np.random.default_rng(seed).random((h // cell + 3, w // cell + 3))
    return ndimage.zoom(g, cell, order=3)[:h, :w]


px0, px1 = int(round(x0c * S)), int(round(x1c * S))
py0, py1 = int(round((1 - y1c) * S)), int(round((1 - y0c) * S))
H, Wd = py1 - py0, px1 - px0
s0, s1 = cav['seam_u']
v_lo, _, v_end = cav['v_metres']
uu = ((np.arange(Wd) + 0.5) / Wd - s0) / (s1 - s0) % 1.0         # around the mouth, 0 = bottom middle
vm = v_lo + (1 - (np.arange(H) + 0.5) / H) * (v_end - v_lo)       # metres from ring 1's lip side; top row = throat
dd = np.clip(vm / v_end, 0, 1)
U, D = np.meshgrid(uu, dd)
phi = 2 * np.pi * U - np.pi / 2
up = np.sin(phi)
noise = 0.55 * value_noise(H, Wd, 6, 1) + 0.3 * value_noise(H, Wd, 2, 2) + 0.15 * rng.random((H, Wd))
t = 0.25 + 0.5 * noise
gum = np.clip(1 - D / 0.14, 0, 1)
t += 0.25 * gum + 0.06 * np.sin(np.pi * 2 * U * 40) * gum                        # gum line, tooth sockets
roof = np.clip((up - 0.25) / 0.5, 0, 1)
rugae = np.sin(2 * np.pi * D * 10) * np.clip((D - 0.08) / 0.1, 0, 1) * np.clip((0.65 - D) / 0.2, 0, 1)
t += 0.14 * rugae * roof * np.exp(-((np.cos(phi)) / 0.55) ** 2)
floor = np.clip((-up - 0.25) / 0.5, 0, 1)
groove = np.exp(-((np.minimum(U, 1 - U)) / 0.025) ** 2)
t -= 0.18 * groove * floor * np.clip(D / 0.1, 0, 1)
fold = np.exp(-(up / 0.18) ** 2)
t -= 0.12 * fold * np.clip(D / 0.15, 0, 1)
t = np.clip(t, 0, 1)
col = ramp[np.clip((t * 63).astype(int), 0, 63)]
dark = 1 - 0.88 * np.clip((D - 0.4) / 0.6, 0, 1) ** 1.3
col = col * dark[..., None]
new['base_color'][py0:py1, px0:px1] = col
height = 0.6 * rugae * roof + 0.4 * gum + 0.25 * noise
gy, gx = np.gradient(ndimage.gaussian_filter(height, 1.0))
nmap = np.stack([-gx * 2.0, gy * 2.0, np.ones_like(gx)], -1)
nmap /= np.linalg.norm(nmap, axis=-1, keepdims=True)
new['normal'][py0:py1, px0:px1] = nmap * 0.5 + 0.5
new['roughness'][py0:py1, px0:px1] = np.clip(rough_cav * 0.85, 0.3, 0.6)
cx0, cy0, cx1, cy1 = R['cavity']['cap_rect']
cp = (slice(int(round((1 - cy1) * S)), int(round((1 - cy0) * S))), slice(int(round(cx0 * S)), int(round(cx1 * S))))
new['base_color'][cp] = ramp[4] * 0.12
new['normal'][cp] = (0.5, 0.5, 1.0)
new['roughness'][cp] = rough_cav * 0.85
report.update({'cavity_px': [px0, py0, Wd, H], 'mouth_palette_texels': int(len(pal)),
               'mouth_ramp_lo_hi': [ramp[0].round(3).tolist(), ramp[-1].round(3).tolist()],
               'cavity_roughness': round(rough_cav * 0.85, 3)})
OUT.mkdir(parents=True, exist_ok=True)
for k, img in new.items():
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT / f'texture_urls_0_{k}.png')
json.dump(report, open(OUT / 'carry_report.json', 'w'), indent=1)
print('CARRIED', json.dumps(report))
