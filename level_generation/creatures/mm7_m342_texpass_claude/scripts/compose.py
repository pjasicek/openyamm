"""Texture-pass maps of m342 from the two 4K Meshy paints on the layout (work/uv_cc4_fine.npz), with one continuous
skin tone (user review 2026-11-01: patches and seams in different skin tones on the face, flat smeared hair).

1. Paint, 4K -> 2K once (Lanczos). Head paint (four close head views) on the head-set pieces (hair strands, eyes,
   mouth) and on the skin shell above the neck, crossfaded into the body paint over y HEAD_LO..HEAD_HI on the shell.
   Shell texels where either paint is not skin (straps, blouse: the head views have no straps) keep the body paint.
2. Classes per texel (piece + colour, the production rules of mm7_m342_claude/scripts/compose_m342.py): dress (green
   on the shell and the bodice/skirt), linen (white), brass, leather, hair (the hair pieces, and the shell's crown where
   the hair cap leaves gaps), eye/mouth detail pieces, earring, legs, skin (the rest of the shell and the hands).
3. Hair fixes: the gold earring paint Meshy smeared on strands by the ears, pale and skin-coloured specks and the
   unpainted crown are filled from the surrounding hair (normalised Gaussian), keeping their luminance detail.
   Hair paint on the neck below NAPE_Y (Meshy projected the hanging hair onto the nape) and the gold of the
   unmodelled left earring painted on the cheek are filled from the skin.
   The hidden legs keep the approved flat stocking colour.
4. Grade (TEXTURE_QUALITY_PASS.md gentle grade, inline): fine 1.0, local 0.3 at 16 texels, contrast 1.06,
   saturation 1.15, then AO x0.5.
5. Skin: one tone. Each welded vertex takes the area-weighted mean of the skin-hue texels around it within a 3D
   Gaussian (before the AO multiply); texels interpolate it from their triangle's vertices, so the field is continuous
   across UV seams, the head/body crossfade and the hand shells. Skin texels are multiplied (linear RGB) by the
   approved skin colour over the field: luminance from a SKIN_SIGMA field, hue and saturation from a tighter
   CHROMA_SIGMA one; the finer hue/saturation deviation that is left is scaled by CHROMA_KEEP (not on the lips).
   Patches larger than about the sigma take the approved skin colour; the paint keeps its shading detail below it
   (lips, brows, nostrils, creases) and the AO. Then the skin's UV seams: both sides of each seam move halfway to
   the other side's colour, faded into their own chart over SEAM_SIGMA texels.
6. Dress and hair (the ramp regions): per-channel quantile curves onto the approved region's distribution, so the
   approved ramps and their luminance ranges hold. Linen, leather and brass: the same per class.
7. Region mask (R dress, G hair) and metal/roughness (production specular/roughness table, Meshy roughness detail)
   from the classes at 1024; normal from the paints (+y down -> glTF +y up), full strength like the approved build.

Usage: compose.py <out prefix> [skin sigma m 0.025] [chroma sigma m 0.012]
Writes <out prefix>_{basecolor,normal,metal_rough,region_mask,material_classes,classes_preview}.png, <out>_report.json
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import texlib  # noqa: E402
import texels  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import texture_quality as TQ  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
M = HERE / 'meshy'
out = sys.argv[1]
SKIN_SIGMA = float(sys.argv[2]) if len(sys.argv) > 2 else 0.025
CHROMA_SIGMA = float(sys.argv[3]) if len(sys.argv) > 3 else 0.012
CHROMA_KEEP = 0.5
SEAM_IN, SEAM_SIGMA = 1.5, 5.0
S = 2048
HEAD_LO, HEAD_HI = 1.33, 1.43
NAPE_Y = 1.56
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)
DETAIL_PIECES = [20, 21, 22, 23, 24, 25, 30, 31, 32]      # eyes, lids, lashes, mouth (y 1.52-1.61, front)
EARRING = 12
SHELL, LEGS, HANDS = 1, 4, (0, 41)
CLASS = {'skin': 1, 'hair': 2, 'eye': 6, 'dress': 8, 'linen': 8, 'leather': 8, 'brass': 9}
SPEC = {'skin': 0.45, 'hair': 0.3, 'dress': 0.2, 'linen': 0.2, 'leather': 0.35, 'brass': 1.0, 'eye': 0.9}
ROUGH = {'skin': 0.5, 'hair': 0.6, 'dress': 0.88, 'linen': 0.85, 'leather': 0.6, 'brass': 0.3, 'eye': 0.2}
PREVIEW = {'skin': (230, 140, 120), 'hair': (40, 60, 230), 'dress': (30, 200, 40), 'linen': (240, 240, 240),
           'leather': (90, 50, 20), 'brass': (250, 210, 0), 'eye': (230, 0, 230)}


def lin(c):
    c = np.asarray(c, np.float32) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    c = np.clip(c, 0, 1)
    return (np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055) * 255).astype(np.float32)


def load(path, size=S, mode='RGB'):
    img = Image.open(path).convert(mode)
    if img.size != (size, size):
        img = img.resize((size, size), Image.Resampling.LANCZOS)
    return np.asarray(img, np.float32)


def hsv(rgb):
    h = np.asarray(Image.fromarray(np.clip(rgb + 0.5, 0, 255).astype(np.uint8)).convert('HSV'), np.float32) / 255
    return h[..., 0] * 360, h[..., 1], h[..., 2]


def wpercentile(v, w, q):
    o = np.argsort(v)
    c = np.cumsum(w[o])
    c /= c[-1]
    return np.interp(q / 100, c, v[o])


def masked_blur(img, mask, sigma):
    m = mask.astype(np.float32)
    den = ndimage.gaussian_filter(m, sigma)
    num = np.stack([ndimage.gaussian_filter(img[..., c] * m, sigma) for c in range(img.shape[-1])], -1)
    return num / np.maximum(den, 1e-6)[..., None], den


T = texels.load()
cov, pos, piece = T['cov'], T['pos'], T['piece']
x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]
lay = np.load(HERE / 'work' / 'uv_cc4_fine.npz')
before = np.load(HERE / 'work' / 'lod0_before.npz')
tri_id, bary = T['tri_id'], T['bary']
t = np.maximum(tri_id, 0)
uv, xyz = lay['uv'], lay['xyz']
area3 = np.linalg.norm(np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]), axis=1) / 2
area2 = np.abs((uv[:, 1, 0] - uv[:, 0, 0]) * (uv[:, 2, 1] - uv[:, 0, 1])
               - (uv[:, 2, 0] - uv[:, 0, 0]) * (uv[:, 1, 1] - uv[:, 0, 1])) / 2
texel_area = np.where(cov, (area3 / np.maximum(area2, 1e-12))[t] / S ** 2, 0).astype(np.float32)   # m^2 per texel
report = {'skin_sigma_m': SKIN_SIGMA, 'chroma_sigma_m': CHROMA_SIGMA}

# ---- 1. paint
body = load(M / 'body_retexture_tp' / 'texture_urls_0_base_color.png')
head = load(M / 'head_retexture_tp' / 'texture_urls_0_base_color.png')


def skinlike(img):
    h, s, v = hsv(img)
    return ((h < 40) | (h > 340)) & (s > 0.15) & (s < 0.7) & (v > 0.4)


shell = cov & (piece == SHELL)
hw = np.where(T['head'] & (piece != SHELL), 1.0, 0.0).astype(np.float32)
ramp_y = np.clip((y - HEAD_LO) / (HEAD_HI - HEAD_LO), 0, 1)
ramp_y = ramp_y * ramp_y * (3 - 2 * ramp_y)
both = ndimage.gaussian_filter((skinlike(body) & skinlike(head)).astype(np.float32), 1.5)
hw[shell] = (ramp_y * np.where(y < 1.50, both, 1.0))[shell]
hw = np.clip(np.nan_to_num(hw), 0, 1)
paint = body * (1 - hw[..., None]) + head * hw[..., None]
paint = texlib.pad(paint, cov)
Image.fromarray(np.clip(paint + 0.5, 0, 255).astype(np.uint8)).save(f'{out}_raw.png')

# ---- 2. classes
h, s, v = hsv(paint)
C = {}
C['eye'] = cov & np.isin(piece, DETAIL_PIECES)
earring = cov & (piece == EARRING)
legs = cov & T['leg']
face = (z > 0.06) & (y > 1.47) & (y < 1.625) & (np.abs(x) < 0.07)
crown = shell & (y > 1.60) & ~face & ~skinlike(paint)  # unpainted top of the scalp between the strands
darkhair = (v < 0.5) & ((h < 45) | (h > 340)) & (s > 0.2)
scalp = shell & (y > NAPE_Y) & ~face & darkhair         # hair painted on the shell under the strands
scalp = ndimage.binary_opening(scalp, iterations=1) | crown
nape = shell & (y > 1.40) & (y <= NAPE_Y) & ~face & darkhair   # hair paint on the neck: skin again (step 3)
nape = ndimage.binary_dilation(nape, iterations=2) & shell & (y <= NAPE_Y + 0.01) & ~face
C['hair'] = (cov & T['head'] & (piece != SHELL) & ~C['eye'] & ~earring) | scalp
green = (h > 70) & (h < 175) & (s > 0.18)
white = (s < 0.2) & (v > 0.45)
gold = (h > 32) & (h < 66) & (s > 0.4) & (v > 0.4)
C['brass'] = cov & (np.isin(piece, [2, 7, 37, 38, 39, 40]) & gold | earring)
ear_gold = shell & (y > 1.45) & (h > 32) & (h < 66) & (s > 0.3) & (v > 0.4)
ear_gold = ndimage.binary_dilation(ear_gold, iterations=4) & shell                  # unmodelled left earring
nape |= ear_gold
C['dress'] = cov & (np.isin(piece, [SHELL, 2]) & green | (piece == 3) & ~white) & ~C['brass'] & ~scalp
C['linen'] = cov & np.isin(piece, [SHELL, 2, 3, *HANDS]) & white & ~C['dress'] & ~C['brass'] & ~scalp
C['leather'] = cov & (np.isin(piece, [2, 7, 37, 38, 39, 40, LEGS]) & ~legs) & ~C['dress'] & ~C['brass'] & ~C['linen']
taken = np.any([m for m in C.values()], axis=0)
C['skin'] = cov & ~taken & ~legs & (np.isin(piece, [SHELL, *HANDS]))
C['leather'] |= cov & ~taken & ~legs & ~C['skin']
report['classes'] = {k: int(m.sum()) for k, m in C.items()}

# ---- 3. hair fixes, legs
outlier = C['hair'] & ~crown & (gold | ((s < 0.22) & (v > 0.45)) | skinlike(paint) & (v > 0.6))
bad = outlier | crown
bad = ndimage.binary_dilation(bad, iterations=2) & C['hair']
good = C['hair'] & ~bad
fill, den = masked_blur(paint, good, 10.0)
for sigma in (24.0, 64.0):                       # wider where the narrow fill found nothing
    wide, wden = masked_blur(paint, good, sigma)
    fill = np.where((den < 0.02)[..., None], wide, fill)
    den = np.maximum(den, wden)
lum = paint @ LUMA
blum, _ = masked_blur(lum[..., None], bad, 6.0)
detail = np.clip((lum / np.maximum(blum[..., 0], 1)) ** 0.6, 0.75, 1.3)
detail[crown] = 1.0
paint[bad] = (fill * detail[..., None])[bad]
report['hair_fixed_texels'] = int(bad.sum())
skin_good = shell & skinlike(paint) & ~nape & (y > 1.35)
fill, den = masked_blur(paint, skin_good, 10.0)
for sigma in (24.0, 64.0):
    wide, wden = masked_blur(paint, skin_good, sigma)
    fill = np.where((den < 0.02)[..., None], wide, fill)
    den = np.maximum(den, wden)
paint[nape] = fill[nape]
report['nape_fixed_texels'] = int(nape.sum())
approved = np.asarray(Image.open(HERE / 'work' / 'approved_fine_basecolor.png').convert('RGB'), np.float32)
paint[legs] = approved[legs]
paint = texlib.pad(paint, cov)

# ---- 4. grade (no AO yet)
ao = np.asarray(Image.open(HERE / 'textures' / 'm342_tp_ao_2k.png').convert('L'), np.float32) / 255
ao = ndimage.gaussian_filter(texlib.pad(ao[..., None], cov & (ao > 0.003))[..., 0], 2.0)
rgb = paint / 255
lum = rgb @ LUMA
blurred = ndimage.gaussian_filter(lum, 16.0)
target = lum + 0.3 * (lum - blurred)
median = float(np.median(lum[cov]))
target = median + 1.06 * (target - median)
rgb = rgb * (np.clip(target, 0, 1) / np.maximum(lum, 1e-4))[..., None]
lum = rgb @ LUMA
rgb = lum[..., None] + 1.15 * (rgb - lum[..., None])
graded = np.clip(rgb, 0, 1) * 255
ao_factor = (1.0 - 0.5 * (1.0 - ao))[..., None]

# ---- 5. one skin tone
weld = before['weld']
tri = before['tri']
wtri = weld[tri]
nweld = int(weld.max()) + 1
skin = C['skin']
glin = lin(graded)
h_r, s_r, v_r = hsv(paint)
# skin hue only: lips (red, under 8 deg) and brows/lashes (dark) would pull the field and tint the skin around them
field_src = skin & (h_r > 8) & (h_r < 40) & (s_r > 0.15) & (s_r < 0.6) & (v_r > 0.5)
report['skin_field_texels'] = int(field_src.sum())
wv = np.zeros(nweld)
cv = np.zeros((nweld, 3))
tt, bb = t[field_src], bary[field_src]
aw = texel_area[field_src]
for k in range(3):
    np.add.at(wv, wtri[tt, k], bb[:, k] * aw)
    np.add.at(cv, wtri[tt, k], (bb[:, k] * aw)[:, None] * glin[field_src])
vpos = np.zeros((nweld, 3))
vpos[weld] = before['pos']
has = wv > 0
tree = cKDTree(vpos[has])
idx_has = np.nonzero(has)[0]


def vertex_field(sigma):
    """Gaussian (3D, sigma m) area-weighted mean of the field-source skin colour around every welded vertex,
    interpolated to every texel from its triangle's vertices (continuous across UV seams)."""
    field = np.zeros((nweld, 3))
    for vi, near in enumerate(tree.query_ball_point(vpos, 3 * sigma)):
        if not near:
            continue
        ids = idx_has[near]
        g = np.exp(-0.5 * ((vpos[ids] - vpos[vi]) ** 2).sum(1) / sigma ** 2) * wv[ids]
        field[vi] = (g[:, None] * (cv[ids] / wv[ids, None])).sum(0) / max(g.sum(), 1e-12)
    empty = np.linalg.norm(field, axis=1) == 0
    if empty.any():
        _, near = cKDTree(vpos[~empty]).query(vpos[empty])
        field[empty] = field[~empty][near]
    return (field[wtri[t]] * bary[..., None]).sum(-2)


