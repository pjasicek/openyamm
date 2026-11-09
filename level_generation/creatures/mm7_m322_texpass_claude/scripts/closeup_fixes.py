"""Close-up fixes on the composed m322 maps (user close-up review, 2026-11-01). Input: textures/m322_tp_* (compose.py)
on work/uv_fine.npz. Output: textures/m322_tp2_* on work/uv_final.npz (uv_fine with only the eye charts replaced by one disc per eyeball).

1. Eyes (r3; the route of ../mm7_m342_texpass_claude face_geom.py, uv_eyes.py, face_paint.py): the 4K head paint's
   irises were shards (each eye triangle painted on its own at 18 px/cm). Each eyeball (pieces 4, 5) is re-charted as
   ONE disc: azimuthal projection around its forward axis, full density to IRIS_KNEE iris radii, SCLERA_SLOPE over
   the sclera to OPEN_KNEE rad and TAIL over the hidden back, at one density factor (up to EYE_SCALE_MAX) that fits
   both discs into the two largest free circles of the atlas; no seam crosses the eye and the disc border is padded. Every eye texel is painted from geometry (sphere fit, axis through the
   centre of the part of the shell in front of the face skin, raised GAZE_UP_DEG): grey-green iris of IRIS_SHARE of
   the visible width with warm collarette, radial fibres and dark limbal ring, round pupil, soft highlight; off-white
   sclera darkening to the corners, shaded softly by its depth in front of the skin (a wider band under the upper
   lid). Skin within LID_IN..LID_OUT of an eyeball takes a soft lid shadow.
2. Mouth: the mouth pieces (8, 9, 11) and the inward-facing lip faces (normal toward the mouth line, behind the
   lips' front in their 1 mm column of x, within MOUTH_BAND of the line) take a dark gradient by depth behind that
   front, and lip surface within 2 mm of the line more than 2 mm behind it, fading out at the corners) take a dark gradient by depth: dark red-brown at the lip
   edge to near black 7 mm in; the weight is blurred so the gap is one soft shadow; specular is off there.
3. Vest strap: the back-facing triangles seen from the front through the hole at the top of the strap (back-side
   faces near either strap top that the hair hides from behind), the reddish flap triangle and the stud piece take
   vest leather (stud: the vest studs' brass).
   Trouser grommets painted skin take the other grommets' metal. The top lacing strip (piece 6, painted skin with a
   dark outline that read as a lace stroke above the lacing) takes the cleavage skin tone, shaded by the skin
   behind it; leftover dark stroke paint on the skin just above it is refilled.
4. Bare skin: leather-, hair- or green-coloured texels on skin-shell faces whose 1.5 cm surroundings are mostly skin
   (a dark stroke above the top lacing strip, strands on the upper back) are refilled from the surrounding skin of
   the same chart.
   Painted laces in the side-lacing gaps and between the front lacing are kept.
Usage: closeup_fixes.py [out prefix, default textures/m322_tp2]
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import eyes_geom  # noqa: E402
import texlib  # noqa: E402
import texture_quality as TQ  # noqa: E402

out = sys.argv[1] if len(sys.argv) > 1 else str(HERE / 'textures' / 'm322_tp2')
src = HERE / 'textures' / 'm322_tp'
S, SMALL = 2048, 1024
EYE_SCALE_MAX = 4.0
IRIS_KNEE, OPEN_KNEE, SCLERA_SLOPE, TAIL = 1.25, 0.9, 0.5, 0.15
MARGIN = 3
MOUTH_LINE_Y = 1.5733
MOUTH_BAND = 0.0032
# eyes r3: the HD head view's muted grey-green (its brightest quartile, lifted: the photo is dimly lit)
IRIS_SHARE, PUPIL_SHARE, GAZE_UP_DEG = 0.55, 0.30, 4.0
IRIS, IRIS_DARK = np.array([118, 128, 114.0]), np.array([86, 96, 88.0])
COLLARETTE, LIMBUS, PUPIL = np.array([132, 116, 84.0]), np.array([54, 60, 56.0]), np.array([10, 10, 12.0])
SCLERA, SCLERA_EDGE = np.array([196, 188, 180.0]), np.array([120, 100, 95.0])
LID_SHADE_UPPER, LID_SHADE_LOWER = 0.0045, 0.0025
LID_IN, LID_OUT = 0.0006, 0.0019
LID_SHADOW, LOWER_MARGIN = np.array([78, 58, 52.0]), np.array([150, 104, 96.0])     # lower margin: pinkish waterline
report = {}

layout = np.load(HERE / 'work' / 'uv_fine.npz')
before = np.load(HERE / 'work' / 'lod0_before.npz')
uv, xyz = layout['uv'].copy(), layout['xyz']
tri, weld, hf, piece = before['tri'], before['weld'], before['head_face'], before['piece']
r = np.load(HERE / 'work' / 'approved_fine_raster2048.npz')
tid, bary = r['tri_id'], r['bary']
cov = tid >= 0
t = np.where(cov, tid, 0)
tp = np.where(cov, piece[t], -1)
point = (xyz[t] * bary[..., None]).sum(-2)
fn = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
area3 = np.linalg.norm(fn, axis=1) / 2
fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
centre = xyz.mean(1)

base = np.asarray(Image.open(f'{src}_basecolor.png').convert('RGB'), np.float64)
normal = np.asarray(Image.open(f'{src}_normal.png').convert('RGB'), np.float64)
mr = np.asarray(Image.open(f'{src}_metal_rough.png').convert('RGB'), np.float64)
classes = np.asarray(Image.open(f'{src}_material_classes.png'), np.uint8).copy()
mask_img = Image.open(f'{src}_region_mask.png').convert('RGBA')
mask = np.stack([np.asarray(c, np.float64) for c in mask_img.split()], -1)          # 1024
mask_s = np.stack([np.asarray(c.resize((S, S), Image.BILINEAR), np.float64) / 255 for c in mask_img.split()], -1)

_, isl = np.unique(TQ.islands(uv, xyz), return_inverse=True)
isl = isl.ravel()
island_map = np.where(cov, isl[t], -1)
objects = ndimage.find_objects(island_map + 1)


def island_blur(img, sigma, valid):
    data = img[..., None] if img.ndim == 2 else img
    res = data.copy()
    pad_px = int(3 * sigma) + 2
    for i, sl in enumerate(objects):
        if sl is None:
            continue
        y0, y1 = max(sl[0].start - pad_px, 0), min(sl[0].stop + pad_px, S)
        x0, x1 = max(sl[1].start - pad_px, 0), min(sl[1].stop + pad_px, S)
        inside = island_map[y0:y1, x0:x1] == i
        m = (inside & valid[y0:y1, x0:x1]).astype(np.float64)
        den = ndimage.gaussian_filter(m, sigma, mode='constant')
        for c in range(data.shape[-1]):
            num = ndimage.gaussian_filter(data[y0:y1, x0:x1, c] * m, sigma, mode='constant')
            res[y0:y1, x0:x1, c][inside] = np.where(den > 1e-3, num / np.maximum(den, 1e-6),
                                                     data[y0:y1, x0:x1, c])[inside]
    return res[..., 0] if img.ndim == 2 else res


def hsv(rgb):
    h = np.asarray(Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    return h[..., 0] * 360, h[..., 1], h[..., 2]


def skinlike(img):
    mx, mn = img.max(-1), img.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1)
    return (img[..., 0] >= img[..., 1]) & (img[..., 1] >= 0.88 * img[..., 2]) & (sat > 0.1) & (sat < 0.48) & (mx > 105)


lum = base @ np.array([0.2126, 0.7152, 0.0722])

# ---- 2. mouth
lipbox = cov & np.isin(tp, [0, 8, 9, 11]) & hf[t] & (np.abs(point[..., 1] - MOUTH_LINE_Y) < MOUTH_BAND) & \
    (point[..., 0] > -0.027) & (point[..., 0] < 0.017)
lip_front_z = float(np.percentile(point[lipbox & (tp == 0)][:, 2], 98))
# front of the lips per 1 mm column of x (the lips curve back toward the corners): depth behind it marks the gap
xb = np.clip(((point[..., 0] + 0.027) / 0.001).astype(int), 0, 43)
front = np.full(44, -np.inf)
np.maximum.at(front, xb[lipbox & (tp == 0)], point[..., 2][lipbox & (tp == 0)])
ok = np.isfinite(front)
front = np.interp(np.arange(44), np.nonzero(ok)[0], front[ok])
front = ndimage.maximum_filter1d(front, 3)
depth = front[xb] - point[..., 2]
interior = cov & np.isin(tp, [8, 9, 11])
ny, nz = fn[t, 1], fn[t, 2]
inward = lipbox & (tp == 0) & (ny * (point[..., 1] - MOUTH_LINE_Y) < 0) & (np.abs(ny) > 0.3) & (nz < 0.5) & \
    (depth > 0.0005)
# lips curve back toward the corners; the gap reaches further left (x -0.026) than right (x 0.010)
corner_fade = np.minimum(np.clip((0.010 - point[..., 0]) / 0.005, 0, 1), np.clip((point[..., 0] + 0.026) / 0.005, 0, 1))
w_mouth = np.where(inward, np.clip((0.5 - nz) / 0.25, 0, 1) * np.clip((np.abs(ny) - 0.3) / 0.2, 0, 1) * corner_fade, 0.0)
w_mouth = np.maximum(w_mouth, interior.astype(np.float64))
# any lip surface well behind the front (the posed mouth opens a little and shows more of the inner lips)
near_line = np.abs(point[..., 1] - MOUTH_LINE_Y) < 0.002
w_mouth = np.maximum(w_mouth, np.where(lipbox & (tp == 0) & near_line, np.clip((depth - 0.002) / 0.001, 0, 1) * corner_fade,
                                       0.0))
w_mouth = np.maximum(np.clip(ndimage.gaussian_filter(w_mouth, 1.5) * 1.3, 0, 1) * lipbox, interior.astype(np.float64))
depth_t = np.clip((depth - 0.0008) / 0.007, 0, 1)
dark = np.array([104, 50, 47.0])[None, None] * (1 - depth_t[..., None]) + np.array([26, 12, 12.0])[None, None] * depth_t[..., None]
base = base * (1 - w_mouth[..., None]) + dark * w_mouth[..., None]
inward_w = w_mouth * (tp == 0)
report['mouth'] = {'interior_texels': int(interior.sum()), 'inward_lip_texels': int((inward_w > 0.5).sum()),
                   'lip_front_z': round(lip_front_z, 4)}

# ---- 3. strap, studs, cords, grommets
hue, sat, val = hsv(base)
leather_px = cov & (tp == 0) & ~hf[t] & (hue > 12) & (hue < 50) & (sat > 0.42) & (val < 0.5)
stud_c = centre[piece == 33].mean(0)
near_leather = leather_px & (np.linalg.norm(point - stud_c, axis=-1) < 0.04)
leather_col = np.median(base[near_leather], 0)
# back-facing faces seen from the front through holes at the strap tops (both straps; front z-buffer winners)
hole_faces = set()
for sx in (-1, 1):
    win = (np.abs(centre[:, 0] - sx * abs(stud_c[0])) < 0.05) & (np.abs(centre[:, 1] - stud_c[1]) < 0.05)
    cand = np.nonzero(win & (piece != 1))[0]
    grid = np.linspace(-0.025, 0.025, 101)
    gx, gy = np.meshgrid(sx * abs(stud_c[0]) + grid, stud_c[1] + grid)
    pts = np.stack([gx.ravel(), gy.ravel()], 1)
    best = np.full(len(pts), -np.inf)
    owner = np.full(len(pts), -1)
    for f in cand:
        p2 = xyz[f, :, :2]
        M = np.array([p2[1] - p2[0], p2[2] - p2[0]]).T
        if abs(np.linalg.det(M)) < 1e-12:
            continue
        st = np.linalg.solve(M, (pts - p2[0]).T)
        b = np.stack([1 - st[0] - st[1], st[0], st[1]], 1)
        ok = (b >= 0).all(1)
        z = b[ok] @ xyz[f, :, 2]
        idx = np.nonzero(ok)[0]
        better = z > best[idx]
        best[idx[better]] = z[better]
        owner[idx[better]] = f
    for f in set(owner[owner >= 0].tolist()):
        if fn[f, 2] < -0.3 and piece[f] == 0 and centre[f, 2] < 0:
            hole_faces.add(f)
# with the pose the hole shows other back faces too: every back-side skin face near either strap top that the hair
# hides from behind (hair shell farther back at the same x, y) takes leather; it is never seen from behind
flip = xyz.copy()
flip[..., 2] *= -1
for sx in (-1, 1):
    near_top = (piece == 0) & (np.abs(centre[:, 0] - sx * abs(stud_c[0])) < 0.05) & \
        (np.abs(centre[:, 1] - stud_c[1]) < 0.05) & (centre[:, 2] < 0) & (fn[:, 2] < -0.3)
    idx = np.nonzero(near_top)[0]
    if len(idx):
        hair_back = -eyes_geom.skin_depth(flip, piece == 1, flip[idx].mean(1))     # nearest hair z seen from behind
        hole_faces |= set(idx[hair_back < centre[idx, 2] - 0.002].tolist())
flap_faces = {8944} | hole_faces
flap = cov & np.isin(t, sorted(flap_faces)) & (tp == 0)
shade = np.clip(lum / max(float(np.median(lum[flap])) if flap.any() else 1, 1), 0.8, 1.2)
base[flap] = leather_col * shade[flap][:, None]
studs = cov & np.isin(tp, [15, 17])
brass = np.median(base[studs], 0)
stud33 = cov & (tp == 33)
base[stud33] = brass * np.clip(lum[stud33] / max(float(np.median(lum[stud33])), 1), 0.6, 1.2)[:, None]
# the top lacing strip (piece 6, a thin band in front of the cleavage, painted skin with a dark outline that reads as
# a lace stroke above the lacing) takes the colour of the skin directly behind it, after the stray refill below
top_strip = cov & (tp == 6)
leg_small = cov & (tp >= 21) & (tp <= 48) & (point[..., 1] < 0.95)
grommet_col = np.median(base[leg_small & ~skinlike(base)], 0)
grommet_skin = leg_small & skinlike(base)
base[grommet_skin] = grommet_col * np.clip(lum[grommet_skin] / max(float(np.median(lum[grommet_skin])), 1), 0.7,
                                           1.25)[:, None]
classes[flap] = 8
classes[stud33 | grommet_skin] = 9
report['strap'] = {'hole_faces': sorted(int(f) for f in hole_faces), 'flap_texels': int(flap.sum()),
                   'leather_srgb': np.round(leather_col).astype(int).tolist(), 'stud_texels': int(stud33.sum()),
                   'brass_srgb': np.round(brass).astype(int).tolist(), 'grommet_skin_texels': int(grommet_skin.sum()),
                   'grommet_srgb': np.round(grommet_col).astype(int).tolist()}

# ---- 4. stray paint on bare skin
hue, sat, val = hsv(base)
foreign = ((hue > 12) & (hue < 50) & (sat > 0.42) & (val < 0.55)) | \
    (((hue < 18) | (hue > 340)) & (sat > 0.45) & (val > 0.3)) | \
    ((base[..., 1] > base[..., 0] + 8) & (base[..., 1] > base[..., 2]))
zone = cov & (tp == 0) & ~hf[t] & (point[..., 1] > 0.98) & (mask_s[..., :2].max(-1) < 0.3) & ~flap
x, y, z = point[..., 0], point[..., 1], point[..., 2]
side_lacing = (np.abs(x) > 0.10) & (y < 1.12)
front_lacing = (np.abs(x) < 0.05) & (y < 1.335) & (z > 0.09)
ys, xs = np.nonzero(zone)
P, F = point[ys, xs], foreign[ys, xs]
rng = np.random.default_rng(0)
pick = rng.choice(len(P), min(len(P), 400000), replace=False)
tree = cKDTree(P[pick])
cand = np.nonzero(F)[0]
frac = np.array([F[pick][n].mean() if len(n) else 1.0 for n in tree.query_ball_point(P[cand], 0.015, workers=-1)])
stray = np.zeros((S, S), bool)
stray[ys[cand[frac < 0.3]], xs[cand[frac < 0.3]]] = True
stray &= ~side_lacing & ~front_lacing
stray = ndimage.binary_dilation(stray, iterations=2) & zone & ~side_lacing & ~front_lacing
skin_ok = zone & skinlike(base) & ~stray
fill = island_blur(base, 8.0, skin_ok)
lab, n = ndimage.label(stray, structure=np.ones((3, 3)))
base[stray] = fill[stray]
behind_faces = np.nonzero((piece == 0) & ~hf & (np.abs(centre[:, 0]) < 0.06) & (np.abs(centre[:, 1] - 1.336) < 0.03))[0]
bt = cKDTree(centre[behind_faces])
sp = point[top_strip]
_, near = bt.query(sp, k=8)
cand_f = behind_faces[near]
import types  # noqa: E402
sys.modules.setdefault('pymeshlab', types.ModuleType('pymeshlab'))
sys.path.insert(0, str(HERE.parent / 'lod_repair_claude' / 'scripts'))
import transfer_textures as TT  # noqa: E402
dd, ww = TT.closest_on_triangles(sp, xyz[cand_f, 0], xyz[cand_f, 1], xyz[cand_f, 2])
best = np.argmin(dd, 1)
rows = np.arange(len(sp))
behind_uv = (uv[cand_f[rows, best]] * ww[rows, best][:, :, None]).sum(1)
classes[top_strip] = 1
# cleavage above the top strip: skin darker than its surroundings there is what is left of the stroke
box = cov & (tp == 0) & ~hf[t] & (np.abs(point[..., 0]) < 0.045) & (point[..., 1] > 1.338) & (point[..., 1] < 1.365) \
    & (point[..., 2] > 0.09) & ~flap
lum2 = base @ np.array([0.2126, 0.7152, 0.0722])
ref_l = float(np.median(lum2[box]))
h2, s2, _ = hsv(base)
smudge = box & (lum2 < 0.86 * ref_l) & (s2 < 0.42)
smudge = ndimage.binary_dilation(smudge, iterations=2) & box
fill2 = island_blur(base, 10.0, box & ~smudge)
base[smudge] = fill2[smudge]
behind = texlib.bilinear(base, behind_uv)
skin_tone = np.median(base[box & ~smudge], 0)
bl = behind @ np.array([0.2126, 0.7152, 0.0722])
base[top_strip] = skin_tone * np.clip((bl / max(float(skin_tone @ np.array([0.2126, 0.7152, 0.0722])), 1)) ** 0.5,
                                      0.9, 1.05)[:, None]
report['cleavage_smudge_texels'] = int(smudge.sum())
report['top_strip'] = {'texels': int(top_strip.sum()), 'behind_distance_mm_p95': round(float(np.percentile(dd[rows, best], 95)) * 1000, 2)}
report['stray'] = {'texels': int(stray.sum()), 'components': int(n),
                   'centres': [np.round(point[lab == i + 1].mean(0), 3).tolist() for i in range(n)
                               if (lab == i + 1).sum() > 30]}

# ---- 1. eyes (r3, after ../mm7_m342_texpass_claude face_geom.py / uv_eyes.py / face_paint.py): each eyeball is
# re-charted as ONE disc (azimuthal projection around its forward axis, linear to KNEE rad, the hidden back compressed
# by TAIL) in the largest free circle of the atlas, and painted entirely from geometry
eye_faces = np.isin(piece, [4, 5])
skin_head = (piece == 0) & hf
geo = eyes_geom.geometry(xyz, piece, skin_head)
keep_tid, _ = texlib.raster(uv[~eye_faces], S)
taken = ndimage.binary_dilation(keep_tid >= 0, iterations=MARGIN)
taken[:MARGIN + 1] = taken[-MARGIN - 1:] = True
taken[:, :MARGIN + 1] = taken[:, -MARGIN - 1:] = True
eyes = {}
for k, e in geo.items():
    c, R = e['centre'], e['radius']
    _, _, pts, vis = e['samples']
    vp = pts[vis]
    width = np.percentile(vp[:, 0], 98) - np.percentile(vp[:, 0], 2)
    d = vp - c
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    axis = d.mean(0)
    axis /= np.linalg.norm(axis)                                    # centre of the visible eye (lid opening)
    up0 = np.array([0, 1.0, 0]) - axis * axis[1]
    up0 /= np.linalg.norm(up0)
    axis = axis * np.cos(np.radians(GAZE_UP_DEG)) + up0 * np.sin(np.radians(GAZE_UP_DEG))   # iris tucks under the upper lid
    e1 = np.cross([0.0, 1.0, 0.0], axis)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(axis, e1)
    iris_deg = float(np.degrees(np.arcsin(min(IRIS_SHARE * width / 2 / R, 0.95))))
    eyes[k] = dict(c=c, R=R, axis=axis, e1=e1, e2=e2, iris_deg=iris_deg, width=width,
                   open_deg=float(np.percentile(np.degrees(np.arccos(np.clip(d @ axis, -1, 1))), 95)))
uv_final = uv.copy()


def radial(theta, e):
    """Disc radius (rad units) of the angle from the axis: full density to IRIS_KNEE iris radii, SCLERA_SLOPE over the
    sclera to OPEN_KNEE rad, TAIL over the hidden back."""
    k1 = np.radians(e['iris_deg']) * IRIS_KNEE
    r1 = np.minimum(theta, k1)
    r2 = np.clip(theta - k1, 0, OPEN_KNEE - k1) * SCLERA_SLOPE
    r3 = np.maximum(theta - OPEN_KNEE, 0) * TAIL
    return r1 + r2 + r3


disc = {}
for k, e in eyes.items():
    f = np.nonzero(piece == k)[0]
    pf = xyz[f]
    a3 = np.linalg.norm(np.cross(pf[:, 1] - pf[:, 0], pf[:, 2] - pf[:, 0]), axis=1).sum() / 2
    u = uv[f] * S
    a2 = np.abs((u[:, 1, 0] - u[:, 0, 0]) * (u[:, 2, 1] - u[:, 0, 1]) - (u[:, 2, 0] - u[:, 0, 0]) * (u[:, 1, 1] - u[:, 0, 1])).sum() / 2
    dd = pf - e['c']
    dd /= np.linalg.norm(dd, axis=-1, keepdims=True)
    theta = np.arccos(np.clip(dd @ e['axis'], -1, 1))
    phi = np.arctan2(dd @ e['e2'], dd @ e['e1'])
    rr = radial(theta, e)
    disc[k] = dict(f=f, old_density=np.sqrt(a2 / a3), rr=rr, phi=phi, theta=theta, unit=float(rr.max()) * np.sqrt(a2 / a3) * e['R'])
# two largest free circles, then one common density factor for both eyes
free = taken.copy()
circles = []
for k in eyes:
    dist = ndimage.distance_transform_edt(~free)
    cy, cx = np.unravel_index(np.argmax(dist), dist.shape)
    rad = float(dist[cy, cx])
    circles.append((cx, cy, rad))
    yy, xx = np.ogrid[:S, :S]
    free |= (yy - cy) ** 2 + (xx - cx) ** 2 <= (rad + MARGIN) ** 2
factor = min(EYE_SCALE_MAX, min((c[2] - 2) / disc[k]['unit'] for c, k in zip(circles, eyes)))
for (cx, cy, rad), (k, e) in zip(circles, eyes.items()):
    q = disc[k]
    scale = factor * q['old_density'] * e['R']
    local = np.stack([q['rr'] * np.cos(q['phi']), -q['rr'] * np.sin(q['phi'])], -1) * scale   # glTF v down: up is -v
    f = q['f']
    uv_final[f] = (local + [cx + 0.5, cy + 0.5]) / S
    pf = xyz[f]
    new = uv_final[f] * S
    a2n = np.abs((new[:, 1, 0] - new[:, 0, 0]) * (new[:, 2, 1] - new[:, 0, 1]) - (new[:, 2, 0] - new[:, 0, 0]) * (new[:, 1, 1] - new[:, 0, 1])) / 2
    a3f = np.linalg.norm(np.cross(pf[:, 1] - pf[:, 0], pf[:, 2] - pf[:, 0]), axis=1) / 2
    iris_f = q['theta'].mean(1) < np.radians(e['iris_deg'])
    vis_f = q['theta'].mean(1) < np.radians(e['open_deg'])
    report[f'eye_{k}'] = {'centre': np.round(e['c'], 4).tolist(), 'radius_mm': round(e['R'] * 1000, 2),
                          'axis': np.round(e['axis'], 3).tolist(), 'visible_width_mm': round(e['width'] * 1000, 1),
                          'iris_deg': round(e['iris_deg'], 1), 'disc_factor': round(factor, 2),
                          'disc_centre_px': [int(cx), int(cy)], 'disc_radius_px': round(rad, 1),
                          'old_px_per_cm': round(float(q['old_density'] / 100), 1),
                          'iris_px_per_cm': round(float(np.sqrt(a2n[iris_f].sum() / a3f[iris_f].sum()) / 100), 1),
                          'visible_px_per_cm': round(float(np.sqrt(a2n[vis_f].sum() / a3f[vis_f].sum()) / 100), 1)}
np.savez(HERE / 'work' / 'uv_final.npz', uv=uv_final, tri=layout['tri'], xyz=xyz)


def smooth(e0, e1, x):
    q = np.clip((x - e0) / (e1 - e0), 0, 1)
    return q * q * (3 - 2 * q)


near_eyes = skin_head & (np.linalg.norm(centre - centre[eye_faces].mean(0), axis=1) < 0.06)
rng = np.random.default_rng(7)
ecov = np.zeros((S, S), bool)
for k, e in eyes.items():
    f = np.nonzero(piece == k)[0]
    tid_e, b_e = texlib.raster(uv_final[f], S, grow=1.5)            # border texels padded: bilinear never leaves the eye
    sel = tid_e >= 0
    pt = (xyz[f][tid_e[sel]] * b_e[sel][..., None]).sum(1)
    d = pt - e['c']
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    th = np.degrees(np.arccos(np.clip(d @ e['axis'], -1, 1)))
    ps = np.arctan2(d @ e['e2'], d @ e['e1'])
    ti = th / e['iris_deg']
    fib = np.zeros_like(ps)
    for freq, amp in ((23, 0.5), (41, 0.35), (67, 0.25), (97, 0.15)):
        phase = rng.uniform(0, 2 * np.pi)
        fib += amp * np.sin(freq * ps + phase + 3.0 * np.sin(5 * ps + phase) * ti)
    fib /= 1.25
    iris = IRIS + (IRIS_DARK - IRIS) * smooth(0.55, 0.95, ti)[:, None]
    iris = iris + (COLLARETTE - iris) * (smooth(PUPIL_SHARE, PUPIL_SHARE + 0.1, ti) * (1 - smooth(0.5, 0.64, ti)) * 0.7)[:, None]
    iris = iris * (1 + 0.16 * fib)[:, None]
    iris = iris + (LIMBUS - iris) * smooth(0.84, 0.98, ti)[:, None]
    # sclera: off-white, darker toward the corners and the hidden back
    sclera = SCLERA + (SCLERA_EDGE - SCLERA) * smooth(e['iris_deg'] + 2, e['open_deg'] + 2, th)[:, None]
    edge = 0.8
    w_iris = 1 - smooth(e['iris_deg'] - edge, e['iris_deg'] + edge, th)
    col = sclera * (1 - w_iris[:, None]) + iris * w_iris[:, None]
    w_pupil = 1 - smooth(e['iris_deg'] * PUPIL_SHARE - edge, e['iris_deg'] * PUPIL_SHARE + edge, th)
    col = col * (1 - w_pupil[:, None]) + PUPIL * w_pupil[:, None]
    # small soft highlight, up and to the viewer's right, fixed on the eye
    hl = e['c'] + e['R'] * (e['axis'] * np.cos(np.radians(8)) + (e['e2'] * 0.75 + e['e1'] * 0.66) * np.sin(np.radians(8)))
    hd = np.linalg.norm(pt - hl, axis=1) / e['R']
    col = col + (255 - col) * (0.5 * np.exp(-0.5 * (hd / 0.045) ** 2))[:, None]
    # lid shade: soft, from the distance along the eyeball to the lid line (where the eyeball passes behind the face
    # skin; the skin plunges steeply there, so depth in front of it does not soften the jagged line); a wider band
    # under the upper lid. Hidden texels are fully shaded.
    _, _, spts, svis = geo[k]['samples']
    d_lid = cKDTree(spts[~svis]).query(pt)[0]
    hidden = (pt[:, 2] - eyes_geom.skin_depth(xyz, near_eyes, pt)) < 0
    d_lid[hidden] = 0
    upper = smooth(-0.15, 0.25, d @ e['e2'])
    reach = LID_SHADE_LOWER + (LID_SHADE_UPPER - LID_SHADE_LOWER) * upper
    shade = 0.55 + 0.45 * smooth(0.0, 1.0, d_lid / reach)
    col *= shade[:, None]
    yy, xx = np.nonzero(sel)
    base[yy, xx] = col
    normal[yy, xx] = (128, 128, 255)
    classes[yy, xx] = 6
    ecov |= sel
    vis_t = ~hidden
    report[f'eye_{k}'].update({'d_lid_mm_p10_50_90_visible': np.round(np.percentile(d_lid[vis_t], [10, 50, 90]) * 1000, 2).tolist(),
                               'shade_p10_50_90_visible': np.round(np.percentile(shade[vis_t], [10, 50, 90]), 2).tolist(),
                               'hidden_share': round(float(hidden.mean()), 3),
                               'texels': int(sel.sum()), 'pupil_deg': round(e['iris_deg'] * PUPIL_SHARE, 1),
                               'iris_srgb_mid': np.round(np.median(col[(ti > 0.45) & (ti < 0.75) & (shade > 0.95)], 0)).astype(int).tolist()})

# lid margins: skin within LID_IN..LID_OUT of an eyeball's surface takes a shadow on the upper margin and a pinkish
# waterline tone on the lower one, fading into the lid paint, so the eye's outline follows this smooth distance
# contour rather than the jagged line where the eyeball passes through the skin.
lid_w = np.zeros((S, S))
lid_up = np.zeros((S, S))
near_eye = np.zeros((S, S), bool)
for k, e in eyes.items():
    dd = point - e['c']
    dist = np.linalg.norm(dd, axis=-1) - e['R']
    dirn = dd / np.maximum(np.linalg.norm(dd, axis=-1, keepdims=True), 1e-9)
    near_open = np.degrees(np.arccos(np.clip(dirn @ e['axis'], -1, 1))) < e['open_deg'] + 12
    w = np.where(cov & (tp == 0) & hf[t] & near_open, 1 - smooth(LID_IN, LID_OUT, dist), 0.0)
    near_eye |= cov & (tp == 0) & hf[t] & (dist < 0.005)
    up = (dirn @ e['e2']) > 0
    lid_up = np.where(w > lid_w, up, lid_up)
    lid_w = np.maximum(lid_w, w)
# the head paint put sclera and iris colour on the lid skin round the eyeballs (it painted a bigger eye than the
# geometric opening): those texels are refilled from the surrounding lid skin of the same chart first
bmx, bmn = base.max(-1), base.min(-1)
bsat = (bmx - bmn) / np.maximum(bmx, 1)
b_skin = (base[..., 0] >= base[..., 1]) & (base[..., 1] >= 0.88 * base[..., 2]) & (bsat > 0.1) & (bsat < 0.5)
eyeish = near_eye & ~b_skin & ((base @ np.array([0.2126, 0.7152, 0.0722])) > 90)          # not skin, not lash-dark
eyeish = ndimage.binary_dilation(eyeish, iterations=1) & near_eye
fill = island_blur(base, 5.0, near_eye & ~eyeish)
base[eyeish] = fill[eyeish]
lid_col = np.where(lid_up[..., None] > 0, LID_SHADOW[None, None], LOWER_MARGIN[None, None])
strength = np.where(lid_up > 0, 0.85, 0.6) * lid_w
base = base * (1 - strength[..., None]) + lid_col * strength[..., None]
report['lid_eye_paint_refilled'] = int(eyeish.sum())
report['lid_margin_texels'] = int((lid_w > 0.5).sum())
eye_small_faces = eye_faces

# ---- gutters on the final layout, maps written
final_tid, _ = texlib.raster(uv_final, S)
fcov = final_tid >= 0
base = texlib.pad(base, fcov)
normal = texlib.pad(normal, fcov)
Image.fromarray(np.clip(base + 0.5, 0, 255).astype(np.uint8)).save(f'{out}_basecolor.png')
Image.fromarray(np.clip(normal + 0.5, 0, 255).astype(np.uint8)).save(f'{out}_normal.png')
Image.fromarray(texlib.pad(classes, fcov)).save(f'{out}_material_classes.png')
small_tid, _ = texlib.raster(uv_final, SMALL)
scov = small_tid >= 0
eye_small = np.zeros((SMALL, SMALL), bool)
eye_small[scov] = eye_small_faces[small_tid[scov]]
mr[eye_small] = (0.45 * 255, 0.3 * 255, 0)
mouth_small = np.asarray(Image.fromarray((np.clip(w_mouth, 0, 1) * 255).astype(np.uint8)).resize((SMALL, SMALL), Image.BOX),
                         np.float64) / 255
mr[..., 0] *= 1 - np.clip(mouth_small * 2, 0, 1) * ~eye_small                     # no specular sheen in the mouth
mr[..., 1] = np.where(eye_small, mr[..., 1], np.maximum(mr[..., 1], 255 * np.clip(mouth_small * 2, 0, 1)))
mask[eye_small] = 0
Image.fromarray(np.clip(texlib.pad(mr, scov) + 0.5, 0, 255).astype(np.uint8)).save(f'{out}_metal_rough.png')
Image.merge('RGBA', [Image.fromarray(np.clip(texlib.pad(mask[..., ch], scov) + 0.5, 0, 255).astype(np.uint8), 'L')
                     for ch in range(4)]).save(f'{out}_region_mask.png', optimize=True)
json.dump(report, open(f'{out}_closeup_report.json', 'w'), indent=1)
print('CLOSEUP', json.dumps(report))
