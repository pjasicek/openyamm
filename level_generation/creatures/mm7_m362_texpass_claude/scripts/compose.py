"""Texture-pass maps of the m362 peasant from the two 4K Meshy paints on the paid layout (work/uv_fine.npz).

1. Paint: body retexture (four HD masters, whole mesh) and head retexture (four close head views, head-set faces only),
   colour and normal 4K -> 2K once (Lanczos), after each 4K map's gutters and island rims take the nearest inner texel.
2. Skin match: the head paint's skin (darker and redder) is mapped onto the body paint's by one per-channel quantile
   curve fitted on the front of the face, where both paints cover the same surface; brows and scalp keep the head
   paint's colours. The head paint replaces the body paint on the head set; on the skin only above the jaw line
   (the head paint's neck is a dull grey-beige), crossfaded over about 1.6 cm.
3. One broad skin tone, measured on the welded mesh (continuous across UV seams): per triangle the mean of its skin
   texels, per vertex the mean of its triangles, normalised diffusion over the mesh edges (lips and brow hair add
   nothing), interpolated per texel. Chroma (EVEN_CHROMA_M) and luminance (EVEN_M) are pulled geometrically towards
   the face's skin colour, face 0.5, neck/jaw crossfade/chest 0.95, hands 0.6; the paint's finer detail stays.
   Then the face's remaining grey-green texels (head paint shading under the eyes and above the lip) take the skin
   chroma (0.8, luminance kept), the neck and chest skin below the jaw take NECK_CHROMA of it, and the top of the
   forehead (head paint: dark olive roots and blond hair painted below the hair fringe) takes the forehead colour
   carried up over the mesh, up to the scalp. Pale blond strokes painted over the ears and temples take the nearest
   skin texel.
4. Gentle grade (claude_shared/grade_basecolor.py, recipe values) with AO baked on the layout.
5. Region mask (2048): R doublet and shoulder rolls (doublet pieces in a violet hue, plus clearly violet paint off the
   skin and hair), G hair (hair pieces, hair-coloured scalp skin, and the scalp above the forehead hairline, which
   takes the hair's median colour), B beard: zero on every skin since the "No beard" follow-up (2026-11-01). The
   native-shaped beard (moustache, chin, jaw to the sideburns, drawn in 3D at rest with a fine strand pattern) is still
   computed, only to fit the channel's ramps, which stay in every material, and to mark the lower face for
   face_features.py.
6. Ramps (textures/m362_tp_ramps.json): doublet and hair from each tier's native palette pixels of the region (as
   ../mm7_m362_claude/scripts/compose_m362.py), rank-matched to the new paint's region luminance; the doublet ramps
   then pinned to the installed doublet's engine colour per skin (mean gain, spread <= PIN_SPREAD x installed).
   Beard (channel kept, no coverage): native beard colours on ab, ac, ba, bb, cb; a skin fit on aa, bc, ca, cc.
7. Normal: both paints' normals with the same crossfade, +y down -> glTF +y up, tilt x0.3 (as the approved build).
8. Metal/roughness: the approved one carried onto the layout (resample_approved.py).

Usage: compose.py <out prefix>   (reads work/uv_fine.npz, work/approved_fine_*, textures/m362_tp_ao_2k.png)
Writes <out>_{basecolor,normal,metal_rough,region_mask}.png, <out>_raw.png, <out>_ramps.json, <out>_report.json.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R  # noqa: E402
import texlib  # noqa: E402
import texture_quality as TQ  # noqa: E402

out = sys.argv[1]
S = 2048
M = HERE / 'meshy'
W = HERE / 'work'
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)
NECK_LO, NECK_HI = 1.430, 1.480          # head paint fades in over the neck below the jaw (chin bottom 1.475)
EVEN_M = 0.015                           # broad skin luminance scale (metres of surface)
EVEN_CHROMA_M = 0.007                    # skin chroma scale
EVEN_FACE, EVEN_BODY, EVEN_HANDS = 0.5, 0.95, 0.6
NECK_CHROMA = 0.7                        # per-texel chroma pull on the neck and chest skin
PIN_SPREAD = 1.2                         # doublet luminance spread allowed above the installed one
X0 = -0.0058                             # face midline (eyes and mouth pieces)
BEARDED = ('m362_ab', 'm362_ac', 'm362_ba', 'm362_bb', 'm362_cb')
VARIANTS = {f'm362_{o}{t}': 363 + 3 * i + j for i, o in enumerate('abc') for j, t in enumerate('abc')}
PALDIR = HERE.parents[2] / 'assets_dev' / 'worlds' / 'mm7' / 'textures'
NATIVE = HERE.parent / 'mm7_m362' / 'native'


def load(path, mode='RGB', inside=None):
    """A Meshy map at 2K. With `inside` (4K coverage), the 4K gutters and each island's outermost texel first take the
    nearest inner texel: Meshy's gutter streaks and dark edge texels otherwise bleed into the islands in the
    downsample and draw thin dark lines along every chart seam."""
    img = Image.open(path).convert(mode)
    if inside is not None:
        a = np.asarray(img, np.float32)
        img = Image.fromarray(np.clip(texlib.pad(a, inside) + 0.5, 0, 255).astype(np.uint8))
    if img.size != (S, S):
        img = img.resize((S, S), Image.Resampling.LANCZOS)
    return np.asarray(img, np.float32)


def smoothstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def wpercentile(v, w, q):
    o = np.argsort(v)
    c = np.cumsum(w[o])
    c /= c[-1]
    return np.interp(q / 100, c, v[o])


def enc(v):
    """linear -> sRGB 0..1"""
    return np.where(v <= 0.0031308, v * 12.92, 1.055 * np.maximum(v, 0) ** (1 / 2.4) - 0.055)


def save(a, path):
    Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8)).save(path)


# ---------------------------------------------------------------- texel data
layout = np.load(W / 'uv_fine.npz')
before = np.load(W / 'lod0_before.npz')
pieces = np.load(W / 'pieces.npz')
r = np.load(W / f'approved_fine_raster{S}.npz')
tri_id, bary = r['tri_id'], r['bary']
cov = tri_id >= 0
t = tri_id[cov]
tri, weld, pos, nrm = before['tri'], before['weld'], before['pos'], before['nrm']
P = np.zeros((S, S, 3), np.float32)
P[cov] = (pos[tri[t]] * bary[cov][:, :, None]).sum(1)
N = np.zeros((S, S, 3), np.float32)
N[cov] = (nrm[tri[t]] * bary[cov][:, :, None]).sum(1)
N /= np.maximum(np.linalg.norm(N, axis=-1, keepdims=True), 1e-6)
piece = np.full((S, S), -1, np.int32)
piece[cov] = pieces['piece'][t]
garment = np.full((S, S), -1, np.int32)
garment[cov] = pieces['garment'][t]
head_face = before['head_face']
uv, xyz = layout['uv'], layout['xyz']
area3 = np.linalg.norm(np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]), axis=1) / 2
area2 = np.abs((uv[:, 1, 0] - uv[:, 0, 0]) * (uv[:, 2, 1] - uv[:, 0, 1])
               - (uv[:, 2, 0] - uv[:, 0, 0]) * (uv[:, 1, 1] - uv[:, 0, 1])) / 2
tri_density = np.sqrt(area2 / np.maximum(area3, 1e-12))
weight = np.zeros((S, S), np.float32)
weight[cov] = 1.0 / np.maximum(tri_density[t], 1e-9) ** 2          # texels -> surface area
isl = TQ.islands(uv.astype(np.float64), xyz.astype(np.float64))
_, isl = np.unique(isl, return_inverse=True)
island_density = np.sqrt(np.bincount(isl, area2) / np.maximum(np.bincount(isl, area3), 1e-12))
median_density = float(np.median(island_density[isl]))
island_map = np.where(cov, isl[np.maximum(tri_id, 0)], -1)
report = {}

# ---------------------------------------------------------------- 1. paint, 2. one skin tone
r4_path = W / 'uv_fine_raster4096.npz'
if not r4_path.exists():
    tri4, _ = texlib.raster(layout['uv'], 4096)
    np.savez_compressed(r4_path, tri_id=tri4)
tri4 = np.load(r4_path)['tri_id']
inside_body = ndimage.binary_erosion(tri4 >= 0)
inside_head = ndimage.binary_erosion((tri4 >= 0) & head_face[np.maximum(tri4, 0)])
body = load(M / 'body_retexture_v2' / 'texture_urls_0_base_color.png', inside=inside_body)
head = load(M / 'head_retexture_v2' / 'texture_urls_0_base_color.png', inside=inside_head)
nweld = int(weld.max()) + 1
count = np.bincount(weld[tri].ravel(), minlength=nweld).astype(np.float32)
hcount = np.bincount(weld[tri[head_face]].ravel(), minlength=nweld).astype(np.float32)
head_w_vert = hcount / np.maximum(count, 1)
share = np.zeros((S, S), np.float32)
share[cov] = (head_w_vert[weld[tri[t]]] * bary[cov]).sum(1)
on_head = np.zeros((S, S), bool)
on_head[cov] = head_face[t]
hw = np.clip(share, 0, 1) * smoothstep(P[..., 1], NECK_LO, NECK_HI) * on_head

skin_piece = np.isin(piece, [0, 1, 2])


def skinlike(img):
    hh = np.asarray(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('HSV'), np.float32)
    deg = hh[..., 0] * 360 / 255
    return ((deg < 40) | (deg > 340)) & (hh[..., 1] > 50) & (hh[..., 2] > 90)


dx = np.abs(P[..., 0] - X0)
# skin of the head takes the head paint above the jaw line only: the head paint's neck is a dull grey-beige
jaw = 1.478 + np.clip(0.03 - P[..., 2], 0, None) * 0.4
hw_skin = smoothstep(P[..., 1], jaw - 0.004, jaw + 0.012)
hw = np.where(piece == 0, np.minimum(hw, hw_skin), hw)
front = cov & on_head & (piece == 0) & (P[..., 1] > 1.48) & (P[..., 1] < 1.60) & (P[..., 2] > 0.02) & (dx < 0.05) \
    & skinlike(head) & skinlike(body)
Q = np.linspace(0, 100, 257)
levels = np.arange(256, dtype=np.float32)
curves = []
for c in range(3):
    qh = wpercentile(head[front, c], weight[front], Q)
    qb = wpercentile(body[front, c], weight[front], Q)
    qh = np.maximum.accumulate(qh + np.arange(len(qh)) * 1e-4)
    curves.append(np.clip(np.interp(levels, qh, qb), 0, 255))
head_m = np.stack([np.interp(head[..., c], levels, curves[c]) for c in range(3)], -1)
report['skin_match'] = {'texels': int(front.sum()),
                        'head_paint': np.round(np.average(head[front], 0, weight[front]), 1).tolist(),
                        'body_paint': np.round(np.average(body[front], 0, weight[front]), 1).tolist(),
                        'head_mapped': np.round(np.average(head_m[front], 0, weight[front]), 1).tolist()}
# the curve is for skin (all of it, so no chart keeps the head paint's grey-green shading); brows and the scalp keep the
# head paint's colours (the curve turned dark brown brows olive)
brow_zone = (P[..., 1] > 1.568) & (P[..., 1] < 1.592) & (dx < 0.058) & (P[..., 2] > 0.015)
brows = brow_zone & ndimage.binary_dilation(head.mean(-1) < 125, iterations=1)    # the dark brow hair itself
# (padded before the blur: a blur over the empty gutters left each chart's rim unmapped, a thin dark line on every seam)
skin_w = ndimage.gaussian_filter(texlib.pad((skin_piece & ~brows).astype(np.float32)
                                            * (1 - smoothstep(P[..., 1], 1.598, 1.606)), cov), 1.0)
head_t = head * (1 - skin_w[..., None]) + head_m * skin_w[..., None]
paint = body * (1 - hw[..., None]) + head_t * hw[..., None]
paint = texlib.pad(paint, cov)

# ---------------------------------------------------------------- 3. one broad skin tone
# The two paints' skin differs in broad tone from place to place (the body paint's neck and jaw sides carry a brown
# shadow, the head paint grey-green shading under the eyes and above the lip, the hands are paler). The broad colour
# is measured on the welded mesh, not per UV island (a per-island blur differs on the two sides of a chart seam and drew
# every seam as a line): per triangle the mean linear colour of its skin texels, per vertex the mean of its triangles,
# then smoothed over the mesh (normalised: lips and brows contribute nothing), and per texel interpolated by its
# barycentrics, so it is continuous across seams. Chroma is pulled at EVEN_CHROMA_M of surface (the grey-green
# patches), luminance at EVEN_M (broad tone only, shading of the form stays), geometrically towards the face's colour.
lips = (((dx / 0.026) ** 2 + ((P[..., 1] - 1.5125) / 0.0085) ** 2) < 1) & (P[..., 2] > 0.03)
lin_paint = R.srgb_to_linear(np.clip(paint, 0, 255) / 255).astype(np.float32)
even_src = cov & skin_piece & ~lips & ~brows & (P[..., 1] < 1.600)
face_ref = even_src & (piece == 0) & (P[..., 1] > 1.49) & (P[..., 1] < 1.60) & (P[..., 2] > 0.02) & (dx < 0.05) \
    & skinlike(paint)
T = np.average(lin_paint[face_ref], 0, weight[face_ref])
lum_lin = lin_paint @ LUMA
chroma = lin_paint / np.maximum(lum_lin, 1e-4)[..., None]
T_lum = float(T @ LUMA)
T_chroma = T / T_lum
ntri = len(tri)
wsrc = (weight * even_src)[cov]
tw = np.bincount(t, wsrc, minlength=ntri)
feats = np.concatenate([chroma[cov], lum_lin[cov][:, None]], 1)
tsum = np.stack([np.bincount(t, wsrc * feats[:, c], minlength=ntri) for c in range(4)], 1)
wtri = weld[tri]
vw = np.zeros(nweld)
vs = np.zeros((nweld, 4))
for k in range(3):
    np.add.at(vw, wtri[:, k], tw)
    np.add.at(vs, wtri[:, k], tsum)
edges = np.unique(np.sort(np.concatenate([wtri[:, [0, 1]], wtri[:, [1, 2]], wtri[:, [2, 0]]]), 1), axis=0)
wpos = np.zeros((nweld, 3))
wpos[weld] = pos
edge_len = float(np.median(np.linalg.norm(wpos[edges[:, 0]] - wpos[edges[:, 1]], axis=1)[
    np.isin(edges[:, 0], np.unique(wtri[pieces['piece'] == 0]))]))


def smooth(num, den, scale):
    """Normalised diffusion over the mesh edges, about `scale` metres."""
    n = max(1, int(round((scale / edge_len) ** 2)))
    deg = np.bincount(edges.ravel(), minlength=nweld).astype(float)
    for _ in range(n):
        nn = num.copy()
        dd = den.copy()
        np.add.at(nn, edges[:, 0], num[edges[:, 1]])
        np.add.at(nn, edges[:, 1], num[edges[:, 0]])
        np.add.at(dd, edges[:, 0], den[edges[:, 1]])
        np.add.at(dd, edges[:, 1], den[edges[:, 0]])
        num, den = nn / (1 + deg)[:, None], dd / (1 + deg)
    return num / np.maximum(den, 1e-12)[:, None], n


low_c, it_c = smooth(vs[:, :3], vw, EVEN_CHROMA_M)
low_l, it_l = smooth(vs[:, 3:], vw, EVEN_M)
bc = bary[cov]
tex_c = (low_c[wtri[t]] * bc[:, :, None]).sum(1)
tex_l = (low_l[wtri[t]] * bc[:, :, None]).sum(1)[:, 0]
strength = np.where(piece == 0, EVEN_BODY - (EVEN_BODY - EVEN_FACE) * smoothstep(P[..., 1], jaw + 0.02, jaw + 0.05),
                    EVEN_HANDS)[cov]
apply = skin_piece[cov] & ~brows[cov]
ratio_c = (T_chroma[None, :] / np.maximum(tex_c, 1e-4)) ** strength[:, None]
ratio_l = (T_lum / np.maximum(tex_l, 1e-4)) ** strength
new = lin_paint[cov] * ratio_c * ratio_l[:, None]
# the chroma ratio keeps the luminance
new = new / np.maximum((new @ LUMA) / np.maximum(lum_lin[cov] * ratio_l, 1e-6), 1e-6)[:, None]
evened = lin_paint.copy()
vals = evened[cov]
vals[apply] = new[apply]
evened[cov] = vals

# grey-green texels on the face skin (the head paint's shading under the eyes, beside the nose and above the lip) are
# smaller than the mesh resolution of the broad pass: each takes the face's skin chroma (0.8), keeping its luminance
hh = np.asarray(Image.fromarray(np.clip(enc(evened) * 255, 0, 255).astype(np.uint8)).convert('HSV'), np.float32)
deg, sat_e = hh[..., 0] * 360 / 255, hh[..., 1] / 255
dull = cov & (piece == 0) & (P[..., 1] > jaw) & (P[..., 1] < 1.600) & ~lips & ~brows & (P[..., 2] > -0.03) \
    & (((deg > 38) & (deg < 200)) | (sat_e < 0.2))
dull_w = ndimage.gaussian_filter(texlib.pad(dull.astype(np.float32), cov), 1.0) * 0.8 * (piece == 0)
lum_e = evened @ LUMA
evened = evened * (1 - dull_w[..., None]) + (T_chroma[None, None, :] * lum_e[..., None]) * dull_w[..., None]
report['dull_texels'] = int(dull.sum())
# below the jaw (body paint: a yellow-brown cast finer than the mesh) each neck and chest skin texel takes NECK_CHROMA
# of the face's skin chroma, luminance kept, fading out over the crossfade so the head paint's face is untouched
neck_w = (NECK_CHROMA * (1 - smoothstep(P[..., 1], jaw + 0.004, jaw + 0.024)) * (piece == 0) * cov).astype(np.float32)
lum_e = evened @ LUMA
evened = evened * (1 - neck_w[..., None]) + (T_chroma[None, None, :] * lum_e[..., None]) * neck_w[..., None]
# the top of the forehead under the hair fringe: the head paint has dark olive roots there; it takes the face's skin
# colour just below (forehead under the brows' height) with the paint's luminance detail, up to the scalp (step 5), so
# no band shows between brow and hair
band = cov & (piece == 0) & (P[..., 2] > -0.03)
# the visible forehead reaches rest height 1.622-1.626 at the front, under the hair fringe; the scalp starts there
scalp_lift = (0.015 * smoothstep(P[..., 2], 0.0, 0.03)).astype(np.float32)
bw = (smoothstep(P[..., 1], 1.590, 1.600) * band).astype(np.float32)
below = band & (P[..., 1] > 1.570) & (P[..., 1] < 1.592) & ~brows
lum_low = ndimage.gaussian_filter(texlib.pad(lum_e, cov), 3.0)
detail = np.clip(lum_e / np.maximum(lum_low, 1e-4), 0.9, 1.1)
# the forehead's own colour carried up over the mesh (normalised diffusion from the skin below), so the top of the
# forehead continues it with no step
wb = (weight * below)[cov]
tsum_b = np.stack([np.bincount(t, wb * evened[cov][:, c], minlength=ntri) for c in range(3)], 1)
tw_b = np.bincount(t, wb, minlength=ntri)
vw_b = np.zeros(nweld)
vs_b = np.zeros((nweld, 3))
for k in range(3):
    np.add.at(vw_b, wtri[:, k], tw_b)
    np.add.at(vs_b, wtri[:, k], tsum_b)
low_b, _ = smooth(vs_b, vw_b, 0.03)
carried = np.zeros_like(evened)
carried[cov] = (low_b[wtri[t]] * bc[:, :, None]).sum(1)
evened = evened * (1 - bw[..., None]) + (carried * detail[..., None]) * bw[..., None]
report['even'] = {'edge_mm': round(edge_len * 1000, 2), 'iterations_chroma': it_c, 'iterations_lum': it_l}
# pale blond strokes the head paint laid over the ears and temples (hair it drew falling over them; the hair pieces sit
# behind): those texels take the nearest skin-coloured texel, so no light streak shows on the ears of any tier
cur = np.clip(enc(evened), 0, 1) * 255
hv = np.asarray(Image.fromarray(cur.astype(np.uint8)).convert('HSV'), np.float32)
ear_zone = cov & (piece == 0) & (P[..., 1] > 1.515) & (P[..., 1] < 1.625) & (np.abs(P[..., 0] - X0) > 0.045) \
    & (P[..., 2] < 0.01)
streak = ear_zone & (hv[..., 1] < 85) & (hv[..., 2] > 195)          # paler and less saturated than the ear skin
streak = ndimage.binary_dilation(streak, iterations=1) & ear_zone
good = cov & ~streak & skinlike(cur) & (piece == 0)
filled = texlib.pad(cur, good)
sw = ndimage.gaussian_filter(streak.astype(np.float32), 0.8)
cur = cur * (1 - sw[..., None]) + filled * sw[..., None]
report['ear_streak_texels'] = int(streak.sum())
paint = texlib.pad(cur, cov)
report['skin_target_srgb'] = np.round(enc(T) * 255, 1).tolist()
raw_path = f'{out}_raw.png'
save(paint, raw_path)

# ---------------------------------------------------------------- 4. gentle grade
subprocess.run([sys.executable, str(HERE.parent / 'claude_shared' / 'grade_basecolor.py'), '--ao',
                str(HERE / 'textures' / 'm362_tp_ao_2k.png'), '--fine', '1.0', '--local', '0.3', '--ao-strength', '0.5',
                '--contrast', '1.06', '--saturation', '1.15', raw_path], check=True)
graded = np.asarray(Image.open(f'{out}_raw_graded.png').convert('RGB'), np.float32)
graded = texlib.pad(graded, cov)

# ---------------------------------------------------------------- 5. region mask
h = np.asarray(Image.fromarray(graded.astype(np.uint8)).convert('HSV'), np.float32)
hue, sat, val = h[..., 0] * 360 / 255, h[..., 1] / 255, h[..., 2] / 255
violet = (hue > 205) & (hue < 300) & (sat > 0.2)
white = (sat < 0.22) & (val > 0.45)
vest_pieces = np.isin(piece, [4, 8, 9, 12])
vest = cov & vest_pieces & (violet | ((sat > 0.15) & ~white & (hue > 190) & (hue < 320)))
# violet paint outside the doublet pieces (shoulder-roll undersides, the doublet edge painted onto the shirt): only the
# doublet is violet on this figure, so any clearly violet texel off the skin and hair recolours with it
vest |= cov & ~np.isin(piece, [0, 1, 2]) & (garment != 3) & (hue > 215) & (hue < 300) & (sat > 0.3) & (val > 0.12)
hair = cov & (garment == 3)
# the head paint draws the hairline and a few loose locks onto the scalp skin: hair-coloured skin texels above the
# eyes or behind the ears join the hair region, so no blond fringe stays on the other tiers
hairlike = cov & (piece == 0) & (hue > 25) & (hue < 95) & (sat > 0.12) \
    & ((P[..., 1] > 1.592) | ((P[..., 2] < -0.005) & (P[..., 1] > 1.52))) & ~skinlike(graded)
hair |= hairlike
report['hairline_texels'] = int(hairlike.sum())
# the scalp above the forehead hairline (rest height 1.611-1.619, at the front 1.626-1.634) shows in the gaps of the
# hair pieces: the head paint has it as a dark olive root band and brown skin, which every tier showed as a dark wedge.
# It takes the hair's median colour with the paint's luminance detail and joins the hair region.
scalp = np.where(piece == 0, smoothstep(P[..., 1] - scalp_lift, 1.611, 1.619), 0.0).astype(np.float32) * cov
hair_col = np.median(graded[hair & (garment == 3)], 0)
lum8 = graded @ LUMA
local = ndimage.gaussian_filter(lum8, 4.0)
detail = np.clip(lum8 / np.maximum(local, 1.0), 0.75, 1.25)[..., None]
graded = graded * (1 - scalp[..., None]) + (hair_col[None, None, :] * detail) * scalp[..., None]
report['scalp_texels'] = int((scalp > 0.5).sum())


def noise3(p, cell, seed):
    """Value noise at points p (n, 3) with an anisotropic cell (3,) in metres, trilinear."""
    q = p / cell
    i = np.floor(q).astype(np.int64)
    f = q - i
    f = f * f * (3 - 2 * f)
    total = np.zeros(len(p), np.float32)
    for corner in range(8):
        o = np.array([(corner >> k) & 1 for k in range(3)])
        k = i + o
        hsh = (k[:, 0] * 73856093) ^ (k[:, 1] * 19349663) ^ (k[:, 2] * 83492791) ^ (seed * 2654435761)
        hsh = (hsh ^ (hsh >> 13)) * 1274126177
        v = ((hsh ^ (hsh >> 16)) & 0xFFFF) / 65535.0
        wgt = np.prod(np.where(o, f, 1 - f), 1)
        total += (v * wgt).astype(np.float32)
    return total


# beard shape at rest (glTF metres, face +z), the native full short beard: moustache under the nose tapering around
# the mouth corners into the chin, the jaw to the sideburns in front of the ears, under the chin; lips and cheeks clear
Pc = P[cov]
ax = np.abs(Pc[:, 0] - X0)
y, z = Pc[:, 1], Pc[:, 2]
upper = 1.5215 - smoothstep(ax, 0.018, 0.034) * 0.017 + smoothstep(0.035 - z, 0.0, 0.06) * 0.05
# the moustache covers the whole upper lip up to the nose, but not the nose's underside (facing down)
upper += np.where(N[cov][:, 1] > -0.45, 0.003 * (1 - smoothstep(ax, 0.014, 0.024)), 0.0)
lower = 1.462 + np.clip(0.02 - z, 0, None) * 0.6
# the moustache band on the upper lip is only 3-5 mm tall: a short top feather there, so it is not all thin edge
top_feather = np.where((z > 0.03) & (ax < 0.026), 0.0022, 0.006)
shape = (smoothstep(upper - y, -0.001, top_feather) * smoothstep(y - lower, 0.0, 0.008)
         * smoothstep(z + 0.024, 0.0, 0.008) * smoothstep(0.060 - ax, 0.0, 0.006))
lower_face = shape * (piece[cov] == 0)                 # before the lip cut: the lower face for face_features.py
lip = ((ax / 0.026) ** 2 + ((y - 1.5122) / 0.0068) ** 2)
shape *= np.where(z > 0.03, smoothstep(lip, 1.0, 1.7), 1.0)
shape *= (piece[cov] == 0)
strands = (0.6 * noise3(Pc, np.array([0.0011, 0.006, 0.0011]), 1)
           + 0.4 * noise3(Pc, np.array([0.0006, 0.0035, 0.0006]), 2))
# density, not opacity, fades at the edge: the core is nearly solid, the edge thins to single strands
beard_v = np.clip((strands - (1 - shape) * 0.7 - 0.22) / 0.28, 0, 1) * np.clip(shape * 4, 0, 1)
beard = np.zeros((S, S), np.float32)
beard[cov] = beard_v
shape_map = np.zeros((S, S), np.float32)
shape_map[cov] = shape
lower_map = np.zeros((S, S), np.float32)
lower_map[cov] = lower_face
shape_map = texlib.pad(shape_map, cov)

# No beard on any skin (user, 2026-11-01): the beard shape stays only to fit the (unused) beard ramps and to mark the
# lower face for face_features.py; its mask coverage is written as zero and the base colour keeps the clean skin.
save(graded, f'{out}_basecolor.png')
graded = np.asarray(Image.open(f'{out}_basecolor.png').convert('RGB'), np.float32)
base01 = graded / 255


def soft(mask):
    return ndimage.gaussian_filter(texlib.pad(mask.astype(np.float32), cov), 0.7)


masks = [soft(vest), np.maximum(soft(hair), texlib.pad(scalp, cov)), np.zeros((S, S), np.float32)]
R.write_mask(masks, f'{out}_region_mask.png', size=S)
mask_check = np.stack([np.asarray(ch, np.float32) / 255 for ch in Image.open(f'{out}_region_mask.png').split()], -1)

# ---------------------------------------------------------------- 6. ramps
def pal(i):
    return np.frombuffer(open(PALDIR / f'pal{i:03d}.act', 'rb').read()[:768], np.uint8).reshape(256, 3) \
        .astype(np.float64) / 255


VJ = json.load(open(HERE.parent / 'mm7_m362' / 'variants.json'))
P363 = (pal(363) * 255).astype(int)
purple = [k for k in range(150, 241) if P363[k][2] > P363[k][0] + 10 and P363[k][2] > P363[k][1] + 10
          and max(np.abs((pal(p) * 255).astype(int)[k] - P363[k]).sum() for p in VARIANTS.values()) > 20]
REGION_IDX = {'vest': sorted(set(VJ['regions'][0]['palette_indices']) | set(purple)), 'hair': list(range(96, 118)),
              'beard': list(range(76, 94))}
GAIN = {'vest': 1.3, 'hair': 1.2, 'beard': 1.1}
QWIN = {'vest': (0.35, 0.97), 'hair': (0.15, 0.99), 'beard': (0.08, 0.72)}   # beard: the bright chin skin read grey
LUT = {tuple(c): i for i, c in enumerate(P363)}
IDX = []
for f in sorted(p for p in NATIVE.glob('m362*.png') if p.name[4] in 'sw'):
    a = np.asarray(Image.open(f).convert('RGBA'))
    IDX.append(np.array([LUT.get(tuple(c), -1) for c in a[a[..., 3] > 0][:, :3].astype(int)]))
IDX = np.concatenate(IDX)
lum = R.luminance(base01)


def native_ramps(reg, sel):
    texel = lum[sel]
    lo, hi = np.percentile(texel, [2, 98])
    srt = np.sort(texel)
    ids = IDX[np.isin(IDX, REGION_IDX[reg])]
    ramps = {}
    for k, p in VARIANTS.items():
        X = pal(p)[ids]
        L = R.luminance(X)
        X = X[np.argsort(L)]
        cols = []
        for i in range(16):
            q = np.searchsorted(srt, lo + (hi - lo) * i / 15) / len(srt)
            q = QWIN[reg][0] + (QWIN[reg][1] - QWIN[reg][0]) * q
            c = X[min(len(X) - 1, int(q * (len(X) - 1)))]
            cols.append([round(float(v), 6) for v in np.clip(R.srgb_to_linear(np.clip(c * GAIN[reg], 0, 1)), 0, 1)])
        ramps[k] = {'range': [round(float(lo), 5), round(float(max(hi, lo + 1e-3)), 5)], 'colors': cols}
    return ramps


RAMPS = {'vest': native_ramps('vest', cov & (masks[0] > 0.5)), 'hair': native_ramps('hair', cov & (masks[1] > 0.5))}
core = cov & (texlib.pad(beard, cov) > 0.25)
beard_native = native_ramps('beard', core)
shaven, fit = R.fit_ramps(base01, {k: base01 for k in VARIANTS if k not in BEARDED},
                          np.where(core, 1.0, 0.0), core_threshold=0.5)
lo, hi = shaven[next(iter(shaven))]['range']
beard_native = {k: v for k, v in beard_native.items()}
for k in BEARDED:                                                    # same luminance range as the shaven fit
    stops = lo + (hi - lo) * np.arange(16) / 15
    old_lo, old_hi = beard_native[k]['range']
    tt = np.clip((stops - old_lo) / (old_hi - old_lo), 0, 1) * 15
    cols = np.array(beard_native[k]['colors'])
    i0 = np.minimum(tt.astype(int), 14)
    fr = (tt - i0)[:, None]
    beard_native[k] = {'range': [lo, hi], 'colors': np.round(cols[i0] * (1 - fr) + cols[i0 + 1] * fr, 6).tolist()}
RAMPS['beard'] = {k: (beard_native[k] if k in BEARDED else shaven[k]) for k in VARIANTS}
report['beard_fit_shaven'] = fit


def apply_ramp(rp, lum_lin):
    tt = np.clip((lum_lin - rp['range'][0]) / (rp['range'][1] - rp['range'][0]), 0, 1) * 15
    cols = np.array(rp['colors'])
    i0 = np.minimum(tt.astype(int), 14)
    fr = (tt - i0)[..., None]
    return cols[i0] * (1 - fr) + cols[i0 + 1] * fr


# The doublet: the 4K paint's cloth sits higher in its luminance range than the approved paint's, so the same native
# rank matching came out about 20 % brighter. Each skin's doublet ramp is pinned to the installed doublet as the engine
# showed it at the same surface points (linear mean gain; spread at most PIN_SPREAD x the installed one).
from glb import Glb  # noqa: E402
installed = Glb(W / 'before_texpass' / 'mm7_m362.glb')
appr_base = R.srgb_to_linear(np.asarray(Image.open(W / 'approved_fine_basecolor.png').convert('RGB'), np.float64) / 255)
appr_mask = np.asarray(Image.open(W / 'approved_fine_region_mask.png').getchannel('R').resize((S, S)), np.float32) / 255
both_vest = cov & (appr_mask > 0.5) & (masks[0] > 0.5)
wv = weight[both_vest]
lum_new = R.srgb_to_linear(base01[both_vest]) @ LUMA.astype(np.float64)
lum_old = appr_base[both_vest] @ LUMA.astype(np.float64)
report['doublet_pin'] = {}
for k in VARIANTS:
    mat = next(m for m in installed.doc['materials'] if m['name'] == 'M362_' + k[-2:].upper())
    old_c = apply_ramp(mat['extras']['openyamm_region_ramps'][0], lum_old)
    new_c = apply_ramp(RAMPS['vest'][k], lum_new)
    o_l, n_l = old_c @ LUMA, new_c @ LUMA
    gain = float(np.average(o_l, weights=wv) / np.average(n_l, weights=wv))
    sd_o = np.sqrt(np.average((o_l - np.average(o_l, weights=wv)) ** 2, weights=wv))
    sd_n = np.sqrt(np.average((n_l * gain - np.average(n_l * gain, weights=wv)) ** 2, weights=wv))
    kc = float(min(1.0, PIN_SPREAD * sd_o / max(sd_n, 1e-6)))
    cols = np.array(RAMPS['vest'][k]['colors']) * gain
    mid = np.average(new_c * gain, 0, weights=wv)
    cols = np.clip(mid + kc * (cols - mid), 0, 1)
    RAMPS['vest'][k] = {'range': RAMPS['vest'][k]['range'], 'colors': np.round(cols, 6).tolist()}
    report['doublet_pin'][k] = {'gain': round(gain, 3), 'contrast': round(kc, 3)}
REGIONS = ['vest', 'hair', 'beard']
ramps = {k: [RAMPS[reg][k] for reg in REGIONS] for k in VARIANTS}
json.dump({'variants': list(VARIANTS), 'regions': REGIONS, 'bearded': list(BEARDED), 'palettes': VARIANTS,
           'ramps': ramps}, open(f'{out}_ramps.json', 'w'), indent=1)

# ---------------------------------------------------------------- 7. normal, 8. metal/roughness
normals = []
for src in ('body', 'head'):
    n = load(M / f'{src}_retexture_v2' / 'texture_urls_0_normal.png',
             inside=inside_body if src == 'body' else inside_head) / 127.5 - 1
    n[..., 1] *= -1                                                   # Meshy +y down -> glTF +y up
    normals.append(n)
n = normals[0] * (1 - hw[..., None]) + normals[1] * hw[..., None]
n[..., :2] *= 0.3
n[..., 2] = np.sqrt(np.clip(1 - (n[..., :2] ** 2).sum(-1), 0.0025, 1))
n /= np.linalg.norm(n, axis=-1, keepdims=True)
n = texlib.pad(n, cov)
Image.fromarray(np.clip((n + 1) * 127.5 + 0.5, 0, 255).astype(np.uint8)).save(f'{out}_normal.png')
shutil.copyfile(W / 'approved_fine_metal_rough.png', f'{out}_metal_rough.png')
report['regions'] = {'vest': int(vest.sum()), 'hair': int(hair.sum()), 'beard_core': int(core.sum())}
json.dump(report, open(f'{out}_report.json', 'w'), indent=1)
np.savez_compressed(f'{out}_texels.npz', P=P.astype(np.float16), piece=piece.astype(np.int16), hw=hw.astype(np.float16),
                    lower_face=lower_map.astype(np.float16))
print('COMPOSED', out, json.dumps(report)[:2000])
