#!/usr/bin/env python3
"""Tier region mask and ramps for the PeasantDM2 body set (CLAUDE_CREATURE_TEXTURES.md: one shared set, region mask + ramps).

MM9 PeasantDM2 skins: A (PEASANTDM2A, row 9 Commoner, the shared paint) dark charcoal-brown ribbed knit tunic, braided
grey cord belt, dark purple-brown striped trousers with orange mending marks, brown leather boots with gold ornaments;
B (PEASANTDM2B, no MONSTERS row) a brown leather laced tunic, a dark brown leather belt with a buckle, dark brown knit
trousers and lighter orange-brown boots; the faces are different men (tier B head image, tier_head.py). Regions:
  R (0) tunic: the knit tunic (body, sleeves, skirt), above the trousers, not the belt, skin or metal;
  G (1) trousers: below the hem on the thighs/upper calves, purple-red hue, not boot leather;
  B (2) boots: saturated leather below the boot top (not the gold ornaments: metal class or bright gold);
  A (3) belt: the braided cord band at the waist (light, low saturation, Y 0.585..0.65).
B's pattern differences (lacing, buckle) are not reproduced: B is A's paint recoloured per region.
Ramps: A fitted to our graded paint itself (A = the accepted look), except belt and boots (MATCH_A: MM9 A's own colours). B's target per texel is the MM9 B region colour at the
texel's luminance quantile, times the gain that maps MM9 A's region onto our paint (median linear luminance). MM9 skin
regions come from the MM9 mesh's own UVs and joints (scripts/mm9_skin_labels.py -> work/mm9_skin_labels.npz).
Writes textures/pdm2_region_mask.png, textures/pdm2_ramps.json, textures/pdm2_tier_preview_<t>.png.
Usage (project folder): tiers_pdm2.py <export glb> <graded basecolor png> <classes png>"""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from pygltflib import GLTF2

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as RV

GLB, BASE, CLASSES = sys.argv[1:4]
N = 1024
W = np.array([0.2126, 0.7152, 0.0722])
g = GLTF2().load(GLB)
blob = g.binary_blob()


def acc(i):
    a = g.accessors[i]
    bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a.type]
    dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a.componentType]
    return np.frombuffer(blob, dt, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)


mesh = next(m for m in g.meshes if any(g.materials[p.material].name == 'PeasantDM2' for p in m.primitives))
prim = next(p for p in mesh.primitives if g.materials[p.material].name == 'PeasantDM2')
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
Y = np.nan_to_num(pos[..., 1], nan=-1)
BOOT_TOP = float(os.environ.get('BOOT_TOP', 0.31))
HEM = float(os.environ.get('HEM', 0.40))
BELT = (float(os.environ.get('BELT_LO', 0.585)), float(os.environ.get('BELT_HI', 0.65)))
legj = np.char.find(low, 'thigh') >= 0
calfj = (np.char.find(low, 'calf') >= 0) | (np.char.find(low, 'foot') >= 0) | (np.char.find(low, 'toe') >= 0)
gold = (hue > 30) & (hue < 60) & (sat > 0.45) & (lum > 0.15)
skin = (hue > 5) & (hue < 40) & (sat > 0.2) & (sat < 0.8) & (lum > 0.10)
metal = cls == 9
leather = cov & (sat > 0.8) & (hue > 15) & (hue < 40) & (Y < BOOT_TOP + 0.03) & ~metal & ~gold
clean = lambda m: ndimage.binary_opening(ndimage.binary_closing(m, iterations=2), iterations=1) & cov
boots = clean(leather & (calfj | (Y < BOOT_TOP)))
redhue = (hue < 20) | (hue > 300)
trousers = clean(cov & ~boots & ~metal & ~gold & ~skin & (Y < HEM + 0.07) & (Y > 0.12) & (legj | calfj | (redhue & (Y < HEM))) & (redhue | legj))
belt = clean(cov & (Y > BELT[0]) & (Y < BELT[1]) & (lum > 0.03) & (sat < 0.5) & ~metal & ~skin)
# the braid's dark gaps fail the light test: grow the light braid texels by 3 px inside the band
belt = ndimage.binary_dilation(belt, iterations=3) & cov & (Y > BELT[0] - 0.005) & (Y < BELT[1] + 0.005) & ~skin & ~metal
tunic = clean(cov & (Y > HEM - 0.06) & ~trousers & ~belt & ~boots & ~skin & ~metal & ~gold & (lum < 0.2))


