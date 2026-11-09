"""Procedural wing texture set for the v2 procedural wings (system Python, numpy): 2048^2 base colour, normal, height,
region weights and material classes in the wing UV layout written by scripts/build_wing.py.

Native look (restored m182sa2, wb0, ad4): a light grey-green membrane covered in a fine reticulated pattern (small
irregular cells with darker green borders and a few pale/yellow flecks), darker veins running out from the finger
bones toward the trailing edge, dark green bones with small scales, ivory claws. Everything is computed from
physical coordinates (membrane planform metres, tube arc length x circumference), so the scale size is the same on
every piece and both membrane layers show the same paint. No lighting is baked (AO comes from the shared bake).
Usage: wing_texture.py <wing_left.npz> <out_prefix>   (writes <prefix>_basecolor_2k.png, _normal_2k.png,
_height_2k.png, _regions.npz, _material_classes.png)"""
import json, sys
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

N = 2048
w = np.load(sys.argv[1]); out = sys.argv[2]
L = json.loads(str(w['layout'])); pts2 = w['pts2']; outline = w['outline']
rng = np.random.default_rng(182)

col, row = np.meshgrid(np.arange(N) + .5, np.arange(N) + .5)
U = col / N; V = 1 - row / N                     # UV of each texel centre (v up)
rgb = np.zeros((N, N, 3)); height = np.zeros((N, N)); region = np.zeros((N, N), int) - 1; classes = np.zeros((N, N), np.uint8)


def voronoi(x, y, cell, jitter=.85, seed=0, aniso=1.):
    """F1, F2 distances (in cell units) and a per-cell random value, for points (x, y) in metres."""
    r = np.random.default_rng(seed); gx = x / cell; gy = y / (cell * aniso)
    ix = np.floor(gx).astype(int); iy = np.floor(gy).astype(int)
    f1 = np.full(x.shape, 9.); f2 = np.full(x.shape, 9.); idv = np.zeros(x.shape)
    table = r.random((4096, 3))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            cx = ix + dx; cy = iy + dy; h = ((cx * 73856093) ^ (cy * 19349663)) & 4095
            px = cx + .5 + (table[h, 0] - .5) * jitter; py = cy + .5 + (table[h, 1] - .5) * jitter
            d = np.hypot(gx - px, gy - py)
            closer = d < f1
            f2 = np.where(closer, f1, np.minimum(f2, d)); idv = np.where(closer, table[h, 2], idv); f1 = np.minimum(f1, d)
    return f1, f2, idv


def smooth_noise(x, y, scale, seed):
    r = np.random.default_rng(seed); g = r.normal(size=(64, 64)); g = ndimage.gaussian_filter(g, 1.5, mode='wrap'); g /= g.std()
    return ndimage.map_coordinates(g, [(y / scale) % 64, (x / scale) % 64], order=1, mode='wrap')


# ---------------------------------------------------------------- membrane
M = L['membrane']; o = np.array(M['origin_uv']); k = M['scale']; pmin = np.array(M['planform_min'])
mu = (U - o[0]) / k + pmin[0]; mv = (V - o[1]) / k + pmin[1]
box = (U >= o[0] - .004) & (V >= o[1] - .004) & (U <= o[0] + (pts2[:, 0].max() - pmin[0] + .004) * k + .004) & (V <= o[1] + (pts2[:, 1].max() - pmin[1] + .004) * k + .004)
mem = box.copy()
x, y = mu[mem], mv[mem]
f1, f2, cid = voronoi(x, y, .0075, seed=1)
border = np.clip((f2 - f1) / .16, 0, 1)                      # 0 on a cell border
cellshade = 1 - .22 * f1 ** 2 + .07 * (cid - .5)
fine1, fine2, _ = voronoi(x, y, .0028, seed=2)
fine = np.clip((fine2 - fine1) / .25, 0, 1)
low = smooth_noise(x, y, .03, 3)
lum = (.80 * cellshade) * (.55 + .45 * border ** .7) * (.93 + .07 * fine)   # no low-frequency variation: the ramp turns it into blotches
# veins: branching random walks from the bones toward the trailing edge
W_ = np.array([.198, -.044]); E_ = np.array([.088, .02])
fingers = [(W_, np.array([.506, .337])), (W_, np.array([.255, .374])), (E_, np.array([.06, .28]))]
def inside_poly(p, poly):
    x, y = p[:, 0], p[:, 1]; res = np.zeros(len(p), bool); j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]; xj, yj = poly[j]
        res ^= ((yi > y) != (yj > y)) & (x < (xj - xi) * (y - yi) / (yj - yi + 1e-18) + xi); j = i
    return res
