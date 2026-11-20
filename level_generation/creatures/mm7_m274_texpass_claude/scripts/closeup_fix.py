"""Close-up fixes on the composed Mage maps (user review 2026-11-01, tier B front head close-up), painted from the
texels' rest-pose positions so every triangle agrees and no paint edge follows a triangle line:

1. Moustache: the whole moustache piece (its own mesh component under the nose, centre bump included) is hair in the
   hair region (B, the beard ramp), with strands running outward and down from the nose: a stripe pattern along rays
   from a point under the nose tip, wavy, broken along its length. Its brightness takes the beard's distribution near
   the mouth (rank-mapped), shadowed on the underside; the hair also fades onto the skin just under the nose.
2. Mouth: a small lower lip (the top of the lower lip's slope under the moustache, lip colour); the upper lip under
   the moustache painted as moustache hair, and only a thin mouth line between it and the lower lip dark; the bare chin and lower-lip front inside the beard painted as
   beard (strands fanning down) and put in the hair region, feathered into the painted beard around it.
3. Eyes: each eyeball (its own component) painted procedurally in eye-local coordinates, both at its texels on the
   layout and in its own 64-px patch of free atlas space (work/nomoustache/patches.json; remove_moustache.py maps the
   LOD0 eyeballs there by the frames written to <out>_eyes.json): sphere centre fitted, axis
   from the centre through the visible cap blended with straight ahead; sclera, a blue-teal iris with radial streaks
   and a darker limbal ring, a round pupil, the upper lid's shadow, a small soft highlight. The lid rims round the eyeball get the lid shadow.

moustache=geometry (default) keeps the moustache piece; flat and bare are for remove_moustache.py, which deletes
it: the exposed upper lip gets a flat painted moustache (strands outward and down, dense to the mouth and the corners,
ragged feathered edge under the nose; hair region) or bare skin, with the mouth line and the small lower lip kept,
and the hole-fill patch is painted to match.

Usage: closeup_fix.py <in prefix> <out prefix> [moustache=geometry|flat|bare] (reads <in>_{basecolor,region_mask,material_classes,metal_rough}.png,
writes <out>_* with the normal map copied, and <out>_closeup.json)."""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

HERE = Path(__file__).resolve().parents[1]
W = HERE / 'work'
src, out = sys.argv[1:3]
OPTS = dict(a.split('=', 1) for a in sys.argv[3:])
MOUSTACHE = OPTS.get('moustache', 'geometry')       # geometry (the moustache piece kept), flat or bare (piece removed)
PATCHES = json.load(open(HERE / 'work' / 'nomoustache' / 'patches.json'))
FILL_BOX = (-0.0135, 0.0005, 1.4515, 1.4655)          # x0, x1, y0, y1 of the hole-fill patch's front projection
S = 2048
LUMA = np.array([0.2126, 0.7152, 0.0722])


def lin(c):
    c = np.clip(np.asarray(c, np.float64) / 255.0, 0, 1)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    c = np.clip(c, 0, 1)
    return 255.0 * np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def vnoise(u, seed):
    """1D value noise, cubic, values 0..1."""
    i = np.floor(u)
    f = u - i
    h = lambda k: np.modf(np.sin(k * 12.9898 + seed * 78.233) * 43758.5453)[0] % 1.0
    f = f * f * (3 - 2 * f)
    return h(i) * (1 - f) + h(i + 1) * f


d = np.load(W / 'lod0_before.npz')
pos, tri, weld, head_face = d['pos'], d['tri'], d['weld'], d['head_face']
r = np.load(W / 'approved_fine_raster2048.npz')
tri_id = r['tri_id']
cov = tri_id >= 0
t = np.maximum(tri_id, 0)
xyz = np.load(W / 'texel_xyz2048.npy').astype(np.float64)
x, y, z = xyz[..., 0], xyz[..., 1], xyz[..., 2]
nweld = int(weld.max()) + 1
wt = weld[tri]
_, part = connected_components(coo_matrix((np.ones(3 * len(tri)), (wt.ravel(), np.roll(wt, 1, 1).ravel())),
                                          shape=(nweld, nweld)), directed=False)
face_part = part[wt[:, 0]]
centre = pos[tri].mean(1)
fn = np.cross(pos[tri[:, 1]] - pos[tri[:, 0]], pos[tri[:, 2]] - pos[tri[:, 0]])
fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
tex_part = np.where(cov, face_part[t], -1)
tex_n = fn[t]

