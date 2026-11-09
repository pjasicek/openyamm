#!/usr/bin/env python3
"""Texture pass maps for the Terror (claude_shared/TEXTURE_QUALITY_PASS.md): meshy/terror_retexture_v2 (4K paint on the
xatlas UVs of work/uv_v3.blend) -> work/retexture_v3/texture_urls_0_{base_color,normal,roughness}.png, 2K, each 4K map
downsampled once. Replaces head_fix_tex.py on the new layout; compose.py reads the result.

No squeeze and no band any more: every face has its own packed texels, so nothing is carried from the old layout. What
stays from the head fix, rebuilt on the new UVs:
- The mouth bag's paint (faces mouth_bag = 1, 2; work/uv_v3_bag.npz): Meshy cannot see inside the mouth, so the flesh is
  procedural as in head_fix_tex.py, from the same palette (the approved Meshy mouth's colours, sampled from the v1 paint
  through head_fix.json's cavity_old_uv) and the same recipe. It is painted in the bag's own rectangle at the new density
  and carried into the atlas per triangle, turning the normal vectors with the island.
- The relocated faces (head_fix.py 'relocated': crotch, inner thighs, tentacle tips hidden in every reference view): the
  shared-texel shards are gone with the overlap. --refill repaints them from the clean surface around them in 3D as the
  head fix did, for a paint that smears there.

Usage: texpass_tex.py [--refill]
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent.parent
M = HERE / 'meshy' / 'terror_retexture_v2'
OLD = HERE / 'meshy' / 'terror_retexture_v1'
OUT = HERE / 'work' / 'retexture_v3'
R = json.load(open(HERE / 'work' / 'head_fix.json'))
B = np.load(HERE / 'work' / 'uv_v3_bag.npz')
REFILL = '--refill' in sys.argv
S = 2048
W = np.array([0.2126, 0.7152, 0.0722])
rng = np.random.default_rng(11)


def load2k(path):
    image = Image.open(path).convert('RGB')
    if image.size != (S, S):
        image = image.resize((S, S), Image.LANCZOS)
    return np.asarray(image, np.float32) / 255


new = {k: load2k(M / f'texture_urls_0_{k}.png') for k in ('base_color', 'normal', 'roughness')}
old = {k: load2k(OLD / f'texture_urls_0_{k}.png') for k in ('base_color', 'roughness')}


def tri_texels(p, eps=0.0):
    """Texel centres inside a triangle in pixel coords (x right, y down): rows, cols, barycentrics."""
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


# ---------------------------------------------------------------- the approved mouth's palette (v1 paint, old layout)
cav_uv = np.array(R['cavity_old_uv']).reshape(-1, 3, 2)
hits = [h for h in (tri_texels(px(t)) for t in cav_uv) if h is not None]
samp = np.concatenate([old['base_color'][h[0], h[1]] for h in hits])
h_red = (samp[:, 0] > samp[:, 1] * 1.25) & (samp[:, 0] > 0.12)
pal = samp[h_red]
pal = pal[np.argsort(pal @ W)]
ramp = np.array([pal[int(q * (len(pal) - 1))] for q in np.linspace(0.03, 0.97, 64)])
ramp = ndimage.uniform_filter1d(ramp, 5, axis=0)
rough_cav = float(np.median(np.concatenate([old['roughness'][h[0], h[1], 1] for h in hits])))

# ---------------------------------------------------------------- cavity paint in the bag's rectangle (head_fix_tex.py)
cav = R['cavity']
x0c, y0c, x1c, y1c = cav['uv_rect']
kind, uv_old, uv_new = B['kind'], B['uv_old'], B['uv_new']


def area(u):
    return np.abs((u[:, 1, 0] - u[:, 0, 0]) * (u[:, 2, 1] - u[:, 0, 1])
                  - (u[:, 2, 0] - u[:, 0, 0]) * (u[:, 1, 1] - u[:, 0, 1])) / 2


ratio = float(np.sqrt(area(uv_new[kind == 1]).sum() / area(uv_old[kind == 1]).sum()))   # new texels / old texels
Wd, H = int(np.ceil((x1c - x0c) * S * ratio)), int(np.ceil((y1c - y0c) * S * ratio))


def value_noise(h, w, cell, seed):
    cell = max(int(round(cell * ratio)), 1)
    g = np.random.default_rng(seed).random((h // cell + 3, w // cell + 3))
    return ndimage.zoom(g, cell, order=3)[:h, :w]


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
height = 0.6 * rugae * roof + 0.4 * gum + 0.25 * noise
gy, gx = np.gradient(ndimage.gaussian_filter(height, ratio))
nxy = np.stack([-gx * 2.0 * ratio, gy * 2.0 * ratio], -1)                        # (old u, old v) tangent axes

# ---------------------------------------------------------------- into the atlas, triangle by triangle
# the island's turn: orthogonal part of the old -> new UV map (normal-map vectors live in UV axes)
d_old = np.stack([uv_old[kind == 1][:, 1] - uv_old[kind == 1][:, 0], uv_old[kind == 1][:, 2] - uv_old[kind == 1][:, 0]], 1)
d_new = np.stack([uv_new[kind == 1][:, 1] - uv_new[kind == 1][:, 0], uv_new[kind == 1][:, 2] - uv_new[kind == 1][:, 0]], 1)
u_svd, _, vt = np.linalg.svd(np.einsum('nia,nib->ab', d_new, d_old))
turn = u_svd @ vt
assert np.linalg.det(turn) > 0, 'xatlas does not mirror islands'
nxy = nxy @ turn.T
nrm = np.concatenate([nxy, np.ones((H, Wd, 1))], -1)
nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
nrm = nrm * 0.5 + 0.5
rough_val = float(np.clip(rough_cav * 0.85, 0.3, 0.6))
painted = 0


def sample(img, x, y):
    return np.stack([ndimage.map_coordinates(img[..., c], [y, x], order=1, mode='nearest') for c in range(3)], -1)


for k, tn, to in zip(kind, uv_new, uv_old):
    hit = tri_texels(px(tn), -0.05)
    if hit is None:
        continue
    iy, ix, bc = hit
    if k == 1:
        q = bc @ to
        x = (q[:, 0] - x0c) / (x1c - x0c) * Wd - 0.5
        y = (1 - (q[:, 1] - y0c) / (y1c - y0c)) * H - 0.5
        new['base_color'][iy, ix] = sample(col, x, y)
        new['normal'][iy, ix] = sample(nrm, x, y)
    else:
        new['base_color'][iy, ix] = ramp[4] * 0.12
        new['normal'][iy, ix] = (0.5, 0.5, 1.0)
    new['roughness'][iy, ix] = rough_val
    painted += len(iy)
report = {'cavity_texels': painted, 'cavity_ratio': round(ratio, 4), 'turn': turn.round(3).tolist(),
          'mouth_palette_texels': int(len(pal)), 'cavity_roughness': round(rough_val, 3)}

# ---------------------------------------------------------------- relocated faces (optional)
if REFILL:
    d = np.load(HERE / 'work' / 'uv3d_terror_v3.npz')
    fill_rc, fill_xyz, fill_n = [], [], []
    for tn, xyz in zip(B['rel_uv_new'], B['rel_xyz']):
        hit = tri_texels(px(tn), -0.02)
        if hit is None:
            continue
        iy, ix, bc = hit
        n = np.cross(xyz[1] - xyz[0], xyz[2] - xyz[0])
        fill_rc.append(np.stack([iy, ix], 1))
        fill_xyz.append(bc @ xyz)
        fill_n.append(np.repeat((n / (np.linalg.norm(n) + 1e-12))[None], len(iy), 0))
    fill_rc, fill_xyz, fill_n = map(np.concatenate, (fill_rc, fill_xyz, fill_n))
    fill_mask = np.zeros((S, S), bool)
    fill_mask[fill_rc[:, 0], fill_rc[:, 1]] = True
    pool_rc, pool_xyz, pool_n = [], [], []
    valid = np.zeros((S, S), bool)
    for t in range(len(d['uv'])):
        hit = tri_texels(px(d['uv'][t]))
        if hit is None:
            continue
        iy, ix, bc = hit
        valid[iy, ix] = True
        pool_rc.append(np.stack([iy[::2], ix[::2]], 1))
        pool_xyz.append(bc[::2] @ d['xyz'][t])
        pool_n.append(np.repeat(d['normal'][t][None], len(iy[::2]), 0))
    pool_rc, pool_xyz, pool_n = map(np.concatenate, (pool_rc, pool_xyz, pool_n))
    valid &= ~fill_mask
    clean = ~fill_mask[pool_rc[:, 0], pool_rc[:, 1]]
    pool_rc, pool_xyz, pool_n = pool_rc[clean], pool_xyz[clean], pool_n[clean]
    dist, idx = cKDTree(pool_xyz).query(fill_xyz, k=24)
    wgt = np.where((pool_n[idx] * fill_n[:, None]).sum(-1) > 0.3, 1 / (dist + 0.004) ** 2, 0)
    wgt[wgt.sum(1) == 0] = 1
    wgt /= wgt.sum(1, keepdims=True)

    def norm_blur(img, mask, sigma):
        m = ndimage.gaussian_filter(mask.astype(np.float32), sigma)
        return np.stack([ndimage.gaussian_filter(img[..., c] * mask, sigma) for c in range(3)], -1) / \
            np.maximum(m, 1e-4)[..., None]

    lab, _ = ndimage.label(fill_mask)
    reg_of = lab[fill_rc[:, 0], fill_rc[:, 1]]
    inside = ndimage.distance_transform_edt(valid)
    kd_pool = cKDTree(pool_xyz)
    hp, vals = {}, {}
    for k in new:
        low = norm_blur(new[k], valid, 4)
        hp[k] = np.where(valid[..., None], new[k] - low, 0)
        vals[k] = (low[pool_rc[idx][..., 0], pool_rc[idx][..., 1]] * wgt[..., None]).sum(1)
    for r in np.unique(reg_of):
        m = reg_of == r
        _, j = kd_pool.query(fill_xyz[m].mean(0))
        cy, cx = pool_rc[j]
        win = inside[max(cy - 40, 0):cy + 41, max(cx - 40, 0):cx + 41]
        oy, ox = np.unravel_index(np.argmax(np.minimum(win, 12)), win.shape)
        cy, cx = max(cy - 40, 0) + oy, max(cx - 40, 0) + ox
        h = int(max(min(inside[cy, cx], 12), 2))
        rel = fill_rc[m] - fill_rc[m].mean(0)
        ty = np.abs((rel[:, 0] + 2 * h) % (4 * h) - 2 * h) - h
        tx = np.abs((rel[:, 1] + 2 * h) % (4 * h) - 2 * h) - h
        sy, sx = np.clip(cy + ty, 0, S - 1), np.clip(cx + tx, 0, S - 1)
        for k in ('base_color', 'roughness'):
            vals[k][m] += np.stack([ndimage.map_coordinates(hp[k][..., c], [sy, sx], order=1, mode='nearest')
                                    for c in range(3)], -1)
    for k in new:
        new[k][fill_rc[:, 0], fill_rc[:, 1]] = np.clip(vals[k], 0, 1)
    report['refilled_texels'] = int(len(fill_rc))

OUT.mkdir(parents=True, exist_ok=True)
for k, img in new.items():
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT / f'texture_urls_0_{k}.png')
json.dump(report, open(OUT / 'carry_report.json', 'w'), indent=1)
print('TEXPASS', json.dumps(report))
