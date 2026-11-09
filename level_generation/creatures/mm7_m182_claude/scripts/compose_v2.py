"""v2 texture compose (system Python): body and head from the bakes of the v1 Meshy paint onto the new mirrored
layout (scripts/bake_v2.py), wings from the procedural set (scripts/wing_texture.py); region mask, material classes,
metal/roughness and native palette ramps as v1 (scripts/compose_textures.py), in the same three-domain atlas.

Body/head steps: texels whose bake rays missed the source take the colour/normal of the nearest hit texel in 3D;
the eye takes the native red iris; the throat (white patch under the jaw, pale stripe down the neck front: Meshy
never saw it, the head hides it in the front master) is repainted with gold ventral plates continued from the
chest (scripts/throat.py); the head set is matched to the body across the neck seam (scripts/neck_seam.py);
AO multiplies the base colour (0.82 + 0.18 AO) as v1.
Writes textures/dragon_* (v2) and textures/dragon_ramps.json; atlas layout in work/atlas_layout.json."""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
P = Path(__file__).resolve().parents[1]; T = P / 'textures'; B = P / 'work/v2/bake'; W2 = P / 'work/v2'; N = 2048; REPO = P.parents[2]
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
sys.path.insert(0, str(REPO / 'tools')); from merge_head_material import Atlas  # noqa: E402
sys.path.insert(0, str(P / 'scripts')); from straighten import straighten  # noqa: E402
import throat, neck_seam  # noqa: E402
GAIN = 1.3
VARIANTS = {'m182_a': 183, 'm182_b': 184, 'm182_c': 185}
EYE = straighten(np.array([[.0022, -.3525, .4283]]))[0]          # v1 left eye moved into the v2 frame
lin = lambda c: np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)


def load(path, mode='RGB', size=N): return np.array(Image.open(path).convert(mode).resize((size, size), Image.Resampling.LANCZOS), float) / 255
def save(a, path): Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255 + .5)).save(path)
def pad(a, cov): return a[tuple(ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True))]
def hsv(rgb):
    h, s, v = np.moveaxis(np.array(Image.fromarray(np.uint8(np.clip(rgb, 0, 1) * 255)).convert('HSV'), float) / 255, -1, 0)
    return h * 360, s, v


D = {}; report = {}
for label in ['body', 'head']:
    r = np.load(W2 / f'uvraster_{label}.npz'); cov = r['piece'] >= 0; pos = r['pos']; nrm = r['normal']
    raw = np.array(Image.open(B / f'{label}_color.png').convert('RGBA'), float) / 255
    hit = (np.array(Image.open(B / f'{label}_hit.png').convert('L'), float) / 255 > .5) & (raw[..., 3] > .5)
    rgb = raw[..., :3].copy(); normal = np.array(Image.open(B / f'{label}_normal.png').convert('RGB'), float) / 255
    miss = cov & ~hit
    if miss.any():
        # colour: the nearest hit in 3D, low-passed, plus the scale detail of a donor 5 cm further down the flank
        # (a plain nearest fill smears the rebuilt shoulder into flat cells)
        src = np.argwhere(cov & hit); tree = cKDTree(pos[cov & hit]); _, j = tree.query(pos[miss]); s = src[j]
        rgb[miss] = rgb[s[:, 0], s[:, 1]]; normal[miss] = normal[s[:, 0], s[:, 1]]
        m = cov.astype(float); low = np.stack([ndimage.gaussian_filter(rgb[..., c] * m, 6) / np.maximum(ndimage.gaussian_filter(m, 6), 1e-4) for c in range(3)], -1)
        donor_pos = pos[miss] + np.array([0, 0, -.05]) * np.sign(pos[miss][:, :1] * 0 + 1)
        _, jd = tree.query(donor_pos); sd = src[jd]
        detail = rgb[sd[:, 0], sd[:, 1]] - low[sd[:, 0], sd[:, 1]]
        rgb[miss] = np.clip(low[miss] + detail, 0, 1)
        normal[miss] = normal[sd[:, 0], sd[:, 1]]
    report[label] = {'covered_texels': int(cov.sum()), 'missed_texels_filled': int(miss.sum())}
    D[label] = {'rgb': rgb, 'normal': normal, 'cov': cov, 'pos': pos, 'nrm': nrm, 'piece': r['piece']}

# throat repaint and neck seam match work across both sets (3D positions)
report['throat'] = throat.repaint(D)
report['neck_seam'] = neck_seam.match(D)

