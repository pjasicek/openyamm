"""Texture-pass maps of the Mage (mm7_m274) from the two 4K Meshy paints on the uv_fine layout.

1. Paint: body retexture (four full-figure HD masters) and head retexture (three head views, head-set faces only:
   face, scalp, ears, beard, braids), both on the same layout; colour and normal 4K -> 2K once (Lanczos). The head is
   a separate mesh piece (no vertex shared with the body), so the head paint covers the head set alone; the blend
   weight is still the per-vertex share of head faces, interpolated.
2. Gentle grade (claude_shared/grade_basecolor.py, recipe values) with AO baked on the layout.
3. Classes on the new paint:
   - head set: hair = saturated ginger texels (saturation and hue score; scalp, temples, eyebrows, moustache, beard,
     braids), eyes from the approved class map (carried at the same surface points), skin = the rest;
   - body set: robe = green cloth, cape and collar = magenta cloth, gold, skin (hands, the neck stump), other (gem,
     shoes). Dark texels whose hue is unreliable take the class of the nearest confident cloth texel.
4. Tone:
   - robe, cape, hair (the three tier regions): linear luminance mapped by quantiles onto the approved region's
     distribution at its approved surface points, so the installed ramps (ranges and colours) give every tier its
     approved colours. Hair is one region: scalp hair and beard share the beard ramp (ginger / dark grey / white).
   - skin: one tone. Face, ears, hands and neck take per-channel quantile curves onto the face skin of the head
     paint (cheeks, forehead, nose), then the face's broad colour is evened (low-frequency chroma towards the skin
     mean, luminance shading kept), so the skin is one continuous tone without islands of different colour.
   - gold: per-channel quantile curves onto the approved gold.
5. Region mask (1024, RGBA: R robe, G cape, B hair) padded into the gutters and feathered; metal/roughness from the
   classes (R specular mask, G roughness = class value + half Meshy's variation, B 0, as compose_m274.py); normal from
   the paints (+y down -> glTF +y up), its tilt scaled to the installed map's p90; class map (8-bit labels).

Eyes: the eyeballs are their own mesh pieces (components of the welded LOD0 with 60-80 triangles at the eye
positions). With eyes=approved (default) their colour is the approved (installed) eye paint carried at the same surface
points, as mm8_m500_claude/scripts/texpass_compose.py does: the 4K head paint drew greyer irises with pink-tinged
whites; eyes=paint keeps the new paint.

Usage: compose.py <out prefix> [eyes=approved|paint] Writes <out prefix>_{basecolor,normal,metal_rough,region_mask,material_classes}.png,
<out prefix>_raw.png (paint before grade), <out prefix>_report.json.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import texlib  # noqa: E402
import seam_heal  # noqa: E402

out = sys.argv[1]
OPTS = dict(a.split('=', 1) for a in sys.argv[2:])
EYES = OPTS.get('eyes', 'approved')
SIGMA = float(OPTS.get('sigma', 6))
DETAIL = float(OPTS.get('detail', 1.0))
HEAL = float(OPTS.get('heal', 6))
RATIO_LO, RATIO_HI = 0.7, 1.4      # cloth detail: weave passes, Meshy's dark patches of low-pass size do not
FEATHER = float(OPTS.get('feather', 0.7))   # region mask edge blur in 2048 texels before the 1024 downsample
S = 2048
SMALL = 1024
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)
M = HERE / 'meshy'
W = HERE / 'work'
SPEC = {'skin': 0.35, 'hair': 0.3, 'cloth': 0.15, 'gold': 1.0, 'gem': 0.9, 'eye': 0.9, 'other': 0.3}
ROUGH = {'skin': 0.6, 'hair': 0.55, 'cloth': 0.88, 'gold': 0.32, 'gem': 0.15, 'eye': 0.2, 'other': 0.7}
CLASS_ID = {'skin': 1, 'hair': 2, 'eye': 6, 'cloth': 8, 'gold': 9, 'gem': 11, 'other': 11}


def load(path, size=S, mode='RGB'):
    img = Image.open(path).convert(mode)
    if img.size != (size, size):
        img = img.resize((size, size), Image.Resampling.LANCZOS)
    return np.asarray(img, np.float32)


def lin(c):
    c = np.clip(c / 255.0, 0, 1)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    c = np.clip(c, 0, 1)
    return 255.0 * np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def hsv(rgb):
    h = np.asarray(Image.fromarray(np.clip(rgb + 0.5, 0, 255).astype(np.uint8)).convert('HSV'), np.float32)
    return h[..., 0] * 360 / 255, h[..., 1] / 255, h[..., 2] / 255


def wpercentile(v, w, q):
    o = np.argsort(v)
    c = np.cumsum(w[o])
    c /= c[-1]
    return np.interp(q / 100, c, v[o])


def quantile_curve(src, src_w, dst, dst_w, n=257):
    q = np.linspace(0, 100, n)
    qs = wpercentile(src, src_w, q)
    qd = wpercentile(dst, dst_w, q)
    qs = np.maximum.accumulate(qs + np.arange(n) * 1e-7)
    return qs, qd


before = np.load(W / 'lod0_before.npz')
tri, weld, head_face = before['tri'], before['weld'], before['head_face']
layout = np.load(W / 'uv_fine.npz')
r = np.load(W / f'approved_fine_raster{S}.npz')
tri_id, bary = r['tri_id'], r['bary']
cov = tri_id >= 0
t = np.maximum(tri_id, 0)
xyz = np.load(W / 'texel_xyz2048.npy')
report = {}

# texel area weights (surface area per texel)
uv, lxyz = layout['uv'], layout['xyz']
area3 = np.linalg.norm(np.cross(lxyz[:, 1] - lxyz[:, 0], lxyz[:, 2] - lxyz[:, 0]), axis=1) / 2
area2 = np.abs((uv[:, 1, 0] - uv[:, 0, 0]) * (uv[:, 2, 1] - uv[:, 0, 1])
               - (uv[:, 2, 0] - uv[:, 0, 0]) * (uv[:, 1, 1] - uv[:, 0, 1])) / 2
weight = np.where(cov, (area3 / np.maximum(area2, 1e-12))[t], 0).astype(np.float32)

# ---- 1. paint
body = load(M / 'body_retexture_v2' / 'texture_urls_0_base_color.png')
head = load(M / 'head_retexture_v2' / 'texture_urls_0_base_color.png')
nweld = int(weld.max()) + 1
count = np.bincount(weld[tri].ravel(), minlength=nweld).astype(np.float32)
hcount = np.bincount(weld[tri[head_face]].ravel(), minlength=nweld).astype(np.float32)
head_w_vert = hcount / np.maximum(count, 1)
hw = np.zeros((S, S), np.float32)
hw[cov] = (head_w_vert[weld[tri[t[cov]]]] * bary[cov]).sum(1)
hw = np.clip(hw, 0, 1)
paint = body * (1 - hw[..., None]) + head * hw[..., None]
paint = texlib.pad(paint, cov)
raw_path = f'{out}_raw.png'
Image.fromarray(np.clip(paint + 0.5, 0, 255).astype(np.uint8)).save(raw_path)

# ---- 2. gentle grade
subprocess.run([sys.executable, str(HERE.parent / 'claude_shared' / 'grade_basecolor.py'),
                '--ao', str(HERE / 'textures' / 'm274_tp_ao_2k.png'), '--fine', '1.0', '--local', '0.3',
                '--ao-strength', '0.5', '--contrast', '1.06', '--saturation', '1.15', raw_path], check=True)
graded = np.asarray(Image.open(f'{out}_raw_graded.png').convert('RGB'), np.float32)

# ---- approved maps at the same surface points
appr = np.asarray(Image.open(W / 'approved_fine_basecolor.png').convert('RGB'), np.float32)
amask = np.stack([np.asarray(ch.resize((S, S), Image.BILINEAR), np.float32)
                  for ch in Image.open(W / 'approved_fine_region_mask.png').convert('RGBA').split()], -1) / 255
# approved class map: production body | head class maps carried through the installed 2080x1024 atlas
T = HERE.parent / 'mm7_m274_claude' / 'textures'
atlas = np.zeros((1024, 2080), np.uint8)
atlas[:, :1024] = np.asarray(Image.open(T / 'm274_material_classes.png'))
atlas[:, 1056:] = np.asarray(Image.open(T / 'm274_head_material_classes.png'))
old_uv = before['uv'][tri]
acls = np.zeros((S, S), np.uint8)
ac, auv = texlib.corresponding_uv(tri_id, bary, old_uv)
acls[ac] = texlib.nearest(atlas[..., None], auv)[:, 0]

# ---- 3. classes
in_head = cov & head_face[t]
in_body = cov & ~head_face[t]
h, s, v = hsv(graded)
# head: hair score from saturation (hair ~0.8, skin ~0.5) and hue (hair ~27 deg, skin ~15 deg)
hair_score = (1 / (1 + np.exp(-(s - 0.64) / 0.04))) * (1 / (1 + np.exp(-(h - 19.0) / 2.0)))
hair_score = ndimage.gaussian_filter(np.where(in_head, hair_score, 0), 1.0) / np.maximum(
    ndimage.gaussian_filter(in_head.astype(np.float32), 1.0), 1e-3)
from scipy.sparse import coo_matrix  # noqa: E402
from scipy.sparse.csgraph import connected_components  # noqa: E402
wt = weld[tri]
edges = np.r_[wt[:, 0], wt[:, 1], wt[:, 2]], np.r_[wt[:, 1], wt[:, 2], wt[:, 0]]
_, part = connected_components(coo_matrix((np.ones(len(edges[0])), edges), shape=(nweld, nweld)), directed=False)
face_part = part[wt[:, 0]]
centre = before['pos'][tri].mean(1)
eye_face = np.zeros(len(tri), bool)
for k in np.unique(face_part[head_face]):
    sel = face_part == k
    c = centre[sel].mean(0)
    if 40 <= sel.sum() <= 100 and 1.46 < c[1] < 1.52 and c[2] > 0.08:
        eye_face |= sel
report['eye_faces'] = int(eye_face.sum())
eye = cov & eye_face[t]
hair = in_head & (hair_score >= 0.5) & ~eye
hair = ndimage.binary_opening(hair, iterations=1) | (in_head & (hair_score >= 0.8) & ~eye)
hair = ndimage.binary_closing(hair, iterations=2) & in_head & ~eye
hskin = in_head & ~hair & ~eye
# body
gold = in_body & (h > 25) & (h < 68) & (s > 0.28) & (v > 0.33)
green = in_body & (h > 70) & (h < 190) & (s > 0.15) & (v > 0.08) & ~gold
magenta = in_body & ((h > 275) | (h < 12)) & (s > 0.3) & (v > 0.08) & ~gold
hand_bones = [i for i, n in enumerate(before['joint_names']) if 'Hand' in str(n) or 'Finger' in str(n)]
hand_w = np.zeros(len(before['pos']))
for k in range(4):
    hand_w += np.where(np.isin(before['joints'][:, k], hand_bones), before['weights'][:, k], 0)
tex_hand = np.zeros((S, S), np.float32)
tex_hand[cov] = (hand_w[tri[t[cov]]] * bary[cov]).sum(1)
skin_hue = (h > 2) & (h < 26) & (s > 0.2) & (s < 0.68) & (v > 0.25)
bskin = in_body & skin_hue & ~gold & ~green & ~magenta & ((acls == 1) | (tex_hand > 0.5))
gem = in_body & (acls == 11) & ((h < 12) | (h > 340)) & (s > 0.5)
dom = before['joints'][np.arange(len(before['pos'])), before['weights'].argmax(1)]
shoe_bones = [i for i, n in enumerate(before['joint_names']) if any(k in str(n) for k in ('Foot', 'Toe', 'Calf'))]
shoe_face = np.isin(dom[tri], shoe_bones).all(1)
shoe = in_body & shoe_face[t] & ~gold
# cloth: the paint's hue where it is reliable; where the paint is dark or grey (surfaces the masters did not show,
# painted near black), the approved region at the same surface points
reliable = v > 0.12
cloth_any = in_body & ~gold & ~bskin & ~gem & ~shoe & ((acls == 8) | green | magenta)
robe = cloth_any & np.where(reliable & (green | magenta), green, amask[..., 0] > amask[..., 1])
cape = cloth_any & np.where(reliable & (green | magenta), magenta, amask[..., 1] >= amask[..., 0]) & \
    ((amask[..., 0] + amask[..., 1] > 0.3) | magenta)
robe &= ~cape
other = in_body & ~gold & ~bskin & ~gem & ~robe & ~cape
skin = hskin | bskin
report['classes_texels'] = {k: int(m.sum()) for k, m in (('hair', hair), ('head_skin', hskin), ('eye', eye),
                                                            ('robe', robe), ('cape', cape), ('gold', gold),
                                                            ('body_skin', bskin), ('gem', gem), ('shoe', shoe), ('other', other))}

# ---- 4. tone
lg = lin(graded)
L = lg @ LUMA
result_lin = lg.copy()
la = lin(appr) @ LUMA
region_report = {}
isl = np.load(W / 'islands.npy')
island_map = np.where(cov, isl[t], -1)
_, island_map = np.unique(island_map, return_inverse=True)
island_map = island_map.reshape(S, S) - 1                      # -1 outside
objs = ndimage.find_objects(island_map + 1)


def broad_from_approved(Lq, sel, asel, sigma=SIGMA):
    """Per island: the approved luminance low-passed over the texels of the region in both maps, times the paint's
    detail (paint over its own low-pass); texels without approved support keep the quantile-mapped paint."""
    outL = Lq.copy()
    for i, sl in enumerate(objs):
        if sl is None:
            continue
        pad_px = int(3 * sigma) + 2
        y0, y1 = max(sl[0].start - pad_px, 0), min(sl[0].stop + pad_px, S)
        x0, x1 = max(sl[1].start - pad_px, 0), min(sl[1].stop + pad_px, S)
        own = island_map[y0:y1, x0:x1] == i
        mp = (own & sel[y0:y1, x0:x1]).astype(np.float32)
        if mp.sum() == 0:
            continue
        ma = (own & sel[y0:y1, x0:x1] & asel[y0:y1, x0:x1]).astype(np.float32)
        da = ndimage.gaussian_filter(ma, sigma, mode='constant')
        dp = np.maximum(ndimage.gaussian_filter(mp, sigma, mode='constant'), 1e-4)
        low_a = ndimage.gaussian_filter(la[y0:y1, x0:x1] * ma, sigma, mode='constant') / np.maximum(da, 1e-4)
        low_p = ndimage.gaussian_filter(Lq[y0:y1, x0:x1] * mp, sigma, mode='constant') / dp
        ratio = np.clip(Lq[y0:y1, x0:x1] / np.maximum(low_p, 1e-5), RATIO_LO, RATIO_HI) ** DETAIL
        support = np.clip((da / dp - 0.15) / 0.35, 0, 1)
        blended = (low_a * ratio) * support + Lq[y0:y1, x0:x1] * (1 - support)
        inside = mp > 0
        outL[y0:y1, x0:x1][inside] = blended[inside]
    return outL


for name, sel, asel in (('robe', robe, cov & ~head_face[t] & (amask[..., 0] > 0.5)),
                        ('cape', cape, cov & ~head_face[t] & (amask[..., 1] > 0.5)),
                        ('hair', hair, cov & head_face[t] & (amask[..., 2] > 0.5))):
    qs, qd = quantile_curve(L[sel], weight[sel], la[asel], weight[asel])
    Lq = np.where(sel, np.interp(L, qs, qd), 0)
    newL = (broad_from_approved(Lq, sel, asel) if name != 'hair' else Lq)[sel]
    # scale the paint's colour to the new luminance; texels the paint left (near) black have no colour to scale and
    # take the approved colour at the same point instead (the ramp replaces the hue in these regions anyway)
    la_lin = lin(appr)[sel]
    black = L[sel] < 2e-4
    scaled = lg[sel] * (newL / np.maximum(L[sel], 1e-5))[:, None]
    scaled[black] = la_lin[black] * (newL[black] / np.maximum(la_lin[black] @ LUMA, 1e-5))[:, None]
    result_lin[sel] = scaled
    region_report[name] = {'paint_L_p50': round(float(wpercentile(L[sel], weight[sel], 50)), 4),
                           'approved_L_p2_50_98': [round(float(wpercentile(la[asel], weight[asel], q)), 4)
                                                   for q in (2, 50, 98)],
                           'result_L_p2_50_98': [round(float(wpercentile(newL, weight[sel], q)), 4)
                                                 for q in (2, 50, 98)]}
report['regions'] = region_report

# skin: per-channel curves onto the face skin of the head paint
P = xyz
face_ref = hskin & (P[..., 2] > 0.07) & (P[..., 1] > 1.44) & (P[..., 1] < 1.57) & ~ndimage.binary_dilation(
    hair | eye, iterations=4)
target = graded[face_ref]
tw = weight[face_ref]
skin_rgb = graded.copy()
for part, sel in (('head', hskin), ('body', bskin)):
    for c in range(3):
        qs, qd = quantile_curve(graded[sel, c], weight[sel], target[:, c], tw)
        skin_rgb[sel, c] = np.interp(graded[sel, c], qs, qd)
# even the broad colour: chroma (rgb / luminance) low-passed per island and pulled to the skin mean; luminance kept
skin_lin = lin(skin_rgb)
SL = skin_lin @ LUMA
chroma = skin_lin / np.maximum(SL, 1e-4)[..., None]
mean_chroma = np.average(chroma[skin], axis=0, weights=weight[skin])
m = skin.astype(np.float32)
den = np.maximum(ndimage.gaussian_filter(m, 12), 1e-4)
low = np.stack([ndimage.gaussian_filter(chroma[..., c] * m, 12) / den for c in range(3)], -1)
EVEN = 0.85
new_chroma = chroma - EVEN * (low - mean_chroma)
# magenta smudges (blue above green: the head paint drew pink patches at the outer eye corners) take the mean chroma
pink = np.clip((new_chroma[..., 2] - new_chroma[..., 1]) / 0.15 + 0.3, 0, 1)[..., None]
new_chroma = new_chroma * (1 - pink) + mean_chroma * pink
report['skin_pink_texels'] = int((skin & (pink[..., 0] > 0.5)).sum())
# broad luminance: also pull the low-frequency level part-way to the skin median (shading detail stays)
lowL = ndimage.gaussian_filter(SL * m, 24) / np.maximum(ndimage.gaussian_filter(m, 24), 1e-4)
medL = float(wpercentile(SL[skin], weight[skin], 50))
evenL = SL * (medL / np.maximum(lowL, 1e-4)) ** 0.5
result_lin[skin] = (new_chroma * evenL[..., None])[skin]
report['skin'] = {'face_ref_srgb_mean': [round(float(x), 1) for x in np.average(target, axis=0, weights=tw)],
                  'mean_chroma': [round(float(x), 3) for x in mean_chroma], 'even': EVEN}

# gold: per-channel curves onto the approved gold
agold = cov & ~head_face[t] & (acls == 9)
gold_rgb = graded.copy()
for c in range(3):
    qs, qd = quantile_curve(graded[gold, c], weight[gold], appr[agold, c], weight[agold])
    gold_rgb[gold, c] = np.interp(graded[gold, c], qs, qd)
result_lin[gold] = lin(gold_rgb)[gold]
ashoe = cov & ~head_face[t] & shoe_face[t]
shoe_rgb = graded.copy()
for c in range(3):
    qs, qd = quantile_curve(graded[shoe, c], weight[shoe], appr[ashoe, c], weight[ashoe])
    shoe_rgb[shoe, c] = np.interp(graded[shoe, c], qs, qd)
result_lin[shoe] = lin(shoe_rgb)[shoe]

if EYES == 'approved':
    result_lin[eye] = lin(appr)[eye]
report['eyes'] = EYES
result = srgb(result_lin)

# seam healing: skin, hair and eyes' neighbours on the head and the hands; cloth and gold keep their seams (the ramps
# and the gold tone hold them)
classes_full = np.zeros((S, S), np.uint8)
for name, sel in (('other', other | shoe), ('cloth', robe | cape), ('skin', skin), ('hair', hair), ('eye', eye),
                  ('gold', gold), ('gem', gem)):
    classes_full[sel] = CLASS_ID[name]
island_density = np.sqrt(np.bincount(isl, area2) / np.maximum(np.bincount(isl, area3), 1e-12))
uniq = np.unique(np.where(cov, isl[t], -1))
uniq = uniq[uniq >= 0]
island_scale = island_density[uniq] / np.median(island_density[isl])
centre_uv = uv.mean(1)
face_class = classes_full[np.clip((centre_uv[:, 1] * S).astype(int), 0, S - 1),
                          np.clip((centre_uv[:, 0] * S).astype(int), 0, S - 1)]
heal_faces = head_face | (face_class == CLASS_ID['skin'])
heal_sel = cov & ((classes_full == CLASS_ID['skin']) | (classes_full == CLASS_ID['hair']))
result, seam_samples = seam_heal.heal(result, classes_full, tri_id, uv, tri, weld, heal_faces & ~eye_face,
                                      island_map, island_scale, falloff=HEAL, sel=heal_sel)
report['seam_heal'] = {'samples': int(seam_samples), 'falloff_texels': HEAL}
result = texlib.pad(np.where(cov[..., None], result, 0), cov)
Image.fromarray(np.clip(result + 0.5, 0, 255).astype(np.uint8)).save(f'{out}_basecolor.png')

# ---- 5. region mask (padded like the colour, feathered), classes, metal/roughness, normal
masks = []
for sel in (robe, cape, hair):
    mm = texlib.pad(np.where(cov, sel.astype(np.float32), 0)[..., None], cov)[..., 0]
    mm = ndimage.gaussian_filter(mm, FEATHER)
    masks.append(np.asarray(Image.fromarray(mm).resize((SMALL, SMALL), Image.BILINEAR)))
mask = np.stack(masks + [np.zeros((SMALL, SMALL), np.float32)], -1)
Image.fromarray(np.clip(mask * 255 + 0.5, 0, 255).astype(np.uint8), 'RGBA').save(f'{out}_region_mask.png')

classes = np.zeros((S, S), np.uint8)
spec = np.full((S, S), SPEC['other'], np.float32)
rough_base = np.full((S, S), ROUGH['other'], np.float32)
for name, sel in (('other', other | shoe), ('cloth', robe | cape | shoe), ('skin', skin), ('hair', hair), ('eye', eye),
                  ('gold', gold), ('gem', gem)):
    classes[sel] = CLASS_ID[name]
    spec[sel] = SPEC[name]
    rough_base[sel] = ROUGH[name]
Image.fromarray(np.asarray(Image.fromarray(classes).resize((SMALL, SMALL), Image.NEAREST))).save(
    f'{out}_material_classes.png')
mrough = np.where(in_head[..., None],
                  load(M / 'head_retexture_v2' / 'texture_urls_0_roughness.png', S, 'L')[..., None],
                  load(M / 'body_retexture_v2' / 'texture_urls_0_roughness.png', S, 'L')[..., None])[..., 0] / 255
rough = rough_base.copy()
for k in np.unique(classes[cov]):
    sel = cov & (classes == k)
    rough[sel] = np.clip(rough_base[sel] + (mrough[sel] - np.median(mrough[sel])) * 0.5, 0.1, 1)
mr = np.stack([texlib.pad(spec[..., None], cov)[..., 0], texlib.pad(rough[..., None], cov)[..., 0],
               np.zeros((S, S), np.float32)], -1)
mr = np.asarray(Image.fromarray(np.clip(mr * 255 + 0.5, 0, 255).astype(np.uint8)).resize((SMALL, SMALL),
                                                                                        Image.Resampling.LANCZOS))
Image.fromarray(mr).save(f'{out}_metal_rough.png')

normals = []
for src in ('body', 'head'):
    n = load(M / f'{src}_retexture_v2' / 'texture_urls_0_normal.png') / 127.5 - 1
    n[..., 1] *= -1                                                   # Meshy +y down -> glTF +y up
    normals.append(n)
n = normals[0] * (1 - hw[..., None]) + normals[1] * hw[..., None]
tilt = np.linalg.norm(n[..., :2], axis=-1)
old_n = np.asarray(Image.open(W / 'before_texpass' / 'normal_installed.png').convert('RGB'), np.float32) / 127.5 - 1
old_cov = np.linalg.norm(old_n, axis=-1) > 0.5
target_tilt = float(np.percentile(np.linalg.norm(old_n[..., :2], axis=-1)[old_cov], 90))
current = float(np.percentile(tilt[cov], 90))
k_tilt = min(1.0, target_tilt / max(current, 1e-6))
n[..., :2] *= k_tilt
n[..., 2] = np.sqrt(np.clip(1 - (n[..., :2] ** 2).sum(-1), 0.0025, 1))
n /= np.linalg.norm(n, axis=-1, keepdims=True)
n = texlib.pad(n, cov)
Image.fromarray(np.clip((n + 1) * 127.5 + 0.5, 0, 255).astype(np.uint8)).save(f'{out}_normal.png')
report['normal'] = {'installed_p90_tilt': round(target_tilt, 3), 'paint_p90_tilt': round(current, 3),
                    'scale': round(k_tilt, 3)}
json.dump(report, open(f'{out}_report.json', 'w'), indent=1)
print('COMPOSED', out, json.dumps(report))
