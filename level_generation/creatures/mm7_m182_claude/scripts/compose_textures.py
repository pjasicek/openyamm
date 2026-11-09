"""Padded MM7 Dragon PBR maps, region mask and native palette ramps for tiers 183/184/185
(structure from mm8_m492_claude/scripts/compose_textures.py; regions and ramps from the MM7 native package).

Regions (mask RGBA = 0..3), from mm7_m182/manifest.json variant regions plus the spine highlights it leaves out:
  0 scales (native indices 1-35, 216-255)      body/head scales and wing spars
  1 membranes (36-61, 104-215)                  wing membranes
  2 ventral gold (62-87)                        throat, belly and tail plates
  3 spines (88-103)                             dorsal spines, cheek frill and crest spikes (yellow-green in tier A)
Ivory horns/claws/teeth, the red mouth and the eyes are in no region (same in every tier). The eyes take the native
red iris (Meshy painted amber). Ramps: each region's native standing/flight pixels ranked by tier-A luminance; the stop
at the rank where the region's texel luminance reaches that stop takes the median native colour x GAIN (the m560
method). Writes textures/dragon_* and textures/dragon_ramps.json; atlas layout in work/atlas_layout.json."""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P = Path(__file__).resolve().parents[1]; T = P / 'textures'; T.mkdir(exist_ok=True); N = 2048; REPO = P.parents[2]
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
sys.path.insert(0, str(REPO / 'tools')); from normal_map_convention import measure  # noqa: E402
from merge_head_material import Atlas  # noqa: E402
GAIN = 1.3
EYES = [np.array((-.0241, -.3563, .4259)), np.array((.0022, -.3525, .4283))]
VARIANTS = {'m182_a': 183, 'm182_b': 184, 'm182_c': 185}

def load(path, mode='RGB'): return np.array(Image.open(path).convert(mode).resize((N, N), Image.Resampling.LANCZOS), float) / 255
def save(a, path): Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255 + .5)).save(path)
def pad(a, cov): return a[tuple(ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True))]
def hsv(rgb):
    h, s, v = np.moveaxis(np.array(Image.fromarray(np.uint8(np.clip(rgb, 0, 1) * 255)).convert('HSV'), float) / 255, -1, 0)
    return h * 360, s, v

def service_map(label, kind):
    a = load(P / 'meshy' / f'{label}_retexture_v1' / f'texture_urls_0_{kind}.png'); source = a.copy()
    for repair in json.loads((P / 'work/texture_uv_parity.json').read_text())[label]['repairs']:
        uv = np.array(repair['target_uv']) * N; dest = np.array(repair['source_uv']) * N
        x0, y0 = np.maximum(np.floor(uv.min(0)).astype(int) - 1, 0); x1, y1 = np.minimum(np.ceil(uv.max(0)).astype(int) + 1, N - 1)
        x, y = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        weights = np.linalg.solve(np.vstack([uv.T, np.ones(3)]), np.stack([x.ravel(), y.ravel(), np.ones(x.size)]))
        mask = (weights >= -.02).all(0); sx, sy = dest.T @ weights[:, mask]
        iy = (N - 1 - (y.ravel()[mask] - .5)).astype(int); ix = (x.ravel()[mask] - .5).astype(int)
        for c in range(a.shape[-1]): a[iy, ix, c] = ndimage.map_coordinates(source[..., c], [N - .5 - sy, sx - .5], order=1, mode='nearest')
    return a

