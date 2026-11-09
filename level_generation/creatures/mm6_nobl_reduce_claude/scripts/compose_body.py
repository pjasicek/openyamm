"""1K body maps for the retextured, chest-repaired Swordsman (rules of ../mm6_nobl_codex/scripts/compose_nobl.py):
- Meshy's tunic buttons/seam, ghost chain and stray paint replaced by the nearest wanted texel in 3D (no blur);
- classes from the new Meshy colours: cloak = olive texels on faces the installed mask called cloak, tunic = red
  texels on its tunic faces, gold = yellow, silver = pale grey, leather = dark brown, cloth = the rest; nothing of the
  installed texture or mask is pasted;
- gold and silver graded to the project's target colours, AO (work/ao_body.npy) multiplied in, then cloak, tunic and
  the rest median-luminance-matched to the same classes of the installed texture, so the installed tier ramps still fit;
- flat colour squares (work/flat_squares.json): cord silver, necklace, pendant and belt buckle gold, gem deep red;
- normal (convention measured), specular/roughness per class; region mask R cloak, G tunic.
REA_SET=detail composes the front detail set the same way (detail_uv.py, meshy/detail_retexture_r62b, work/ao_detail.npy).
Writes textures/nobl_<set>_{basecolor,normal,metal_rough}_<1k|2k>.png, nobl_<set>_region_mask.png, review/<set>_classes.png."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P = Path(__file__).resolve().parents[1]; ROOT = P.parents[2]
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
sys.path.insert(0, str(ROOT / 'tools')); from normal_map_convention import measure  # noqa: E402
from merge_head_material import read_glb, image_of  # noqa: E402
import os
SET = os.environ.get('REA_SET', 'body')          # body, or detail (the front detail set, detail_uv.py)
N = 2048 if SET == 'detail' else 1024            # the detail section keeps Meshy's full resolution
M = P / ('meshy/detail_retexture_r62b' if SET == 'detail' else 'meshy/body_retexture_r62'); T = P / 'textures'
TARGET = {'gold': (183, 145, 62), 'silver': (160, 164, 160)}
FLAT = {1: ((192, 196, 200), 'silver'), 2: ((183, 145, 62), 'gold'), 3: ((183, 145, 62), 'gold'), 4: ((122, 16, 28), 'gem'), 5: ((183, 145, 62), 'gold')}
SURFACE = {'leather': (.3, .65), 'silver': (.75, .35), 'gold': (.85, .3), 'cloth': (.05, .9), 'gem': (.9, .2)}
AO_STRENGTH, AO_FLOOR = .5, .3


def raster(uv, n=N, pos3=None):
    cov = np.zeros((n, n), bool); tri = np.full((n, n), -1, np.int32); pos = np.zeros((n, n, 3), np.float32)
    for i, t in enumerate(uv * n):
        lo = np.maximum(0, np.floor(t.min(0)).astype(int)); hi = np.minimum(n - 1, np.ceil(t.max(0)).astype(int))
        m = np.column_stack([t[1] - t[0], t[2] - t[0]])
        if hi[0] < lo[0] or hi[1] < lo[1] or abs(np.linalg.det(m)) < 1e-12:
            continue
        xx, yy = np.meshgrid(np.arange(lo[0], hi[0] + 1) + .5, np.arange(lo[1], hi[1] + 1) + .5)
        w = (np.stack([xx, yy], -1) - t[0]) @ np.linalg.inv(m).T; w0 = 1 - w.sum(-1)
        inside = (w[..., 0] >= -.02) & (w[..., 1] >= -.02) & (w0 >= -.02)
        rows = n - 1 - (yy[inside] - .5).astype(int); cols = (xx[inside] - .5).astype(int)
        cov[rows, cols] = True; tri[rows, cols] = i
        if pos3 is not None:
            p = pos3[i]; pos[rows, cols] = w0[inside, None] * p[0] + w[inside, 0, None] * p[1] + w[inside, 1, None] * p[2]
    return cov, tri, pos


def hsv(rgb):
    return np.asarray(Image.fromarray(np.uint8(np.clip(rgb, 0, 1) * 255)).convert('HSV'), float) / 255


def classes(rgb, cov, cloak_face, tunic_face):
    h = hsv(rgb); hue, sat, val = h[..., 0] * 360, h[..., 1], h[..., 2]
    yellow = (hue > 32) & (hue < 65) & (sat > .3) & (val > .35)
    red = ((hue < 25) | (hue > 320)) & (sat > .25)
    pale = (sat < .18) & (val > .5)
    c = {}
    c['cloak'] = cov & cloak_face & ~pale & ~(yellow & (val > .6) & (sat > .5))
    c['tunic'] = cov & tunic_face & red & ~yellow
    c['gold'] = cov & yellow & ~c['cloak']
    c['silver'] = cov & pale & ~c['cloak'] & ~c['tunic']
    c['leather'] = cov & (hue > 5) & (hue < 45) & (sat > .25) & (val < .45) & ~c['cloak'] & ~c['tunic'] & ~c['gold']
    c['cloth'] = cov & ~np.any([c[k] for k in ('cloak', 'tunic', 'gold', 'silver', 'leather')], axis=0)
    return c


def meshy(suffix, mode='RGB'):
    im = Image.open(M / f'texture_urls_0_{suffix}.png').convert(mode)
    if SET == 'detail':   # the detail faces filled the lower-left 94 % of the upload's UV square (1925 px of 2048)
        w, h = im.size; im = im.crop((0, round(h * .06), round(w * .94), h))
    return np.asarray(im.resize((N, N), Image.LANCZOS), float) / 255


blur = lambda x, sg: ndimage.gaussian_filter(x, sg)


def save(a, p):
    Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255 + .5)).save(p, optimize=True)


def pad(a, c):
    return a[tuple(ndimage.distance_transform_edt(~c, return_distances=False, return_indices=True))]


report = {}
# new surface
d = np.load(P / f'work/{SET}_uv.npz'); cov, tri, pos = raster(d['uv'], pos3=d['pos'])
tcls, tpart = d['cls'][np.maximum(tri, 0)], d['part'][np.maximum(tri, 0)]
flat = cov & (tpart > 0); surf = cov & ~flat
# the analytic emblem: a gold V below the belt on the tabard's front layer (y < -0.14; a layer behind it at -0.13
# would show a second stroke), where the installed emblem sits (x 0.048-0.09, z 0.84-0.92 m)
EX0, ETOP, ETIP, EHALF, EWID = .069, .916, .852, .021, .0045


def emblem_dist():
    px, pz = pos[..., 0], pos[..., 2]

    def seg(ax, az, bx, bz):
        vx, vz = bx - ax, bz - az; t = np.clip(((px - ax) * vx + (pz - az) * vz) / (vx * vx + vz * vz), 0, 1)
        return np.hypot(px - ax - t * vx, pz - az - t * vz)
    dist = np.minimum(seg(EX0 - EHALF, ETOP, EX0, ETIP), seg(EX0 + EHALF, ETOP, EX0, ETIP))
    dist = np.minimum(dist, np.abs(px - EX0) + np.abs(pz - (ETIP + .004)) - .0035)   # small diamond at the tip
    front = (pos[..., 1] < -.14) & (pos[..., 2] < .93) & (np.abs(px - EX0) < .05)
    return np.where(front, dist, 1.0)


edist = emblem_dist()
a = meshy('base_color')
from scipy.spatial import cKDTree


def fill3d(bad, good):
    """unwanted paint takes the colour of the nearest wanted texel on the surface (3D, not texture space: no blur and
    no bleeding across unrelated UV islands)"""
    if bad.any() and good.any():
        a[bad] = a[good][cKDTree(pos[good]).query(pos[bad])[1]]


# Meshy painted buttons and a seam down the tunic and tabard (not in the references or the sprite): on tunic faces,
# small texels far darker than their cloth neighbourhood (gold emblem excluded) take the nearest cloth colour
h = hsv(a); gold_px = (h[..., 0] * 360 > 32) & (h[..., 0] * 360 < 65) & (h[..., 1] > .3) & (h[..., 2] > .35)
zone = surf & (tcls == 2) & ~gold_px; L = R.luminance(a)
local = blur(L * zone, 6) / np.maximum(blur(zone.astype(float), 6), 1e-6)
dots = ndimage.binary_dilation(zone & (L < .55 * local), iterations=2) & zone
fill3d(dots, zone & ~dots)
# Meshy's own emblem left a dark outline around where ours goes: dark outliers within 2 cm of it take nearby cloth
near_e = surf & (edist < .02); Le = R.luminance(a)
loc_e = blur(Le * near_e, 6) / np.maximum(blur(near_e.astype(float), 6), 1e-6)
dark_e = ndimage.binary_dilation(near_e & (Le < .7 * loc_e), iterations=1) & near_e
fill3d(dark_e, near_e & ~dark_e); report['emblem_outline_filled'] = int(dark_e.sum())
if SET == 'detail':
    # groups (detail_groups.py): 0 collar/neck, 1 capelet, 2 chest, 3 tabard, 4 belt/clasp (reads the body texture)
    grp = np.load(P / 'work/detail_groups.npy')[np.maximum(tri, 0)]
    h = hsv(a); goldp = (h[..., 0] * 360 > 32) & (h[..., 0] * 360 < 65) & (h[..., 1] > .3) & (h[..., 2] > .35)
    # Meshy's gold on the tunic (a ghost of the modelled chain, its own emblem) and the paint within 1.2 cm of the
    # modelled necklace; cord paint spilled onto the tunic
    stray = (h[..., 0] * 360 > 15) & (h[..., 0] * 360 < 65) & (h[..., 1] > .3) & (h[..., 2] > .3)   # orange to gold
    zone = surf & np.isin(grp, [2, 3]); paint = ndimage.binary_dilation(zone & stray, iterations=1) & zone
    bu = np.load(P / 'work/body_uv.npz'); chain = bu['pos'][np.isin(bu['part'], [2, 3, 4])].reshape(-1, 3)
    near = np.zeros_like(zone); near[zone] = cKDTree(chain).query(pos[zone])[0] < .012
    paint |= near | (zone & (h[..., 1] < .18) & (h[..., 2] > .45))
    fill3d(paint, zone & ~paint)
    # the clasp's gold spilled onto the capelet corners (Meshy's silver trim along the capelet edge is kept)
    cape = surf & (grp == 1); cgold = cape & goldp
    fill3d(cgold, cape & ~cgold)
    report.update(detail_gold_removed=int(paint.sum()), capelet_gold_filled=int(cgold.sum()))
if SET == 'body':
    # Meshy's own emblem on the tabard faces that stay in the body set (the analytic emblem is drawn below), cord paint
    # beside the capelet corners, clasp gold on the capelet
    h = hsv(a); goldp = (h[..., 0] * 360 > 32) & (h[..., 0] * 360 < 65) & (h[..., 1] > .3) & (h[..., 2] > .35)
    tab = surf & (pos[..., 2] < .93) & (pos[..., 2] > .7) & (pos[..., 1] < -.08) & (np.abs(pos[..., 0] + .007) < .16)
    upper = surf & (pos[..., 2] > 1.2) & (pos[..., 2] < 1.4) & (pos[..., 1] < -.08) & (np.abs(pos[..., 0] + .007) < .25)
    cape = surf & (tcls == 1) & (pos[..., 2] > 1.2)
    stray = (h[..., 0] * 360 > 15) & (h[..., 0] * 360 < 65) & (h[..., 1] > .3) & (h[..., 2] > .3)   # orange to gold
    paint = (tab & stray) | (upper & (h[..., 1] < .18) & (h[..., 2] > .45)) | (cape & goldp)
    fill3d(paint, (tab | upper | cape) & ~paint)
    report['body_paint_filled'] = int(paint.sum())
# tunic faces: the installed tunic class, plus red paint anywhere on the torso below the collar (Meshy paints the
# V under the clasp as tunic, as the references show; the installed mask had it as undershirt, so it stayed red in
# every tier). The collar (z > 1.39) keeps its own colours.
torso = (pos[..., 2] > .5) & (pos[..., 2] < 1.39) & (np.abs(pos[..., 0] + .007) < .22) & (pos[..., 1] < .02)
hh = hsv(a); burgundy = ((hh[..., 0] * 360 < 12) | (hh[..., 0] * 360 > 320)) & (hh[..., 1] > .3)   # not belt leather
cl = classes(a, surf, tcls == 1, (tcls == 2) | (torso & burgundy))
# installed body texture and classes (reference distributions only)
doc, binary = read_glb(ROOT / 'assets_source/worlds/mm6/models/mm6_nobl.glb'); mat = doc['materials'][0]
obase = np.asarray(image_of(doc, binary, mat['pbrMetallicRoughness']['baseColorTexture']['index'])[0].convert('RGB'), float)[:, :1024] / 255
omask = np.asarray(image_of(doc, binary, mat['extras']['openyamm_region_mask']['index'])[0].convert('RGBA'), float)[:, :1024] / 255
src = np.load(P / 'work/mesh_in.npz'); w = src['wuv'].reshape(-1, 3, 2); body = w[:, :, 0].mean(1) < .5
ouv = w[body].copy(); ouv[..., 0] *= 2080 / N
ocov, _, _ = raster(ouv, n=1024)
ocl = classes(obase, ocov, omask[..., 0] > .5, omask[..., 1] > .5)

graded = a.copy()
for k, tgt in TARGET.items():
    m = cl[k]
    if m.any():
        graded[m] = a[m] * (np.array(tgt) / 255 / np.maximum(np.median(a[m], 0), 1e-3))
ao = np.load(P / f'work/ao_{SET}.npy')
graded *= (1 - AO_STRENGTH * (1 - np.maximum(ao, AO_FLOOR)))[..., None]
rest, orest = cl['leather'] | cl['cloth'], ocl['leather'] | ocl['cloth']
for name, new, old in (('cloak', cl['cloak'], ocl['cloak']), ('tunic', cl['tunic'], ocl['tunic']), ('rest', rest, orest)):
    ref = R.luminance(obase[old]); q = np.linspace(0, 1, 101)
    # median match only: one gain per region keeps Meshy's own fabric contrast (a full quantile match stretched its
    # fine noise over the installed texture's fold-shading range: speckled, mossy cloth); iterate, gains act on sRGB
    for _ in range(4):
        lum = R.luminance(np.clip(graded[new], 0, 1))
        graded[new] = np.clip(graded[new] * (np.median(ref) / max(np.median(lum), 1e-4)) ** .45, 0, 1)
    report[name] = {'texels': int(new.sum()), 'lum_p10_50_90': [np.round(np.quantile(R.luminance(np.clip(graded[new], 0, 1)), [.1, .5, .9]), 3).tolist(),
                                                               np.round(np.quantile(ref, [.1, .5, .9]), 3).tolist()]}
graded = np.clip(graded, 0, 1)
# the tier ramps were rank-matched to the installed (smoothed) texture, so they spread small luminance steps over the
# whole native palette: Meshy's fine fabric grain would turn into speckle. Inside the two ramped cloth regions the fine
# luminance detail is compressed around a small local mean (masked, sigma 1.5 texels); folds and shading stay.
for m in (cl['cloak'], cl['tunic']):
    lum = R.luminance(graded); wsum = ndimage.gaussian_filter(m.astype(float), 1.5)
    local = ndimage.gaussian_filter(lum * m, 1.5) / np.maximum(wsum, 1e-6)
    target = local * (np.maximum(lum, 1e-4) / np.maximum(local, 1e-4)) ** .4
    for _ in range(3):   # gains act on sRGB values, luminance is linear
        cur = R.luminance(graded)
        graded[m] = np.clip(graded[m] * ((target[m] / np.maximum(cur[m], 1e-4)) ** .45)[:, None], 0, 1)

normal = meshy('normal'); score = measure(np.uint8(normal * 255 + .5)); assert abs(score) > .15, score
if score < 0:
    normal[..., 1] = 1 - normal[..., 1]
normal = normal * 2 - 1; normal /= np.maximum(np.linalg.norm(normal, axis=-1, keepdims=True), 1e-8); normal = (normal + 1) / 2
rough_m = meshy('roughness', 'L'); spec = np.zeros((N, N)); rough = np.zeros((N, N))
surf_cls = {'leather': cl['leather'], 'silver': cl['silver'], 'gold': cl['gold'],
            'cloth': cl['cloak'] | cl['tunic'] | cl['cloth']}
for k, m in surf_cls.items():
    if m.any():
        spec[m] = SURFACE[k][0]; rough[m] = np.clip(SURFACE[k][1] + .5 * (rough_m[m] - np.median(rough_m[m])), .2, 1)
for prt, (rgb, kind) in FLAT.items():
    m = flat & (tpart == prt)
    graded[m] = np.array(rgb) / 255; normal[m] = (.5, .5, 1); spec[m], rough[m] = SURFACE[kind]
    report[f'flat_{prt}'] = int(m.sum())
masks = [cl['cloak'], cl['tunic']]
if True:
    # one clean gold V below the belt (both sets, so faces of either show the same emblem), see emblem_dist()
    emb = np.clip((EWID - edist) / .0018 + .5, 0, 1) * surf
    gold = np.array(TARGET['gold']) / 255 * (1 - AO_STRENGTH * (1 - np.maximum(ao, AO_FLOOR)))[..., None]
    graded = graded * (1 - emb[..., None]) + gold * emb[..., None]
    spec = spec * (1 - emb) + SURFACE['gold'][0] * emb; rough = rough * (1 - emb) + SURFACE['gold'][1] * emb
    masks = [m & (emb < .5) for m in masks]; report['emblem_texels'] = int((emb > .5).sum())
RES = f'{N // 1024}k'
save(pad(graded, cov), T / f'nobl_{SET}_basecolor_{RES}.png'); save(pad(normal, cov), T / f'nobl_{SET}_normal_{RES}.png')
save(np.stack([pad(spec, cov), pad(rough, cov), np.zeros((N, N))], -1), T / f'nobl_{SET}_metal_rough_{RES}.png')
R.write_mask([ndimage.gaussian_filter(pad(m.astype(float), cov), .7 * N / 1024) * ~flat for m in masks], T / f'nobl_{SET}_region_mask.png', size=N)
overlay = graded * .35
for k, col in (('cloak', (.2, .8, .2)), ('tunic', (.9, .1, .3)), ('gold', (1, .8, 0)), ('silver', (.7, .8, 1)), ('leather', (.6, .35, .1))):
    overlay[cl[k]] = col
(P / 'review').mkdir(exist_ok=True); save(overlay, P / f'review/{SET}_classes.png')
report.update(tunic_dots_filled=int(dots.sum()), classes={k: int(v.sum()) for k, v in cl.items()}, installed_classes={k: int(v.sum()) for k, v in ocl.items()}, normal_correlation=score)
(P / f'work/compose_{SET}.json').write_text(json.dumps(report, indent=1)); print(json.dumps(report))
