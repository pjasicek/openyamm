#!/usr/bin/env python3
"""PeasantM5 tier region mask and ramps for the body set (copy of mm9_peasantm1_claude/scripts/tiers_pm1.py, adapted).

MM9 PeasantM5 skins: A (PEASANTM5A, row 48 Shopkeeper) warm tan-brown linen shirt; B (PEASANTM5B, row 46 Town) the same cut in
a darker brown woven cloth (plus a silver medallion on a chain, not modelled: deviation in the README). Trousers, belt, boots and
neckline braid are the same design in both. Regions:
  R (0) shirt: every shirt texel (body, sleeves, braid) above the boots, belt band excluded;
  G (1) trousers: grey knit leg texels between the boot tops and the shirt hem.
Both tiers take MM9's own colours by luminance quantile x the gain that maps MM9 A's shirt onto our paint (the 4K paint came
out more yellow-tan than MM9's warm brown, so tier A is pulled to MM9 A too); trousers MM9 knit at TROUSER_GAIN x the skin.
Writes textures/pm5_region_mask.png, textures/pm5_ramps.json, textures/pm5_tier_preview_<t>.png.
Usage (project folder): tiers_pm5.py <export glb (unmirrored body_tex)> <graded basecolor png> <classes png>"""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from pygltflib import GLTF2

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as RV

GLB, BASE, CLASSES = sys.argv[1:4]
N = 1024
CAP = 0.55            # share of the upper arm (shoulder -> elbow) the B short sleeve covers (MM9 B render)
FEATHER = 0.02        # m, soft edge of the cap line
W = np.array([0.2126, 0.7152, 0.0722])
g = GLTF2().load(GLB)
blob = g.binary_blob()


def acc(i):
    a = g.accessors[i]
    bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a.type]
    dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a.componentType]
    return np.frombuffer(blob, dt, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)


mesh = next(m for m in g.meshes if any(g.materials[p.material].name == 'PeasantM5' for p in m.primitives))
prim = next(p for p in mesh.primitives if g.materials[p.material].name == 'PeasantM5')
P = acc(prim.attributes.POSITION).astype(np.float64)
UV = acc(prim.attributes.TEXCOORD_0).astype(np.float64)
JN = acc(prim.attributes.JOINTS_0).astype(int)
WT = acc(prim.attributes.WEIGHTS_0).astype(np.float64)
TRI = acc(prim.indices).reshape(-1, 3).astype(int)
skin = g.skins[0]
names = [g.nodes[j].name for j in skin.joints]
IBM = acc(skin.inverseBindMatrices).reshape(-1, 4, 4)
head = {n: np.linalg.inv(IBM[k].T)[:3, 3] for k, n in enumerate(names)}   # glTF column-major
dom = JN[np.arange(len(JN)), WT.argmax(1)]

# rasterise: texel -> position, dominant joint
pos = np.full((N, N, 3), np.nan)
jt = -np.ones((N, N), int)
for t in TRI:
    uv = UV[t] * N
    # glTF UV: v grows down the image (compose_texpass.py coverage), no flip
    x0, y0 = np.floor(uv.min(0)).astype(int)
    x1, y1 = np.ceil(uv.max(0)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0)
    x1, y1 = min(x1, N - 1), min(y1, N - 1)
    if x1 < x0 or y1 < y0:
        continue
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    a, b, c = uv
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-12:
        continue
    l0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
    l1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
    l2 = 1 - l0 - l1
    ins = (l0 >= -1e-3) & (l1 >= -1e-3) & (l2 >= -1e-3)
    if not ins.any():
        continue
    L = np.stack([l0, l1, l2], -1)[ins]
    yy, xx = (ys[ins] - 0.5).astype(int), (xs[ins] - 0.5).astype(int)
    pos[yy, xx] = L @ P[t]
    jt[yy, xx] = dom[t][L.argmax(1)]
cov = jt >= 0

base = np.asarray(Image.open(BASE).convert('RGB').resize((N, N), Image.LANCZOS), np.float64) / 255
cls = np.asarray(Image.open(CLASSES).convert('L').resize((N, N), Image.NEAREST))
lin = RV.srgb_to_linear(base)
lum = lin @ W
mx, mn = base.max(2), base.min(2)
sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
r, gg, bb = base[..., 0], base[..., 1], base[..., 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (gg - bb), 2 * r - gg - bb)) % 360