for label in ['body', 'head']:
    d = D[label]; rgb, cov, pos, nrm = d['rgb'], d['cov'], d['pos'], d['nrm']; h, s, v = hsv(rgb)
    ivory = cov & (s < .32) & (v > .5) & ~d.get('throat', np.zeros_like(cov))
    classes = np.zeros((N, N), np.uint8); classes[cov] = 1
    mouth = cov & ((h < 25) | (h > 330)) & (s > .3) & (pos[..., 1] < -.33) & (pos[..., 2] < .43)
    eye = np.zeros((N, N), bool)
    if label == 'head':
        eye = cov & (np.linalg.norm(pos - EYE, axis=-1) < .0042) & (d['piece'] == 0)
        iris = eye & (v > .22); rgb[iris] = rgb[iris].max(1)[:, None] * np.array([1., .12, .06])
    ventral = (nrm[..., 2] < -.25) | ((nrm[..., 1] < -.55) & (np.abs(pos[..., 0]) < .035) & (pos[..., 2] < .40))
    gold = cov & (((h > 35) & (h < 62) & (s > .45) & (v > .30) & ventral & ~mouth & ~eye) | d.get('throat', np.zeros_like(cov)))
    spines = cov & (h > 35) & (h < 95) & (s > .45) & (v > .40) & ~ventral & ~mouth & ~eye & ~ivory & ~gold
    scales = cov & ~ivory & ~mouth & ~eye & ~gold & ~spines
    classes[ivory] = 4; classes[ivory & mouth] = 5; classes[eye] = 6; classes[mouth & ~ivory] = 7
    teeth = ivory & (pos[..., 1] < -.35) & (pos[..., 2] < .425) & (np.abs(pos[..., 0]) < .02); classes[teeth] = 5
    ao = ndimage.gaussian_filter(pad(load(B / f'{label}_ao_1k.png', 'L'), cov), 1.0); rgb = rgb * (.82 + .18 * ao[..., None])
    d.update({'rgb': rgb, 'masks': [scales, np.zeros((N, N), bool), gold, spines], 'classes': classes, 'ao': ao})
    report[label] |= {'region_texels': [int(m.sum()) for m in d['masks']], 'eye_texels': int(eye.sum()), 'mouth_texels': int(mouth.sum())}

# wings: procedural set
wr = np.load(W2 / 'wings_proc_regions.npz')['region']; wcov = np.load(W2 / 'uvraster_wings.npz')['piece'] >= 0
wrgb = load(W2 / 'wings_proc_basecolor_2k.png'); wn = load(W2 / 'wings_proc_normal_2k.png')
wcls = np.array(Image.open(W2 / 'wings_proc_material_classes.png'), np.uint8)
painted = wr >= 0 | (wcls > 0)
wao = ndimage.gaussian_filter(load(B / 'wings_ao_1k.png', 'L'), 1.0)
wao = np.where(wcov & (wr == 0), wao, 1.); wrgb = wrgb * (.85 + .15 * wao[..., None])   # AO on the bones only: both membrane layers share texels, their mixed AO came out as clouds
# the arm leaves the shoulder in body colour and darkens to the bone colour over its first 40 %
lay = json.loads(str(np.load(W2 / 'wing_left.npz')['layout'])); A = lay['arm']
bd = D['body']; near = bd['cov'] & (np.linalg.norm(bd['pos'] - np.array([.065, -.268, .30]), axis=-1) < .035)
body_mean = np.median(bd['rgb'][near], 0)
cc, rr = np.meshgrid(np.arange(N) + .5, np.arange(N) + .5); U_ = cc / N; V_ = 1 - rr / N
arm = (U_ >= A['origin_uv'][0] - .003) & (U_ <= A['origin_uv'][0] + A['length'] * A['scale'] + .006) & (V_ >= A['origin_uv'][1] - .003) & (V_ <= A['origin_uv'][1] + 1.2 * A['height_uv'])
sfrac = np.clip((U_ - A['origin_uv'][0]) / (A['length'] * A['scale']), 0, 1)
wgt = np.clip(1 - sfrac / .4, 0, 1) ** 1.5 * arm
lum_w = wrgb @ np.array([.2126, .7152, .0722]); lum_b = float(body_mean @ np.array([.2126, .7152, .0722]))
arm_mean = np.median(lum_w[arm & (sfrac > .5)])
tinted = body_mean[None, None, :] * (lum_w / max(arm_mean, 1e-4))[..., None] * (lum_b / max(lum_b, 1e-4))
wrgb = wrgb * (1 - wgt[..., None]) + np.clip(tinted, 0, 1) * wgt[..., None]
D['wings'] = {'rgb': wrgb, 'normal': wn, 'cov': wcls > 0, 'masks': [wr == 0, wr == 1, np.zeros((N, N), bool), np.zeros((N, N), bool)],
              'classes': wcls, 'ao': wao}
report['wings'] = {'membrane_texels': int((wr == 1).sum()), 'bone_texels': int((wr == 0).sum())}