vein_pts = []
for a, b in fingers + [(np.array([0., 0.]), W_)]:
    for t in np.linspace(.15, .9, 6):
        p = a + (b - a) * t; d = b - a; n_ = np.array([d[1], -d[0]]) / np.linalg.norm(d)
        for side in (1, -1):
            if rng.random() < .35: continue
            q = p.copy(); heading = n_ * side * .8 + d / np.linalg.norm(d) * .6; heading /= np.linalg.norm(heading)
            for step in range(int(rng.integers(6, 16))):
                heading = heading + rng.normal(size=2) * .25; heading /= np.linalg.norm(heading)
                q2 = q + heading * .004
                if not inside_poly(q2[None], outline)[0]: break
                vein_pts += list(q + (q2 - q) * np.linspace(0, 1, 6)[:, None]); q = q2
vein_pts = np.array(vein_pts)
dv = cKDTree(vein_pts).query(np.c_[x, y])[0]
vein = np.exp(-(dv / .0007) ** 2)
lum *= 1 - .30 * vein
fleck = (rng.random(x.shape) < .0009)
lum = np.where(fleck, lum * 1.25, lum)
mem_rgb = np.c_[.66 * lum, .73 * lum, .58 * lum]
mem_rgb = np.clip(mem_rgb, 0, 1)
rgb[mem] = mem_rgb; height[mem] = .35 * (1 - f1 ** 2) * border + .25 * vein - .2 * (1 - border)
region[mem] = 1; classes[mem] = 3

# ---------------------------------------------------------------- tubes (bones)
for i in range(L['tube_count']):
    name = L['pieces'][i + 1]; T = L[name]; o = np.array(T['origin_uv']); kt = T['scale']; h = T['height_uv']
    m = (U >= o[0] - .003) & (U <= o[0] + T['length'] * kt + .006) & (V >= o[1] - .003) & (V <= o[1] + 1.2 * h)
    s = (U[m] - o[0]) / kt; a = ((V[m] - o[1]) / h) % 1.; circ = h / kt
    x, y = s, a * circ
    f1, f2, cid = voronoi(x, y, .0042, seed=10 + i, aniso=.8)
    edge = np.clip((f2 - f1) / .22, 0, 1)
    lum = (.30 + .05 * (cid - .5)) * (.55 + .45 * edge) * (1 - .25 * f1 ** 2)
    knuckle = np.zeros_like(s)
    for jt in (0., T['length']):
        knuckle += np.exp(-((s - jt) / .01) ** 2)
    lum *= 1 - .15 * knuckle
    rgb[m] = np.c_[.55 * lum, .80 * lum, .50 * lum]; height[m] = .5 * (1 - f1 ** 2) * edge - .3 * (1 - edge)
    region[m] = 0; classes[m] = 1

# ---------------------------------------------------------------- claws (shared patch)
cb = L['claws']['box']; m = (U >= cb[0] - .004) & (U <= cb[2] + .004) & (V >= cb[1] - .004) & (V <= cb[3] + .004)
f = np.clip((U[m] - cb[0]) / (cb[2] - cb[0]), 0, 1)
base = np.array([.62, .55, .38]); tip = np.array([.93, .90, .80])
streak = .04 * np.sin((V[m] - cb[1]) * 260)
rgb[m] = np.clip(base * (1 - f[:, None] ** .7) + tip * f[:, None] ** .7 + streak[:, None], 0, 1); height[m] = 0; region[m] = -1; classes[m] = 4

# ---------------------------------------------------------------- write
img = np.uint8(np.clip(rgb, 0, 1) * 255 + .5)
Image.fromarray(img).save(out + '_basecolor_2k.png')
hgt = ndimage.gaussian_filter(height, .7)
gy, gx = np.gradient(hgt)                              # rows go down (v decreases), columns right (u increases)
strength = 2.2
n = np.dstack([-gx * strength, gy * strength, np.ones_like(hgt)]); n /= np.linalg.norm(n, axis=-1, keepdims=True)
Image.fromarray(np.uint8((n * .5 + .5) * 255 + .5)).save(out + '_normal_2k.png')
Image.fromarray(np.uint8(np.clip(hgt * .5 + .5, 0, 1) * 255)).save(out + '_height_2k.png')
np.savez_compressed(out + '_regions.npz', region=region)
Image.fromarray(classes).save(out + '_material_classes.png')
print('WING_TEXTURE', {'membrane_texels': int((region == 1).sum()), 'bone_texels': int((region == 0).sum()), 'claw_texels': int((classes == 4).sum()),
                       'veins': len(vein_pts)})