field_lum = vertex_field(SKIN_SIGMA)
field_chroma = vertex_field(CHROMA_SIGMA)
appr_skin = cov & skin & skinlike(approved)
target_srgb = np.array([wpercentile(approved[appr_skin, c], texel_area[appr_skin], 50) for c in range(3)])
target_lin = lin(target_srgb)
LIN_W = np.array([0.2126, 0.7152, 0.0722])
# luminance from the wide field, hue/saturation from the tight one
gain = (target_lin @ LIN_W) / np.maximum(field_lum @ LIN_W, 1e-4)
gain = gain[..., None] * (target_lin / (target_lin @ LIN_W)) / np.maximum(
    field_chroma / np.maximum(field_chroma @ LIN_W, 1e-4)[..., None], 1e-4)
gain = np.clip(gain, 0.4, 2.5)
weight = ndimage.gaussian_filter(skin.astype(np.float32), 0.8) * cov
toned_lin = glin * gain
# fine hue/saturation left below the chroma field (greyish or yellowish specks beside the mouth): halve the deviation
# from the target hue, except on the lips
lips = ndimage.binary_dilation(skin & ((h_r < 8) | (h_r > 340)) & (s_r > 0.3), iterations=2)
t_lum = float(target_lin @ LIN_W)
lum_t = np.maximum(toned_lin @ LIN_W, 1e-5)[..., None]
chroma = toned_lin / lum_t
target_c = target_lin / t_lum
squeezed = lum_t * target_c * np.clip(chroma / target_c, 1e-3, None) ** CHROMA_KEEP
lip_w = ndimage.gaussian_filter(lips.astype(np.float32), 1.0)[..., None]
toned_lin = squeezed * (1 - lip_w) + toned_lin * lip_w
skin_lin = glin * (1 - weight[..., None]) + toned_lin * weight[..., None]
result = srgb(skin_lin) * ao_factor
# AO darkens the mean a little: pin the skin median to the approved one
med = np.array([wpercentile(result[skin, c], texel_area[skin], 50) for c in range(3)])
k = lin(target_srgb) / np.maximum(lin(med), 1e-4)
result_lin = lin(result)
result_lin[skin] *= k
result = srgb(result_lin)
report['skin'] = {'target': target_srgb.round(1).tolist(), 'pinned_gain': np.round(k, 3).tolist(),
                  'field_gain_p5_p95': np.percentile(gain[skin], [5, 95], axis=0).round(3).tolist()}