# native pixels per region (standing and flight frames, all five views), ramps as v1
manifest = json.loads((REPO / 'level_generation/creatures/mm7_m182/manifest.json').read_text())
index_sets = [r['native_indices'] for r in manifest['variants'][0]['regions']] + [list(range(88, 104))]
sprites = REPO / 'assets_dev/engine/sprites'; listing = {e.lower(): e for e in os.listdir(sprites)}
ids = np.concatenate([np.asarray(Image.open(sprites / listing[f'm182{a}{v}.bmp'])).ravel() for a in ('sa', 'wa', 'wb', 'wc', 'wd', 'we', 'wf') for v in range(5)])
ids = ids[ids != 0]
side_ids = np.concatenate([np.asarray(Image.open(sprites / listing[f'm182{a}{v}.bmp'])).ravel() for a in ('sa', 'wa', 'wb', 'wc', 'wd', 'we', 'wf') for v in (1, 2, 3)])
side_ids = side_ids[side_ids != 0]
# Native rank mapping per region. The membrane index set also paints the dark shading of edge-on and shadowed wings
# (its pixels span sRGB 5..254), and plain rank matching spread the procedural membrane over that whole range: dark
# green with bright cell dots (v1's dark mottling). v2 samples the side views (broad membranes) and maps texture
# rank q to native rank 0.25 + 0.50 q^0.8 (top 25 % left out: baked highlights), from the set's grey-green entries only (saturation < 0.45; the set also
# holds the yellow dorsal accents): cell interiors land on the light grey-green of the restored membranes (median
# sRGB ~100/110/85), cell borders and veins on mid greens. The spine set ends in near-white highlights that
# turned dorsal spines white; its top 15 % is left out.
QMAP = {1: lambda q: .25 + .50 * q ** .8, 3: lambda q: .85 * q}
pal = {pid: np.frombuffer((REPO / f'assets_dev/worlds/mm7/textures/pal{pid}.act').read_bytes()[:768], np.uint8).reshape(256, 3) / 255 for pid in VARIANTS.values()}
ramps = {name: [] for name in VARIANTS}; ramp_report = []
for region, index_set in enumerate(index_sets):
    lum = np.concatenate([R.luminance(D[l]['rgb'])[D[l]['masks'][region]] for l in D])
    values = np.sort(lum); lo, hi = np.percentile(values, [.5, 99.5]); quant = np.searchsorted(values, np.linspace(lo, hi, 16)) / len(values)
    native = (side_ids if region == 1 else ids); native = native[np.isin(native, index_set)]
    if region == 1:                                  # the set also holds the yellow dorsal accents: keep the grey-greens
        c = pal[183][native]; sat = (c.max(1) - c.min(1)) / np.maximum(c.max(1), 1e-6); native = native[sat < .45]
    order = np.argsort(R.luminance(pal[183][native])); half = max(2, len(order) // 100)
    if region in QMAP: quant = QMAP[region](quant)
    for name, pid in VARIANTS.items():
        colours = pal[pid][native][order]; stops = []
        for q in quant:
            c0 = int(q * (len(order) - 1)); rgb = np.median(colours[max(0, c0 - half):c0 + half + 1], axis=0)
            stops.append(R.srgb_to_linear(np.clip(rgb * GAIN, 0, 1)).tolist())
        ramps[name].append({'range': [float(lo), float(hi)], 'colors': stops})
    ramp_report.append({'region': region, 'texels': int(len(values)), 'native_pixels': int(len(native)),
                        'native_median_srgb': {name: np.round(np.median(pal[pid][native], 0), 3).tolist() for name, pid in VARIANTS.items()}})

for label, d in D.items():
    cov = d['cov']; classes = d['classes']; rough = np.full((N, N), .80); spec = np.full((N, N), .18)
    for cls, r_, s_ in [(3, .84, .10), (4, .45, .35), (5, .35, .45), (6, .15, .55), (7, .75, .08)]: rough[classes == cls] = r_; spec[classes == cls] = s_
    spec *= .35 + .65 * d['ao']
    maps = {'basecolor': pad(d['rgb'], cov), 'normal': pad(d['normal'], cov), 'metal_rough': np.stack([pad(spec, cov), pad(rough, cov), np.zeros_like(rough)], -1),
            'ao': pad(d['ao'], cov)}
    for name, a in maps.items(): save(a, T / f'dragon_{label}_{name}_2k.png')
    Image.fromarray(pad(classes, cov)).save(T / f'dragon_{label}_material_classes.png')
    weights = [ndimage.gaussian_filter(pad(w.astype(float), cov), .65) for w in d['masks']]
    R.write_mask(weights, T / f'dragon_{label}_region_mask.png', size=N)
a = Atlas((N, N), (N, N)); ab = Atlas((a.width, N), (N, N))
for name in ['basecolor_2k', 'normal_2k', 'metal_rough_2k', 'ao_2k', 'material_classes', 'region_mask']:
    images = [Image.open(T / f'dragon_{label}_{name}.png') for label in ['body', 'head', 'wings']]
    ab.compose(a.compose(images[0], images[1]), images[2]).save(T / f'dragon_{name}.png')
cfg = {'variants': list(VARIANTS), 'palettes': VARIANTS, 'materials': [{'base': 'Dragon_A', 'prefix': 'Dragon', 'mask': 'dragon_region_mask.png',
       'regions': ['scales', 'membranes', 'ventral_gold', 'spines'], 'ramps': ramps}], 'gain': GAIN, 'ramp_report': ramp_report, 'report': report}
(T / 'dragon_ramps.json').write_text(json.dumps(cfg, indent=2) + '\n')
(P / 'work/atlas_layout.json').write_text(json.dumps({'width': ab.width, 'height': N, 'domain_width': N, 'offsets': [0, N + 32, 2 * N + 64]}, indent=2) + '\n')
print('COMPOSE', json.dumps(report))