# components of the head piece: the main head, the moustache (60-120 triangles in front of the mouth), the eyeballs
head_parts = np.unique(face_part[head_face])
main = max(head_parts, key=lambda k: (face_part == k).sum())
moustache, eyes = None, []
for k in head_parts:
    sel = face_part == k
    c = centre[sel].mean(0)
    if 40 <= sel.sum() <= 100 and 1.46 < c[1] < 1.52 and c[2] > 0.08:
        eyes.append(k)
    elif 60 <= sel.sum() <= 140 and 1.44 < c[1] < 1.47 and c[2] > 0.12 and abs(c[0]) < 0.01:
        moustache = k
assert moustache is not None and len(eyes) == 2, (moustache, eyes)
on_main = cov & (tex_part == main)
on_must = cov & (tex_part == moustache)

base = np.asarray(Image.open(f'{src}_basecolor.png').convert('RGB'), np.float64)
lb = lin(base)
L = lb @ LUMA
classes = np.asarray(Image.open(f'{src}_material_classes.png').resize((S, S), Image.NEAREST)).copy()
mask_img = Image.open(f'{src}_region_mask.png').convert('RGBA')
mask = np.stack([np.asarray(ch, np.float64) for ch in mask_img.split()], -1) / 255     # 1024
ao = np.asarray(Image.open(HERE / 'textures' / 'm274_tp_ao_2k.png').convert('L'), np.float64) / 255
ao = ndimage.gaussian_filter(np.where(ao > 0.003, ao, np.median(ao[cov])), 1.5)
shade_ao = np.clip(ao / np.median(ao[on_main]), 0.5, 1.15) ** 0.7

# beard brightness near the mouth: target distribution of the procedural hair
ref = on_main & (classes == 2) & (y > 1.38) & (y < 1.45) & (z > 0.11) & (np.abs(x) < 0.05)
ref_L = np.sort(L[ref])
ref_chroma = np.median(lb[ref] / np.maximum(L[ref], 1e-5)[:, None], axis=0)
report = {'moustache_component': int(moustache), 'eye_components': [int(e) for e in eyes],
          'beard_reference_texels': int(ref.sum()),
          'beard_L_p10_50_90': [round(float(np.percentile(ref_L, q)), 4) for q in (10, 50, 90)]}


def strands(sel, cx, cy, k_ang, seed):
    """Brightness of strands along rays from (cx, cy) in the front plane, rank-mapped onto the beard's distribution."""
    dx, dy = x[sel] - cx, cy - y[sel]
    th = np.arctan2(dx, dy)
    rr = np.hypot(dx, dy)
    thw = th + 0.025 * np.sin(rr * 700 + th * 5) + 0.01 * np.sin(rr * 2300 + seed)
    s = 0.6 * vnoise(thw * k_ang, seed) + 0.4 * vnoise(thw * k_ang * 2.3 + 5, seed + 1)
    s *= 0.75 + 0.25 * vnoise(rr * 1500 + th * 40, seed + 2)                 # breaks along the strand
    rank = np.argsort(np.argsort(s)) / max(len(s) - 1, 1)
    return np.interp(rank, np.linspace(0, 1, len(ref_L)), ref_L)


def strand_field(xs, ys, cx, cy, k_ang, seed):
    dx, dy = xs - cx, cy - ys
    th = np.arctan2(dx, dy)
    rr = np.hypot(dx, dy)
    thw = th + 0.025 * np.sin(rr * 700 + th * 5) + 0.01 * np.sin(rr * 2300 + seed)
    f = 0.6 * vnoise(thw * k_ang, seed) + 0.4 * vnoise(thw * k_ang * 2.3 + 5, seed + 1)
    return f * (0.75 + 0.25 * vnoise(rr * 1500 + th * 40, seed + 2))


# strand field values over a fixed sample of the upper lip, so any texel set (face or fill patch) maps alike
_gx, _gy = np.meshgrid(np.linspace(-0.04, 0.04, 400), np.linspace(1.444, 1.468, 120))
FLAT_K = 13.0                                           # strands about 2-3 texels wide on the upper lip
FIELD_REF = np.sort(strand_field(_gx.ravel(), _gy.ravel(), 0.0, 1.469, FLAT_K, 3.0))


