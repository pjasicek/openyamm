"""Texture-pass maps of the m322 elf from the two 4K Meshy paints on our layout (work/uv_fine.npz).

1. Paint: the body retexture (full-figure masters) everywhere; the head retexture (head masters, head-set faces only:
   face, ears, scalp, neck top, hair shell, eyes, mouth) over the head set. Colour and normal 4K -> 2K once (Lanczos).
   The head paint fades in over HEAD_FADE m of surface distance (geodesic on the head set) from the head-set boundary
   on the neck, so neither paint ends at an edge.
2. One skin tone: the head paint's skin takes a per-channel gain so its skin in the neck band equals the body paint's
   skin there (both paints exist on the head set). Hair shell and eyes keep the head paint unchanged.
3. Gentle grade (claude_shared/grade_basecolor.py's recipe values, saturation 1.0: the skin is already matched) with
   AO baked on the layout; its blurs stay inside each chart (a texture-space blur lit a small chest chart from its
   gutter). Then seam levelling (scripts/seam_level.py): a smooth additive correction per chart makes both sides
   of every chart seam of one colour class agree (a small chart beside the eye came back lighter than its
   neighbours). Before the grade, hair strands the body paint projected onto torso skin are refilled from the surrounding
   paint.
4. Region mask, by geometry first: G hair = the hair shell, plus scalp texels of the skin shell that lie within
   SCALP_REACH of the hair shell, under it (the hair lies outward along the surface normal), and are painted
   hair-coloured (never lips, brows, ears or cheeks); R cloth = green
   texels of the skin shell below the vest (the trousers, waistband included). Inside each region the paint's linear luminance is
   quantile-matched to the approved paint's (same regions on the installed GLB), so the nine tiers' ramps keep their
   colours; only the pattern is the new paint's.
   Irises: chroma x IRIS_CHROMA and a light blur inside the eye shells (muted grey-green as the HD head views).
5. Normal: the paints' (+y down -> glTF +y up), blended like the colour, tilt scaled to the approved map's p90.
6. Metal/roughness (R specular mask, G roughness) and material classes from the new classes with the production
   rule (../mm7_m322_claude/scripts/compose_m322.py SPEC/ROUGH, Meshy roughness modulation).

Usage: compose.py <out prefix>
Writes <out>_{basecolor,normal,metal_rough,region_mask,material_classes}.png, <out>_raw.png (paint before grade), <out>_report.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import texlib  # noqa: E402
from glb import Glb  # noqa: E402

out = sys.argv[1]
S, SMALL = 2048, 1024
HEAD_FADE = 0.045
SCALP_REACH = 0.022
SMOOTH_RINGS = 12
IRIS_CHROMA = 0.55
W = np.array([0.2126, 0.7152, 0.0722])
M = HERE / 'meshy'
SPEC = {'skin': 0.45, 'cloth': 0.2, 'leather': 0.35, 'metal': 0.7, 'hair': 0.3, 'eye': 0.9}
ROUGH = {'skin': 0.55, 'cloth': 0.85, 'leather': 0.6, 'metal': 0.35, 'hair': 0.65, 'eye': 0.2}
CLASS_ID = {'skin': 1, 'hair': 2, 'cloth': 8, 'leather': 8, 'metal': 9, 'eye': 6}


def lin(c):
    c = np.asarray(c, np.float64) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055) * 255


def load(path, mode='RGB', size=S):
    img = Image.open(path).convert(mode)
    if img.size != (size, size):
        img = img.resize((size, size), Image.Resampling.LANCZOS)
    return np.asarray(img, np.float64)


def hsv(rgb):
    h = np.asarray(Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    return h[..., 0] * 360, h[..., 1], h[..., 2]


def wquant(v, w, q):
    o = np.argsort(v)
    c = np.cumsum(w[o])
    c /= c[-1]
    return np.interp(q, c, v[o])


layout = np.load(HERE / 'work' / 'uv_fine.npz')
before = np.load(HERE / 'work' / 'lod0_before.npz')
r = np.load(HERE / 'work' / 'approved_fine_raster2048.npz')
tri_id, bary = r['tri_id'], r['bary']
cov = tri_id >= 0
t = np.where(cov, tri_id, 0)
tri, weld, head_face, piece = before['tri'], before['weld'], before['head_face'], before['piece']
xyz = layout['xyz']
uv = layout['uv']
nweld = int(weld.max()) + 1
wtri = weld[tri]
tp = piece[t]                                   # per-texel piece
point = (xyz[t] * bary[..., None]).sum(-2)      # per-texel bind position
area3 = np.linalg.norm(np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]), axis=1) / 2
area2 = np.abs((uv[:, 1, 0] - uv[:, 0, 0]) * (uv[:, 2, 1] - uv[:, 0, 1])
               - (uv[:, 2, 0] - uv[:, 0, 0]) * (uv[:, 1, 1] - uv[:, 0, 1])) / 2
weight = np.where(cov, (area3 / np.maximum(area2, 1e-12))[t], 0)   # texel -> surface area
report = {}

# ---- 1. head weight: geodesic distance from the head-set boundary over the head-set faces
wpos = np.zeros((nweld, 3))
wpos[weld] = before['pos']
in_head = np.zeros(nweld, bool)
in_body = np.zeros(nweld, bool)
in_head[wtri[head_face].ravel()] = True
in_body[wtri[~head_face].ravel()] = True
boundary = np.nonzero(in_head & in_body)[0]
e = np.concatenate([wtri[head_face][:, [0, 1]], wtri[head_face][:, [1, 2]], wtri[head_face][:, [2, 0]]])
length = np.linalg.norm(wpos[e[:, 0]] - wpos[e[:, 1]], axis=1)
graph = coo_matrix((np.r_[length, length], (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])),
                   shape=(nweld, nweld)).tocsr()
dist = dijkstra(graph, indices=boundary, min_only=True)
s = np.clip(dist / HEAD_FADE, 0, 1)
w_vert = np.where(in_head, s * s * (3 - 2 * s), 0.0)
hw = np.where(cov & head_face[t], (w_vert[wtri[t]] * bary).sum(-1), 0.0)
dist_texel = np.where(cov & head_face[t], (np.minimum(dist, 1.0)[wtri[t]] * bary).sum(-1), 0.0)

body = load(M / 'body_retexture_v2' / 'texture_urls_0_base_color.png')
head = load(M / 'head_retexture_v2' / 'texture_urls_0_base_color.png')

# ---- 2. one skin tone: head-paint gain from the neck band (skin-coloured in both paints)


def skinlike(img):
    mx, mn = img.max(-1), img.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1)
    return (img[..., 0] >= img[..., 1]) & (img[..., 1] >= 0.9 * img[..., 2]) & (sat > 0.12) & (sat < 0.5) & (mx > 120)


both = cov & head_face[t] & (tp == 0) & skinlike(body) & skinlike(head)
# per-face sums of linear colour over skin texels of both paints, onto welded vertices, then diffused over the
# head-set skin shell (normalised convolution, about SMOOTH_RINGS rings): broad tone per paint, ratio per vertex
fsum_b = np.zeros((len(tri), 3))
fsum_h = np.zeros((len(tri), 3))
fcnt = np.bincount(t[both], minlength=len(tri)).astype(np.float64)
for c in range(3):
    fsum_b[:, c] = np.bincount(t[both], lin(body[both][:, c]), minlength=len(tri))
    fsum_h[:, c] = np.bincount(t[both], lin(head[both][:, c]), minlength=len(tri))
skin_faces = head_face & (piece == 0)
vb = np.zeros((nweld, 3))
vh = np.zeros((nweld, 3))
vc = np.zeros(nweld)
for k in range(3):
    np.add.at(vb, wtri[skin_faces, k], fsum_b[skin_faces])
    np.add.at(vh, wtri[skin_faces, k], fsum_h[skin_faces])
    np.add.at(vc, wtri[skin_faces, k], fcnt[skin_faces])
es = np.concatenate([wtri[skin_faces][:, [0, 1]], wtri[skin_faces][:, [1, 2]], wtri[skin_faces][:, [2, 0]]])
A = coo_matrix((np.ones(2 * len(es)), (np.r_[es[:, 0], es[:, 1]], np.r_[es[:, 1], es[:, 0]])),
               shape=(nweld, nweld)).tocsr()
A.data[:] = 1.0
deg = np.asarray(A.sum(1)).ravel()
for _ in range(SMOOTH_RINGS):
    vb = (vb + A @ vb) / (1 + deg)[:, None]
    vh = (vh + A @ vh) / (1 + deg)[:, None]
    vc = (vc + A @ vc) / (1 + deg)
ratio_v = np.clip(vb / np.maximum(vh, 1e-6), 0.5, 2.0)
global_ratio = fsum_b[skin_faces].sum(0) / fsum_h[skin_faces].sum(0)
ratio_v[vc < 1e-3] = global_ratio
report['skin_ratio_global_linear'] = global_ratio.round(4).tolist()
report['skin_ratio_vertex_p5_p95'] = np.percentile(ratio_v[np.unique(wtri[skin_faces])], [5, 95], axis=0).round(3).tolist()
head_adj = head.copy()
skin_set = cov & head_face[t] & (tp == 0)
ratio_t = (ratio_v[wtri[t]] * bary[..., None]).sum(-2)
head_adj[skin_set] = srgb(lin(head[skin_set]) * ratio_t[skin_set])
# mouth bits and the eyelid skin of the eye shells (separate shells, outside the diffusion graph): the global ratio
mouth = cov & (np.isin(tp, [8, 9, 11]) | (np.isin(tp, [4, 5]) & skinlike(head)))
head_adj[mouth] = srgb(lin(head[mouth]) * global_ratio)
paint = body * (1 - hw[..., None]) + head_adj * hw[..., None]

# islands (charts) per texel: every blur below stays inside its chart, so gutters never bleed across seams
import texture_quality as TQ  # noqa: E402
_, isl = np.unique(TQ.islands(uv.astype(np.float64), xyz.astype(np.float64)), return_inverse=True)
isl = isl.ravel()
island_map = np.where(cov, isl[t], -1)
objects = ndimage.find_objects(island_map + 1)


def island_blur(img, sigma, valid=None):
    """Gaussian of img (H,W[,C]) inside each chart, over the texels where valid (default: the chart)."""
    one = img.ndim == 2
    data = img[..., None] if one else img
    res = data.copy()
    pad_px = int(3 * sigma) + 2
    for i, sl in enumerate(objects):
        if sl is None:
            continue
        y0, y1 = max(sl[0].start - pad_px, 0), min(sl[0].stop + pad_px, S)
        x0, x1 = max(sl[1].start - pad_px, 0), min(sl[1].stop + pad_px, S)
        inside = island_map[y0:y1, x0:x1] == i
        m = (inside & (True if valid is None else valid[y0:y1, x0:x1])).astype(np.float64)
        den = np.maximum(ndimage.gaussian_filter(m, sigma, mode='constant'), 1e-6)
        for c in range(data.shape[-1]):
            num = ndimage.gaussian_filter(data[y0:y1, x0:x1, c] * m, sigma, mode='constant')
            res[y0:y1, x0:x1, c][inside] = (num / den)[inside]
    return res[..., 0] if one else res


# hair strands the body paint projected onto torso and arm skin (hair hangs behind the shoulders): refilled from the
# surrounding paint of the same chart (skin, or the vest strap it crosses)
hue0, sat0, val0 = hsv(paint)
strand = cov & ~head_face[t] & (tp == 0) & (point[..., 1] > 0.95) & ((hue0 < 20) | (hue0 > 340)) & (sat0 > 0.42) \
    & (val0 > 0.35) & (val0 < 0.92)
strand = ndimage.binary_dilation(strand, iterations=2) & cov & ~head_face[t] & (tp == 0) & (point[..., 1] > 0.95)
# each strand texel takes the material of its nearest untouched texel (skin, or the vest strap it crosses) and is
# filled from that material only, so leather never smears onto skin
clean = cov & ~strand
skin_ok = clean & skinlike(paint)
_, (iy, ix) = ndimage.distance_transform_edt(~clean, return_indices=True)
to_skin = skin_ok[iy, ix]
fill = np.where(to_skin[..., None], island_blur(paint, 8.0, skin_ok), island_blur(paint, 4.0, clean & ~skin_ok))
ok = strand & np.isfinite(fill).all(-1) & (fill.sum(-1) > 0)
paint[ok] = fill[ok]
report['strand_texels_refilled'] = int(ok.sum())
paint = texlib.pad(paint, cov)
raw_path = f'{out}_raw.png'
Image.fromarray(np.clip(paint + 0.5, 0, 255).astype(np.uint8)).save(raw_path)

# ---- 3. gentle grade (recipe values: AO 0.5, local 0.3 at 16 px, contrast 1.06; fine detail kept; saturation 1.0),
# as claude_shared/grade_basecolor.py but with the local-contrast blur inside each chart
ao = np.asarray(Image.open(HERE / 'textures' / 'm322_tp_ao_2k.png').convert('L'), np.float64) / 255
# grey closing first: the bake left dark specks and dotted lines (one under the right eye) smaller than 5 texels
ao = island_blur(ndimage.grey_closing(texlib.pad(ao, cov), size=(5, 5)), 2.0)
rgb = paint / 255 * (1.0 - 0.5 * (1.0 - ao))[..., None]
lum = rgb @ W
target = lum + 0.3 * (lum - island_blur(lum, 16.0))
median = float(np.median(lum[cov]))
target = median + 1.06 * (target - median)
rgb = rgb * (np.clip(target, 0, 1) / np.maximum(lum, 1e-4))[..., None]
graded = texlib.pad(np.clip(rgb * 255, 0, 255), cov)

# seam levelling over chart seams of one colour class (a small face chart came back lighter than its neighbours)
import seam_level  # noqa: E402


def colour_class(c):
    """0 skin, 1 green cloth, 2 hair red, 3 other"""
    mx, mn = c.max(-1), c.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1)
    green = (c[:, 1] > c[:, 0] + 8) & (c[:, 1] > c[:, 2])
    skin = (c[:, 0] >= c[:, 1]) & (c[:, 1] >= 0.9 * c[:, 2]) & (sat > 0.12) & (sat < 0.44) & (mx > 120)
    red = (c[:, 0] > c[:, 1] * 1.4) & (sat >= 0.44)
    return np.where(skin, 0, np.where(green, 1, np.where(red, 2, 3)))


Image.fromarray(np.clip(graded + 0.5, 0, 255).astype(np.uint8)).save(f'{out}_graded.png')
graded, report['seam_level'] = seam_level.level(graded, tri_id, bary, uv, wtri, isl, classify=colour_class)

# ---- 4. regions
hue, sat, val = hsv(graded)
hair_tris = np.nonzero(piece == 1)[0]
rng = np.random.default_rng(0)
samples = []
for k in range(24):
    b = rng.dirichlet((1, 1, 1), len(hair_tris))
    samples.append((xyz[hair_tris] * b[..., None]).sum(1))
hair_pts = np.concatenate(samples)
hair_tree = cKDTree(hair_pts)
scalp_cand = cov & head_face[t] & (tp == 0)
d_hair = np.full((S, S), np.inf)
d_hair[scalp_cand], nearest_hair = hair_tree.query(point[scalp_cand])
# the hair must lie outward of the surface (covering it), not merely nearby: the ear bases sit next to the hair
fn = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
v = hair_pts[nearest_hair] - point[scalp_cand]
outward = ((v * fn[t[scalp_cand]]).sum(1) / np.maximum(d_hair[scalp_cand], 1e-9) > 0.3) | (d_hair[scalp_cand] < 0.004)
d_hair[np.nonzero(scalp_cand)[0][~outward], np.nonzero(scalp_cand)[1][~outward]] = np.inf
redness = ((hue < 28) | (hue > 340))
hair_paint = np.clip((sat - 0.44) / 0.12, 0, 1) * redness * (val < 0.9)
near = np.clip((SCALP_REACH - d_hair) / 0.006, 0, 1)
scalp = np.where(scalp_cand, hair_paint * near, 0.0)
scalp = ndimage.gaussian_filter(scalp, 1.2) * scalp_cand
hair = np.where(cov & (tp == 1), 1.0, np.clip(scalp, 0, 1))
green = (graded[..., 1] > graded[..., 0] + 8) & (graded[..., 1] > graded[..., 2])
cloth = (cov & ~head_face[t] & (tp == 0) & green & (point[..., 1] < 1.25)).astype(np.float64)
cloth = np.clip(ndimage.gaussian_filter(cloth, 0.7), 0, 1) * (cov & (tp == 0))
regions = {'cloth': cloth, 'hair': hair}
report['scalp_texels'] = int((scalp > 0.5).sum())

# luminance matched to the approved regions (approved paint and mask at the same surface points)
appr = np.asarray(Image.open(HERE / 'work' / 'approved_fine_basecolor.png').convert('RGB'), np.float64)
amask = np.stack([np.asarray(ch.resize((S, S), Image.BILINEAR), np.float64)
                  for ch in Image.open(HERE / 'work' / 'approved_fine_region_mask.png').convert('RGBA').split()], -1) / 255
result = graded.copy()
glin = lin(graded)
L_new = glin @ W
L_appr = lin(appr) @ W
Q = np.linspace(0, 1, 257)
for k, (name, m) in enumerate(regions.items()):
    sel_new = m > 0.5
    sel_old = cov & (amask[..., k] > 0.5)
    qa = wquant(L_appr[sel_old], weight[sel_old], Q)
    qn = wquant(L_new[sel_new], weight[sel_new], Q)
    qn = np.maximum.accumulate(qn + np.arange(len(qn)) * 1e-7)
    mapped = np.interp(L_new, qn, qa)
    scale = mapped / np.maximum(L_new, 1e-5)
    matched = srgb(glin * scale[..., None])
    result = result * (1 - m[..., None]) + matched * m[..., None]
    report[name] = {'approved_luma_q10_50_90': np.round(np.interp([.1, .5, .9], Q, qa), 4).tolist(),
                    'paint_luma_q10_50_90': np.round(np.interp([.1, .5, .9], Q, qn), 4).tolist(),
                    'texels': int(sel_new.sum()), 'approved_texels': int(sel_old.sum())}

# irises: the head paint's are a saturated green with a crackled pattern; the HD head views and the approved paint
# have a muted grey-green iris. Inside the eye shells, green texels keep their luminance, lose IRIS_CHROMA of their
# chroma and take a light blur (crackle softened); pupils, whites and lids are unchanged.
eh, es, ev = hsv(result)
iris = cov & np.isin(tp, [4, 5]) & (eh > 70) & (eh < 200) & (es > 0.15)
iris_w = np.clip(ndimage.gaussian_filter(iris.astype(np.float64), 0.8), 0, 1) * np.isin(tp, [4, 5])
soft = island_blur(result, 0.9)
lum_r = (result @ W)[..., None]
toned_iris = lum_r + IRIS_CHROMA * (soft - (soft @ W)[..., None])
result = result * (1 - iris_w[..., None]) + toned_iris * iris_w[..., None]
report['iris'] = {'texels': int(iris.sum()), 'mean_srgb': np.round(result[iris].mean(0)).astype(int).tolist()}
for name, m in regions.items():
    report[name]['result_luma_q10_50_90'] = np.round(np.percentile((lin(result[m > 0.5]) @ W), [10, 50, 90]), 4).tolist()
result = texlib.pad(result, cov)
Image.fromarray(np.clip(result + 0.5, 0, 255).astype(np.uint8)).save(f'{out}_basecolor.png')

mask_full = np.stack([texlib.pad(cloth, cov), texlib.pad(hair, cov)], 0)
channels = [Image.fromarray(np.clip(m * 255 + 0.5, 0, 255).astype(np.uint8), 'L').resize((SMALL, SMALL), Image.BOX)
            for m in mask_full] + [Image.new('L', (SMALL, SMALL), 0)] * 2
Image.merge('RGBA', channels).save(f'{out}_region_mask.png', optimize=True)

# ---- 5. normal
normals = []
for src in ('body', 'head'):
    n = load(M / f'{src}_retexture_v2' / 'texture_urls_0_normal.png') / 127.5 - 1
    n[..., 1] *= -1                                                   # Meshy +y down -> glTF +y up
    normals.append(n)
n = normals[0] * (1 - hw[..., None]) + normals[1] * hw[..., None]
g = Glb(HERE / 'work' / 'before_texpass' / 'mm7_m322.glb')
old_n = np.asarray(g.image(2).convert('RGB'), np.float64) / 127.5 - 1
old_cov = np.asarray(g.image(0).convert('L')) > 0
target = float(np.percentile(np.linalg.norm(old_n[..., :2], axis=-1)[old_cov], 90))
current = float(np.percentile(np.linalg.norm(n[..., :2], axis=-1)[cov], 90))
k_tilt = min(1.0, target / max(current, 1e-6))
n[..., :2] *= k_tilt
n[..., 2] = np.sqrt(np.clip(1 - (n[..., :2] ** 2).sum(-1), 0.0025, 1))
n /= np.linalg.norm(n, axis=-1, keepdims=True)
n = texlib.pad(n, cov)
Image.fromarray(np.clip((n + 1) * 127.5 + 0.5, 0, 255).astype(np.uint8)).save(f'{out}_normal.png')
report['normal'] = {'approved_p90_tilt': round(target, 3), 'paint_p90_tilt': round(current, 3), 'scale': round(k_tilt, 3)}

# ---- 6. classes, specular mask and roughness
rough_m = (load(M / 'body_retexture_v2' / 'texture_urls_0_roughness.png', 'L') * (1 - hw)
           + load(M / 'head_retexture_v2' / 'texture_urls_0_roughness.png', 'L') * hw) / 255
cls = {}
cls['eye'] = cov & np.isin(tp, [4, 5])
cls['hair'] = cov & (hair > 0.5) & ~cls['eye']
cls['cloth'] = cov & (cloth > 0.5)
skin = cov & np.isin(tp, [0, 2, 3, 8, 9, 11]) & ~cls['hair'] & ~cls['cloth'] & ~cls['eye'] & \
    ((hue < 35) | (hue > 330)) & (sat > 0.12) & (sat < 0.6) & (val > 0.42)
skin |= cov & np.isin(tp, [2, 3, 8, 9, 11]) | (cov & head_face[t] & (tp == 0) & ~cls['hair'])
cls['skin'] = skin & ~cls['eye']
cls['metal'] = cov & ~np.isin(tp, [0, 1, 2, 3, 4, 5, 8, 9, 11]) & (hue > 30) & (hue < 65) & (sat > 0.3) & (val > 0.35)
cls['leather'] = cov & ~(cls['eye'] | cls['hair'] | cls['cloth'] | cls['skin'] | cls['metal'])
spec = np.zeros((S, S))
rgh = np.full((S, S), 0.8)
cm = np.zeros((S, S), np.uint8)
for kname, m in cls.items():
    if not m.any():
        continue
    cm[m] = CLASS_ID[kname]
    spec[m] = SPEC[kname]
    rgh[m] = np.clip(ROUGH[kname] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
mr = np.stack([texlib.pad(spec, cov), texlib.pad(rgh, cov), np.zeros((S, S))], -1)
Image.fromarray(np.clip(mr * 255 + 0.5, 0, 255).astype(np.uint8)).resize((SMALL, SMALL), Image.BOX).save(
    f'{out}_metal_rough.png')
Image.fromarray(cm).save(f'{out}_material_classes.png')
report['classes'] = {k: int(m.sum()) for k, m in cls.items()}
json.dump(report, open(f'{out}_report.json', 'w'), indent=1)
print('COMPOSED', out, json.dumps(report))