def pad_soft(w):
    w = ndimage.gaussian_filter(w.astype(float), 0.8) * cov
    w = np.where(cov, np.maximum(w, 0), 0)
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    return w[iy, ix]


masks = {'tunic': tunic, 'trousers': trousers, 'boots': boots, 'belt': belt}
WS = [pad_soft(masks[k]) for k in ('tunic', 'trousers', 'boots', 'belt')]
# feathered masks overlap at region borders: normalise so the weights never sum above 1
tot = np.maximum(sum(WS), 1.0)
WS = [w / tot for w in WS]
T = Path('textures')
RV.write_mask(WS, T / 'pdm2_region_mask.png', size=N)

LAB = np.load('work/mm9_skin_labels.npz')['lab']
BELT_ROWS = (234, 251, 22, 121)                # y0, y1, x0, x1 in the 256 px skin (both skins)
beltm = np.zeros_like(LAB, bool); beltm[BELT_ROWS[0]:BELT_ROWS[1], BELT_ROWS[2]:BELT_ROWS[3]] = True
SKREG = {'tunic': (LAB == 2) & ~beltm & (np.arange(256)[:, None] < 230), 'trousers': LAB == 4, 'boots': LAB == 5,
         'belt': beltm}


def skin_pixels(tier, key):
    a = np.asarray(Image.open(f'source/mm9/skins/pdm2{tier}.png').convert('RGB'), np.float64) / 255
    px = a[SKREG[key]]
    if key == 'boots':                          # leave the gold ornaments out of the leather
        mx_, mn_ = px.max(1), px.min(1)
        hh = np.degrees(np.arctan2(np.sqrt(3) * (px[:, 1] - px[:, 2]), 2 * px[:, 0] - px[:, 1] - px[:, 2])) % 360
        px = px[~((hh > 35) & (hh < 60) & (mx_ > 0.6))]
    return RV.srgb_to_linear(px)


MATCH_A = {'belt': 1.0, 'boots': 0.5}
report = {}
ramps = {'pdm2_a': [], 'pdm2_b': []}
for key, w in zip(('tunic', 'trousers', 'boots', 'belt'), WS):
    core = w > 0.9
    la = skin_pixels('a', key)
    lb = skin_pixels('b', key)
    own_gain = np.median(lum[core]) / np.median(la @ W)
    if key == 'tunic':
        tunic_gain = own_gain
    # belt and boots: our paint is far brighter than MM9's relative to the tunic (belt 3.4x: a silver-white band; boots
    # orange): tier A takes MM9 A's own colours there with a gain pulled toward the tunic's (MATCH_A 1 = the tunic's)
    k = MATCH_A.get(key, 0.0)
    gain = tunic_gain ** k * own_gain ** (1 - k)
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
    target_a = quantile_target(la) if k > 0 else base
    fit, err = RV.fit_ramps(base, {'pdm2_a': target_a, 'pdm2_b': target}, w)
    for v in ramps:
        ramps[v].append(fit[v])
    report[key] = {'texels_core': int(core.sum()), 'mm9_a_px': len(la), 'mm9_b_px': len(lb),
                   'gain_mm9a_to_ours': round(float(own_gain), 3), 'gain_used': round(float(gain), 3), 'match_a': k, 'fit_8bit': err}
doc = {'variants': ['pdm2_a', 'pdm2_b'],
       'materials': [{'base': 'PeasantDM2', 'prefix': 'PeasantDM2', 'mask': 'pdm2_region_mask.png', 'ramps': ramps}],
       'regions': ['R tunic (A charcoal knit, B brown leather)', 'G trousers (A purple-brown stripes, B dark brown)',
                   'B boots (A brown, B orange-brown; gold ornaments shared)', 'A belt (A braided grey cord, B dark leather)'],
       'source': 'MM9 PEASANTDM2A (a: row 9), PEASANTDM2B (b: no row); tiers_pdm2.py', 'report': report}
json.dump(doc, open(T / 'pdm2_ramps.json', 'w'), indent=1)


def apply(v):
    out = lin.copy()
    for k, w in enumerate(WS):
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
    Image.fromarray(np.uint8(np.clip(s, 0, 1) * 255)).save(T / f'pdm2_tier_preview_{v}.png')


for v in ramps:
    apply(v)
dbg = np.zeros((N, N, 3)); dbg[..., 0] = WS[0]; dbg[..., 1] = WS[1]; dbg[..., 2] = WS[2]; dbg += WS[3][..., None] * 0.8
Image.fromarray(np.uint8(np.clip(dbg, 0, 1) * 255)).save('review/tier_masks.png')
print('TIERS', json.dumps(report))
