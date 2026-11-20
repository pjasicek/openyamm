"""Texture-pass maps of m372 from the two 4K Meshy paints on our layout (2026-11-01).

The user found the installed textures blurry, flat and blotchy (face and hood) and asked for seamless faces in every
skin, so unlike the Troll pass the approved colours are NOT carried at low frequency: the new paint defines the look.
What is held: the installed region ramps (unchanged), by matching each ramped region's luminance distribution to the
approved one at the same surface points, so every skin keeps its colours.

1. Paint: body retexture (full-figure masters) and head retexture (bust masters; the upload was the bust above
   1.25 m). Colour and normal 4K -> 2K once (Lanczos). The head-set pieces (head with neck and chest skin, fringe,
   eyes, circlet, rim beads) take the head paint entirely, so no skin carries a crossfade; the gown and the hands
   keep the body paint; the hood and the neckline beads crossfade from the body paint to the head paint over CROSS_Y.
2. Gentle grade (claude_shared/grade_basecolor.py, recipe values) with AO baked on the layout.
3. Skin (head piece minus hair, hands): one albedo (SKIN_ALBEDO, the HD head masters' lit skin) x the paint's own
   luminance detail over a 6 mm low pass taken in 3D (so UV seams cannot show in it), clamped 0.8-1.2 (wider for
   eyelids, brows and nostrils), plus a compressed share of the low pass (form). Paint that is not skin-coloured
   (hair painted under the hood, bead green bled onto the neck, dark wedges) keeps no detail. Large blotches go;
   pores, creases and eyelids stay; face, neck, chest and hands share one tone. Lips (red paint in the mouth zone) and
   the eye shells keep their graded paint.
4. Ramped regions (gown, veil + lining, hair): a monotone luminance curve per region maps the graded paint's
   area-weighted luminance quantiles onto the approved ones at the same surface points; RGB is scaled by the
   luminance ratio. The ramps see the same distribution; the pattern and sharpness are the new paint's.
5. Region mask: gown and hood by piece (gown piece: lining where the new paint is pale, limited to faces near the
   approved lining), hair = fringe + the approved crown faces of the head piece; feathered 1 texel.
6. Normal: the paint's (+y down -> glTF +y up), tilt scaled to the approved map's p90, halved on skin.
7. Metal/roughness: the approved map carried onto the layout (resample_approved.py).
8. Eyes: painted procedurally by eyes.py on charts of their own (the head paint drew irises off the shells and onto
   the lids), together with the lid skin hugging the eyeball. Here: the nostrils one soft shadow; the mouth opening
   (inward-facing lip triangles and interior) a dark gradient.

Usage: compose.py <layout npz> <approved prefix> <ao png> <out prefix>
Writes <out prefix>_{basecolor,normal,metal_rough,region_mask}.png, _raw.png, _classes.png, _report.json.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import texlib  # noqa: E402
import texture_quality as TQ  # noqa: E402
import eyefit  # noqa: E402
import normfix  # noqa: E402

layout_path, approved, ao_path, out = sys.argv[1:5]
S = 2048
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)
M = HERE / 'meshy'
HEAD_PIECES = {1, 9, 10, 11, 14, 16, 18, 21, 22, 24, 25, 42}      # head set: the head, fringe, eyes, brows, circlet
EYE_PIECES = {10, 11}
HAND_PIECES = {2, 3}
SIDE_PIECES = {21, 22, 24, 25, 42}  # bead clusters at the hood rim
CROSS_Y = (1.30, 1.42)
SKIN_SIGMA_M = 0.006          # surface low pass of the skin repaint (6 mm)
DETAIL = (0.8, 1.2)
FORM = 0.35                   # kept share (log) of the skin's low-pass variation
VEIL_SOFT = 0.5
BEAD_MAX_CM2 = 1.5
GOWN_SOFT = 0.4
CONTRAST = {}                  # hair: the v3 paint's strands need no compression (0.6 on the v2 paint)
LIP_TONE = (192, 124, 114)      # sRGB: muted rose, a little darker than the skin (204, 151, 130)
LIP_UPPER = 0.95
LIP_LOWER = 0.88
DOWN_LIFT = 0.0
UNDERSIDE_TURN = 0.7
UNDERSIDE_NORMAL = np.array([0.0, -0.25, 1.0]) / np.linalg.norm([0.0, -0.25, 1.0])
SPIKE_CLEAR = 0.007
NOSE_R = 0.016
CORNER_MARK = np.array([-0.035, 1.497, 0.08])
LIP_SOFT_M = 0.0009
SLIT_SIGMA_M = 0.0008
SLIT_CORE_M = 0.0012             # the line's flat core (half width)
SLIT_DARK = 0.32
INWARD_TONE = 0.32
SHELF_DARK = 0.3
MOUTH_FILL = 0.32                # = SLIT_DARK: the fill is the curve's centre colour
NOSTRIL_DARK = 0.6
NOSTRIL_SIGMA = 0.0016
GAP_LIFT = 1.3
FACE_X = -0.0072
MOUTH_Y = 1.5138                 # the slit between the lips (selects the mouth opening's boundary)
SKIN_ALBEDO = (204, 151, 130)  # sRGB: the HD head masters' lit cheek and forehead
PAINT = os.environ.get('PAINT', 'v3')            # meshy/{body,head}_retexture_<PAINT>: the paints of the layout


def load(path, size=S, mode='RGB'):
    img = Image.open(path).convert(mode)
    if img.size != (size, size):
        img = img.resize((size, size), Image.Resampling.LANCZOS)
    return np.asarray(img, np.float32)


def lin(c):
    c = np.asarray(c, np.float32) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    c = np.clip(c, 0, 1)
    return 255.0 * np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def wpercentile(v, w, q):
    o = np.argsort(v)
    c = np.cumsum(w[o])
    c /= c[-1]
    return np.interp(q, c, v[o])


def hsv(rgb):
    h = np.asarray(Image.fromarray(np.clip(rgb + 0.5, 0, 255).astype(np.uint8)).convert('HSV'), np.float32) / 255
    return h[..., 0] * 360, h[..., 1], h[..., 2]


layout = np.load(layout_path)
before = np.load(HERE / 'work' / 'lod0_before.npz')
piece_face = np.load(HERE / 'work' / 'face_piece_lod0.npy')
region_face = before['region']
r = np.load(f'{approved}_raster{S}.npz')
tri_id, bary = r['tri_id'], r['bary']
cov = tri_id >= 0
t = tri_id[cov]
uv, xyz = layout['uv'], layout['xyz']
pos = np.zeros((S, S, 3), np.float32)
pos[cov] = (xyz[t] * bary[cov][:, :, None]).sum(1)
piece = np.full((S, S), -1, np.int32)
piece[cov] = piece_face[t]
region = np.full((S, S), -1, np.int32)
region[cov] = region_face[t]
area3 = np.linalg.norm(np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]), axis=1) / 2
area2 = np.abs((uv[:, 1, 0] - uv[:, 0, 0]) * (uv[:, 2, 1] - uv[:, 0, 1])
               - (uv[:, 2, 0] - uv[:, 0, 0]) * (uv[:, 1, 1] - uv[:, 0, 1])) / 2
tri_density = np.sqrt(area2 / np.maximum(area3, 1e-12)) * S        # texels per metre
weight = np.zeros((S, S), np.float32)
weight[cov] = 1.0 / np.maximum(tri_density[t], 1e-9) ** 2
density = np.zeros((S, S), np.float32)
density[cov] = tri_density[t]
report = {}

# ---- 1. paint
body = load(M / f'body_retexture_{PAINT}' / 'texture_urls_0_base_color.png')
head = load(M / f'head_retexture_{PAINT}' / 'texture_urls_0_base_color.png')
y = pos[..., 1]
hw = np.clip((y - CROSS_Y[0]) / (CROSS_Y[1] - CROSS_Y[0]), 0, 1)
hw = hw * hw * (3 - 2 * hw)
hw[np.isin(piece, list(HEAD_PIECES))] = 1.0
hw[np.isin(piece, list(HAND_PIECES))] = 0.0
hw[piece == 0] = 0.0          # the gown: body paint only (the head masters' hood fell onto its shoulders)
hw[~cov] = 0
paint = body * (1 - hw[..., None]) + head * hw[..., None]
paint = texlib.pad(paint, cov)
raw_path = f'{out}_raw.png'
Image.fromarray(np.clip(paint + 0.5, 0, 255).astype(np.uint8)).save(raw_path)

# ---- 2. gentle grade
subprocess.run([sys.executable, str(HERE.parent / 'claude_shared' / 'grade_basecolor.py'), '--ao', ao_path,
                '--fine', '1.0', '--local', '0.3', '--ao-strength', '0.5', '--contrast', '1.06', '--saturation', '1.15',
                raw_path], check=True)
graded = np.asarray(Image.open(f'{out}_raw_graded.png').convert('RGB'), np.float32)

# ---- classes
h, s, v = hsv(graded)
hair_face = (piece_face == 9) | ((piece_face == 1) & (region_face == 3))
hair = np.zeros((S, S), bool)
hair[cov] = hair_face[t]
eyeball_face = eyefit.eyeball_faces()
eye = np.zeros((S, S), bool)
eye[cov] = eyeball_face[t] > 0
# bead green painted on the hood and the rim bead clusters stays paint (dark green beads in every skin, as the
# modelled beads); the rest of the clusters is hood cloth
bead = cov & (h > 70) & (h < 170) & (s > 0.30) & (v < 0.55)
bead = ndimage.binary_opening(bead, iterations=1)
# beads are small: green patches over BEAD_MAX_CM2 of surface (the head paint smeared gown green over the hood
# below the jaw) are hood cloth
lab, nlab = ndimage.label(bead)
if nlab:
    patch_area = ndimage.sum(weight, lab, np.arange(1, nlab + 1)) * 1e4      # cm^2
    big = np.zeros(nlab + 1, bool)
    big[1:] = patch_area > BEAD_MAX_CM2
    bead &= ~big[lab]
side = cov & np.isin(piece, list(SIDE_PIECES))
# head-piece faces the approved build gave the hood mask keep it (where the head pokes through the hood), except the
# inner walls on the left (x > 0, z < 5 cm) seen through a gap in the left cheek (a sage or blue wedge in the installed
# skins): skin. (Single faces are not enough: the 1K mask carries the neighbouring wall's hood mask onto slivers.)
hc = xyz.mean(1)
gap_faces = (hc[:, 0] > 0) & (hc[:, 2] < 0.05)
head_hood = cov & (piece == 1) & (region == 2)
head_hood[cov] &= ~gap_faces[t]
skin_piece = (cov & (np.isin(piece, [1] + list(HAND_PIECES))) & ~hair & ~head_hood & ~eye)
lips = np.zeros((S, S), bool)                                       # decided in step 3
skin = skin_piece
veil_piece = (cov & (piece == 4) & ~bead) | (side & ~bead) | head_hood
gown_piece = cov & (piece == 0)
# lining (pale) inside the gown piece: within 1.5 cm (on the body) of the approved lining faces, below the shoulders
pale = (s < 0.36) & (v > 0.40)
appr_lining = gown_piece & (region == 2)
near_lining = np.zeros((S, S), bool)
cand = gown_piece & (y < 1.30)
near_lining[cand] = cKDTree(pos[appr_lining][::3]).query(pos[cand])[0] < 0.015
lining = gown_piece & near_lining & pale
lining = ndimage.binary_closing(ndimage.binary_opening(lining, iterations=1), iterations=2) & gown_piece & near_lining
gown = gown_piece & ~lining
# legs above the shoes and accessory faces the approved build masked (belt faces painted as gown cloth) keep the
# approved face's region
accessory = cov & ~np.isin(piece, [0, 1, 2, 3, 4, 9] + sorted(EYE_PIECES) + sorted(SIDE_PIECES))
gown |= accessory & (region == 1)
veil = veil_piece | lining | (accessory & (region == 2))
classes = {'skin': skin, 'lips': lips, 'hair': hair, 'eye': eye, 'gown': gown, 'veil': veil}

# ---- 3. skin: one albedo x the paint's own luminance detail; low passes in 3D (no UV seams in them)
# from the raw paint (before the grade): the AO is applied once afterwards to all skin alike, so skin that keeps no
# paint detail is not lighter than its occluded neighbours
result = graded.copy()
L = lin(paint) @ LUMA
logL = np.log(np.maximum(L, 1e-4))
x, z = pos[..., 0], pos[..., 2]
xf = x - FACE_X                 # across the face from its midline (the eyes' midpoint; the head sits off x = 0)
front = skin & (piece == 1) & (z > 0.085) & (y > 1.50) & (y < 1.565) & (np.abs(x) > 0.012)
rgb_raw = paint / 255.0
chroma = rgb_raw / np.maximum(rgb_raw.sum(-1, keepdims=True), 1e-4)
c_ref = np.median(chroma[front], 0)
l_ref = float(np.median(logL[front]))
# skin likelihood of the paint: chroma near the face's and not much darker (hair painted under the hood, bead
# colour bled onto the neck, dark wedges are not skin: their detail is not kept)
d = np.sqrt((np.linalg.norm(chroma - c_ref, axis=-1) / 0.045) ** 2 + (np.minimum(logL - l_ref, 0) / 0.8) ** 2)
q = np.exp(-0.5 * d ** 2) * skin


def lowpass3d(values, wts, sel, sigma_m, voxel=0.002):   # the grid spans the selected texels only
    """Weighted Gaussian low pass of per-texel values over the 3D surface positions (per connected part box)."""
    out = np.zeros(values.shape, np.float32)
    for part in ([1], [2], [3]):
        m = sel & np.isin(piece, part)
        if not m.any():
            continue
        p3 = pos[m]
        lo = p3.min(0) - 4 * sigma_m
        idx = np.floor((p3 - lo) / voxel).astype(int)
        shape = tuple(idx.max(0) + int(8 * sigma_m / voxel) + 2)
        num = np.zeros(shape, np.float32)
        den = np.zeros(shape, np.float32)
        np.add.at(num, tuple(idx.T), values[m] * wts[m])
        np.add.at(den, tuple(idx.T), wts[m])
        sg = sigma_m / voxel
        num = ndimage.gaussian_filter(num, sg)
        den = ndimage.gaussian_filter(den, sg)
        coords = ((p3 - lo) / voxel - 0.5).T
        a = ndimage.map_coordinates(num, coords, order=1, mode='nearest')
        b = ndimage.map_coordinates(den, coords, order=1, mode='nearest')
        out[m] = a / np.maximum(b, 1e-6)
    return out


area_w = weight / max(float(weight[skin].mean()), 1e-12)
low = np.exp(lowpass3d(logL, q * area_w + 1e-4 * skin, skin, SKIN_SIGMA_M))
# feature zones keep more of the paint's dark detail: the brows above the eye shells, the nostrils. The lids around
# the shells do not: the head paint drew a second eye white and iris on them
eyes_c = [pos[cov & (piece == k)].mean(0) for k in sorted(EYE_PIECES)]
feature = np.zeros((S, S), np.float32)
for c in eyes_c:
    dx, dy = np.abs(x - c[0]) / 0.022, (y - c[1] - 0.016) / 0.009
    feature = np.maximum(feature, np.clip(1.5 - np.sqrt(dx ** 2 + dy ** 2), 0, 1))
lid = np.zeros((S, S), bool)
lid[skin] = cKDTree(pos[eye][::2]).query(pos[skin])[0] < 0.004
nose = np.clip(1.5 - np.sqrt((xf / 0.016) ** 2 + ((y - 1.527) / 0.012) ** 2), 0, 1) * (z > 0.095) * skin
feature = feature * skin
lo_clip = DETAIL[0] - 0.35 * feature
hi_clip = DETAIL[1] + 0.05 * feature
lo_clip = np.where(lid | (nose > 0), 0.9, lo_clip)
hi_clip = np.where(lid | (nose > 0), 1.08, hi_clip)
detail = np.clip(L / np.maximum(low, 1e-4), lo_clip, hi_clip)
qs = lowpass3d(q, skin.astype(np.float32), skin, 0.002)        # soft, seam-free edges of the kept detail
detail = 1 + (detail - 1) * np.maximum(np.clip(qs * 1.5, 0, 1), feature)   # not-skin paint keeps no detail
ref = float(np.exp(np.median(np.log(low[front]))))
form = np.clip((low / ref) ** FORM, 0.8, 1.1)
albedo = lin(np.array(SKIN_ALBEDO, np.float32))
ao = np.asarray(Image.open(ao_path).convert('L').resize((S, S), Image.BILINEAR), np.float32) / 255
ao = ndimage.gaussian_filter(texlib.pad(ao[..., None], ao > 0.003)[..., 0], 2.0)
# round 3: the AO was baked with the spike fan (LOD0 3593/3594/3596, removed by fix_mesh.py) lying across the right
# cheek, and the head paint's normal map drew its edge: a thin dark scratch from the mouth corner to the jaw. No AO
# and (step 6) no paint relief or paint detail within SPIKE_CLEAR of it.
spike = before['pos'][before['tri'][[3593, 3594, 3596]]].reshape(-1, 3)
far_v = spike[np.argmin(spike[:, 1])]
near_vs = np.unique(spike[np.linalg.norm(spike - far_v, axis=1) > 1e-6], axis=0)
seg_d = np.full((S, S), np.inf, np.float32)
for a_ in near_vs:
    ab_ = far_v - a_
    tt_ = np.clip(((pos - a_) @ ab_) / (ab_ @ ab_), 0, 1)
    seg_d = np.minimum(seg_d, np.linalg.norm(pos - (a_ + tt_[..., None] * ab_), axis=-1))
clear = np.clip(1 - (seg_d - SPIKE_CLEAR) / SPIKE_CLEAR, 0, 1) * cov
ao = ao * (1 - clear) + clear
# the paint itself drew the spike's shadow on the cheek (the upload carried the spike): no paint detail there either
detail = detail * (1 - clear) + clear
ao_f = 1.0 - 0.5 * (1.0 - ao)                                  # the grade's AO strength
# texel normals (flat per triangle; the windings point outwards: 0 inverted closed parts)
fnrm = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
fnrm /= np.maximum(np.linalg.norm(fnrm, axis=1, keepdims=True), 1e-12)
nrm = np.zeros((S, S, 3), np.float32)
nrm[cov] = fnrm[t]
shade = np.ones((S, S), np.float32)
# smooth (vertex-interpolated) rest normals: the faceted undersides shade in steps, the lift below follows them softly
snrm = np.zeros((S, S, 3), np.float32)
snrm[cov] = (before['nrm'][before['tri'][t]] * bary[cov][..., None]).sum(1)
snrm /= np.maximum(np.linalg.norm(snrm, axis=-1, keepdims=True), 1e-6)
# nostrils (face follow-up): two small soft shadows at the nostril openings (the centres of the downward-facing
# triangles under the nose tip, one per side), nothing spreading onto the upper lip
nostril = (nose > 0.3) & (nrm[..., 1] < -0.3) & (y > 1.522) & (y < 1.540)
x_mid = float(np.median(x[nostril]))
nostril_c = [pos[nostril & (x < x_mid)].mean(0), pos[nostril & (x >= x_mid)].mean(0)]
for nc in nostril_c:
    d2 = ((pos - nc) ** 2).sum(-1)
    shade *= np.where(skin, 1 - NOSTRIL_DARK * np.exp(-0.5 * d2 / NOSTRIL_SIGMA ** 2), 1).astype(np.float32)
# round 3 (as the accepted m342 face): the down-facing undersides shade much darker than their neighbours in faceted
# steps (one dark blob under the nose tip; a dark mark at her right mouth corner, where the spike fan was). Their albedo
# is lifted by up to DOWN_LIFT so they shade like their neighbours; the two small nostril shadows above stay.
nose_base = np.array([nostril_c[0], nostril_c[1]]).mean(0)
down = np.clip(-snrm[..., 1] / 0.8, 0, 1)
down = down * down * (3 - 2 * down)
lift_zone = np.clip(1 - (np.linalg.norm(pos - nose_base, axis=-1) - 0.6 * NOSE_R) / (0.4 * NOSE_R), 0, 1)
lift_zone = np.maximum(lift_zone, np.clip(1 - (np.linalg.norm(pos - CORNER_MARK, axis=-1) - 0.006) / 0.006, 0, 1))
shade *= np.where(skin, 1 + DOWN_LIFT * down * lift_zone, 1).astype(np.float32)
nose_zone = lift_zone
# the wedge seen through the gap in the left cheek: its inner walls face away from the light; lift them
gap = np.zeros((S, S), bool)
gap[cov] = gap_faces[t] & (piece_face[t] == 1) & (region_face[t] == 2)
shade[gap & skin] *= GAP_LIFT
# between the nose and the lip: no paint smudge, little AO (the nostril shadows above are the only darkening)
nose_lip = skin & (np.abs(xf) < 0.022) & (y > 1.512) & (y < 1.548) & (z > 0.09)
nl = lowpass3d(nose_lip.astype(np.float32), np.ones((S, S), np.float32), skin & (np.abs(xf) < 0.03) & (y > 1.50)
               & (y < 1.56) & (z > 0.08), 0.002, 0.0005)
nl = np.clip(nl * 1.5, 0, 1)
detail = detail * (1 - nl) + np.clip(detail, 0.95, 1.05) * nl
form = form * (1 - nl) + np.clip(form, 0.97, 1.03) * nl
ao_f = ao_f * (1 - nl) + (1.0 - 0.15 * (1.0 - ao)) * nl
new = albedo[None, :] * (detail * form * ao_f * shade)[skin][:, None]
result[skin] = srgb(new)
report['skin_shading'] = {'nostril_texels': int(nostril.sum()),
                          'gap_texels': int((gap & skin).sum())}
# lips (face follow-up): a muted rose only a little darker than the skin, soft into it, no outline. The shape is the
# paint's red lips, its edge softened in 3D; the colour is LIP_TONE x the skin's own detail and AO (no paint outline)
redness = (rgb_raw[..., 0] - rgb_raw[..., 1]) / np.maximum(rgb_raw[..., 0], 1e-3)
mouth = np.clip(1.6 - np.sqrt((xf / 0.026) ** 2 + ((y - 1.508) / 0.011) ** 2), 0, 1) * (z > 0.085)
lip_ind = (np.clip((redness - 0.36) / 0.12, 0, 1) * mouth * skin_piece).astype(np.float32)
msel = skin_piece & (mouth > 0)
lip_w = lowpass3d(lip_ind, np.ones((S, S), np.float32), msel, LIP_SOFT_M, 0.0003) * (mouth > 0)
lip_w = np.clip((lip_w - 0.2) / 0.6, 0, 1)
lip_w = lip_w * lip_w * (3 - 2 * lip_w)
# the slit: a curve through the mouth opening's boundary (open edges of the head between the lips)
wpos_all = np.zeros((int(before['weld'].max()) + 1, 3))
wpos_all[before['weld']] = before['pos']
wtri = before['weld'][before['tri']]
edge_count = {}
for f in np.nonzero(piece_face == 1)[0]:
    for k in range(3):
        e = tuple(sorted((wtri[f, k], wtri[f, (k + 1) % 3])))
        edge_count[e] = edge_count.get(e, 0) + 1
open_v = np.unique([v for e, n in edge_count.items() if n == 1 for v in e])
ov = wpos_all[open_v]
ov = ov[(np.abs(ov[:, 0] - FACE_X) < 0.025) & (np.abs(ov[:, 1] - MOUTH_Y) < 0.004) & (ov[:, 2] > 0.1)]
# the lips close towards the corners (no opening there): the corners of the painted lips extend the curve
lipx = x[lip_w > 0.5]
corners = []
for xc in (np.percentile(lipx, 1), np.percentile(lipx, 99)):
    near = (lip_w > 0.5) & (np.abs(x - xc) < 0.0015)
    corners.append([xc, float(np.median(y[near]))])
corners = np.array(corners)
fit_x = np.concatenate([ov[:, 0], np.repeat(corners[:, 0], 8)])
fit_y = np.concatenate([ov[:, 1], np.repeat(corners[:, 1], 8)])
slit_poly = np.polyfit(fit_x, fit_y, 2)
slit_x = (float(corners[:, 0].min()), float(corners[:, 0].max()))
mid_x, half_x = (slit_x[0] + slit_x[1]) / 2, (slit_x[1] - slit_x[0]) / 2 * 1.12   # the gap reaches the corners
dy = y - np.polyval(slit_poly, x)
taper = np.clip(1 - ((x - mid_x) / half_x) ** 2, 0, 1) ** 0.35
inward = msel & (np.abs(dy) < 0.0025) & (taper > 0) & ((nrm[..., 2] < 0.6) | (np.abs(nrm[..., 1]) > 0.5))
# the dark line: a smooth curve painted on the front of the lips (it, not the triangle edges, draws the slit)
# the slit's colour depends only on the 3D distance from the smooth curve, on every face alike (front lip faces,
# inward faces, the mouth fill), so the jagged gap edges fall inside one smooth gradient
slit_w = np.exp(-0.5 * (np.maximum(np.abs(dy) - SLIT_CORE_M * taper, 0) / (SLIT_SIGMA_M * np.maximum(taper, 0.05)))
               ** 2) * (taper > 0) * msel
# the inward-facing faces between the lips (visible from the front) are a mid lip shadow, lighter than the line:
# their lighting darkens them, and their jagged edges must not contrast with the lips
in_w = np.zeros((S, S), np.float32)                # (round 3: the inward faces follow the curve's gradient)
tone = lin(np.array(LIP_TONE, np.float32))
tone_up = tone * LIP_UPPER                                       # one rose for both lips; the lower lip faces the
lip_lin = np.where((dy > 0)[..., None], tone_up, tone * LIP_LOWER)    # light and is held a little darker
lip_col = srgb(lip_lin * (detail * form * ao_f * shade)[..., None])
skin_col = result
lip_mix = skin_col * (1 - lip_w[..., None]) + lip_col * lip_w[..., None]
slit_col = srgb(tone * SLIT_DARK * ao_f[..., None])
inward_col = srgb(np.broadcast_to(tone * INWARD_TONE, slit_col.shape))
# the lower lip's inner shelf (faces turned up under the upper lip, within 3 mm below the curve) is occluded by the
# upper lip; it caught the light as pale shards: held in the upper lip's shadow
shelf = msel & (dy < 0) & (dy > -0.003) & (snrm[..., 1] > 0.2)
shelf_w = lowpass3d(shelf.astype(np.float32), np.ones((S, S), np.float32), msel, 0.0004, 0.0002)
lip_mix = lip_mix * (1 - SHELF_DARK * np.clip(shelf_w * 1.5, 0, 1))[..., None]
mixed = lip_mix * (1 - slit_w[..., None]) + slit_col * slit_w[..., None]
mixed = mixed * (1 - in_w[..., None]) + inward_col * in_w[..., None]
result = np.where(msel[..., None], mixed, result)
report['mouth_fill_srgb'] = np.round(srgb(tone * MOUTH_FILL), 0).astype(int).tolist()     # fix_mesh.py's fill
report['mouth'] = {'slit_poly': [round(float(c), 4) for c in slit_poly], 'slit_x': [round(v, 4) for v in slit_x],
                   'lip_texels': int((lip_w > 0.5).sum()), 'slit_texels': int((slit_w > 0.5).sum()),
                   'nostril_centres': [np.round(c, 4).tolist() for c in nostril_c]}
lips = (lip_w > 0.5) | (slit_w > 0.5) | (in_w > 0.5)
skin = skin_piece & ~lips
report['skin'] = {'albedo_srgb': list(SKIN_ALBEDO), 'chroma_ref': c_ref.round(4).tolist(),
                  'paint_face_srgb': srgb(np.median(lin(paint)[front], 0)).round(1).tolist(),
                  'texels': int(skin.sum()), 'lips_texels': int(lips.sum()),
                  'low_skin_share': round(float((q[skin_piece] < 0.3).mean()), 4)}
classes['skin'], classes['lips'] = skin, lips

# ---- 4. ramped regions: luminance quantiles onto the approved ones at the same surface points
appr = np.asarray(Image.open(f'{approved}_basecolor.png').convert('RGB'), np.float32)
LA = lin(appr) @ LUMA
appr_mask = np.stack([np.asarray(ch.resize((S, S), Image.BILINEAR), np.float32)
                      for ch in Image.open(f'{approved}_region_mask.png').convert('RGBA').split()], -1) / 255
Q = np.linspace(0, 1, 129)
Lr = lin(result) @ LUMA
# gown texels painted pale (the head masters' hood projected onto the shoulders) take the surrounding gown
gm = classes['gown'] & ~pale
outlier = classes['gown'] & pale
if outlier.any():
    gw = gm.astype(np.float32)
    fill = np.stack([ndimage.gaussian_filter(result[..., c] * gw, 8.0) for c in range(3)], -1)
    fill /= np.maximum(ndimage.gaussian_filter(gw, 8.0), 1e-4)[..., None]
    result[outlier] = fill[outlier]
report['gown_pale_filled_texels'] = int(outlier.sum())
# the gown's fine grain and the hood's knit speckle (both amplified by steep ramps) are softened first
for name, soft in (('veil', VEIL_SOFT), ('gown', GOWN_SOFT)):
    vm = classes[name].astype(np.float32)
    blur = np.stack([ndimage.gaussian_filter(result[..., c] * vm, 1.5) for c in range(3)], -1)
    blur /= np.maximum(ndimage.gaussian_filter(vm, 1.5), 1e-4)[..., None]
    result[classes[name]] = result[classes[name]] * (1 - soft) + blur[classes[name]] * soft
Lr = lin(result) @ LUMA
for name in ('gown', 'veil', 'hair'):
    sel = classes[name]
    w = weight[sel]
    # the approved distribution only where the approved mask has the same region (not where the new classes moved
    # a boundary, e.g. a lining edge)
    asel = sel & (appr_mask[..., ('gown', 'veil', 'hair').index(name)] > 0.5)
    qa = wpercentile(LA[asel], weight[asel], Q)
    if name in CONTRAST:                       # hair: the paint's dark strand gaps fell under the narrow hair ramp
        med = float(np.interp(0.5, Q, qa))
        mean = float(qa.mean())
        qa = med + CONTRAST[name] * (qa - med)
        qa = np.maximum(qa + (mean - float(qa.mean())), 1e-4)      # keep the region's mean (the tier colour)
    qn = wpercentile(Lr[sel], w, Q)
    qn = np.maximum.accumulate(qn + np.arange(len(qn)) * 1e-6)
    target = np.interp(Lr[sel], qn, qa)
    ratio = target / np.maximum(Lr[sel], 1e-5)
    result[sel] = srgb(lin(result[sel]) * ratio[:, None])
    report[name] = {'share': round(float(w.sum() / weight[cov].sum()), 4),
                    'approved_lum_p5_50_95': [round(float(x), 4) for x in wpercentile(LA[asel], weight[asel], np.array([.05, .5, .95]))],
                    'paint_lum_p5_50_95': [round(float(x), 4) for x in np.interp([.05, .5, .95], Q, qn)]}

result = texlib.pad(result, cov)
Image.fromarray(np.clip(result + 0.5, 0, 255).astype(np.uint8)).save(f'{out}_basecolor.png')

# ---- 5. region mask (RGBA as installed: R gown, G veil + lining, B hair, A unused)
mask = np.zeros((S, S, 4), np.float32)
for k, name in enumerate(('gown', 'veil', 'hair')):
    m = texlib.pad(classes[name].astype(np.float32)[..., None], cov)[..., 0]
    mask[..., k] = ndimage.gaussian_filter(m, 0.7)
mask[~cov] = texlib.pad(mask, cov)[~cov]
mask8 = np.clip(mask * 255 + 0.5, 0, 255).astype(np.uint8)
# each channel on its own: an RGBA resize premultiplies by the (empty) alpha channel
small = [Image.fromarray(mask8[..., k]).resize((1024, 1024), Image.Resampling.BOX) for k in range(4)]
Image.merge('RGBA', small).save(f'{out}_region_mask.png')
Image.fromarray(mask8, 'RGBA').save(f'{out}_region_mask_2k.png')

# ---- 6. normal
normals = []
for src in ('body', 'head'):
    n = load(M / f'{src}_retexture_{PAINT}' / 'texture_urls_0_normal.png') / 127.5 - 1
    n[..., 1] *= -1                                                   # Meshy +y down -> glTF +y up
    normals.append(n)
n = normals[0] * (1 - hw[..., None]) + normals[1] * hw[..., None]
tilt = np.linalg.norm(n[..., :2], axis=-1)
old_n = np.asarray(Image.open(HERE / 'work' / 'before_texpass' / 'img2_m372_normal_1k_head_atlas.png').convert('RGB'),
                   np.float32) / 127.5 - 1
target_tilt = float(np.percentile(np.linalg.norm(old_n[..., :2], axis=-1), 90))
current = float(np.percentile(tilt[cov], 90))
k_tilt = min(1.0, target_tilt / max(current, 1e-4))
scale = np.full((S, S), k_tilt, np.float32)
scale[skin | lips] *= 0.5
scale *= (1 - 0.7 * nose_zone).astype(np.float32)          # round 3: no bump detail on the nose's underside
# round 3: the head paint's normal map drew the removed spike's edge as a scratch on the cheek (the cook triples it)
scale *= (1 - clear).astype(np.float32)
scale[eye] = 0.0
n[..., :2] *= scale[..., None]
n[..., 2] = np.sqrt(np.clip(1 - (n[..., :2] ** 2).sum(-1), 0.0025, 1))
n /= np.linalg.norm(n, axis=-1, keepdims=True)
n = texlib.pad(n, cov)
nmap = np.clip((n + 1) * 127.5 + 0.5, 0, 255)
# round 3: the nose's down-facing underside gets almost no light (one dark blob between the nostrils, though its
# albedo is already near white): the normal map turns its shading normal toward the front, as far as it faces down
# (normfix.encode: the engine's own tangent frame, divided by the cook's relief lift)
tilt_w = (down * lift_zone * skin)
yy, xx = np.nonzero(lift_zone * skin > 0)
if len(yy):
    w_ = UNDERSIDE_TURN * tilt_w[yy, xx][:, None]
    tgt = snrm[yy, xx] * (1 - w_) + UNDERSIDE_NORMAL[None] * w_
    tt_ = tri_id[yy, xx]
    enc = normfix.encode(tgt.astype(np.float64), xyz[tt_], uv[tt_], before['nrm'][before['tri'][tt_]],
                         bary[yy, xx], normfix.cook_relief_scale(nmap))
    a_ = np.clip(tilt_w[yy, xx] * 4, 0, 1)[:, None]          # the paint's relief stays where nothing is turned
    nmap[yy, xx] = nmap[yy, xx] * (1 - a_) + enc * a_
    nmap = np.where(cov[..., None], nmap, texlib.pad(nmap, cov))   # the gutters follow (bilinear at chart edges)
report['nose_underside_texels'] = int(len(yy))
# round 3: no paint relief in the mouth (the cook lifts this map's relief x3 and the slit's tiny triangles turned it
# into noise); the painted line draws the slit
wf = np.clip(np.maximum.reduce([in_w, slit_w, lip_w]) * 1.5, 0, 1)[..., None]   # soft into the skin's relief
nmap = nmap * (1 - wf) + np.array([127.5, 127.5, 255.0]) * wf
report['flat_mouth_texels'] = int((wf[..., 0] > 0.5).sum())
Image.fromarray(nmap.astype(np.uint8)).save(f'{out}_normal.png')
report['normal'] = {'approved_p90_tilt': round(target_tilt, 3), 'paint_p90_tilt': round(current, 3),
                    'scale': round(k_tilt, 3)}

# ---- 7. metal/roughness
# round 3: the lips are matte (m342's lips had wrongly been given the eyes' gloss): lip 0.12 / 0.7, the slit and the
# faces between the lips 0.05 / 0.95, boxed from 2048 onto the approved 1024 map
mr_img = Image.open(f'{approved}_metal_rough.png').convert('RGB')
mrn = np.asarray(mr_img, np.float32) / 255
over = np.full((S, S, 2), -1, np.float32)
over[lips & ~(slit_w > 0.5) & ~(in_w > 0.5)] = (0.12, 0.7)
over[(slit_w > 0.5) | (in_w > 0.5)] = (0.05, 0.95)
nn = mrn.shape[0]
for c in range(2):
    have = over[..., c] >= 0
    num = np.asarray(Image.fromarray(np.where(have, over[..., c], 0)).resize((nn, nn), Image.Resampling.BOX))
    den = np.asarray(Image.fromarray(have.astype(np.float32)).resize((nn, nn), Image.Resampling.BOX))
    put = den > 0.2
    mrn[..., c][put] = num[put] / den[put]
Image.fromarray(np.clip(mrn * 255 + 0.5, 0, 255).astype(np.uint8)).save(f'{out}_metal_rough.png')
report['matte_lip_texels'] = int((over[..., 0] >= 0).sum())

preview = np.zeros((S, S, 3), np.uint8)
for name, col in (('gown', (20, 160, 40)), ('veil', (170, 230, 190)), ('hair', (170, 100, 20)), ('skin', (235, 180, 150)),
                  ('lips', (220, 20, 40)), ('eye', (255, 0, 255))):
    preview[classes[name]] = col
Image.fromarray(preview).save(f'{out}_classes.png')
json.dump(report, open(f'{out}_report.json', 'w'), indent=1)
print('COMPOSED', out, json.dumps(report))
