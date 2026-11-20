"""Procedural eyes for the m372 texture pass (coordinator follow-up 2026-11-01: on the other MM7 peasants each eyeball
triangle showed a different piece of the Meshy paint, so the iris looked shattered and blocky).

1. Layout: the eyeball faces (eyefit.eyeball_faces: the shells, pieces 10 and 11, plus head-piece faces lying on
   the eyeball) leave their xatlas charts. Each eye gets one chart of its own, an
   azimuthal map around the eye's forward axis (eyefit.py): radius = theta up to VISIBLE_DEG, compressed x0.04 beyond
   (the part under the lids), at EYE_DENSITY x the face's density, placed in free atlas space (MARGIN px from every
   other chart). Every other face keeps its UV. Writes work/<layout>e.npz.
2. Paint, in eye-local coordinates (one function for the eyeball faces and for the head skin hugging the eyeball,
   so z-fighting lid faces and shards agree with the eyeball under them): inside an almond lid opening (HD head
   views) the eye, outside a dark lash line and the lid's soft shadow; (angle theta from the forward axis, azimuth phi), so every triangle agrees: an
   off-white sclera shaded towards the corners, an iris of the HD head views' grey-green with radial fibres, a darker
   limbal ring and a lighter collarette, a round pupil, one small soft highlight up and to the viewer's left. Normal
   flat; no region mask (the eyes are the same in every skin); metal/roughness of the approved eye class (spec 0.9,
   roughness 0.2).
Usage: eyes.py <layout npz> <maps prefix in> <maps prefix out>
Writes <out>_{basecolor,normal,metal_rough,region_mask}.png and work/<layout stem>e.npz."""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import texlib  # noqa: E402
import eyefit  # noqa: E402
import normfix  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
layout_path, src, dst = sys.argv[1:4]
S = 2048
VISIBLE_DEG = 45.0
OUTER = 0.04
EYE_DENSITY = 5000.0          # texels per metre on the visible eyeball (the face 2300; the largest free squares are ~95 px)
MARGIN = 4
FORWARD = np.array([0.0, -0.10, 1.0]) / np.linalg.norm([0.0, -0.10, 1.0])   # both eyes straight ahead, as the HD views
IRIS_DEG = 20.0               # iris radius: about half the lid opening's width (HD head views, installed eyes)
PUPIL = 0.32                  # pupil radius / iris radius
SCLERA = np.array([229, 223, 216], np.float32)
SCLERA_BACK = np.array([150, 122, 116], np.float32)
IRIS_IN = np.array([118, 126, 104], np.float32)
IRIS_MID = np.array([92, 102, 88], np.float32)
LIMBAL = np.array([46, 50, 44], np.float32)
PUPIL_C = np.array([14, 12, 12], np.float32)
OPEN_H, OPEN_UP, OPEN_DOWN = 40.0, 11.0, 15.0     # lid opening (degrees): the upper lid over the iris top (HD views)
LASH_DEG, LASH, LID_FADE = 3.0, 0.3, 6.0         # upper lash line width and darkness, lid shadow fade-out
LOWER_DEG, LOWER_LINE = 2.0, 0.78                # the subtle lower-lid line
RIM = 0.9                                        # the shell's rim at the eyeball
SHARD = 0.85                                     # skin shards in front of the eyeball, inside the opening
LID_ON_BALL = 1.0                                 # lid colour painted on the eyeball outside the opening
LID_SHADOW = 0.9
HUG_M = 0.003                                     # skin within this of an eyeball's sphere is repainted with it

lay = np.load(layout_path)
uv = lay['uv'].copy()
before_uv = lay['uv'].copy()                       # the input layout (the skin's UVs stay there)
tri, xyz = lay['tri'], lay['xyz']
piece = np.load(HERE / 'work' / 'face_piece_lod0.npy')
fr = eyefit.frames()
eyeball = eyefit.eyeball_faces(fr)          # per face: 10 / 11 for the eyeball it lies on, else 0
report = {}


def eye_basis(f):
    up = np.array([0.0, 1.0, 0.0])
    x = np.cross(up, f)
    x /= np.linalg.norm(x)
    y = np.cross(f, x)
    return x, y


def local(points, k):
    c = fr[k]['centre']
    d = points - c
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    x, y = eye_basis(FORWARD)
    theta = np.degrees(np.arccos(np.clip(d @ FORWARD, -1, 1)))
    phi = np.arctan2(d @ y, d @ x)
    return theta, phi


def radial(theta):
    return np.where(theta <= VISIBLE_DEG, theta, VISIBLE_DEG + OUTER * (theta - VISIBLE_DEG))


