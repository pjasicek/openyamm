"""Runtime maps of the retextured reduced archer on the fresh 2048 x 1024 atlas (uv_fresh.py UVMap): body squares
(left) from the Meshy body retexture, head squares (right) remapped exactly from the installed accepted maps.
- body: Meshy base colour x AO (work/ao_<label>.png), boots darkened as in the installed compose (compose_arc1.py),
  Meshy normal (convention measured, strength REA_NORMAL), specular/roughness by material class: cloth (trouser
  and sleeve blue on every body piece but hands and arrows, also the tier region), skin (hands, painted skin on the main body), arrows, leather;
- head: base colour, normal (re-expressed in the new face frames), specular/roughness and region mask from the
  installed atlas at the same surface point; neck skin follows the body skin's change below 1.50 m;
- tier ramps from the native palettes 660/661/662 against the new cloth luminance (compose_arc1.py method).
Inputs: work/retex_faces_<label>.npz, meshy/<job>/, work/latest/mm6_arc1.glb. Writes textures/arc1_<label>_*.png and
textures/arc1_<label>_ramps.json. Usage: compose_retex.py <label> <meshy job>"""
import io, json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
sys.path.insert(0, str(P.parents[2] / 'tools')); import normal_map_convention as NM  # noqa: E402
import os  # noqa: E402
label, job = sys.argv[1:3]
WD, HT = 2048, 1024
T = P / 'textures'; T.mkdir(exist_ok=True)
F = np.load(P / 'work' / f'retex_faces_{label}.npz')
pos, old, upl, rt, head, comp = F['pos'], F['old'], F['upload'], F['runtime'], F['head'], F['comp']
HANDS, ARROWS, BRACERS, HAIR = [1, 2], [4, 9, 11, 13, 17, 18, 19], [8, 15], 21


def glb_images(path):
    raw = Path(path).read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n]); b0 = 28 + n
    out = {}
    for im in doc['images']:
        bv = doc['bufferViews'][im['bufferView']]; o = b0 + bv.get('byteOffset', 0)
        out[im['name']] = Image.open(io.BytesIO(raw[o:o + bv['byteLength']]))
    return out


def arr(img, mode='RGB'):
    return np.asarray(img.convert(mode), np.float64) / 255


def sample(img, uv):
    """Bilinear sample of an HxWxC image at UVs (v up)."""
    h, w = img.shape[:2]
    coords = np.array([(1 - uv[:, 1]) * h - .5, uv[:, 0] * w - .5])
    return np.stack([ndimage.map_coordinates(img[:, :, k], coords, order=1, mode='nearest') for k in range(img.shape[2])], 1)


# rasterise the runtime layout: per texel triangle id and barycentrics
tri = -np.ones((HT, WD), np.int64); bary = np.zeros((HT, WD, 3))
for t, uv in enumerate(rt):
    p = uv * [WD, HT]; p[:, 1] = HT - p[:, 1]
    x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
    x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, WD - 1), min(y1, HT - 1)
    if x1 < x0 or y1 < y0:
        continue
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
    a, b, c = p
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-12:
        continue
    w0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
    w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
    w2 = 1 - w0 - w1
    m = (w0 >= -1e-3) & (w1 >= -1e-3) & (w2 >= -1e-3)
    iy, ix = (ys[m] - .5).astype(int), (xs[m] - .5).astype(int)
    tri[iy, ix] = t; bary[iy, ix] = np.stack([w0[m], w1[m], w2[m]], 1)