# ---- 5b. skin seams: each side of a UV seam between skin triangles moves halfway to the other side's colour (linear
# RGB, sampled SEAM_IN texels inside each chart along the edge); the offset fades into its own chart over SEAM_SIGMA
def seam_blend(img, sel):
    uvp = uv * S
    edge_of = {}
    for f in np.unique(t[sel]):
        for k in range(3):
            edge_of.setdefault(tuple(sorted((wtri[f, k], wtri[f, (k + 1) % 3]))), []).append((f, k))
    lin_img = lin(img)
    off = np.zeros((S, S, 3), np.float32)
    hits = np.zeros((S, S), np.float32)
    n_edges = 0
    for sides in edge_of.values():
        if len(sides) != 2:
            continue
        (fa, ka), (fb, kb) = sides
        # the same welded edge, possibly in opposite order on the two sides
        va, vb = wtri[fa, ka], wtri[fa, (ka + 1) % 3]
        a0, a1 = uvp[fa, ka], uvp[fa, (ka + 1) % 3]
        b0, b1 = (uvp[fb, kb], uvp[fb, (kb + 1) % 3]) if wtri[fb, kb] == va else (uvp[fb, (kb + 1) % 3], uvp[fb, kb])
        if np.abs(a0 - b0).max() + np.abs(a1 - b1).max() < 1e-3:
            continue                                               # not a seam
        n = int(np.clip(max(np.linalg.norm(a1 - a0), np.linalg.norm(b1 - b0)) / 1.0, 2, 200))
        s_ = np.linspace(0.05, 0.95, n)[:, None]
        pts = []
        for f, p0, p1, k in ((fa, a0, a1, ka), (fb, b0, b1, kb)):
            opp = uvp[f, (k + 2) % 3]
            on = p0 + (p1 - p0) * s_
            mid = (p0 + p1) / 2
            inward = opp - mid
            inward /= max(np.linalg.norm(inward), 1e-6)
            pts.append(on + inward * SEAM_IN)
        ia = np.clip(pts[0].astype(int), 0, S - 1)
        ib = np.clip(pts[1].astype(int), 0, S - 1)
        ok = sel[ia[:, 1], ia[:, 0]] & sel[ib[:, 1], ib[:, 0]]
        if not ok.any():
            continue
        n_edges += 1
        ca = texlib.bilinear(lin_img, pts[0][ok] / S)
        cb = texlib.bilinear(lin_img, pts[1][ok] / S)
        for idx, d in ((ia[ok], (cb - ca) / 2), (ib[ok], (ca - cb) / 2)):
            np.add.at(off, (idx[:, 1], idx[:, 0]), d)
            np.add.at(hits, (idx[:, 1], idx[:, 0]), 1)
    isl = TQ.islands(uv.astype(np.float64), xyz.astype(np.float64))
    _, isl = np.unique(isl, return_inverse=True)
    island_map = np.where(cov, isl[t], -1)
    out = lin_img.copy()
    seed = hits > 0
    for i, sl in enumerate(ndimage.find_objects(island_map + 1)):
        if sl is None:
            continue
        pad_px = int(3 * SEAM_SIGMA) + 2
        y0, y1 = max(sl[0].start - pad_px, 0), min(sl[0].stop + pad_px, S)
        x0, x1 = max(sl[1].start - pad_px, 0), min(sl[1].stop + pad_px, S)
        inside = (island_map[y0:y1, x0:x1] == i) & sel[y0:y1, x0:x1]
        sd = seed[y0:y1, x0:x1] & inside
        if not sd.any():
            continue
        o = off[y0:y1, x0:x1] / np.maximum(hits[y0:y1, x0:x1], 1)[..., None] * sd[..., None]
        num = np.stack([ndimage.gaussian_filter(o[..., c], SEAM_SIGMA) for c in range(3)], -1)
        den = ndimage.gaussian_filter(sd.astype(np.float32), SEAM_SIGMA)
        avg = num / np.maximum(den, 1e-6)[..., None]
        dist = ndimage.distance_transform_edt(~sd)
        fade = np.exp(-0.5 * (dist / SEAM_SIGMA) ** 2)[..., None]
        block = out[y0:y1, x0:x1]
        block[inside] = np.clip(block + avg * fade, 0, 1)[inside]
    return srgb(out), n_edges