D = {}; report = {}
for label in ['body', 'head', 'wings']:
    d = np.load(P / 'work' / f'uvraster_{label}.npz'); cov = d['piece'] >= 0; pos = d['pos']; nrm = d['normal']
    rgb = service_map(label, 'base_color'); h, s, v = hsv(rgb)
    ivory = cov & (s < .32) & (v > .5)
    classes = np.zeros((N, N), np.uint8); classes[cov] = 1          # 1 hide, 3 membrane, 4 horn/claw, 5 tooth, 6 eye, 7 mouth
    masks = [np.zeros((N, N), bool) for _ in range(4)]
    if label == 'wings':
        masks[1] = cov & ~ivory; classes[masks[1]] = 3
        # Meshy left blurred dark blotches in the membranes: lift low-frequency darkening (sigma 16 px), keep the
        # fine scale pattern and the thin spars (brighten only, at most 2.2x)
        lin = R.srgb_to_linear(rgb); L = lin @ R.LUMA; m = masks[1].astype(float)
        low = ndimage.gaussian_filter(L * m, 16) / np.maximum(ndimage.gaussian_filter(m, 16), 1e-4)
        factor = np.clip(np.median(low[masks[1]]) / np.maximum(low, 1e-4), 1., 2.2) * m + (1 - m)
        rgb = np.clip(np.where(lin <= .0031308, lin * factor[..., None] * 12.92, 1.055 * np.maximum(lin * factor[..., None], 0) ** (1 / 2.4) - .055), 0, 1)
        report['wing_blotch_lift'] = {'median_factor': float(np.median(factor[masks[1]])), 'p95_factor': float(np.percentile(factor[masks[1]], 95))}
    else:
        mouth = cov & ((h < 25) | (h > 330)) & (s > .3) & (pos[..., 1] < -.33) & (pos[..., 2] < .43)
        eye = np.zeros((N, N), bool)
        if label == 'head':
            for c in EYES: eye |= cov & (np.linalg.norm(pos - c, axis=-1) < .0042) & (d['piece'] == 0)
            iris = eye & (v > .22)
            rgb[iris] = rgb[iris].max(1)[:, None] * np.array([1., .12, .06])
        ventral = (nrm[..., 2] < -.25) | ((nrm[..., 1] < -.55) & (np.abs(pos[..., 0] + .005) < .035) & (pos[..., 2] < .40))
        gold = cov & (h > 35) & (h < 62) & (s > .45) & (v > .30) & ventral & ~mouth & ~eye
        spines = cov & (h > 35) & (h < 95) & (s > .45) & (v > .40) & ~ventral & ~mouth & ~eye & ~ivory
        scales = cov & ~ivory & ~mouth & ~eye & ~gold & ~spines
        masks = [scales, np.zeros((N, N), bool), gold, spines]
        classes[ivory] = 4; classes[ivory & mouth] = 5; classes[eye] = 6; classes[mouth & ~ivory] = 7
        teeth = ivory & (pos[..., 1] < -.35) & (pos[..., 2] < .425) & (np.abs(pos[..., 0] + .011) < .02); classes[teeth] = 5
    classes[ivory & (classes == 1)] = 4
    ao = ndimage.gaussian_filter(pad(load(T / f'dragon_{label}_ao_1k.png', 'L'), cov), 1.0); rgb *= .82 + .18 * ao[..., None]
    normal = service_map(label, 'normal'); correlation = measure(np.uint8(normal * 255 + .5))
    if correlation < -.15: normal[..., 1] = 1 - normal[..., 1]
    geo = load(T / f'dragon_{label}_geometry_normal_2k.png', 'RGBA'); valid = geo[..., 3] > .5
    n1 = geo[..., :3] * 2 - 1; n1[~valid] = (0, 0, 1); n2 = normal * 2 - 1
    t = n1 + np.array([0, 0, 1]); u = n2 * np.array([-1, -1, 1]); n = t * np.sum(t * u, axis=-1)[..., None] / np.maximum(t[..., 2:3], 1e-5) - u
    n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-5); normal = n * .5 + .5
    D[label] = {'rgb': rgb, 'masks': masks, 'classes': classes, 'ao': ao, 'normal': normal, 'cov': cov}
    report.setdefault(label, {}); report[label] |= {'covered_texels': int(cov.sum()), 'normal_bake_misses': int((cov & ~valid).sum()), 'normal_source_correlation': correlation,
                     'region_texels': [int(m.sum()) for m in masks], 'eye_texels': int((classes == 6).sum()), 'mouth_texels': int((classes == 7).sum()),
                     'ivory_texels': int(ivory.sum())}

# native pixels per region, standing and flight frames, all five views
manifest = json.loads((REPO / 'level_generation/creatures/mm7_m182/manifest.json').read_text())
index_sets = [r['native_indices'] for r in manifest['variants'][0]['regions']] + [list(range(88, 104))]
sprites = REPO / 'assets_dev/engine/sprites'; listing = {e.lower(): e for e in os.listdir(sprites)}
ids = np.concatenate([np.asarray(Image.open(sprites / listing[f'm182{a}{v}.bmp'])).ravel() for a in ('sa', 'wa', 'wb', 'wc', 'wd', 'we', 'wf') for v in range(5)])
ids = ids[ids != 0]
pal = {pid: np.frombuffer((REPO / f'assets_dev/worlds/mm7/textures/pal{pid}.act').read_bytes()[:768], np.uint8).reshape(256, 3) / 255 for pid in VARIANTS.values()}
ramps = {name: [] for name in VARIANTS}; ramp_report = []
for region, index_set in enumerate(index_sets):
    lum = np.concatenate([R.luminance(D[l]['rgb'])[D[l]['masks'][region]] for l in D])
    values = np.sort(lum); lo, hi = np.percentile(values, [.5, 99.5]); quant = np.searchsorted(values, np.linspace(lo, hi, 16)) / len(values)
    native = ids[np.isin(ids, index_set)]; order = np.argsort(R.luminance(pal[183][native])); half = max(2, len(order) // 100)
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
    maps = {'basecolor': pad(d['rgb'], cov), 'normal': pad(d['normal'], cov), 'metal_rough': np.stack([pad(spec, cov), pad(rough, cov), np.zeros_like(rough)], -1), 'ao': pad(d['ao'], cov)}
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
print('COMPOSE', json.dumps(report), json.dumps(ramp_report))