# ---- 1. layout: one azimuthal chart per eye in free space
others = eyeball == 0
occupied, _ = texlib.raster(uv[others], S)
occupied = ndimage.binary_dilation(occupied >= 0, iterations=MARGIN)
free = ~occupied
free[:MARGIN, :] = free[-MARGIN:, :] = free[:, :MARGIN] = free[:, -MARGIN:] = False
integral = np.pad(np.cumsum(np.cumsum(free.astype(np.int32), 0), 1), ((1, 0), (1, 0)))
for k in sorted(fr):
    faces = np.nonzero(eyeball == k)[0]
    theta, phi = local(xyz[faces], k)
    rho = np.radians(radial(theta)) * fr[k]['radius'] * EYE_DENSITY / S        # in UV units
    chart = np.stack([rho * np.cos(phi), -rho * np.sin(phi)], -1)               # glTF v down: +y up -> -v
    lo, hi = chart.reshape(-1, 2).min(0), chart.reshape(-1, 2).max(0)
    w, h = np.ceil((hi - lo) * S).astype(int) + 2
    # first free w x h window, scanning rows
    win = integral[h:, w:] - integral[:-h, w:] - integral[h:, :-w] + integral[:-h, :-w]
    ys, xs = np.nonzero(win[:S - h + 1, :S - w + 1] == w * h)
    if not len(ys):
        raise SystemExit(f'no free {w}x{h} window for eye {k}')
    y0, x0 = ys[0], xs[0]
    uv[faces] = chart - lo + (np.array([x0, y0]) + 1) / S
    free[max(y0 - MARGIN, 0):y0 + h + MARGIN, max(x0 - MARGIN, 0):x0 + w + MARGIN] = False
    integral = np.pad(np.cumsum(np.cumsum(free.astype(np.int32), 0), 1), ((1, 0), (1, 0)))
    report[f'eye_{k}'] = {'chart_px': [int(w), int(h)], 'at_px': [int(x0), int(y0)],
                          'max_theta_deg': round(float(theta.max()), 1), 'radius_m': round(fr[k]['radius'], 4),
                          'centre': np.round(fr[k]['centre'], 4).tolist()}
out_layout = Path(layout_path).with_name(Path(layout_path).stem + 'e.npz')
np.savez(out_layout, uv=uv, tri=tri, xyz=xyz)

# ---- 2. paint
base = np.asarray(Image.open(f'{src}_basecolor.png').convert('RGB'), np.float32)
normal = np.asarray(Image.open(f'{src}_normal.png').convert('RGB'), np.float32)
relief_scale = normfix.cook_relief_scale(normal)
before = np.load(HERE / 'work' / 'lod0_before.npz')
vnrm = before['nrm'][before['tri']].astype(np.float64)                 # per face corner: the rest vertex normals
mr_img = Image.open(f'{src}_metal_rough.png').convert('RGB')
mr = np.asarray(mr_img.resize((S, S), Image.NEAREST), np.float32)
mask_img = Image.open(f'{src}_region_mask.png').convert('RGBA')
eye_faces = eyeball > 0
tid, bary = texlib.raster(uv[eye_faces], S, grow=2.0)
cov = tid >= 0
fidx = np.nonzero(eye_faces)[0]
pts = (xyz[fidx[tid[cov]]] * bary[cov][:, :, None]).sum(1)
pk = eyeball[fidx[tid[cov]]]
rng = np.random.default_rng(7)
fib_phase = rng.uniform(0, 2 * np.pi, 3)


def opening_sd(theta, phi):
    """Signed angular distance (degrees) to the lid opening, an almond in eye-local tangent angles (a across, b up):
    negative inside. HD head views: width 2.33 iris diameters, the upper lid just over the iris top, the lower lid
    at its bottom."""
    a = theta * np.cos(phi)
    b = theta * np.sin(phi)
    s = np.clip(1 - (a / OPEN_H) ** 2, 0, 1) ** 0.6
    return np.maximum.reduce([b - OPEN_UP * s, -OPEN_DOWN * s - b, np.abs(a) - OPEN_H])