skin_seam = skin & ~lips
result, n_seam = seam_blend(result, skin_seam)
report['skin_seam_edges_blended'] = n_seam

# ---- 6. ramp regions and other classes: per-channel quantile curves onto the approved distribution
amask = np.stack([np.asarray(ch.resize((S, S), Image.BILINEAR), np.float32)
                  for ch in Image.open(HERE / 'work' / 'approved_fine_region_mask.png').convert('RGBA').split()], -1) / 255
Q = np.linspace(0, 100, 257)
levels = np.arange(256, dtype=np.float32)
targets = {'dress': amask[..., 0] > 0.5, 'hair': amask[..., 1] > 0.5}
h_a, s_a, v_a = hsv(approved)
targets['linen'] = (s_a < 0.2) & (v_a > 0.45) & np.isin(piece, [SHELL, 2, 3]) & (amask[..., :2].max(-1) < 0.1)
targets['leather'] = C['leather'] & (v_a < 0.35)
targets['brass'] = C['brass'] & (h_a > 32) & (h_a < 66) & (s_a > 0.4)
report['tone'] = {}
for name, aset in targets.items():
    aset = aset & cov & ~legs
    nset = C[name] & ~bad if name == 'hair' else C[name]
    if aset.sum() < 200 or nset.sum() < 200:
        continue
    curves = []
    for c in range(3):
        qa = wpercentile(approved[aset, c], texel_area[aset], Q)
        qn = wpercentile(result[nset, c], texel_area[nset], Q)
        qn = np.maximum.accumulate(qn + np.arange(len(qn)) * 1e-4)
        curves.append(np.interp(levels, qn, qa))
    before_mean = [round(float(np.average(result[nset, c], weights=texel_area[nset])), 1) for c in range(3)]
    sel = C[name]
    result[sel] = np.stack([np.interp(result[sel, c], levels, curves[c]) for c in range(3)], -1)
    report['tone'][name] = {'approved': [round(float(np.average(approved[aset, c], weights=texel_area[aset])), 1)
                                         for c in range(3)],
                            'paint': before_mean,
                            'result': [round(float(np.average(result[sel, c], weights=texel_area[sel])), 1)
                                       for c in range(3)]}
