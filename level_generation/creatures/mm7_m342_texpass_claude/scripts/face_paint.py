"""Close-up fixes (user review 2026-11-01): procedural eyes, lid margins, lips, mouth and nostrils, painted over the
composed maps (compose.py, layout work/uv_cc4_fine.npz) onto the eye layout work/uv_eyes.npz (uv_eyes.py: one disc
chart per eyeball in free atlas space; every other chart unchanged).

- Eyeballs (pieces 22, 30): colour from the angle to the eye's forward axis (face_geom.eyes: pupil centred in the lid
  opening) and the azimuth around it, so every triangle agrees and the paint is sharp at any density: off-white sclera
  darkening toward the back, a blue-grey iris (references_head) with a warm collarette, radial fibres and a darker
  limbal ring, a round black pupil, a small soft highlight. Flat normal; wet specular.
- Lash cards (20, 31 upper; 21, 32 lower): the dark lash line and the lower lid's shadow, one colour each with a
  little luminance grain; matte.
- Skin shell within LID_IN of the eyeball surface (the lid margins hugging the eye, where pale and orange paint
  showed as shards): lid shadow (lighter on the lower margin), fading out by LID_OUT.
- Mouth: the visible lips are the skin shell, closed over the mouth with the gap as a crease. The lip pieces (23
  lower, 24 upper) and the mouth interior (25) show only inside the gap: all of them take a dark gradient by depth,
  and so do the shell's crease texels (smooth normal turned away from the front, near the mouth line); the outer lip
  paint stays. They lose the eyes' gloss, and the shell's lips get a matte lip material (their faceted upper faces
  glinted white).
- Nostrils: shell texels within NOSE_R of the nostril centre take their luminance from a 3D Gaussian (NOSE_SIGMA) of
  the surrounding luminance, floored at NOSE_FLOOR of the skin's; the down-facing underside (the paint there was
  already light: its hard dark wedge is shading) is lifted by up to NOSE_LIFT so it shades like its neighbours; the
  normal map's tilt there is reduced.
- Hidden legs: white stockings (the installed linen white); they had come out dress green in every tier.

Usage: face_paint.py <in prefix> <out prefix>   (e.g. textures/m342_tp textures/m342_tp2)
Writes <out>_{basecolor,normal,metal_rough,region_mask,material_classes}.png and <out>_face_report.json."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import face_geom  # noqa: E402
import texels  # noqa: E402
import texlib  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
src, dst = sys.argv[1], sys.argv[2]
S, N = 2048, 1024
LUMA = np.array([0.2126, 0.7152, 0.0722])
IRIS_DEG, PUPIL_DEG, EDGE_DEG = 22.0, 7.5, 0.8
SCLERA, SCLERA_BACK = np.array([229, 223, 216.0]), np.array([150, 122, 116.0])
IRIS, IRIS_DARK, COLLARETTE = np.array([112, 126, 140.0]), np.array([62, 70, 82.0]), np.array([128, 108, 82.0])
LIMBUS, PUPIL = np.array([46, 50, 58.0]), np.array([8, 8, 10.0])
LASH, LOWER_LID, LID_SHADOW = np.array([30, 22, 19.0]), np.array([138, 92, 77.0]), np.array([66, 46, 39.0])
LOWER_MARGIN = np.array([128, 86, 72.0])
LID_IN, LID_OUT = 0.0008, 0.0025
MOUTH_FRONT, MOUTH_BACK = np.array([86, 34, 34.0]), np.array([20, 8, 8.0])
MOUTH_X, MOUTH_Y = -0.008, 1.535
STOCKING = np.array([215, 214, 227.0])                   # the installed linen white
NOSE_R, NOSE_SIGMA, NOSE_FLOOR, NOSE_LIFT = 0.016, 0.0025, 0.8, 0.35
report = {}

T = texels.load()
cov, pos, piece, tri_id, bary = T['cov'], T['pos'], T['piece'], T['tri_id'], T['bary']
before = np.load(HERE / 'work' / 'lod0_before.npz')
eye_lay = np.load(HERE / 'work' / 'uv_eyes.npz')
base = np.asarray(Image.open(f'{src}_basecolor.png').convert('RGB'), np.float32)
normal = np.asarray(Image.open(f'{src}_normal.png').convert('RGB'), np.float32) / 127.5 - 1
mr = np.asarray(Image.open(f'{src}_metal_rough.png').convert('RGB'), np.float32) / 255
mask = np.asarray(Image.open(f'{src}_region_mask.png').convert('RGBA'), np.float32) / 255
classes = np.asarray(Image.open(f'{src}_material_classes.png'), np.uint8).copy()
skin_l = float(np.array([213, 149, 121.0]) @ LUMA)
eyes = face_geom.eyes(samples=20000)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def texel_normals(sel):
    """Smooth (vertex-interpolated) rest normals of the texels in sel."""
    t = tri_id[sel]
    n = (before['nrm'][before['tri'][t]] * bary[sel][..., None]).sum(1)
    return n / np.linalg.norm(n, axis=1, keepdims=True)


# ---- 1. eyeballs on their new disc charts
spec_paint = np.zeros((S, S), np.float32) - 1      # per-texel specular / roughness overrides (2048, then box to 1024)
rough_paint = np.zeros((S, S), np.float32) - 1
grain_rng = np.random.default_rng(7)
eye_cov = np.zeros((S, S), bool)
for k, e in eyes.items():
    f = np.nonzero(before['piece'] == k)[0]
    tid, b = texlib.raster(eye_lay['uv'][f], S, grow=1.5)
    sel = tid >= 0
    p = (eye_lay['xyz'][f][tid[sel]] * b[sel][..., None]).sum(1)
    d = p - e['centre']
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    axis = e['axis']
    e1 = np.cross([0.0, 1.0, 0.0], axis)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(axis, e1)
    th = np.degrees(np.arccos(np.clip(d @ axis, -1, 1)))
    ps = np.arctan2(d @ e2, d @ e1)
    t = th / IRIS_DEG
    # iris: blue-grey, darker toward the rim, warm collarette round the pupil, radial fibres
    fib = np.zeros_like(ps)
    for freq, amp in ((23, 0.5), (41, 0.35), (67, 0.25), (97, 0.15)):
        phase = grain_rng.uniform(0, 2 * np.pi)
        fib += amp * np.sin(freq * ps + phase + 3.0 * np.sin(5 * ps + phase) * t)
    fib /= 1.25
    iris = IRIS + (IRIS_DARK - IRIS) * smooth(0.55, 0.95, t)[:, None]
    iris = iris + (COLLARETTE - iris) * (smooth(0.30, 0.40, t) * (1 - smooth(0.48, 0.62, t)) * 0.75)[:, None]
    iris = iris * (1 + 0.16 * fib)[:, None]
    iris = iris + (LIMBUS - iris) * smooth(0.84, 0.98, t)[:, None]
    sclera = SCLERA + (SCLERA_BACK - SCLERA) * smooth(IRIS_DEG + 4, 48, th)[:, None]
    w_iris = 1 - smooth(IRIS_DEG - EDGE_DEG, IRIS_DEG + EDGE_DEG, th)
    col = sclera * (1 - w_iris[:, None]) + iris * w_iris[:, None]
    w_pupil = 1 - smooth(PUPIL_DEG - EDGE_DEG, PUPIL_DEG + EDGE_DEG, th)
    col = col * (1 - w_pupil[:, None]) + PUPIL * w_pupil[:, None]
    # small soft highlight up and toward the nose-side light (fixed on the eye)
    hl = e['centre'] + e['radius'] * (axis * np.cos(np.radians(9)) + (e2 * 0.75 - e1 * 0.66) * np.sin(np.radians(9)))
    hd = np.linalg.norm(p - hl, axis=1) / e['radius']
    col = col + (255 - col) * (0.55 * np.exp(-0.5 * (hd / 0.045) ** 2))[:, None]
    yy, xx = np.nonzero(sel)
    base[yy, xx] = col
    normal[yy, xx] = (0, 0, 1)
    spec_paint[yy, xx], rough_paint[yy, xx] = 0.45, 0.3
    mask[..., :][(yy // 2, xx // 2)] = 0
    classes[(yy // 2, xx // 2)] = 6
    eye_cov |= sel
    report[face_geom.EYES[k]] = {'axis': axis.round(4).tolist(), 'radius_mm': round(e['radius'] * 1e3, 2),
                                 'texels': int(sel.sum()), 'iris_deg': IRIS_DEG, 'pupil_deg': PUPIL_DEG}

# ---- 2. lash cards, lid margins
for kk, colour in ((20, LASH), (31, LASH), (21, LOWER_LID), (32, LOWER_LID)):
    sel = cov & (piece == kk)
    grain = (base[sel] @ LUMA) / max(float(np.median(base[sel] @ LUMA)), 1)
    base[sel] = colour * np.clip(grain, 0.85, 1.15)[:, None] ** 0.5
    normal[sel] = (0, 0, 1)
    spec_paint[sel], rough_paint[sel] = 0.15, 0.85
lid_w = np.zeros((S, S), np.float32)
for k, e in eyes.items():
    dist = np.linalg.norm(np.nan_to_num(pos) - e['centre'], axis=-1) - e['radius']
    lid_w = np.maximum(lid_w, np.where(cov & (piece == 1), 1 - smooth(LID_IN, LID_OUT, dist), 0))
sel = lid_w > 0
eye_y = np.mean([e['centre'][1] for e in eyes.values()])
upper = smooth(-0.002, 0.002, pos[sel][:, 1] - eye_y)[:, None]        # the lower margin takes a lighter shadow
shadow = LOWER_MARGIN + (LID_SHADOW - LOWER_MARGIN) * upper
base[sel] = base[sel] * (1 - lid_w[sel, None]) + shadow * lid_w[sel, None]
report['lid_margin_texels'] = int((lid_w > 0.5).sum())

# ---- 3. lips and mouth
for kk in (23, 24, 25):
    sel = cov & (piece == kk)
    n = texel_normals(sel)
    z = pos[sel][:, 2]
    depth = smooth(0.0, 1.0, (0.109 - z) / 0.012)
    dark = MOUTH_FRONT + (MOUTH_BACK - MOUTH_FRONT) * depth[:, None]
    w = np.ones(len(z))                       # the visible lips are the skin shell; these pieces show only in the gap
    base[sel] = base[sel] * (1 - w[:, None]) + dark * w[:, None]
    normal[sel] = (0, 0, 1)
    spec_paint[sel] = np.where(w > 0.5, 0.05, 0.3)
    rough_paint[sel] = np.where(w > 0.5, 0.95, 0.62)
    classes[tuple(np.array(np.nonzero(sel)) // 2)] = 1
    report[f'mouth_piece_{kk}_dark_share'] = round(float((w > 0.5).mean()), 3)

# the lip crease on the skin shell (closed over the mouth: the gap is a fold): texels near the mouth line whose smooth
# normal turns away from the front take the same dark gradient
sel = cov & (piece == 1) & (np.abs(np.nan_to_num(pos[..., 0]) - MOUTH_X) < 0.028) & \
    (pos[..., 1] > MOUTH_Y - 0.010) & (pos[..., 1] < MOUTH_Y + 0.010) & (pos[..., 2] > 0.095)
n = texel_normals(sel)
z = pos[sel][:, 2]
w = 1 - smooth(0.05, 0.45, n[:, 2])
w *= 1 - smooth(0.006, 0.010, np.abs(pos[sel][:, 1] - MOUTH_Y))
dark = MOUTH_FRONT + (MOUTH_BACK - MOUTH_FRONT) * smooth(0.0, 1.0, (0.112 - z) / 0.012)[:, None]
base[sel] = base[sel] * (1 - w[:, None]) + dark * w[:, None]
crease = np.zeros((S, S), np.float32)
crease[sel] = w
spec_paint = np.where(crease > 0.3, 0.05, spec_paint)
rough_paint = np.where(crease > 0.3, 0.95, rough_paint)
report['lip_crease_texels'] = int((w > 0.5).sum())
# the shell's lips: faceted, and the upper faces caught the light as pale glints with skin gloss; matte lip material
lips = cov & (piece == 1) & (np.abs(np.nan_to_num(pos[..., 0]) - MOUTH_X) < 0.03) & \
    (np.abs(np.nan_to_num(pos[..., 1]) - MOUTH_Y) < 0.014) & (pos[..., 2] > 0.095)
hsv = np.asarray(Image.fromarray(np.clip(base + 0.5, 0, 255).astype(np.uint8)).convert('HSV'), np.float32)
lips &= ((hsv[..., 0] < 11) | (hsv[..., 0] > 240)) & (hsv[..., 1] > 75)
spec_paint = np.where(lips & (crease <= 0.3), 0.12, spec_paint)
rough_paint = np.where(lips & (crease <= 0.3), 0.7, rough_paint)
report['shell_lip_texels'] = int(lips.sum())

# ---- 4. nostrils: smooth luminance in 3D
shell = cov & (piece == 1)
cand = shell & (np.abs(np.nan_to_num(pos[..., 0]) + 0.008) < 0.03) & (pos[..., 1] > 1.54) & (pos[..., 1] < 1.60)
tip = pos[cand][np.argmax(pos[cand][:, 2])]
nost = tip + np.array([0.0, -0.006, -0.006])                     # below and behind the tip, between the nostrils
dist = np.linalg.norm(np.nan_to_num(pos) - nost, axis=-1)
region = shell & (dist < NOSE_R)
yy, xx = np.nonzero(region)
pts = pos[yy, xx]
lum = base[yy, xx] @ LUMA
tree = cKDTree(pts)
smooth_l = np.empty_like(lum)
for i, nb in enumerate(tree.query_ball_point(pts, 3 * NOSE_SIGMA)):
    g = np.exp(-0.5 * ((pts[nb] - pts[i]) ** 2).sum(1) / NOSE_SIGMA ** 2)
    smooth_l[i] = (g * lum[nb]).sum() / g.sum()
smooth_l = np.maximum(smooth_l, NOSE_FLOOR * skin_l)
w = 1 - smooth(0.6 * NOSE_R, NOSE_R, dist[yy, xx])
ratio = np.clip(smooth_l / np.maximum(lum, 1), 0.6, 3.0)
# the underside faces down and shades much darker than its neighbours in faceted steps: lift its albedo
down = smooth(0.0, 0.8, -texel_normals(region)[:, 1])
ratio = ratio * (1 + NOSE_LIFT * down)
base[yy, xx] = base[yy, xx] * (1 + (ratio - 1) * w)[:, None]
spec_paint[yy, xx] = np.where(w > 0.5, 0.3, spec_paint[yy, xx])
normal[yy, xx, :2] *= (1 - 0.7 * w)[:, None]
report['nostril'] = {'tip': tip.round(4).tolist(), 'texels': int(region.sum()),
                     'min_lum_before': round(float(lum.min()), 1),
                     'min_lum_after': round(float((base[yy, xx] @ LUMA).min()), 1)}

# ---- 4b. the hidden legs: white stockings as production meant (its single petticoat UV point had come out dress
# green after the reduction, unrecoloured, so every tier showed green shins under the lifted hem)
legs = T['leg']
base[legs] = STOCKING
normal[legs] = (0, 0, 1)
spec_paint[legs], rough_paint[legs] = 0.2, 0.85
report['leg_texels'] = int(legs.sum())

# ---- 5. pad over the new coverage, write
full_tid, _ = texlib.raster(eye_lay['uv'], S)
cov2 = full_tid >= 0
base = texlib.pad(np.clip(base, 0, 255), cov2)
normal[..., 2] = np.sqrt(np.clip(1 - (normal[..., :2] ** 2).sum(-1), 0.0025, 1))
normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
normal = texlib.pad(normal, cov2)
Image.fromarray(np.clip(base + 0.5, 0, 255).astype(np.uint8)).save(f'{dst}_basecolor.png')
Image.fromarray(np.clip((normal + 1) * 127.5 + 0.5, 0, 255).astype(np.uint8)).save(f'{dst}_normal.png')
cov_n = np.asarray(Image.fromarray(cov2.astype(np.uint8) * 255).resize((N, N), Image.Resampling.BOX)) > 0
for c, over in ((0, spec_paint), (1, rough_paint)):
    have = over >= 0
    num = np.asarray(Image.fromarray(np.where(have, over, 0).astype(np.float32)).resize((N, N), Image.Resampling.BOX))
    den = np.asarray(Image.fromarray(have.astype(np.float32)).resize((N, N), Image.Resampling.BOX))
    put = den > 0.2
    mr[..., c][put] = num[put] / den[put]
mr = texlib.pad(mr, cov_n)
Image.fromarray(np.clip(mr * 255 + 0.5, 0, 255).astype(np.uint8)).save(f'{dst}_metal_rough.png')
mask = texlib.pad(mask, cov_n)
Image.fromarray(np.clip(mask * 255 + 0.5, 0, 255).astype(np.uint8), 'RGBA').save(f'{dst}_region_mask.png')
Image.fromarray(classes).save(f'{dst}_material_classes.png')
np.save(f'{dst}_coverage.npy', cov2)
json.dump(report, open(f'{dst}_face_report.json', 'w'), indent=1)
print('FACE_PAINT', json.dumps(report))
