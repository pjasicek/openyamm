"""Eyes, eyelid rims, mouth and nostrils of the m362 texture pass, after compose.py (edits its maps in place).

The Meshy head paint lays each eyeball triangle's piece of the eye separately (the iris reads shattered and blocky,
pale shards sit on the lid rims and in the eye corners) and draws pale shards and hard dark spikes in the mouth slit
and the nostrils. These are painted procedurally on the rest-pose surface instead:

- Eyes (pieces 16 and 18): each eyeball's sphere is fitted to its vertices; its forward axis runs from the centre to the
  head paint's pupil (the darkest texels; both look straight ahead with a slight outward turn, as the HD head views).
  The two axes are made mirror-symmetric. The eyeball triangles get a new chart each: an azimuthal map around the axis
  into the largest free discs of the atlas (the paid layout's other charts are untouched; the eyes take no Meshy paint),
  the visible cap (to EYE_CAP) on 85 % of the disc radius. Colour in eye-local angles, so every triangle agrees: off-
  white sclera darkening towards the corners, an iris in the HD head views' blue-grey with radial fibres, a lighter
  collarette and a dark limbal ring, a round pupil and a small soft highlight; the layout's AO at the same surface
  points (lid occlusion). Flat normal, no region, the approved eye metal/roughness.
- Lid rims: head skin within RIM_MM of the eyeball surface that faces along it (not outward like the lid's front),
  and pale texels at the eyeball's edge, take a dark lid shadow.
- Under the eyes: the head paint's dark grey-green crescents take the cheek skin around them, slightly shaded.
- Mouth: the mouth interior (piece 29) is a dark red-brown gradient, darker with depth; the lip faces turned into the
  slit fade into it, so the opening is one soft shadow.
- Lower face (2026-11-01, no beard on any skin): the former beard area takes the cheeks' chroma, and texels darker
  than the cheeks are lifted half way, so no stubble shadow or grey-green tint is left.
- Undershirt (2026-11-01): the chest skin in the opening below the collar becomes the off-white undershirt of the
  sleeves and collar (their colour, a sleeve's own weave, soft folds, AO), unrecoloured like them; the four tie bars
  across it are dark leather all round.
- Nostrils: dark paint and downward-facing skin under the nose tip take the surrounding skin colour shaded by how
  far the surface faces down (a smooth shadow, no dark spike).

Usage: face_features.py <maps prefix>  (reads work/uv_fine.npz; writes work/uv_final.npz, work/eyes.json and the
<prefix>_{basecolor,normal,region_mask,metal_rough}.png in place)."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import texlib  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
W = HERE / 'work'
prefix = sys.argv[1]
S = 2048
EYES = (16, 18)
MOUTH = 29
EYE_CAP = 50.0                       # degrees of the visible cap on 85 % of the disc radius
IRIS_DEG, PUPIL_FRAC = 26.0, 0.36
RIM_MM = 1.6
LOWER_CHROMA = 1.0                   # chroma pull of the former beard area to the cheeks
SHIRT_TOP = 1.396                    # rest height of the collar's lower edge in the chest opening
LACES = (41, 42, 43, 44)             # the four tie bars across the opening
LEATHER = np.array([64, 45, 34], np.float32)
X0, MOUTH_Y = -0.0058, 1.5125
SCLERA = np.array([226, 220, 213], np.float32)
SCLERA_EDGE = np.array([200, 176, 168], np.float32)
IRIS_IN = np.array([120, 134, 148], np.float32)
IRIS_OUT = np.array([84, 97, 112], np.float32)
LIMBAL = np.array([44, 54, 66], np.float32)
PUPIL = np.array([12, 12, 14], np.float32)
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)


def smoothstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def noise1(x, seed):
    """Smooth periodic-free value noise along x (array)."""
    i = np.floor(x).astype(np.int64)
    f = x - i
    h = lambda k: (((k * 2654435761 + seed * 97531) ^ ((k * 2654435761 + seed * 97531) >> 13)) & 0xFFFF) / 65535.0
    f = f * f * (3 - 2 * f)
    return h(i) * (1 - f) + h(i + 1) * f


layout = np.load(W / 'uv_fine.npz')
before = np.load(W / 'lod0_before.npz')
pieces = np.load(W / 'pieces.npz')['piece']
tri, pos, nrm = before['tri'], before['pos'], before['nrm']
uv_new = layout['uv'].copy()
base = np.asarray(Image.open(f'{prefix}_basecolor.png').convert('RGB'), np.float32).copy()
normal = np.asarray(Image.open(f'{prefix}_normal.png').convert('RGB'), np.uint8).copy()
mask = np.asarray(Image.open(f'{prefix}_region_mask.png').convert('RGBA'), np.uint8).copy()
mr_img = Image.open(f'{prefix}_metal_rough.png').convert('RGB')
mr = np.asarray(mr_img, np.uint8).copy()
ao = np.asarray(Image.open(HERE / 'textures' / 'm362_tp_ao_2k.png').convert('L'), np.float32) / 255
head_paint = np.asarray(Image.open(HERE / 'meshy' / 'head_retexture_v2' / 'texture_urls_0_base_color.png')
                        .convert('RGB').resize((S, S), Image.Resampling.LANCZOS), np.float32)
r = np.load(W / f'approved_fine_raster{S}.npz')
tri_id, bary = r['tri_id'], r['bary']
cov = tri_id >= 0
t = tri_id[cov]
P = np.zeros((S, S, 3), np.float32)
P[cov] = (pos[tri[t]] * bary[cov][:, :, None]).sum(1)
N = np.zeros((S, S, 3), np.float32)
N[cov] = (nrm[tri[t]] * bary[cov][:, :, None]).sum(1)
N /= np.maximum(np.linalg.norm(N, axis=-1, keepdims=True), 1e-6)
piece = np.full((S, S), -1, np.int32)
piece[cov] = pieces[t]
mr_small = np.asarray(mr_img.resize((S, S), Image.Resampling.NEAREST), np.uint8)
report = {}

# ---------------------------------------------------------------- eyes: spheres, axes, discs
eye_faces = np.isin(pieces, EYES)
occupied = cov & ~eye_faces[np.maximum(tri_id, 0)]
free = ~ndimage.binary_dilation(occupied, iterations=3)
free[:3], free[-3:], free[:, :3], free[:, -3:] = False, False, False, False
eyes = {}
# forward axes from the head paint's pupils, made mirror-symmetric (mean outward turn and mean lift of the two)
AXES = {}
raw_axes = {}
for k in EYES:
    f = np.nonzero(pieces == k)[0]
    q = pos[np.unique(tri[f])]
    sol = np.linalg.lstsq(np.c_[2 * q, np.ones(len(q))], (q ** 2).sum(1), rcond=None)[0]
    sel = piece == k
    lum = head_paint[sel] @ LUMA
    a = P[sel][lum < np.percentile(lum, 3)].mean(0) - sol[:3]
    raw_axes[k] = a / np.linalg.norm(a)
centre_x = {k: float(np.mean(pos[np.unique(tri[pieces == k])][:, 0])) for k in EYES}
out_turn = np.mean([abs(raw_axes[k][0]) for k in EYES])
lift = np.mean([raw_axes[k][1] for k in EYES])
for k in EYES:
    sign = np.sign(centre_x[k] - X0)
    a = np.array([sign * out_turn, lift, 1.0])
    a[2] = np.sqrt(max(1 - a[0] ** 2 - a[1] ** 2, 0.5))
    AXES[k] = a / np.linalg.norm(a)
for k in EYES:
    f = np.nonzero(pieces == k)[0]
    v = np.unique(tri[f])
    q = pos[v]
    sol = np.linalg.lstsq(np.c_[2 * q, np.ones(len(q))], (q ** 2).sum(1), rcond=None)[0]
    c = sol[:3]
    rad = float(np.sqrt(sol[3] + c @ c))
    sel = piece == k
    lum = head_paint[sel] @ LUMA
    dark = lum < np.percentile(lum, 3)
    axis = P[sel][dark].mean(0) - c
    axis /= np.linalg.norm(axis)
    axis = AXES.get(k, axis)
    up = np.array([0.0, 1.0, 0.0]) - axis[1] * axis
    up /= np.linalg.norm(up)
    side = np.cross(up, axis)
    dist = ndimage.distance_transform_edt(free)
    cy, cx = np.unravel_index(np.argmax(dist), dist.shape)
    R = float(dist.max()) - 1.0
    yy, xx = np.ogrid[:S, :S]
    free &= ~(((yy - cy) ** 2 + (xx - cx) ** 2) < (R + 4) ** 2)
    eyes[k] = dict(c=c, r=rad, axis=axis, up=up, side=side, cx=float(cx), cy=float(cy), R=R)
    # corner UVs: azimuthal map around the axis
    d = pos[tri[f]] - c
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    theta = np.degrees(np.arccos(np.clip(d @ axis, -1, 1)))
    phi = np.arctan2(d @ up, d @ side)
    g = np.where(theta < EYE_CAP, 0.85 * theta / EYE_CAP,
                 0.85 + 0.15 * np.clip((theta - EYE_CAP) / (130 - EYE_CAP), 0, 1))
    rr = g * R
    uv_new[f, :, 0] = (cx + 0.5 + rr * np.cos(phi)) / S
    uv_new[f, :, 1] = (cy + 0.5 - rr * np.sin(phi)) / S
    report[f'eye_{k}'] = {'centre': np.round(c, 4).tolist(), 'radius_mm': round(rad * 1000, 2),
                          'axis': np.round(axis, 3).tolist(), 'disc_px': [int(cx), int(cy), round(R, 1)],
                          'max_theta': round(float(theta.max()), 1),
                          'cap_px_per_cm': round(0.85 * R / (np.radians(EYE_CAP) * rad * 100), 1)}
np.savez(W / 'uv_final.npz', uv=uv_new, tri=layout['tri'], xyz=layout['xyz'])

# ---------------------------------------------------------------- eyes: paint the discs
ef = np.nonzero(eye_faces)[0]
tid_e, bary_e = texlib.raster(uv_new[ef], S)
cov_e = tid_e >= 0
fe = ef[tid_e[cov_e]]
Pe = (pos[tri[fe]] * bary_e[cov_e][:, :, None]).sum(1)
old_uv = (layout['uv'][fe] * bary_e[cov_e][:, :, None]).sum(1)          # the same surface point on the paid layout
ao_e = texlib.bilinear(ao[..., None], old_uv)[:, 0]
eye_mr = np.median(mr_small[np.isin(piece, EYES)], 0)
col = np.zeros((len(fe), 3), np.float32)
for k in EYES:
    e = eyes[k]
    m = pieces[fe] == k
    d = Pe[m] - e['c']
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    th = np.degrees(np.arccos(np.clip(d @ e['axis'], -1, 1)))
    ph = np.arctan2(d @ e['up'], d @ e['side'])
    rho = th / IRIS_DEG                                              # 0 centre .. 1 iris edge
    fib = 0.75 * noise1(ph * 38 / np.pi + rho * 1.5, 1 + k) + 0.25 * noise1(ph * 90 / np.pi, 7 + k)
    iris = IRIS_IN * (1 - smoothstep(rho, 0.3, 0.95)[:, None]) + IRIS_OUT * smoothstep(rho, 0.3, 0.95)[:, None]
    iris = iris * (0.82 + 0.36 * fib)[:, None]
    iris = iris * (1 + 0.18 * (1 - smoothstep(rho, PUPIL_FRAC, PUPIL_FRAC + 0.18)))[:, None]   # collarette
    limb = smoothstep(rho, 0.80, 0.98)
    iris = iris * (1 - limb[:, None]) + LIMBAL * limb[:, None]
    pupil = 1 - smoothstep(rho, PUPIL_FRAC - 0.04, PUPIL_FRAC + 0.02)
    iris = iris * (1 - pupil[:, None]) + PUPIL * pupil[:, None]
    edge = smoothstep(th, 45, 75)
    sclera = SCLERA * (1 - edge[:, None]) + SCLERA_EDGE * edge[:, None]
    in_iris = 1 - smoothstep(rho, 0.98, 1.04)
    c_eye = sclera * (1 - in_iris[:, None]) + iris * in_iris[:, None]
    # highlight: a small soft spot up and to the side of the pupil (fixed in eye space)
    hl_dir = e['axis'] * np.cos(np.radians(9)) + (e['up'] * 0.7 - e['side'] * 0.7) * np.sin(np.radians(9))
    hl = np.degrees(np.arccos(np.clip(d @ (hl_dir / np.linalg.norm(hl_dir)), -1, 1)))
    c_eye += (1 - smoothstep(hl, 1.2, 3.2))[:, None] * 160
    col[m] = c_eye
col *= (1 - 0.65 * (1 - np.clip(ao_e, 0, 1)))[:, None]
disc = np.zeros((S, S), bool)
for k in EYES:
    e = eyes[k]
    yy, xx = np.ogrid[:S, :S]
    disc |= ((yy - e['cy']) ** 2 + (xx - e['cx']) ** 2) <= (e['R'] + 2) ** 2
img = np.zeros((S, S, 3), np.float32)
img[cov_e] = np.clip(col, 0, 255)
img = texlib.pad(img, cov_e)
base[disc] = img[disc]
normal[disc] = (128, 128, 255)
mask[disc] = 0
mr_full = np.asarray(Image.fromarray(mr).resize((S, S), Image.Resampling.NEAREST), np.uint8).copy()
mr_full[disc] = eye_mr
report['eye_metal_rough'] = eye_mr.tolist()

# ---------------------------------------------------------------- lid rims
skin0 = cov & (piece == 0)
rim_w = np.zeros((S, S), np.float32)
for k in EYES:
    e = eyes[k]
    rel = P - e['c']
    dn = np.linalg.norm(rel, axis=-1)
    radial = rel / np.maximum(dn, 1e-6)[..., None]
    gap = (dn - e['r']) * 1000                                       # mm above the eyeball surface
    facing = (N * radial).sum(-1)
    front = (rel @ e['axis']) > 0.0
    rim = skin0 & front & (gap < RIM_MM) & (facing < 0.55)
    w = (1 - smoothstep(gap, RIM_MM * 0.5, RIM_MM)) * (1 - smoothstep(facing, 0.3, 0.55))
    pale = skin0 & front & (gap < 1.2) & ((base @ LUMA) > 150)
    rim_w = np.maximum(rim_w, np.where(rim, w, 0) + np.where(pale, 1.0, 0))
rim_w = np.clip(ndimage.gaussian_filter(rim_w, 0.7), 0, 1) * skin0
lid = texlib.pad(base, skin0 & (rim_w < 0.05))
lid_shadow = lid * 0.5
base = base * (1 - rim_w[..., None]) + lid_shadow * rim_w[..., None]
report['lid_rim_texels'] = int((rim_w > 0.5).sum())

# ---------------------------------------------------------------- under the eyes
# the head paint's dark grey-green crescents under the lower lids (deeper than the compose step's chroma fix): skin
# darker than the cheek skin around it takes that skin, slightly shaded, feathered
under = np.zeros((S, S), bool)
for k in EYES:
    e = eyes[k]
    rel = P - e['c']
    under |= skin0 & (rel[..., 1] < -0.002) & (rel[..., 1] > -0.014) & (np.abs(rel[..., 0]) < 0.017) \
        & (rel[..., 2] > 0.0) & (rim_w < 0.3)
lum_b = base @ LUMA
clean_u = skin0 & ~(under & (lum_b < np.percentile(lum_b[under], 70)))
cheek = texlib.pad(ndimage.gaussian_filter(texlib.pad(base, clean_u), (6, 6, 0)), cov)
dark_u = np.clip((cheek @ LUMA * 0.97 - lum_b) / np.maximum(cheek @ LUMA * 0.25, 1), 0, 1)
w_u = ndimage.gaussian_filter((under * np.minimum(1.0, dark_u + 0.3)).astype(np.float32), 1.5) * skin0
base = base * (1 - w_u[..., None]) + (cheek * 0.95) * w_u[..., None]
report['under_eye_texels'] = int((w_u > 0.5).sum())

# ---------------------------------------------------------------- mouth
mouth = cov & (piece == MOUTH)
front_z = 0.050
depth = np.clip((front_z - P[..., 2]) / 0.02, 0, 1)
mouth_col = np.array([92, 44, 42], np.float32)[None, None] * (1 - depth[..., None]) \
    + np.array([26, 12, 12], np.float32)[None, None] * depth[..., None]
base[mouth] = mouth_col[mouth]
dx = np.abs(P[..., 0] - X0)
dy = P[..., 1] - MOUTH_Y
ell = (dx / 0.027) ** 2 + (dy / 0.0085) ** 2
into_slit = -np.sign(dy) * N[..., 1]                                 # > 0: the lip face turns towards the slit
lip_in = skin0 & (ell < 1.3) & (np.abs(dy) < 0.006) & (P[..., 2] > 0.025)
w_lip = np.clip((into_slit - 0.15) / 0.5, 0, 1) * (1 - smoothstep(np.abs(dy), 0.0025, 0.006)) * lip_in
w_lip = ndimage.gaussian_filter(w_lip.astype(np.float32), 0.8) * skin0
lip_dark = mouth_col * 0.9
base = base * (1 - w_lip[..., None]) + lip_dark * w_lip[..., None]
report['lip_inner_texels'] = int((w_lip > 0.5).sum())

# ---------------------------------------------------------------- nostrils
# the underside of the nose: dark paint there (the nostril spike) takes the surrounding skin colour shaded by how far
# the surface faces down, feathered, so the nostrils read as one soft shadow
nose = skin0 & (dx < 0.022) & (P[..., 1] > 1.512) & (P[..., 1] < 1.536) & (P[..., 2] > 0.04)
lum_b = base @ LUMA
clean = skin0 & ~(nose & (lum_b < np.percentile(lum_b[nose], 60)))
skin_near = texlib.pad(ndimage.gaussian_filter(texlib.pad(base, clean), (5, 5, 0)), cov)
down = np.clip((-N[..., 1] + 0.1) / 0.8, 0, 1)
shade = 0.86 - 0.26 * down
dark = np.clip((skin_near @ LUMA * 0.92 - lum_b) / np.maximum(skin_near @ LUMA * 0.35, 1), 0, 1)
w_n = ndimage.gaussian_filter((nose * np.maximum(dark, 0.6 * down)).astype(np.float32), 1.2) * skin0 * nose
base = base * (1 - w_n[..., None]) + (skin_near * shade[..., None]) * w_n[..., None]
report['nostril_texels'] = int((w_n > 0.5).sum())

# ---------------------------------------------------------------- lower face: clean shaven (no beard on any skin)
# the former beard area (moustache, chin, jaw, sideburns) and the chin's underside take the cheeks' chroma
# (LOWER_CHROMA),
# so no stubble shadow or grey-green tint is left above the upper lip or on the chin; lips and the mouth stay
texels = np.load(HERE / 'textures' / 'm362_tp_texels.npz')
lower = texels['lower_face'].astype(np.float32)
# and the underside of the chin down to the throat, where the crossfade left a brown stubble-like band
dx = np.abs(P[..., 0] - X0)
under_chin = (smoothstep(P[..., 1], 1.444, 1.452) * (1 - smoothstep(P[..., 1], 1.478, 1.486))
              * (1 - smoothstep(dx, 0.04, 0.05)) * smoothstep(P[..., 2], -0.02, -0.01)).astype(np.float32)
lower = np.maximum(lower, under_chin * (piece == 0))
# the lip vermilion spans rest height 1.504-1.514 at the front (measured on the paint); the skin above it is upper lip
lips_zone = ((((dx / 0.026) ** 2 + ((P[..., 1] - 1.5092) / 0.0052) ** 2) < 1) & (P[..., 2] > 0.03)) | (piece == MOUTH)
cheeks = skin0 & (P[..., 1] > 1.525) & (P[..., 1] < 1.548) & (dx > 0.026) & (dx < 0.046) & (P[..., 2] > 0.015)
lin_b = (np.clip(base, 0, 255) / 255) ** 2.2
lum_l = lin_b @ LUMA
chroma_ref = np.mean(lin_b[cheeks] / np.maximum(lum_l[cheeks], 1e-4)[:, None], 0)
w_lf = ndimage.gaussian_filter(np.clip(lower * 1.6, 0, 1) * ~lips_zone, 1.5) * LOWER_CHROMA * skin0 * ~lips_zone
# texels darker than the cheeks (the painted shadow under the nose read as a moustache) are lifted half way
lum_ref = float(np.median(lum_l[cheeks]))
lum_t = np.where(lum_l < lum_ref, lum_l * (lum_ref / np.maximum(lum_l, 1e-4)) ** 0.5, lum_l)
lum_t = lum_l + (lum_t - lum_l) * (w_lf / LOWER_CHROMA)
lin_b = lin_b * (1 - w_lf[..., None]) + (chroma_ref[None, None, :] * lum_l[..., None]) * w_lf[..., None]
lin_b *= (lum_t / np.maximum(lum_l, 1e-6))[..., None]
base = np.clip(lin_b, 0, 1) ** (1 / 2.2) * 255
report['lower_face_texels'] = int((w_lf > 0.5 * LOWER_CHROMA).sum())

# ---------------------------------------------------------------- undershirt in the chest opening, leather laces
# the chest skin below the collar (piece 0 under SHIRT_TOP) becomes the off-white undershirt of the sleeves and collar:
# the sleeves' median colour with their own weave (luminance detail of a patch cut from a sleeve, mirrored tiles laid
# by rest position at the same texel density), soft vertical folds and the layout's AO; flat normal, the sleeves'
# metal/roughness and no region (the shirt is not recoloured on any skin, like the sleeves and collar)
sleeve = cov & np.isin(piece, [10, 11])
shirt_col = np.median(base[sleeve], 0)
dist_s = ndimage.distance_transform_edt(piece == 10)
sy, sx = np.unravel_index(np.argmax(dist_s), dist_s.shape)
half = int(dist_s.max() / 1.5)
patch = (base @ LUMA)[sy - half:sy + half, sx - half:sx + half]
weave = patch / np.maximum(ndimage.gaussian_filter(patch, 3.0), 1)
weave = np.clip(weave, 0.8, 1.2)
n_p = weave.shape[0]
texel_per_m = 1283 / 1.70 * S / 2048
chest = cov & (piece == 0) & (P[..., 1] < SHIRT_TOP + 0.006)
w_sh = (1 - smoothstep(P[..., 1], SHIRT_TOP - 0.004, SHIRT_TOP + 0.006)) * chest
yy_, xx_ = (P[..., 1] * texel_per_m).astype(np.int64), (P[..., 0] * texel_per_m).astype(np.int64)
mi = lambda v: np.abs(((v % (2 * n_p)) + 2 * n_p) % (2 * n_p) - n_p + 0.5).astype(np.int64).clip(0, n_p - 1)
detail = weave[mi(yy_), mi(xx_)]
folds = 1 + 0.07 * (noise1(P[..., 0] / 0.016, 3) * 2 - 1) \
    + 0.04 * (noise1(P[..., 1] / 0.05 + P[..., 0] / 0.03, 4) * 2 - 1)
ao_sh = 1 - 0.5 * (1 - ao)
# the factors are normalised over the opening so its median is the sleeves' own colour (the sleeves' paint already
# carries their AO); the opening's AO only shades it relative to that
fac = detail * folds * ao_sh
fac = fac / np.median(fac[chest & (w_sh > 0.5)])
shirt = shirt_col[None, None, :] * np.minimum(fac, 1.12)[..., None]
base = base * (1 - w_sh[..., None]) + shirt * w_sh[..., None]
sel = w_sh > 0.5
normal[sel] = (128, 128, 255)
mask[sel] = 0
mr_full[sel] = np.median(mr_full[sleeve], 0)
report['undershirt_texels'] = int(sel.sum())
laces = cov & np.isin(piece, LACES)
lace_tone = 0.85 + 0.3 * noise1(P[..., 0] / 0.004 + P[..., 1] / 0.003, 5)
base[laces] = (LEATHER[None, None, :] * (lace_tone * ao_sh)[..., None])[laces]
normal[laces] = (128, 128, 255)
mask[laces] = 0
mr_full[laces] = np.median(mr_full[cov & (piece == 15)], 0)
report['lace_texels'] = int(laces.sum())

base = np.where(disc[..., None], base, texlib.pad(base, cov | disc))
Image.fromarray(np.clip(base + 0.5, 0, 255).astype(np.uint8)).save(f'{prefix}_basecolor.png')
Image.fromarray(normal).save(f'{prefix}_normal.png')
Image.fromarray(mask, 'RGBA').save(f'{prefix}_region_mask.png')
Image.fromarray(np.asarray(Image.fromarray(mr_full).resize(mr_img.size, Image.Resampling.NEAREST))).save(
    f'{prefix}_metal_rough.png')
json.dump(report, open(W / 'eyes.json', 'w'), indent=1)
print('FEATURES', json.dumps(report))