def lid_shade(sd, ph, theta):
    """Outside the opening (round 3, as the accepted m342 eyes): above, a dark lash line then a soft lid shadow fading
    out by LID_FADE degrees; below, only a subtle lower-lid line. Both fade toward the corners (no dark fleck where the
    upper and lower lids meet)."""
    upper = np.sin(ph) > 0
    across = np.abs(theta * np.cos(ph)) / OPEN_H
    corner = np.clip((1.0 - across) / 0.35, 0, 1)
    up_line = np.clip(1 - sd / LASH_DEG, 0, 1) ** 0.7
    up = np.where(sd < LASH_DEG, LASH + (LID_SHADOW - LASH) * (1 - up_line),
                  LID_SHADOW + (1 - LID_SHADOW) * np.clip((sd - LASH_DEG) / (LID_FADE - LASH_DEG), 0, 1))
    low = 1 - (1 - LOWER_LINE) * np.clip(1 - sd / LOWER_DEG, 0, 1)
    sh = np.where(upper, up, low)
    return 1 - (1 - sh) * np.where(upper, 0.5 + 0.5 * corner, corner)


def eye_colour(points, k):
    theta, phi = local(points, k)
    r = theta / IRIS_DEG                                          # 1 at the iris edge
    # sclera: off-white, a little darker towards the corners
    # sclera darkening toward the corners (the accepted m342 eyes' colours and range)
    back = np.clip((theta - IRIS_DEG - 4) / (48 - IRIS_DEG - 4), 0, 1)
    back = back * back * (3 - 2 * back)
    c = SCLERA + (SCLERA_BACK - SCLERA) * back[:, None]
    # iris: radial fibres (azimuthal noise), lighter collarette near the pupil, darker limbal ring
    fib = (0.5 * np.sin(phi * 37 + fib_phase[0]) + 0.3 * np.sin(phi * 71 + fib_phase[1])
           + 0.2 * np.sin(phi * 113 + 4 * r + fib_phase[2]))
    iris = IRIS_MID + (IRIS_IN - IRIS_MID) * np.clip(1.6 - 1.6 * r, 0, 1)[:, None]
    iris = iris * (1 + 0.10 * fib)[:, None]
    limb = np.clip((r - 0.78) / 0.22, 0, 1)[:, None]
    iris = iris * (1 - limb) + LIMBAL * limb
    edge = np.clip((1.0 - r) / 0.06, 0, 1)[:, None]
    c = c * (1 - edge) + iris * edge
    pup = np.clip((PUPIL - r) / 0.04 + 0.5, 0, 1)[:, None]
    c = c * (1 - pup) + PUPIL_C * pup
    # highlight up and to the viewer's left
    x, y = eye_basis(FORWARD)
    d = points - fr[k]['centre']
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    hdir = FORWARD * np.cos(np.radians(8)) + (0.55 * y - 0.83 * x) * np.sin(np.radians(8))
    hl = np.exp(-0.5 * (np.degrees(np.arccos(np.clip(d @ hdir, -1, 1))) / 1.6) ** 2)[:, None]
    c = c * (1 - 0.75 * hl) + np.array([250, 250, 248], np.float32) * 0.75 * hl
    # the upper lid's soft shadow on the eyeball just below it
    sd = opening_sd(theta, phi)
    c = c * (1 - 0.35 * np.clip(1 + sd / 4.0, 0, 1) * (np.sin(phi) > 0))[:, None]
    return c, sd


def lin_(c):
    c = np.asarray(c, np.float32) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb_(c):
    c = np.clip(c, 0, 1)
    return 255 * np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


