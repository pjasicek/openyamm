#!/usr/bin/env python3
"""Shared texture set, region mask and per-tier ramps for the Sea Monster (CLAUDE_CREATURE_TEXTURES.md; from
mm9_jelly_claude/scripts/compose_jelly.py). Usage: compose_sea.py

Regions (structural): R body scales, G belly (bind normal facing down), B fins (dorsal sail, tail spines, tail fin),
A hands/claws and teeth; the mouth lining (mouth_rebuild.py's cavity, painted here from its MouthCos/MouthSin/MouthV
parameter groups) and the eyeballs are in
no region, so every tier keeps their own colours. Tier colours per region come from the MM9 skins projected onto our texels through the fitted
bind pose (nearest MM9 surface point): A SeaCreatureF (Sea Monster Male, row 177), B SeaCreatureM (Female, 178).
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

BODY = 'sea'
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV

T = HERE / 'textures'
M = HERE / 'meshy' / f'{BODY}_retexture_v2'    # 4K on the xatlas UVs (texture quality pass, 2026-10-30)
W = np.array([0.2126, 0.7152, 0.0722])
TIERS = {'sea_a': 'seaF/skins/seaF.png', 'sea_b': 'seaM/skins/seaM.png'}
TIER_A = next(iter(TIERS))
REGIONS = ('body', 'belly', 'fins', 'claws')
MAT = 'Sea'
# the retexture is about twice as bright as the HD masters' navy body; in game tier A read as bright cyan
DARKEN = 0.72


def lin(c):
    return RV.srgb_to_linear(c)


def encode(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def hsv(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn + 1e-9
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, d / (mx + 1e-9), mx


def raster(npz, size, fields):
    d = np.load(npz)
    uv = d['uv'] * size
    tri = np.full((size, size), -1, np.int32)
    out = {f: np.zeros((size, size), np.float32) for f in fields}
    for t in range(len(uv)):
        p = uv[t]
        x0, x1 = max(int(np.floor(p[:, 0].min())), 0), min(int(np.ceil(p[:, 0].max())), size - 1)
        y0, y1 = max(int(np.floor(p[:, 1].min())), 0), min(int(np.ceil(p[:, 1].max())), size - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = p
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        l3 = 1 - l1 - l2
        inside = (l1 >= -1e-4) & (l2 >= -1e-4) & (l3 >= -1e-4)
        if not inside.any():
            continue
        iy, ix = np.nonzero(inside)
        rows, cols = size - 1 - (iy + y0), ix + x0
        tri[rows, cols] = t
        for f in fields:
            v = d[f][t]
            out[f][rows, cols] = l1[inside] * v[0] + l2[inside] * v[1] + l3[inside] * v[2]
    return tri, out, d


def pad(img, covered):
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]


def feather(m, covered):
    m = pad(m.astype(np.float32), covered)
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0)),
                      np.float32) / 255


EYE_NPZ = HERE / 'work' / f'uv3d_{BODY}_eye.npz'
MOUTH_NPZ = {k: HERE / 'work' / f'uv3d_{BODY}_{k}.npz' for k in ('mouth', 'mcos', 'msin', 'mv')}


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def mouth_texels(size):
    """Texels of the cavity triangles (any vertex in mouth_rebuild.py's 'Mouth' group) and their paint parameters
    (u around the lip loop from the MouthCos/MouthSin groups, v lip -> throat from MouthV), or None."""
    if not all(p.exists() for p in MOUTH_NPZ.values()):
        return None
    tri, f, d = raster(MOUTH_NPZ['mouth'], size, ['grp'])
    cav = (tri >= 0) & (d['grp'].max(1)[np.maximum(tri, 0)] > 0.5)
    par = {k: raster(MOUTH_NPZ[k], size, ['grp'])[1]['grp'] for k in ('mcos', 'msin', 'mv')}
    u = (np.arctan2(par['msin'] - 0.5, par['mcos'] - 0.5) / (2 * np.pi)) % 1.0
    return cav, u, np.clip(par['mv'], 0, 1)


def paint_mouth(img):
    """Mouth lining on the cavity texels (u: corner A 0, upper half to corner B 0.5, lower half back to 1; v: lip 0 ..
    throat 1): dark lip edge, gums, olive-green palate with transverse ridges and floor (MM9's green mouth), a paler
    tongue with a median groove in the lower half, darkening into a red-black throat. sRGB float."""
    size = img.shape[0]
    mt = mouth_texels(size)
    if mt is None:
        return img
    cav, U, V = mt
    u, v = U[cav], V[cav]
    rng = np.random.default_rng(11)
    grid = (128, 512)                                        # noise in (v, u) parameter space
    fine = ndimage.gaussian_filter(rng.normal(size=grid), 1.2, mode='wrap')
    coarse = ndimage.gaussian_filter(rng.normal(size=grid), 6, mode='wrap')
    gi = np.clip((v * grid[0]).astype(int), 0, grid[0] - 1), np.clip((u * grid[1]).astype(int), 0, grid[1] - 1)
    noise = fine[gi] / (np.abs(fine).max() + 1e-9)
    nco = coarse[gi] / (np.abs(coarse).max() + 1e-9)

    def c(*rgb):
        return np.array(rgb, np.float32) / 255

    lining = np.where((u < 0.5)[:, None], c(70, 84, 38), c(64, 78, 34))
    ridge = 0.5 + 0.5 * np.sin(2 * np.pi * v * 9)            # palate ridges across the mouth (constant v)
    pal = np.exp(-((u - 0.25) / 0.12) ** 2) * smooth(0.12, 0.25, v) * (1 - smooth(0.6, 0.8, v))
    lining = lining * (1 - 0.28 * (pal * ridge)[:, None])
    du = np.abs(u - 0.75)                                      # tongue: lower half centre, groove along it
    tongue = smooth(0.13, 0.08, du) * smooth(0.12, 0.25, v) * (1 - smooth(0.78, 0.92, v))
    tcol = c(122, 138, 58) * (1 - 0.35 * np.exp(-(du / 0.008) ** 2))[:, None]
    lining = lining * (1 - tongue[:, None]) + tcol * tongue[:, None]
    gum = smooth(0.03, 0.07, v) * (1 - smooth(0.13, 0.2, v))  # gums behind the lip
    lining = lining * (1 - gum[:, None]) + c(96, 44, 40) * gum[:, None]
    lip = 1 - smooth(0.0, 0.05, v)                             # lip edge near the skin colour
    lining = lining * (1 - lip[:, None]) + c(34, 46, 58) * lip[:, None]
    deep = smooth(0.3, 1.0, v)                                 # throat: toward red-black
    lining = lining * (1 - 0.6 * deep[:, None]) + c(60, 12, 14) * (0.35 * deep * (1 - deep))[:, None]
    lining = lining * (1 - 0.85 * smooth(0.65, 1.0, v))[:, None]
    corner = np.minimum(np.minimum(u, np.abs(u - 0.5)), 1 - u)
    lining = lining * (0.75 + 0.25 * smooth(0.0, 0.06, corner))[:, None]
    lining = lining * (1 + 0.10 * noise + 0.08 * nco)[:, None]
    out = img.copy()
    out[cav] = np.clip(lining, 0, 1)
    return out


EYE_R_IRIS, EYE_R_SOCKET = 0.048, 0.064   # m from the eyeball centre: red eye, then a dark rim into the skin


def eye_fields(size):
    """Per texel: eye weight (1 on the eyeball and the socket skin around it, fading to 0 at EYE_R_SOCKET) and the eye
    colour: MM9's red eye with a dark vertical pupil, from each texel's bind position in the eye's own frame (axis =
    mean skin normal of the socket). The retexture painted a blue-grey socket patch with a thin red slit; this replaces
    both, and the texels leave every tier region. Returns (weight, rgb) or None."""
    if not EYE_NPZ.exists():
        return None
    de = np.load(EYE_NPZ)
    ex = de['xyz'][de['grp'].max(1) > 0.5].reshape(-1, 3)
    cx = float((ex[:, 0].max() + ex[:, 0].min()) / 2)
    centres = [ex[(ex[:, 0] - cx) * sd > 0].mean(0) for sd in (1, -1)]
    db = np.load(HERE / 'work' / f'uv3d_{BODY}.npz')
    fields = HERE / 'work' / f'uv3d_{BODY}_eyefields.npz'
    np.savez(fields, uv=db['uv'], px=db['xyz'][..., 0], py=db['xyz'][..., 1], pz=db['xyz'][..., 2],
             nx=np.repeat(db['normal'][:, 0:1], 3, 1), ny=np.repeat(db['normal'][:, 1:2], 3, 1),
             nz=np.repeat(db['normal'][:, 2:3], 3, 1))
    tri_, f_, _ = raster(fields, size, ['px', 'py', 'pz', 'nx', 'ny', 'nz'])
    cov = tri_ >= 0
    p = np.stack([f_['px'], f_['py'], f_['pz']], -1)
    nrm = np.stack([f_['nx'], f_['ny'], f_['nz']], -1)
    weight = np.zeros((size, size), np.float32)
    rgb = np.zeros((size, size, 3), np.float32)
    for c in centres:
        q = p - c
        dist = np.linalg.norm(q, axis=-1)
        near = cov & (dist < EYE_R_SOCKET)
        a = nrm[near & (dist > 0.03)].mean(0)
        a /= np.linalg.norm(a)
        h = np.cross(a, [0, 0, 1.0]); h /= np.linalg.norm(h)
        up = np.cross(h, a)
        qh, qu = q @ h, q @ up
        rho = np.hypot(qh, qu)
        w = np.where(near, 1 - smooth(EYE_R_IRIS, EYE_R_SOCKET, rho), 0)
        iris = 1 - smooth(EYE_R_IRIS - 0.008, EYE_R_IRIS, rho)
        glow = 1 - 0.45 * smooth(0.0, EYE_R_IRIS, rho)          # brighter toward the centre
        col = np.array([0.80, 0.07, 0.04]) * glow[..., None]
        rim = np.array([0.06, 0.03, 0.04])
        col = col * iris[..., None] + rim * (1 - iris[..., None])
        pupil = (1 - smooth(0.006, 0.011, np.abs(qh))) * (1 - smooth(0.026, 0.034, np.abs(qu)))
        col = col * (1 - 0.92 * pupil[..., None])
        sel = w > weight
        weight = np.where(sel, w, weight)
        rgb = np.where(sel[..., None], col, rgb)
    return weight, rgb


def paint_eyes(img):
    """MM9's red eyes over the eyeball and its socket (eye_fields)."""
    ef = eye_fields(img.shape[0])
    if ef is None:
        return img
    w, rgb = ef
    return img * (1 - w[..., None]) + rgb * w[..., None]


def mouth_eye_mask(size):
    """True on texels the tier ramps must not recolour: the mouth lining and the eyeballs (MM9's red eyes)."""
    m = np.zeros((size, size), bool)
    mt = mouth_texels(size)
    if mt is not None:
        m |= ndimage.binary_dilation(mt[0], iterations=2)
    ef = eye_fields(size)
    if ef is not None:
        m |= ndimage.binary_dilation(ef[0] > 0.02, iterations=1)
    return m


# ---------------- our texel classes (1K)
S = 1024
tri, f, dbody = raster(HERE / 'work' / f'uv3d_{BODY}.npz', S, ['limb', 'head'])
covered = tri >= 0
part = np.where(covered, dbody['part'][np.maximum(tri, 0)], -1)
base2k = np.asarray(Image.open(M / 'texture_urls_0_base_color.png').convert('RGB').resize((2048, 2048), Image.LANCZOS),
                    np.float32) / 255   # 4K Meshy paint downsampled once
base = np.asarray(Image.fromarray((base2k * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS), np.float32) / 255
h, s, v = hsv(base)
HUES = ((320, 20), (20, 150), (150, 250), (250, 320))  # red/magenta, olive/brown/yellow, teal/blue, violet


def hue_classes(h, covered, sigma):
    """Per-texel hue bin, smoothed (indicator maps blurred, argmax) so scale patterns do not flicker between bins."""
    ind = []
    for lo, hi in HUES:
        m = ((h >= lo) | (h < hi)) if lo > hi else ((h >= lo) & (h < hi))
        ind.append(ndimage.gaussian_filter((m & covered).astype(np.float32), sigma))
    return np.argmax(np.stack(ind), 0)


tri_c = np.maximum(tri, 0)
chain_t = dbody['chain'][tri_c]
comp_t = dbody['comp'][tri_c]
zc = dbody['xyz'].mean(1)[:, 2]
tmp = HERE / 'work' / 'uv3d_sea_fields.npz'
dcl = np.load(HERE / 'work' / 'uv3d_sea_claws.npz')
np.savez(tmp, **{k: dbody[k] for k in dbody.files}, px=dbody['xyz'][..., 0], py=dbody['xyz'][..., 1],
         pz=dbody['xyz'][..., 2], nz=np.repeat(dbody['normal'][:, 2:3], 3, 1), claw=dcl['grp'])
_, fx, _ = raster(tmp, S, ['px', 'py', 'pz', 'grp', 'nz', 'claw'])
part_t = dbody['part'][tri_c]
ypc = dbody['xyz'].mean(1)[:, 1][tri_c]
fins = covered & ((comp_t == 1) | ((part_t == 2) & (ypc > 0)) | (fx['grp'] > 0.5))
claws = covered & ~fins & ((fx['claw'] > 0.5) | ((part_t == 2) & (ypc <= 0)))
belly = covered & ~fins & ~claws & (fx['nz'] < -0.35)
bodym = covered & ~fins & ~claws & ~belly
keep_base = mouth_eye_mask(S)
fins, claws, belly, bodym = (m & ~keep_base for m in (fins, claws, belly, bodym))
flesh, green, mouth, violet = bodym, belly, fins, claws
classes = np.zeros((S, S), np.uint8)
for k, m in enumerate((flesh, green, mouth, violet)):  # body, belly, fins, claws
    classes[m] = k + 1
regions = [feather(m, covered) for m in (flesh, green, mouth, violet)]
RV.write_mask(regions, T / f'{BODY}_region_mask.png')
Image.fromarray(classes * 80).save(T / f'{BODY}_material_classes.png')
tri2, _, _ = raster(HERE / 'work' / f'uv3d_{BODY}.npz', 2048, [])
painted = paint_eyes(paint_mouth(pad(base2k, tri2 >= 0)))
Image.fromarray((painted * 255).astype(np.uint8)).save(T / f'{BODY}_basecolor.png')
nrm = np.asarray(Image.open(M / 'texture_urls_0_normal.png').convert('RGB').resize((2048, 2048), Image.LANCZOS),
                 np.float32) / 255
nrm = pad(nrm, tri2 >= 0)
mt2 = mouth_texels(2048)
if mt2 is not None:
    nrm[ndimage.binary_dilation(mt2[0], iterations=2)] = (0.5, 0.5, 1.0)   # smooth wet lining
Image.fromarray((nrm * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS).save(
    T / f'{BODY}_normal_1k.png')
rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((S, S), Image.LANCZOS),
                   np.float32) / 255
rough = np.where(violet, np.clip(rough, 0.25, 0.45), np.clip(rough, 0.35, 0.6))  # wet scales, glossy claws
rough = pad(rough, covered)
mt1 = mouth_texels(S)
if mt1 is not None:
    rough[ndimage.binary_dilation(mt1[0], iterations=1)] = 0.45   # wet, but not the old mirror-like panel
ao = np.asarray(Image.open(T / f'{BODY}_ao_2k.png').convert('L').resize((S, S), Image.LANCZOS), np.float32) / 255
Image.merge('RGB', [Image.fromarray((ao * 255).astype(np.uint8)), Image.fromarray((rough * 255).astype(np.uint8)),
                    Image.new('L', (S, S), 0)]).save(T / f'{BODY}_metal_rough_1k.png')

# ---------------- MM9 tier colours on our texels: every texel's bind position takes the colour of the nearest point
# of the MM9 model's surface (our mesh is fitted to the MM9 bind pose), sampled in each tier's MM9 skin. Only colour
# statistics per region are taken from it (bands below); the mask stays structural.
from scipy.spatial import cKDTree
dmm = np.load(HERE / 'work' / f'uv3d_mm9_{BODY}.npz')
rng = np.random.default_rng(0)
pts, uvs = [], []
areas = 0.5 * np.linalg.norm(np.cross(dmm['xyz'][:, 1] - dmm['xyz'][:, 0], dmm['xyz'][:, 2] - dmm['xyz'][:, 0]), axis=1)
density = 4e5 / areas.sum()  # about 400k surface samples in all
for t in range(len(dmm['xyz'])):
    X, U = dmm['xyz'][t], dmm['uv'][t]
    area = 0.5 * np.linalg.norm(np.cross(X[1] - X[0], X[2] - X[0]))
    n = max(8, int(area * density))
    r = rng.random((n, 2)); flip = r.sum(1) > 1; r[flip] = 1 - r[flip]
    w = np.column_stack([1 - r.sum(1), r])
    pts.append(w @ X); uvs.append(w @ U)
pts, uvs = np.concatenate(pts), np.concatenate(uvs)
P3 = np.stack([fx['px'], fx['py'], fx['pz']], -1)[covered]
_, nn = cKDTree(pts).query(P3)
muv = uvs[nn]
ms = 256
col = np.clip((muv[:, 0] * ms).astype(int), 0, ms - 1)
row = np.clip(((1 - muv[:, 1]) * ms).astype(int), 0, ms - 1)
skins = {k: np.asarray(Image.open(HERE / 'source' / p).convert('RGB'), np.float32) / 255 for k, p in TIERS.items()}
proj = {}
for k in TIERS:
    img = np.zeros((S, S, 3), np.float32)
    img[covered] = skins[k][row, col]
    proj[k] = img
Image.fromarray((np.concatenate([proj[k] for k in TIERS], 1) * 255).astype(np.uint8)).save(
    HERE / 'work' / 'mm9_projected_tiers.png')
mm9_sets = {'body': flesh, 'belly': green, 'fins': mouth, 'claws': violet}
counts = {k: int(m.sum()) for k, m in mm9_sets.items()}


def chroma_targets(graded, weight, mm9_mask):
    core = weight > 0.5
    glum = lin(graded[core]) @ W
    rank = np.empty(glum.size)
    rank[np.argsort(glum)] = (np.arange(glum.size) + 0.5) / glum.size
    ours = lin(graded[core])
    our_sat = float(np.abs(ours / np.maximum(glum, 1e-3)[:, None] - 1).mean())

    def bands(k):
        pal = lin(proj[k][mm9_mask & (weight > 0.5)])
        pal = pal[np.argsort(pal @ W)]
        mid = pal[int(0.15 * len(pal)):int(0.95 * len(pal))]
        out = []
        for b in np.array_split(mid, 6):
            c = b / np.maximum(b @ W, 1e-3)[:, None]
            m = c.mean(0)
            # multi-hue skins (the iridescent bell: purple darks, lavender-blue mids, teal lights) average toward
            # grey: keep each luminance band's mean hue but restore the texels' own mean saturation
            dev = m - 1
            target = 1.0 * float(np.linalg.norm(c - 1, axis=1).mean())
            n = float(np.linalg.norm(dev))
            out.append(1 + dev * (max(target, n) / max(n, 1e-6)) if n > 1e-6 else m)
        return pal, np.array(out)

    pal_a, band_a = bands(TIER_A)
    k_sat = float(np.clip(our_sat / max(float(np.abs(band_a - 1).mean()), 1e-3), 0.8, 1.8))
    targets = {TIER_A: graded.copy()}
    for k in TIERS:
        # tier A too takes its MM9 skin's hue (SeaCreatureF navy blue; the retexture came out cyan), at our luminance
        pal, band = bands(k)
        x = np.clip(rank, 0, 1) * (len(band) - 1)
        i0 = np.minimum(x.astype(int), len(band) - 2)
        fr = (x - i0)[:, None]
        chroma = band[i0] * (1 - fr) + band[i0 + 1] * fr
        chroma = 1 + (chroma - 1) * k_sat
        # brightness: the MM9 tier/A ratio, and all tiers pulled toward MM9 A's own (darker) brightness, at most 35 %
        gain = float((pal @ W).mean()) / float((pal_a @ W).mean()) * float(
            np.clip(float((pal_a @ W).mean()) / float(glum.mean()), 0.65, 1.0)) * DARKEN
        tgt = graded.copy()
        tgt[core] = encode(np.clip(chroma * (glum * gain)[:, None], 0, 1))
        targets[k] = tgt
    return targets


graded = RV.load_srgb(T / f'{BODY}_basecolor_graded.png', S) if (T / f'{BODY}_basecolor_graded.png').exists() else base
report, ramps = [], {k: [] for k in TIERS}
previews = {k: graded.copy() for k in TIERS}
for name, weight in zip(REGIONS, regions):
    targets = chroma_targets(graded, weight, mm9_sets[name])
    fitted, rep = RV.fit_ramps(graded, targets, weight)
    for k in TIERS:
        ramps[k].append(fitted[k])
        core = weight > 0.5
        previews[k][core] = targets[k][core]
    report.append({'region': name, **{k: v.get('mean_abs_8bit') if isinstance(v, dict) else v for k, v in rep.items()}})
json.dump({'variants': list(TIERS), 'mm9_region_texels': counts, 'report': report,
           'sources': {k: f'source/{p}' for k, p in TIERS.items()},
           'materials': [{'base': MAT, 'prefix': MAT, 'mask': f'{BODY}_region_mask.png', 'ramps': ramps}]},
          open(T / f'{BODY}_ramps.json', 'w'), indent=1)
prev = np.zeros((S, S, 3))
prev[flesh] = (0.2, 0.4, 0.9)
prev[green] = (0.9, 0.7, 0.4)
prev[mouth] = (0.6, 0.8, 0.2)
prev[violet] = (0.9, 0.2, 0.2)
(HERE / 'review').mkdir(exist_ok=True)
row = [prev] + [previews[k] for k in TIERS]
Image.fromarray((np.concatenate(row, 1) * 255).astype(np.uint8)).resize((512 * len(row), 512)).save(
    HERE / 'review' / f'{BODY}_texture_classes_tiers.png')
print('COMPOSED', json.dumps({'mm9_texels': counts, 'fit': report}))