cov = tri >= 0; ti = tri[cov]; bw = bary[cov]
interp = lambda corner: np.einsum('nk,nkc->nc', bw, corner[ti])
P3 = interp(pos); isHead = head[ti] == 1; cmp_ = comp[ti]
print('COVERAGE body', round(float(cov[:, :WD // 2].mean()), 3), 'head', round(float(cov[:, WD // 2:].mean()), 3))

# body from Meshy
M = P / 'meshy' / job
mrgb = arr(Image.open(M / 'texture_urls_0_base_color.png'))
mnrm_img = Image.open(M / 'texture_urls_0_normal.png').convert('RGB')
score = NM.measure(np.asarray(mnrm_img)); mnrm = arr(mnrm_img)
if score < -.15:
    mnrm[:, :, 1] = 1 - mnrm[:, :, 1]
mrough = arr(Image.open(M / 'texture_urls_0_roughness.png'), 'L')[..., None]
U = interp(upl)
rgb = sample(mrgb, U); nrm = sample(mnrm, U) * 2 - 1; rough = sample(mrough, U)[:, 0]
ao = sample(arr(Image.open(P / 'work' / f'ao_{label}.png'), 'L')[..., None], interp(rt))[:, 0]
hsv = np.asarray(Image.fromarray((rgb[None] * 255 + .5).astype('uint8')).convert('HSV'), float)[0] / 255
h, s, v = hsv[:, 0] * 360, hsv[:, 1], hsv[:, 2]
body = ~isHead
cloth = body & ~np.isin(cmp_, HANDS + ARROWS) & (h > 170) & (h < 275) & (s > .12)
skin = body & (np.isin(cmp_, HANDS) | ((cmp_ == 0) & (h > 8) & (h < 40) & (s > .18) & (s < .62) & (v > .5)))
boots = body & (cmp_ == 0) & (P3[:, 2] < .85) & ~cloth & ~skin
rgb[boots] *= [.83, .80, .77]
rgb *= (1 - .45 * (1 - np.clip(ao, .25, 1)))[:, None]
strength = float(os.environ.get('REA_NORMAL', '0.7'))
nrm[:, :2] *= strength; nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-8)
cls = np.full(len(ti), 8)
cls[skin] = 7; cls[cloth] = 4; cls[body & np.isin(cmp_, ARROWS)] = 1
spec = np.full(len(ti), .18); rr = np.full(len(ti), .65)
for c, sp, ro in [(1, .12, .68), (4, .05, .86), (7, .16, .69), (8, .18, .65)]:
    spec[cls == c] = sp; rr[cls == c] = ro
rr = np.clip(rr + (rough - .5) * .15, .1, .95)
region = cloth.astype(float)

# head and bracers from the installed maps at the same surface point (both kept exactly by the reduction; Meshy
# painted the right bracer skin and the left one only half leather)
old_maps = glb_images(P / 'work' / 'latest' / 'mm6_arc1.glb')
oname = lambda key: next(k for k in old_maps if key in k)
keepOld = isHead | (body & np.isin(cmp_, BRACERS))
O = interp(old)[keepOld]
rgb[keepOld] = sample(arr(old_maps[oname('basecolor')]), O)
omr = sample(arr(old_maps[oname('metal_rough')]), O); spec[keepOld] = omr[:, 0]; rr[keepOld] = omr[:, 1]
region[keepOld] = sample(arr(old_maps[oname('region_mask')], 'RGBA'), O)[:, 0]
# normals: tangent-space vector re-expressed from the old to the new face frame (per triangle, flat)


def frames(uvs):
    e1, e2 = pos[:, 1] - pos[:, 0], pos[:, 2] - pos[:, 0]
    d1, d2 = uvs[:, 1] - uvs[:, 0], uvs[:, 2] - uvs[:, 0]
    r = 1 / np.where(np.abs(d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]) < 1e-12, 1e-12, d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1])
    tg = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) * r[:, None]; bt = (e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) * r[:, None]
    nn = np.cross(e1, e2); nn /= np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-12)
    tg -= nn * np.sum(tg * nn, 1, keepdims=True); tg /= np.maximum(np.linalg.norm(tg, axis=1, keepdims=True), 1e-12)
    bt -= nn * np.sum(bt * nn, 1, keepdims=True); bt /= np.maximum(np.linalg.norm(bt, axis=1, keepdims=True), 1e-12)
    return tg, bt