def flat_moustache(xs, ys):
    """Brightness and hair weight of the flat moustache painted on the upper lip: strands outward and down from
    under the nose, dense down to the mouth and at the corners, a ragged feathered edge under the nose."""
    f = strand_field(xs, ys, 0.0, 1.469, FLAT_K, 3.0)
    Lf = np.interp(np.searchsorted(FIELD_REF, f) / len(FIELD_REF), np.linspace(0, 1, len(ref_L)), ref_L)
    rag = 0.0016 * (vnoise(xs * 900, 7.0) - 0.5) + 0.0008 * (vnoise(xs * 2600, 8.0) - 0.5)
    w = (1 - smooth(1.4585 + rag, 1.4650 + rag, ys)) * smooth(1.4450, 1.4462, ys) * (1 - smooth(0.031, 0.040, np.abs(xs)))
    edge = smooth(1.4560, 1.4600, ys)                            # strand tips thin out the top edge only
    w *= 1 - edge * (1 - smooth(0.25, 0.55, f)) * 0.6
    return Lf, w


skin_ref = on_main & (classes == 1) & (y > 1.46) & (y < 1.49) & (np.abs(x) > 0.025) & (np.abs(x) < 0.045) & (z > 0.1)
skin_lin = np.median(lb[skin_ref], axis=0)
report['moustache_mode'] = MOUSTACHE
new = lb.copy()
hair_w = np.zeros((S, S))          # target 1 in the hair region
skin_w = np.zeros((S, S))          # target 0 in the hair region (lip, mouth, eyes)

# ---- 1. moustache
NOSE = (0.0, 1.469)
if MOUSTACHE == 'geometry':
    Lm = strands(on_must, *NOSE, 45.0, 3.0)
    ny = tex_n[on_must][:, 1]
    Lm *= np.where(ny < -0.4, 0.78, np.where(ny > 0.6, 0.85, 1.0)) * shade_ao[on_must]
    new[on_must] = ref_chroma * Lm[:, None]
    hair_w[on_must] = 1
    classes[on_must] = 2
    # soft hair on the skin just under the nose (above the moustache's top edge)
    under = on_main & (np.abs(x) < 0.032) & (y > 1.4605) & (y < 1.467) & (z > 0.125)
    wu = 0.3 * (1 - smooth(1.4625, 1.4655, y[under])) * (1 - smooth(0.024, 0.032, np.abs(x[under])))
    Lu = strands(under, *NOSE, 45.0, 3.0)
    new[under] = new[under] * (1 - wu[:, None]) + (ref_chroma * Lu[:, None]) * wu[:, None]
    hair_w[under] = np.maximum(hair_w[under], wu)
else:
    # moustache piece removed: the upper lip (nose to mouth) gets a flat painted moustache, or bare skin
    ul = on_main & (np.abs(x) < 0.042) & (y > 1.4435) & (y < 1.4685) & (z > 0.112)
    lat = 1 - smooth(0.031, 0.040, np.abs(x[ul]))
    pores = 0.97 + 0.06 * vnoise(x[ul] * 5000 + y[ul] * 3100, 13.0)
    skin_col = skin_lin * (pores * shade_ao[ul])[:, None]
    base_w = smooth(1.4450, 1.4462, y[ul]) * lat * (1 - smooth(1.4655, 1.4685, y[ul]))
    new[ul] = new[ul] * (1 - base_w[:, None]) + skin_col * base_w[:, None]
    if MOUSTACHE == 'flat':
        Lf, wf = flat_moustache(x[ul], y[ul])
        hair_col = ref_chroma * (Lf * shade_ao[ul])[:, None]
        new[ul] = new[ul] * (1 - wf[:, None]) + hair_col * wf[:, None]
        hair_w[ul] = np.maximum(hair_w[ul], wf)
        classes[ul] = np.where(wf > 0.5, 2, np.where(base_w > 0.5, 1, classes[ul]))
        skin_w[ul] = np.maximum(skin_w[ul], base_w * (1 - wf))
    else:
        classes[ul] = np.where(base_w > 0.5, 1, classes[ul])
        skin_w[ul] = np.maximum(skin_w[ul], base_w)