# the lid skin colour: the composed skin around the eyes (outside the opening, away from the lash line)
lay_r = np.load(HERE / 'work' / 'approved_v2_raster2048.npz')        # texel -> face of the input layout
o_tid, o_bary = lay_r['tri_id'], lay_r['bary']
o_cov = (o_tid >= 0)
o_cov[o_cov] = (eyeball[o_tid[o_cov]] == 0) & (piece[o_tid[o_cov]] == 1)
o_pts = (xyz[o_tid[o_cov]] * o_bary[o_cov][:, :, None]).sum(1)
o_nrm = (vnrm[o_tid[o_cov]] * o_bary[o_cov][:, :, None]).sum(1)
o_nrm /= np.linalg.norm(o_nrm, axis=1, keepdims=True)
ring_nrm = []
o_yx = np.nonzero(o_cov)
col = np.zeros((len(pts), 3), np.float32)
face_pts = (o_pts[:, 2] > 0.08) & (o_pts[:, 1] > 1.50) & (o_pts[:, 1] < 1.55)
skin_mr = np.median(mr[o_cov][face_pts], 0)
hug_all = np.zeros(len(o_pts), bool)
ring_pts, ring_col = [], []
for k in sorted(fr):
    rr = np.linalg.norm(o_pts - fr[k]['centre'], axis=1)
    dist = np.abs(rr - fr[k]['radius'])
    th, ph = local(o_pts, k)
    near = (dist < HUG_M) & (th < 70)
    # the skin just outside the hugging band: the tone the lids on the eyeball take (no patch of its own)
    ring = (dist >= HUG_M) & (dist < 2 * HUG_M) & (th < 70)
    ring_pts.append(o_pts[ring])
    ring_col.append(lin_(base[o_cov][ring]))
    ring_nrm.append(o_nrm[ring])
    # skin hugging the eyeball: the lash line and lid shadow on the composed skin, fading out with the distance from
    # the eyeball; skin shards inside the opening (in front of the eyeball, off its surface) a little darker skin
    sd = opening_sd(th[near], ph[near])
    upper = np.sin(ph[near]) > 0
    fade = np.clip(1 - (dist[near] - 0.001) / (HUG_M - 0.001), 0, 1)
    sh = np.where(sd < 0, SHARD, lid_shade(np.maximum(sd, 0), ph[near], th[near]))
    # the lid rim where the head shell meets the eyeball: a soft socket shadow, so the shell's edge does not read as
    # a cut-out against the eyeball's lid-coloured part
    sh = sh * (RIM + (1 - RIM) * np.clip(dist[near] / HUG_M, 0, 1))
    shade = 1 - (1 - sh) * fade
    vals = base[o_cov].copy()
    vals[near] = srgb_(lin_(base[o_cov][near]) * shade[:, None])
    base[o_cov] = vals
    mvals = mr[o_cov].copy()
    mvals[near] = skin_mr
    mr[o_cov] = mvals
    hug_all |= near
ring_tree = cKDTree(np.concatenate(ring_pts))
ring_col = np.concatenate(ring_col)
ring_nrm = np.concatenate(ring_nrm)
eye_in = np.zeros(len(pts), np.float32)
lid_nrm = np.zeros((len(pts), 3))
for k in sorted(fr):
    m = pk == k
    cc, sd = eye_colour(pts[m], k)
    th, ph = local(pts[m], k)
    inside = np.clip(0.5 - sd / 0.8, 0, 1)[:, None]
    _, nb = ring_tree.query(pts[m], k=12)
    skin_here = ring_col[nb].mean(1)
    lid_nrm[m] = ring_nrm[nb].mean(1)
    # (its shading is matched by the normal map below: the lids' normal; no albedo compensation)
    comp = np.ones(int(m.sum()))
    lidc = srgb_(skin_here * LID_ON_BALL * comp[:, None] * lid_shade(np.maximum(sd, 0), ph, th)[:, None])
    col[m] = cc * inside + lidc * (1 - inside)
    eye_in[m] = inside[:, 0]
report['hugging_skin_texels'] = int(hug_all.sum())
base[cov] = col
# the eyeball's lid-coloured part shades with the lids' normal (its sphere normals lit it differently from the skin
# around it: a hard-edged patch); the eye inside the opening keeps a flat normal. normfix.encode divides by the cook's
# relief lift, so the game shows about this normal.
f_eye = fidx[tid[cov]]
flat = np.array([127.5, 127.5, 255.0])
enc = normfix.encode(lid_nrm.copy(), xyz[f_eye], uv[f_eye], vnrm[f_eye], bary[cov], relief_scale)
w_eye = eye_in[:, None]
normal[cov] = flat * w_eye + enc * (1 - w_eye)
report['relief_scale_in_game'] = round(relief_scale, 3)
mr[cov] = np.where(eye_in[:, None] > 0.5, np.array([230, 51, 0], np.float32), skin_mr)   # lid parts: skin gloss
Image.fromarray(np.clip(base + 0.5, 0, 255).astype(np.uint8)).save(f'{dst}_basecolor.png')
Image.fromarray(normal.astype(np.uint8)).save(f'{dst}_normal.png')
Image.fromarray(mr.astype(np.uint8)).resize(mr_img.size, Image.NEAREST).save(f'{dst}_metal_rough.png') \
    if mr_img.size != (S, S) else Image.fromarray(mr.astype(np.uint8)).save(f'{dst}_metal_rough.png')
# the eye charts' small mask texels are cleared (eyes stay unmasked in every skin)
m4 = np.asarray(mask_img, np.uint8).copy()
small = np.asarray(Image.fromarray(cov.astype(np.uint8) * 255).resize(mask_img.size, Image.BOX)) > 0
m4[small] = 0
Image.fromarray(m4, 'RGBA').save(f'{dst}_region_mask.png')
report['eye_texels'] = int(cov.sum())
report['layout'] = str(out_layout.name)
json.dump(report, open(f'{dst}_eyes.json', 'w'), indent=1)
print('EYES', json.dumps(report))