To, Bo = frames(old); Tn, Bn = frames(rt)
on = sample(arr(old_maps[oname('normal')]), O) * 2 - 1
th = ti[keepOld]
vec = on[:, 0:1] * To[th] + on[:, 1:2] * Bo[th]
nrm[keepOld] = np.stack([np.sum(vec * Tn[th], 1), np.sum(vec * Bn[th], 1), on[:, 2]], 1)
# neck: the head set was matched to the installed body skin; move its skin by the body skin's change (new / installed
# at the same chest and neck points), fading out by 1.50 m
neck_body = body & skin & (cmp_ == 0) & (P3[:, 2] > 1.30) & (P3[:, 2] < 1.41)
before = sample(arr(old_maps[oname('basecolor')]), interp(old)[neck_body])
bh = np.asarray(Image.fromarray((before[None] * 255 + .5).astype('uint8')).convert('HSV'), float)[0] / 255
both = (bh[:, 0] * 360 > 8) & (bh[:, 0] * 360 < 40) & (bh[:, 1] > .18) & (bh[:, 1] < .62) & (bh[:, 2] > .5)  # skin in both
gain = np.median(rgb[neck_body][both], 0) / np.median(before[both], 0)
hh = np.asarray(Image.fromarray((rgb[None] * 255 + .5).astype('uint8')).convert('HSV'), float)[0] / 255
head_skin = isHead & (cmp_ == 0) & (hh[:, 0] * 360 > 5) & (hh[:, 0] * 360 < 45) & (hh[:, 1] > .12) & (hh[:, 2] > .3)
w = np.clip((1.50 - P3[:, 2]) / .09, 0, 1) * head_skin
rgb *= 1 + (gain - 1) * w[:, None]
print('NECK gain', np.round(gain, 3), 'skin texels in both', int(both.sum()), 'head skin texels faded', int((w > 0).sum()))

# forehead: the installed head set paints a red-orange fringe on the face skin between the hair mesh's locks. Face
# texels above the brows that are hair-coloured and not under the hair mesh (no hair triangle within 6 cm along the
# face normal) become skin: a smooth skin field from the surrounding forehead skin texels, flat normal, skin
# specular/roughness
hair = pos[comp == HAIR]


def hits(orig, d, tris, reach=.06):
    """Per ray: any triangle hit within reach (Moller-Trumbore, chunked)."""
    out = np.zeros(len(orig), bool)
    e1, e2, v0 = tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0], tris[:, 0]
    for i in range(0, len(orig), 2048):
        o, dd = orig[i:i + 2048, None], d[i:i + 2048, None]
        pv = np.cross(dd, e2); det = np.sum(e1 * pv, -1); inv = 1 / np.where(np.abs(det) < 1e-12, 1e-12, det)
        tv = o - v0; u = np.sum(tv * pv, -1) * inv; qv = np.cross(tv, e1); v = np.sum(dd * qv, -1) * inv
        t = np.sum(e2 * qv, -1) * inv
        out[i:i + 2048] = ((np.abs(det) > 1e-12) & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-4) & (t < reach)).any(1)
    return out


fn = np.cross(pos[:, 1] - pos[:, 0], pos[:, 2] - pos[:, 0]); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
face = isHead & (cmp_ == 0) & (P3[:, 2] > 1.585)   # above the eye centres
idx = np.where(face)[0]
covered = np.zeros(len(ti), bool); covered[idx] = hits(P3[idx], fn[ti[idx]], hair)
hh = np.asarray(Image.fromarray((rgb[None] * 255 + .5).astype('uint8')).convert('HSV'), float)[0] / 255
hue, sat, val = hh[:, 0] * 360, hh[:, 1], hh[:, 2]
dark = np.zeros((HT, WD), bool); dark[cov] = face & (val < .42)
lab, n = ndimage.label(dark); size = ndimage.sum(dark, lab, np.arange(1, n + 1))
brow = np.isin(lab, 1 + np.where(size >= 120)[0])[cov]   # brows and lashes stay; small dark hair specks go
hairy = face & ~covered & ~brow & (((sat > .6) & (hue < 26)) | (hue < 14) | (hue > 340))
skin_ok = face & ~covered & ~hairy & (sat > .2) & (sat < .6) & (hue > 14) & (hue < 40)
grow = np.zeros((HT, WD), bool); grow[cov] = hairy
grow = ndimage.binary_dilation(grow, iterations=2) & cov
fix = grow[cov] & face & ~covered & ~brow
field = np.zeros((HT, WD, 3)); wt = np.zeros((HT, WD))
sk = np.zeros((HT, WD), bool); sk[cov] = skin_ok
field[cov] = rgb * skin_ok[:, None]; wt[cov] = skin_ok
sig = 10
wsum = ndimage.gaussian_filter(wt, sig)
blur = np.stack([ndimage.gaussian_filter(field[:, :, k], sig) for k in range(3)], 2) / np.maximum(wsum, 1e-6)[..., None]
trust = np.clip(wsum / .15, 0, 1)[..., None]   # few skin texels nearby: the forehead's median skin
blur = blur * trust + np.median(rgb[skin_ok], 0) * (1 - trust)
soft = ndimage.gaussian_filter(grow.astype(float), 1.5)[cov]
a = np.clip(soft[fix] * 1.6, 0, 1)[:, None]
rgb[fix] = rgb[fix] * (1 - a) + blur[cov][fix] * a
nrm[fix] = nrm[fix] * (1 - a) + np.array([0, 0, 1.]) * a; nrm[fix] /= np.linalg.norm(nrm[fix], axis=1, keepdims=True)
spec[fix] = .16; rr[fix] = .69
print('FOREHEAD face texels', int(face.sum()), 'under hair', int(covered.sum()), 'hair-coloured fixed', int(hairy.sum()),
      'with feather', int(fix.sum()))


