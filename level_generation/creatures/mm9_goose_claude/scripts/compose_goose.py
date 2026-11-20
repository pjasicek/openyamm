#!/usr/bin/env python3
"""Shared texture set, region mask and ramps for the MM9 goose (rows 293 Goose, goose.dtx; 262 The Great Honk,
goosebrown.dtx). Usage: compose_goose.py   (from mm9_crow_claude/scripts/compose_crow.py)

Tier A (goose_a) is the white farm goose of the HD masters and the 4K Meshy paint (identity ramps). Tier B
(goose_b) is GOOSEBROWN.dtx, a Canada-goose design on the same MM9 UV layout: black neck and head, a white cheek
patch, a brown back and wings, a cream breast, a black bill and dark feet. The white paint carries the feather detail;
the brown skin's colours come through four regions:
  R back  - MM9 brown texels (back, wings, flanks)       G pale - MM9 pale texels (breast, belly, cheek patch, vent)
  B neck  - MM9 black texels (neck and head)              A bill + feet - our bill (head texels ahead of the eyes'
            line, orange in the paint) and legs/feet (leg chain below the body)
The R/G/B split is transferred from GOOSEBROWN.dtx: each of our texels (bind-pose 3D position) takes the class of the
nearest MM9 surface samples (8 nearest, majority) on goose.abc in the same bind pose; the class map is smoothed and
feathered. Eyes (separate pieces) stay out of every region.
Outputs in textures/: goose_basecolor.png (2K, padded; graded by grade_basecolor.py), goose_normal_1k.png,
goose_metal_rough_1k.png (R AO, G roughness, B 0), goose_material_classes.png, goose_region_mask.png, goose_ramps.json.
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
import region_variants as RV
from glb_pose import Glb

T = HERE / 'textures'
M = HERE / 'meshy' / 'goose_retexture_v2'
W = np.array([0.2126, 0.7152, 0.0722])
TIERS = {'goose_a': 'goose/skins/goose.png', 'goose_b': 'goosebrown/skins/goosebrown.png'}
TIER_A = 'goose_a'
REGIONS = ('back', 'pale', 'neck', 'billfeet')
MAT = 'Goose'
LIFT = 0.3958          # mm9_rig_source.py lift (the MM9 bind's lowest point on the floor)
# per region of the brown skin: share of the palette kept (darkest first: the mid-tone border texels washed the brown
# and the black out), albedo factor (the white paint's luminance already sits high) and saturation
PAL = {'back': (0.7, 0.9, 1.0), 'pale': (1.0, 0.9, 1.35), 'neck': (0.7, 1.0, 0.4), 'billfeet': (0.6, 1.0, 0.7)}
S = 1024


def lin(c):
    return RV.srgb_to_linear(c)


def encode(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def hsv(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn + 1e-9
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, d / (mx + 1e-9), mx


def raster(npz, size):
    """Per texel: triangle index, barycentric-interpolated bind position (Blender Z-up) and head/limb weights."""
    d = np.load(npz)
    uv = d['uv'] * size
    tri = np.full((size, size), -1, np.int32)
    xyz = np.zeros((size, size, 3), np.float32)
    head = np.zeros((size, size), np.float32)
    limb = np.zeros((size, size), np.float32)
    for t in range(len(uv)):
        p = uv[t]
        x0, x1 = max(int(np.floor(p[:, 0].min())), 0), min(int(np.ceil(p[:, 0].max())), size - 1)
        y0, y1 = max(int(np.floor(p[:, 1].min())), 0), min(int(np.ceil(p[:, 1].max())), size - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = p
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        l3 = 1 - l1 - l2
        inside = (l1 >= -1e-4) & (l2 >= -1e-4) & (l3 >= -1e-4)
        if not inside.any():
            continue
        iy, ix = np.nonzero(inside)
        rows, cols = size - 1 - (iy + y0), ix + x0
        L = np.stack([l1[inside], l2[inside], l3[inside]], 1)
        tri[rows, cols] = t
        xyz[rows, cols] = L @ d['xyz'][t]
        head[rows, cols] = L @ d['head'][t]
        limb[rows, cols] = L @ d['limb'][t]
    return tri, xyz, head, limb, d


def pad(img, covered):
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]


def feather(m, covered):
    m = pad(m.astype(np.float32), covered)
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)),
                      np.float32) / 255


# ---------------- MM9 goose.abc surface samples (bind pose, Blender Z-up, lifted) with their skin UV
g = Glb(HERE / 'source' / 'goosebrown' / 'goosebrown.glb')
doc = g.json
prim = doc['meshes'][0]['primitives'][0]
A_ = prim['attributes']
gp = g.accessor(A_['POSITION'])
guv = g.accessor(A_['TEXCOORD_0'])
jn = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
jj, ww = g.accessor(A_['JOINTS_0']).astype(int), g.accessor(A_['WEIGHTS_0'])
dom = np.array([jn[jj[i][int(np.argmax(ww[i]))]] for i in range(len(gp))])
bp = np.stack([gp[:, 0], -gp[:, 2], gp[:, 1] + LIFT], 1)          # glTF Y-up -> Blender Z-up
tris = g.accessor(prim['indices']).reshape(-1, 3).astype(int)
bary = [(a / 6, b / 6, 1 - a / 6 - b / 6) for a in range(7) for b in range(7 - a)]
sp, suv, slab = [], [], []
for t in tris:
    labs = list(dom[t])
    lab = max(set(labs), key=labs.count)
    for l1, l2, l3 in bary:
        sp.append(l1 * bp[t[0]] + l2 * bp[t[1]] + l3 * bp[t[2]])
        suv.append(l1 * guv[t[0]] + l2 * guv[t[1]] + l3 * guv[t[2]])
        slab.append(lab)
sp, suv, slab = np.array(sp), np.array(suv), np.array(slab)
skins = {k: np.asarray(Image.open(HERE / 'source' / p).convert('RGB'), np.float32) / 255 for k, p in TIERS.items()}
n9 = skins['goose_b'].shape[0]
px = np.clip((suv * n9).astype(int), 0, n9 - 1)
col_b = skins['goose_b'][px[:, 1], px[:, 0]]
lum_b = col_b @ W
h_b, s_b, v_b = hsv(col_b)
# MM9 brown-skin classes: 0 back (brown), 1 pale, 2 neck (black)
cls9 = np.where(lum_b < 0.16, 2, np.where((lum_b > 0.5) & (s_b < 0.4), 1, 0))
is_billfeet9 = np.array([s_ == 'Xbeak' or s_.startswith(('Xleg', 'Xfoot', 'Xtoe')) for s_ in slab])

# ---------------- our texels (1K)
tri, xyz, headw, limb, dbody = raster(HERE / 'work' / 'uv3d_goose.npz', S)
covered = tri >= 0
ti = np.maximum(tri, 0)
part = np.where(covered, dbody['part'][ti], -1)
base2k = np.asarray(Image.open(M / 'texture_urls_0_base_color.png').convert('RGB').resize((2048, 2048), Image.LANCZOS),
                    np.float32) / 255   # 4K -> 2K once (the creature cook caps colour at 2048)
base = np.asarray(Image.fromarray((base2k * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS), np.float32) / 255
eyes = covered & (part == 2)
hh, ss, vv = hsv(base)
orange = (hh > 18) & (hh < 60) & (ss > 0.35)
# bill: head texels ahead of the eye line that are orange in the paint; feet: below the body (legs and webs)
eyemid = dbody['xyz'][dbody['part'] == 2].reshape(-1, 3).mean(0)
bill = covered & ~eyes & (headw > 0.5) & (xyz[..., 1] < eyemid[1] - 0.01) & orange
feet = covered & ~eyes & (xyz[..., 2] < 0.12) & (np.abs(xyz[..., 0]) > 0.015) & ((limb > 0.2) | (xyz[..., 2] < 0.06))
bill = ndimage.binary_dilation(bill, iterations=3) & covered & ~eyes & (headw > 0.5)   # no pale seam at the bill base
billfeet = bill | feet
kd = cKDTree(sp[~is_billfeet9])
_, nn = kd.query(xyz[covered], k=8)
votes = cls9[~is_billfeet9][nn]
cls = np.full((S, S), -1, np.int32)
cls[covered] = np.array([np.bincount(v, minlength=3).argmax() for v in votes])
# corrections to the raw transfer: the low-poly skin's soft black/white borders read as mid-tone 'back' on the neck
# (tan blots on the throat), and it has a pale eye-ring. Above the shoulders there is only black and the white
# cheek/chin patch, which stops at MM9's own lower end (CHEEK_Z) and below the eyes.
cheek9 = sp[(cls9 == 1) & (sp[:, 2] > 0.55) & ~is_billfeet9]
CHEEK_Z = float(np.percentile(cheek9[:, 2], 8))
neckz = covered & (xyz[..., 2] > 0.52)
cls[neckz & (cls == 0)] = 2
cls[neckz & (xyz[..., 2] < CHEEK_Z + 1.2 * np.abs(xyz[..., 0]))] = 2      # the patch narrows to a point on the throat
kb = cKDTree(xyz[bill])
near_bill = covered & ~bill & ~eyes & (xyz[..., 2] > 0.6)
d_, _ = kb.query(xyz[near_bill])
cls[np.nonzero(near_bill)[0][d_ < 0.014], np.nonzero(near_bill)[1][d_ < 0.014]] = 2  # black feathers ring the bill base
cls[neckz & (xyz[..., 2] > eyemid[2] - 0.005)] = 2
rest = covered & ~eyes & ~billfeet
regions_bool = [rest & (cls == 0), rest & (cls == 1), rest & (cls == 2), billfeet]
classes = np.zeros((S, S), np.uint8)
classes[covered] = 2                       # feathers (fur/hair class)
classes[billfeet] = 4                      # bill, scaly feet (claw/horn class)
classes[eyes] = 6
# the shader mixes the regions in channel order, so where two feathered masks meet at 0.5 each a quarter of the white
# base shows through (a pale line round the dark bill): each mask runs 4 texels under the later regions it borders
under = [regions_bool[k] | (ndimage.binary_dilation(regions_bool[k], iterations=4) & np.any(regions_bool[k + 1:], axis=0))
         if k < 3 else regions_bool[k] for k in range(4)]
regions = [feather(m, covered) for m in under]
RV.write_mask(regions, T / 'goose_region_mask.png')
Image.fromarray(classes * 20).save(T / 'goose_material_classes.png')
tri2, _, _, _, _ = raster(HERE / 'work' / 'uv3d_goose.npz', 2048)
# the eye piece: Meshy paints a pale grey ball around the pupil; a goose's eye is dark with a thin rim
eye2 = (tri2 >= 0) & (dbody['part'][np.maximum(tri2, 0)] == 2)
base2k[eye2] *= 0.4
Image.fromarray((pad(base2k, tri2 >= 0) * 255).astype(np.uint8)).save(T / 'goose_basecolor.png')
nrm = np.asarray(Image.open(M / 'texture_urls_0_normal.png').convert('RGB').resize((2048, 2048), Image.LANCZOS), np.float32) / 255
Image.fromarray((pad(nrm, tri2 >= 0) * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS).save(T / 'goose_normal_1k.png')
rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((S, S), Image.LANCZOS),
                   np.float32) / 255
rough = np.where(eyes, 0.15, np.where(billfeet, 0.5, np.clip(rough, 0.6, 0.85)))
rough = pad(rough, covered)
ao = np.asarray(Image.open(T / 'goose_ao_2k.png').convert('L').resize((S, S), Image.LANCZOS), np.float32) / 255
Image.merge('RGB', [Image.fromarray((ao * 255).astype(np.uint8)), Image.fromarray((rough * 255).astype(np.uint8)),
                    Image.new('L', (S, S), 0)]).save(T / 'goose_metal_rough_1k.png')

# ---------------- MM9 skin texel sets per region (128 x 128, goose.abc UV layout), per tier
yy, xx = np.mgrid[:n9, :n9] + 0.5
cover9 = np.zeros((n9, n9), np.int32) - 1      # skin texels on MM9 triangles: their dominant bone class
from PIL import ImageDraw
lay = {r: Image.new('L', (n9, n9), 0) for r in ('billfeet', 'body')}
for t in tris:
    labs = list(dom[t]); lab = max(set(labs), key=labs.count)
    r = 'billfeet' if lab == 'Xbeak' or lab.startswith(('Xleg', 'Xfoot', 'Xtoe')) else 'body'
    ImageDraw.Draw(lay[r]).polygon([tuple(guv[i] * n9) for i in t], fill=255)
lay = {r: np.asarray(m) > 0 for r, m in lay.items()}
EYE9 = (27.5, 12.5, 2.6)       # the dark eye texels (x, y, radius) in both skins
eye9 = (xx - EYE9[0]) ** 2 + (yy - EYE9[1]) ** 2 < EYE9[2] ** 2


def mm9_sets(tier):
    sk = skins[tier]
    lum = sk @ W
    _, sat, _ = hsv(sk)
    c = np.where(lum < 0.16, 2, np.where((lum > 0.5) & (sat < 0.4), 1, 0))
    if tier == 'goose_b':
        body = lay['body'] & ~lay['billfeet'] & ~eye9
        return {'back': body & (c == 0), 'pale': body & (c == 1), 'neck': body & (c == 2),
                'billfeet': lay['billfeet'] & ~eye9}
    return {r: np.zeros((n9, n9), bool) for r in REGIONS}


sets = {k: mm9_sets(k) for k in TIERS}
counts = {k: {r: int(m.sum()) for r, m in v.items()} for k, v in sets.items()}


def targets_for(graded, weight, name):
    core = weight > 0.5
    targets = {TIER_A: graded.copy()}
    glum = lin(graded[core]) @ W
    rank = np.empty(glum.size)
    rank[np.argsort(glum)] = (np.arange(glum.size) + 0.5) / glum.size
    # rank transfer: our texel at luminance rank r takes the colour of the brown skin's texel at rank r in the same
    # region (window-averaged), so the white paint's feather detail drives the brown design's colours
    for k in TIERS:
        if k == TIER_A:
            continue
        keep, albedo, sat = PAL[name]
        pal = lin(skins[k][sets[k][name]])
        pal = pal[np.argsort(pal @ W)][:max(8, int(keep * sets[k][name].sum()))]
        grey = (pal @ W)[:, None]
        pal = grey + (pal - grey) * sat
        win = max(1, len(pal) // 25)
        csum = np.concatenate([np.zeros((1, 3)), np.cumsum(pal, 0)])
        q = np.clip((rank * len(pal)).astype(int), 0, len(pal) - 1)
        lo, hi = np.clip(q - win, 0, len(pal)), np.clip(q + win + 1, 0, len(pal))
        tgt = graded.copy()
        tgt[core] = encode(np.clip((csum[hi] - csum[lo]) / (hi - lo)[:, None] * albedo, 0, 1))
        targets[k] = tgt
    return targets


graded = RV.load_srgb(T / 'goose_basecolor_graded.png', S) if (T / 'goose_basecolor_graded.png').exists() else base
report, ramps = [], {k: [] for k in TIERS}
previews = {k: graded.copy() for k in TIERS}
for name, weight in zip(REGIONS, regions):
    targets = targets_for(graded, weight, name)
    fitted, rep = RV.fit_ramps(graded, targets, weight)
    for k in TIERS:
        ramps[k].append(fitted[k])
        core = weight > 0.5
        previews[k][core] = targets[k][core]
    report.append({'region': name, **{k: v.get('mean_abs_8bit') if isinstance(v, dict) else v for k, v in rep.items()}})
materials = [{'base': MAT, 'prefix': MAT, 'mask': 'goose_region_mask.png', 'ramps': ramps}]
json.dump({'variants': list(TIERS), 'mm9_region_texels': counts, 'report': report,
           'sources': {k: f'source/{p}' for k, p in TIERS.items()}, 'materials': materials},
          open(T / 'goose_ramps.json', 'w'), indent=1)
prev = np.zeros((S, S, 3))
for m, c in zip(regions_bool, ((0.55, 0.35, 0.2), (0.95, 0.9, 0.8), (0.1, 0.1, 0.1), (0.9, 0.6, 0.1))):
    prev[m] = c
prev[eyes] = (0.2, 0.4, 1.0)
(HERE / 'review').mkdir(exist_ok=True)
row = [prev] + [previews[k] for k in TIERS]
Image.fromarray((np.concatenate(row, 1) * 255).astype(np.uint8)).resize((512 * len(row), 512)).save(
    HERE / 'review' / 'goose_texture_classes_tiers.png')
print('COMPOSED', json.dumps({'mm9_texels': counts, 'fit': report,
                              'our_texels': {k: int(m.sum()) for k, m in zip(REGIONS, regions_bool)},
                              'eyes': int(eyes.sum())}))