result[legs] = approved[legs]
result = texlib.pad(result, cov)
Image.fromarray(np.clip(result + 0.5, 0, 255).astype(np.uint8)).save(f'{out}_basecolor.png')

# ---- 7. mask, metal/roughness, classes, normal
N = 1024
pv = np.zeros((S, S, 3), np.uint8)
cls = np.zeros((S, S), np.uint8)
spec = np.zeros((S, S), np.float32)
rough_m = load(M / 'body_retexture_tp' / 'texture_urls_0_roughness.png', S, 'L') / 255 * (1 - hw) + \
    load(M / 'head_retexture_tp' / 'texture_urls_0_roughness.png', S, 'L') / 255 * hw
rgh = np.full((S, S), 0.8, np.float32)
for name, m in C.items():
    pv[m] = PREVIEW[name]
    cls[m] = CLASS[name]
    spec[m] = SPEC[name]
    rgh[m] = np.clip(ROUGH[name] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
legs_appr_mr = np.asarray(Image.open(HERE / 'work' / 'approved_fine_metal_rough.png').convert('RGB').resize((S, S),
                                                                                                        Image.NEAREST))
spec[legs] = legs_appr_mr[legs][:, 0] / 255
rgh[legs] = legs_appr_mr[legs][:, 1] / 255
cls[legs] = CLASS['linen']
Image.fromarray(pv).save(f'{out}_classes_preview.png')


def small(a, mode):
    a = texlib.pad(a[..., None] if a.ndim == 2 else a, cov)
    img = Image.fromarray(np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8).squeeze())
    return np.asarray(img.resize((N, N), Image.Resampling.BOX), np.float32) / 255


