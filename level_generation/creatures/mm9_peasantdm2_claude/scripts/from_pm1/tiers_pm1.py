#!/usr/bin/env python3
"""Tier region mask and ramps for the body set (CLAUDE_CREATURE_TEXTURES.md: one shared set, region mask + ramps).

MM9 PeasantM1 skins: A (PEASANTM1A, rows 43 and 296) olive-brown wool jacket with long sleeves; B (PEASANTM1B, row 56)
the same cut in rust-red wool with SHORT sleeves over the cream shirt sleeves. Trousers, boots and shirt are the same
pixels in both skins (medians equal to the level). So two regions:
  R (0) jacket: every jacket texel (body, collar/hood, the shoulder cap of the sleeve);
  G (1) sleeve: arm texels past CAP of the upper arm (MM9 B: the cream shirt sleeve; MM9 A: the jacket sleeve).
Texels -> rest 3D position and dominant joint by rasterising the export GLB's body primitive in UV space. Jacket =
olive wool by colour (not the cream shirt, the grey trousers, the drawstring or metal) above the boot tops.

Ramps per tier from that tier's own MM9 pixels: A's ramp is fitted to our graded paint itself (A = the accepted look).
B's target per texel is the MM9 B region colour at the texel's luminance quantile, times the gain that maps MM9 A's
region onto our paint (median linear luminance), so B relates to its skin as our A relates to MM9 A; fit_ramps then
solves the 16 stops under the shader's lookup. Writes textures/pm1_region_mask.png, textures/pm1_ramps.json and a
preview textures/pm1_tier_preview_<t>.png (what the shader makes of each tier).
Usage (project folder): tiers_pm1.py <export glb> <graded basecolor png> <classes png>"""
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


mesh = next(m for m in g.meshes if any(g.materials[p.material].name == 'PeasantM1' for p in m.primitives))
prim = next(p for p in mesh.primitives if g.materials[p.material].name == 'PeasantM1')
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
wool = cov & (sat > 0.3) & (hue > 22) & (hue < 70) & (lum > 0.004) & (cls != 9)
shirt = cov & (sat < 0.3) & (lum > 0.12)
jacket = wool & ~shirt & (pos[..., 1] > boot_top)
# arms: everything painted on the arm is sleeve (the hands are in the head set); t along the upper arm
t = np.zeros((N, N))
for s in 'LR':
    u, f = head[f'Bip01 {s} UpperArm'], head[f'Bip01 {s} Forearm']
    ax = (f - u) / np.linalg.norm(f - u)
    side = np.sign(u[0])
    m = cov & (np.sign(np.nan_to_num(pos[..., 0])) == side)
    tt = (np.nan_to_num(pos) - u) @ ax / np.linalg.norm(f - u)
    t[m] = tt[m]
arm_cloth = is_arm & (sat > 0.2) & (lum > 0.004)
sleeve_w = np.clip((t - CAP) / (2 * FEATHER / 0.21) + 0.5, 0, 1) * arm_cloth
jacket_w = (jacket | arm_cloth).astype(float) * (1 - sleeve_w)


def pad_soft(w):
    w = ndimage.gaussian_filter(w, 0.8) * cov + w * 0       # feather inside the islands
    w = np.where(cov, np.maximum(w, 0), 0)
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    return w[iy, ix]                                          # pad into gutters and cracks


# trousers (B channel, 2026-11-01 viewer check): the paint's knit trousers came out near-white with dark stripes where
# MM9's (the same pixels in both skins) are a dark grey-brown knit; grey texels on the legs between the boot tops and the
# jacket hem take MM9's trouser colours (by luminance quantile) at TROUSER_GAIN x MM9 (albedo vs the skin's baked shade)
legs = cov & ((np.char.find(low, 'thigh') >= 0) | (np.char.find(low, 'calf') >= 0) | (np.char.find(low, 'spine') >= 0)
              | (np.char.find(low, 'bone') >= 0))
hip_top = head['Bip01 Spine'][1] - 0.02
trousers_w = (legs & (sat < 0.28) & (pos[..., 1] > boot_top) & (pos[..., 1] < hip_top) & ~jacket).astype(float)
wR, wG, wB = pad_soft(jacket_w), pad_soft(sleeve_w), pad_soft(trousers_w)
T = Path('textures')
RV.write_mask([wR, wG, wB], T / 'pm1_region_mask.png', size=N)
TROUSER_GAIN = 1.3

# MM9 skin regions (256 px): jacket body, sleeve; same rectangles in both skins
REG = {'jacket': (30, 95, 130, 250), 'sleeve': (160, 5, 225, 75), 'trousers': (145, 85, 235, 195)}


def skin_pixels(tier, key):
    a = np.asarray(Image.open(f'source/mm9/skins/pm1{tier}.png').convert('RGB'), np.float64) / 255
    x0, y0, x1, y1 = REG[key]
    return RV.srgb_to_linear(a[y0:y1, x0:x1].reshape(-1, 3))


report = {}
ramps = {'pm1_a': [], 'pm1_b': []}
for k, (key, w) in enumerate((('jacket', wR), ('sleeve', wG), ('trousers', wB))):
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
    target_a = base if key != 'trousers' else quantile_target(la)
    fit, err = RV.fit_ramps(base, {'pm1_a': target_a, 'pm1_b': target}, w)
    for v in ramps:
        ramps[v].append(fit[v])
    report[key] = {'texels_core': int(core.sum()), 'gain_mm9a_to_ours': round(float(gain), 3), 'fit_8bit': err}
doc = {'variants': ['pm1_a', 'pm1_b'],
       'materials': [{'base': 'PeasantM1', 'prefix': 'PeasantM1', 'mask': 'pm1_region_mask.png', 'ramps': ramps}],
       'regions': ['R jacket (A olive wool, B rust-red wool incl. the short sleeve cap)',
                   'G sleeve past %.0f %% of the upper arm (A jacket sleeve, B cream shirt sleeve)' % (CAP * 100),
                   'B trousers (both tiers MM9 knit at %.2f x the skin colour)' % TROUSER_GAIN],
       'source': 'MM9 PEASANTM1A (a: rows 43, 296), PEASANTM1B (b: row 56); tiers_pm1.py', 'report': report}
json.dump(doc, open(T / 'pm1_ramps.json', 'w'), indent=1)


def apply(v):
    out = lin.copy()
    for k, w in enumerate((wR, wG, wB)):
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
    Image.fromarray(np.uint8(np.clip(s, 0, 1) * 255)).save(T / f'pm1_tier_preview_{v}.png')


for v in ramps:
    apply(v)
print('TIERS', json.dumps(report))