jn = np.array(names)[np.clip(jt, 0, None)]
low = np.char.lower(jn.astype(str))
is_arm = cov & ((np.char.find(low, 'clavicle') >= 0) | (np.char.find(low, 'arm') >= 0) | (np.char.find(low, 'hand') >= 0))
boot_top = 0.5 * (head['Bip01 L Calf'][1] + head['Bip01 L Foot'][1]) + 0.08     # GLB y up
belt = cov & (pos[..., 1] > 0.94) & (pos[..., 1] < 1.07) & (lum < np.median(lum[cov]) * 0.8)
shirtc = cov & (sat > 0.25) & (hue > 15) & (hue < 60) & (cls != 9) & (pos[..., 1] > boot_top) & ~belt
legs = cov & ((np.char.find(low, 'thigh') >= 0) | (np.char.find(low, 'calf') >= 0))
trousers = legs & (sat < 0.3) & (pos[..., 1] > boot_top)
shirt_w = (shirtc & ~trousers).astype(float)
trousers_w = trousers.astype(float)


def pad_soft(w):
    w = ndimage.gaussian_filter(w, 0.8) * cov + w * 0       # feather inside the islands
    w = np.where(cov, np.maximum(w, 0), 0)
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    return w[iy, ix]                                          # pad into gutters and cracks


wR, wG = pad_soft(shirt_w), pad_soft(trousers_w)
T = Path('textures')
RV.write_mask([wR, wG], T / 'pm5_region_mask.png', size=N)
TROUSER_GAIN = 1.3

# MM9 skin regions (256 px): jacket body, sleeve; same rectangles in both skins
REG = {'shirt': (12, 95, 130, 180), 'trousers': (146, 90, 188, 215)}   # x0, y0, x1, y1 in the 256 px skins (read off mm9_skin_x4)


def skin_pixels(tier, key):
    a = np.asarray(Image.open(f'source/mm9/skins/pm5{tier}.png').convert('RGB'), np.float64) / 255
    x0, y0, x1, y1 = REG[key]
    return RV.srgb_to_linear(a[y0:y1, x0:x1].reshape(-1, 3))


report = {}
ramps = {'pm5_a': [], 'pm5_b': []}
for k, (key, w) in enumerate((('shirt', wR), ('trousers', wG))):
    core = w > 0.9
    la = skin_pixels('a', key)
    lb = skin_pixels('b', key)
    gain = np.median(lum[core]) / np.median(la @ W) if key != 'trousers' else TROUSER_GAIN
    q = np.zeros_like(lum)
    rank = np.argsort(np.argsort(lum[core]))
    q[core] = rank / max(len(rank) - 1, 1)

    def quantile_target(px):
        order = np.argsort(px @ W)
        t_lin = lin.copy()
        idx = np.clip((q[core] * (len(order) - 1)).astype(int), 0, len(order) - 1)
        t_lin[core] = np.clip(px[order[idx]] * gain, 0, 1)
        return np.where(t_lin <= 0.0031308, t_lin * 12.92, 1.055 * np.power(np.clip(t_lin, 0, 1), 1 / 2.4) - 0.055)
    target = quantile_target(lb)
    target_a = quantile_target(la)
    fit, err = RV.fit_ramps(base, {'pm5_a': target_a, 'pm5_b': target}, w)
    for v in ramps:
        ramps[v].append(fit[v])
    report[key] = {'texels_core': int(core.sum()), 'gain_mm9a_to_ours': round(float(gain), 3), 'fit_8bit': err}
doc = {'variants': ['pm5_a', 'pm5_b'],
       'materials': [{'base': 'PeasantM5', 'prefix': 'PeasantM5', 'mask': 'pm5_region_mask.png', 'ramps': ramps}],
       'regions': ['R shirt (A warm tan-brown linen, B darker brown woven; MM9 colours by luminance quantile)',
                   'G trousers (both tiers MM9 knit at %.2f x the skin colour)' % TROUSER_GAIN],
       'source': 'MM9 PEASANTM5A (a: row 48 Shopkeeper), PEASANTM5B (b: row 46 Town); tiers_pm5.py', 'report': report}
json.dump(doc, open(T / 'pm5_ramps.json', 'w'), indent=1)


def apply(v):
    out = lin.copy()
    for k, w in enumerate((wR, wG)):
        rp = ramps[v][k]
        lo, hi = rp['range']
        tt = np.clip((lum - lo) / (hi - lo), 0, 1) * 15
        i0 = np.floor(tt).astype(int).clip(0, 15)
        i1 = (i0 + 1).clip(0, 15)
        f = (tt - i0)[..., None]
        C = np.array(rp['colors'])
        col = C[i0] * (1 - f) + C[i1] * f
        out = out * (1 - w[..., None]) + col * w[..., None]
    s = np.where(out <= 0.0031308, out * 12.92, 1.055 * np.power(np.clip(out, 0, 1), 1 / 2.4) - 0.055)
    Image.fromarray(np.uint8(np.clip(s, 0, 1) * 255)).save(T / f'pm5_tier_preview_{v}.png')


for v in ramps:
    apply(v)
print('TIERS', json.dumps(report))