# ---- 2. mouth
front = on_main & (z > 0.12) & (np.abs(x) < 0.045)
lip = front & (y > 1.435) & (y < 1.4445) & (z > 0.135)
lw = smooth(1.4355, 1.4375, y[lip]) * (1 - smooth(1.4428, 1.4440, y[lip])) * (1 - smooth(0.0085, 0.0115, np.abs(x[lip])))
lip_lin = lin([186, 102, 92])
shade = np.clip(L[lip] / np.maximum(ndimage.gaussian_filter(L, 3)[lip], 1e-4), 0.75, 1.25) ** 0.5 * shade_ao[lip]
new[lip] = new[lip] * (1 - lw[:, None]) + (lip_lin * shade[:, None]) * lw[:, None]
# the upper lip under the moustache (visible between its lower edge and the mouth) is moustache hair; only a thin
# mouth line between it and the lower lip is dark
if MOUSTACHE == 'geometry':
    upper = front & (y > 1.4440) & (y < 1.4625) & (z < 0.1475) & (np.abs(x) < 0.034)
    uw = smooth(1.4450, 1.4462, y[upper]) * (1 - smooth(0.026, 0.034, np.abs(x[upper])))
    Lup = strands(upper, *NOSE, 45.0, 3.0) * shade_ao[upper]
    new[upper] = new[upper] * (1 - uw[:, None]) + (ref_chroma * Lup[:, None]) * uw[:, None]
    hair_w[upper] = np.maximum(hair_w[upper], uw)
    classes[upper] = np.where(uw > 0.5, 2, classes[upper])
mouth = front & (y > 1.4425) & (y < 1.4470) & (z < (0.1475 if MOUSTACHE == 'geometry' else 0.2)) & (np.abs(x) < 0.026)
mw = smooth(1.4425, 1.4437, y[mouth]) * (1 - smooth(1.4452, 1.4466, y[mouth])) * (1 - smooth(0.017, 0.025, np.abs(x[mouth])))
dark = lin([34, 20, 18])
new[mouth] = new[mouth] * (1 - mw[:, None]) + dark * mw[:, None]
# the lip mask and the mouth are skin (no ramp); fully dark mouth texels are class 7
lip_full = np.zeros((S, S))
lip_full[lip] = lw
mouth_full = np.zeros((S, S))
mouth_full[mouth] = mw
skin_w = np.maximum(skin_w, np.maximum(lip_full, mouth_full))
cl_lip = np.zeros((S, S), bool)
cl_lip[lip] = lw > 0.5
classes[cl_lip] = 1
cl_mouth = np.zeros((S, S), bool)
cl_mouth[mouth] = mw > 0.5
classes[cl_mouth] = 7
# bare chin / lower-lip front inside the beard: beard strands, feathered into the painted beard around it
# the patch is every zone texel the hair region does not fully cover yet (the old skin patch and its feathered rim,
# which showed as an orange outline), except the lip and the mouth line
mask_b2048 = np.asarray(Image.fromarray((mask[..., 2] * 255).astype(np.uint8)).resize((S, S), Image.BILINEAR),
                        np.float64) / 255
zone = front & (y > 1.390) & (y < 1.4455) & (np.abs(x) < 0.040)
bare = zone & ((classes == 1) | (mask_b2048 < 0.9)) & (lip_full < 0.5) & (mouth_full < 0.5)
CHIN = (0.0, 1.50)
proc = np.zeros((S, S))
proc[zone] = strands(zone, *CHIN, 150.0, 11.0) * shade_ao[zone]
dist = ndimage.distance_transform_edt(~bare)                 # texels from the bare patch (0 inside)
fw = np.where(zone, 1 - smooth(1.5, 4.0, dist), 0) * (1 - lip_full) * (1 - mouth_full)
new[zone] = new[zone] * (1 - fw[zone][:, None]) + (ref_chroma * proc[zone][:, None]) * fw[zone][:, None]
hair_w = np.maximum(hair_w, fw)
classes[bare & (fw > 0.5)] = 2
report['mouth'] = {'lip_texels': int((lip_full > 0.5).sum()), 'mouth_dark_texels': int((mouth_full > 0.5).sum()),
                   'chin_to_beard_texels': int((bare & (fw > 0.5)).sum())}

# ---- 3. eyes
up = np.array([0.0, 1.0, 0.0])
IRIS, LIMBUS, PUPIL = 0.50, 0.09, 0.17
iris_in, iris_out, ring = lin([98, 138, 150]), lin([60, 96, 112]), lin([26, 38, 48])
sclera, sclera_edge, pupil_c = lin([206, 196, 186]), lin([172, 146, 136]), lin([10, 10, 12])
lid_col = lin([118, 82, 72])
eye_report = []
eye_frames = []