def image(values, channels):
    a = np.zeros((HT, WD, channels)); a[cov] = values.reshape(len(ti), channels)
    for half in (slice(0, WD // 2), slice(WD // 2, WD)):   # pad each square from its own islands
        sub, c = a[:, half], cov[:, half]
        _, ind = ndimage.distance_transform_edt(~c, return_indices=True)
        a[:, half] = sub[tuple(ind)]
    return a


def save(a, path, mode='RGB'):
    Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype('uint8').squeeze(), mode).save(path, optimize=True)


save(image(rgb, 3), T / f'arc1_{label}_basecolor.png')
save(image(nrm * .5 + .5, 3), T / f'arc1_{label}_normal.png')
save(image(np.stack([spec, rr, np.zeros_like(rr)], 1), 3), T / f'arc1_{label}_metal_rough.png')
reg = image(region, 1)[:, :, 0]
R.write_mask([ndimage.gaussian_filter(reg, .65)], T / f'arc1_{label}_region_mask.png', size=(WD, HT))
cl = np.zeros((HT, WD), np.uint8); cl[cov] = np.where(isHead, 3, cls); Image.fromarray(cl).save(T / f'arc1_{label}_classes.png')

# tier ramps (compose_arc1.py): native cloth pixels per palette against the new cloth luminance
native = {k: [] for k in ['arc1_a', 'arc1_b', 'arc1_c']}
for view in range(5):
    ims = [np.asarray(Image.open(P.parent / 'mm6_arc1/native_variants' / f'arc1sta{view}_{pal}.png').convert('RGBA'), float) / 255
           for pal in [660, 661, 662]]
    a, b, c = ims
    changed = (a[:, :, 3] > .5) & (np.maximum(abs(a[:, :, :3] - b[:, :, :3]).max(2), abs(a[:, :, :3] - c[:, :, :3]).max(2)) > 8 / 255) & (a[:, :, :3].max(2) > .1)
    for key, im in zip(native, ims):
        native[key].append(im[:, :, :3][changed])
native = {k: np.concatenate(x) for k, x in native.items()}
lum = np.sort(R.luminance(rgb[cloth])); lo, hi = np.percentile(lum, [2, 98]); base_mid = float(np.median(lum))
order = np.argsort(R.luminance(native['arc1_a'])); ramps = {}
for variant, colors in native.items():
    linear = R.srgb_to_linear(colors)[order]
    mid = np.median(linear[int(len(linear) * .65):int(len(linear) * .80)], axis=0)
    stops = [np.clip(mid * (max(x, 1e-6) / base_mid) ** .65, 0, 1) for x in np.linspace(lo, hi, 16)]
    ramps[variant] = [{'range': [float(lo), float(hi)], 'colors': np.round(stops, 6).tolist()}]
(T / f'arc1_{label}_ramps.json').write_text(json.dumps(ramps, indent=1) + '\n')
print('CLASSES', {int(c): int((cls[body] == c).sum()) for c in np.unique(cls[body])}, 'cloth texels', int(cloth.sum()),
      'ramp range', round(lo, 4), round(hi, 4), 'normal score', round(score, 3))