mr = np.stack([small(spec, 'L'), small(rgh, 'L'), np.zeros((N, N), np.float32)], -1)
Image.fromarray(np.clip(mr * 255 + 0.5, 0, 255).astype(np.uint8)).save(f'{out}_metal_rough.png')
cov_n = np.asarray(Image.fromarray(cov.astype(np.uint8) * 255).resize((N, N), Image.Resampling.BOX)) > 0
mask = np.zeros((N, N, 4), np.float32)
for c, name in enumerate(('dress', 'hair')):
    m = small(C[name].astype(np.float32), 'L')
    m = texlib.pad(m[..., None], cov_n)[..., 0]
    mask[..., c] = ndimage.gaussian_filter(m, 0.7)
Image.fromarray(np.clip(mask * 255 + 0.5, 0, 255).astype(np.uint8), 'RGBA').save(f'{out}_region_mask.png')
cls_n = np.asarray(Image.fromarray(cls).resize((N, N), Image.NEAREST))
Image.fromarray(cls_n).save(f'{out}_material_classes.png')

normals = []
for src in ('body', 'head'):
    n = load(M / f'{src}_retexture_tp' / 'texture_urls_0_normal.png') / 127.5 - 1
    n[..., 1] *= -1                                                   # Meshy +y down -> glTF +y up
    normals.append(n)
n = normals[0] * (1 - hw[..., None]) + normals[1] * hw[..., None]
n[C['eye'] | legs] = (0, 0, 1)
n[..., 2] = np.sqrt(np.clip(1 - (n[..., :2] ** 2).sum(-1), 0.0025, 1))
n /= np.linalg.norm(n, axis=-1, keepdims=True)
n = texlib.pad(n, cov)
Image.fromarray(np.clip((n + 1) * 127.5 + 0.5, 0, 255).astype(np.uint8)).save(f'{out}_normal.png')
np.savez_compressed(f'{out}_classes.npz', **{k: v for k, v in C.items()}, legs=legs, hw=hw)
json.dump(report, open(f'{out}_report.json', 'w'), indent=1)
print('COMPOSED', out, json.dumps(report))