def eye_colour(v, axis, e1, e2, k):
    """Colour of eyeball directions v (unit, eye-local frame axis/e1/e2): iris, limbal ring, pupil, sclera that
    darkens to the lid colour towards the cap's edge (no pale shards where the low-poly lids leave it showing), the
    upper lid's shadow and a soft highlight."""
    a = np.arccos(np.clip(v @ axis, -1, 1))
    phi = np.arctan2(v @ e2, v @ e1)
    streak = 0.6 * vnoise(phi * 24 / np.pi, 21 + k) + 0.4 * vnoise(phi * 57 / np.pi, 22 + k)
    tir = np.clip(a / IRIS, 0, 1)[:, None]
    col = (iris_in * (1 - tir) + iris_out * tir) * (0.8 + 0.4 * streak[:, None])
    col = col * (1 - smooth(IRIS - LIMBUS, IRIS, a)[:, None]) + ring * smooth(IRIS - LIMBUS, IRIS, a)[:, None]
    scl = sclera * (1 - smooth(0.75, 1.0, a)[:, None]) + sclera_edge * smooth(0.75, 1.0, a)[:, None]
    scl = scl * (1 - smooth(0.95, 1.2, a)[:, None]) + lid_col * smooth(0.95, 1.2, a)[:, None]
    col = col * (1 - smooth(IRIS, IRIS + 0.03, a)[:, None]) + scl * smooth(IRIS, IRIS + 0.03, a)[:, None]
    col = col * smooth(PUPIL - 0.02, PUPIL + 0.01, a)[:, None] + pupil_c * (1 - smooth(PUPIL - 0.02, PUPIL + 0.01, a))[:, None]
    hdir = axis + 0.22 * up - 0.15 * e1                  # highlight up and to one side, the same on both eyes
    hdir /= np.linalg.norm(hdir)
    hl = np.exp(-0.5 * (np.arccos(np.clip(v @ hdir, -1, 1)) / 0.04) ** 2)[:, None]
    lid = smooth(0.25, 0.75, v @ up)[:, None]                   # the upper lid's shadow on the top of the eyeball
    col = col * (1 - 0.45 * lid)
    return col * (1 - 0.85 * hl) + 0.85 * hl


patch = np.zeros((S, S), bool)                                   # texels of the extra patches (eyes, hole fill)
for k in sorted(eyes, key=lambda e: centre[face_part == e].mean(0)[0]):
    vid = np.unique(wt[face_part == k])
    wpos = np.zeros((nweld, 3))
    wpos[weld] = pos
    P = wpos[vid]
    A = np.c_[2 * P, np.ones(len(P))]
    sol = np.linalg.lstsq(A, (P ** 2).sum(1), rcond=None)[0]
    c = sol[:3]
    R = float(np.sqrt(sol[3] + c @ c))
    cap = P.mean(0) - c
    axis = cap / np.linalg.norm(cap) + np.array([0, 0, 1.0])
    axis /= np.linalg.norm(axis)
    e1 = np.cross(up, axis)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(axis, e1)
    sel = cov & (tex_part == k)
    v = xyz[sel] - c
    v /= np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)
    new[sel] = eye_colour(v, axis, e1, e2, k)
    skin_w[sel] = 1
    classes[sel] = 6
    # the eye's own patch (LOD0 eyeballs are mapped there by remove_moustache.py): planar along the axis
    name = 'eye_left_x_neg' if c[0] < 0 else 'eye_right_x_pos'
    x0, y0, side = PATCHES[name]
    jj, ii = np.mgrid[0:side, 0:side]
    pa = (ii + 0.5) / side * 2 - 1
    pb = -((jj + 0.5) / side * 2 - 1)
    rr = np.hypot(pa, pb)
    sc = np.where(rr > 1, 1 / np.maximum(rr, 1e-9), 1.0)
    pa, pb = pa * sc, pb * sc
    vv = pa[..., None] * e1 + pb[..., None] * e2 + np.sqrt(np.clip(1 - pa ** 2 - pb ** 2, 0, 1))[..., None] * axis
    new[y0:y0 + side, x0:x0 + side] = eye_colour(vv.reshape(-1, 3), axis, e1, e2, k).reshape(side, side, 3)
    skin_w[y0:y0 + side, x0:x0 + side] = 1
    classes[y0:y0 + side, x0:x0 + side] = 6
    patch[y0:y0 + side, x0:x0 + side] = True
    eye_frames.append({'component': int(k), 'patch': name, 'box': [x0, y0, side], 'centre': c.tolist(), 'radius': R,
                       'axis': axis.tolist(), 'e1': e1.tolist(), 'e2': e2.tolist()})
    # lid shadow on the skin round the eyeball (the rims and corners that showed pale shards)
    rim = on_main & (np.linalg.norm(xyz - c, axis=-1) < R + 0.003) & (z > c[2] - 0.004)
    dd = np.linalg.norm(xyz[rim] - c, axis=-1)
    ws = 0.5 * (1 - smooth(R + 0.0005, R + 0.003, dd))
    new[rim] = new[rim] * (1 - ws[:, None]) + (new[rim] * 0.45) * ws[:, None]
    eye_report.append({'centre': [round(float(q), 4) for q in c], 'radius': round(R, 4),
                       'axis': [round(float(q), 3) for q in axis], 'texels': int(sel.sum()),
                       'rim_texels': int((ws > 0.1).sum()), 'patch': [x0, y0, side]})
json.dump(eye_frames, open(f'{out}_eyes.json', 'w'), indent=1)

# the hole-fill patch (the 5-edge opening of the face under the removed moustache), front projection of FILL_BOX
x0, y0, side = PATCHES['hole_fill']
jj, ii = np.mgrid[0:side, 0:side]
fx = FILL_BOX[0] + (ii + 0.5) / side * (FILL_BOX[1] - FILL_BOX[0])
fy = FILL_BOX[3] - (jj + 0.5) / side * (FILL_BOX[3] - FILL_BOX[2])
ao_fill = float(np.median(shade_ao[on_main & (np.abs(x) < 0.012) & (y > 1.452) & (y < 1.465)]))
fill = skin_lin * ao_fill * np.ones((side, side, 3))
fill_w = np.zeros((side, side))
if MOUSTACHE == 'flat':
    Lf, wf = flat_moustache(fx.ravel(), fy.ravel())
    wf = wf.reshape(side, side)
    fill = fill * (1 - wf[..., None]) + ref_chroma * (Lf.reshape(side, side) * ao_fill)[..., None] * wf[..., None]
    fill_w = wf
new[y0:y0 + side, x0:x0 + side] = fill
hair_w[y0:y0 + side, x0:x0 + side] = fill_w
skin_w[y0:y0 + side, x0:x0 + side] = 1 - fill_w
classes[y0:y0 + side, x0:x0 + side] = np.where(fill_w > 0.5, 2, 1)
patch[y0:y0 + side, x0:x0 + side] = True
report['eyes'] = eye_report

# ---- write: colour (gutters padded), hair mask channel edited at 1024 by area-averaged targets, classes, MR, normal
cov = cov | patch                                              # the patches are painted texels too
rgb = srgb(new)
_, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
rgb = np.where(cov[..., None], rgb, rgb[iy, ix])
Image.fromarray(np.clip(rgb + 0.5, 0, 255).astype(np.uint8)).save(f'{out}_basecolor.png')


def down(a):
    return a.reshape(1024, 2, 1024, 2).mean((1, 3))


# averages over the covered texels only: island-edge mask texels must not be diluted by the empty gutter half
cov_f = cov.astype(np.float64)
hw = down(hair_w * cov_f) / np.maximum(down(cov_f), 1e-9)
sw = down(skin_w * cov_f) / np.maximum(down(cov_f), 1e-9)
b = mask[..., 2]
b = b + (1 - b) * hw
b = b * (1 - sw)
# pad the edited channel into the gutters (nearest covered texel), as compose.py pads the mask
cov_small = down(cov.astype(np.float64)) > 0
_, (my, mx) = ndimage.distance_transform_edt(~cov_small, return_indices=True)
mask[..., 2] = np.where(cov_small, b, b[my, mx])
# the patches lie in free atlas space that compose.py padded with neighbouring regions (the robe): no robe or cape there
patch_small = down(patch.astype(np.float64)) > 0
mask[patch_small, 0] = 0
mask[patch_small, 1] = 0
Image.fromarray(np.clip(mask * 255 + 0.5, 0, 255).astype(np.uint8), 'RGBA').save(f'{out}_region_mask.png')
Image.fromarray(np.asarray(Image.fromarray(classes).resize((1024, 1024), Image.NEAREST))).save(
    f'{out}_material_classes.png')
shutil.copyfile(f'{src}_metal_rough.png', f'{out}_metal_rough.png')
shutil.copyfile(f'{src}_normal.png', f'{out}_normal.png')
json.dump(report, open(f'{out}_closeup.json', 'w'), indent=1)
print('CLOSEUP', out, json.dumps(report))
