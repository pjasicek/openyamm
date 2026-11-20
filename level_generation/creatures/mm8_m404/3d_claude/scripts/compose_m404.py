"""Shared 1K body/head maps, material classes and native mantle ramps for the three warrior tiers."""
from pathlib import Path
import json
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
p = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(p.parents[1] / 'claude_shared'))
import region_variants as regions
out = p / 'textures'
out.mkdir(exist_ok=True)
size = 1024
palettes = {'m404_a': 405, 'm404_b': 406, 'm404_c': 407}


def load(path, mode='RGB'):
    return np.asarray(Image.open(path).convert(mode).resize((size, size), Image.Resampling.LANCZOS), float) / 255


def save(values, path):
    Image.fromarray(np.rint(np.clip(values, 0, 1) * 255).astype('uint8')).save(path)


def pad(image, covered):
    _, indices = ndimage.distance_transform_edt(~covered, return_indices=True)
    result = image[tuple(indices)]
    result[covered] = image[covered]
    return result


def hsv(image):
    values = np.asarray(Image.fromarray(np.uint8(np.clip(image, 0, 1) * 255)).convert('HSV'), float) / 255
    return values[..., 0] * 360, values[..., 1], values[..., 2]


def srgb(linear):
    return np.where(linear <= .0031308, linear * 12.92, 1.055 * np.maximum(linear, 0) ** (1 / 2.4) - .055)


def skin_grade(image, mask):
    lum = regions.luminance(image)
    blurred = ndimage.gaussian_filter(np.where(mask, lum, 0), 6)
    weight = ndimage.gaussian_filter(mask.astype(float), 6)
    detail = np.clip(lum / np.maximum(blurred / np.maximum(weight, 1e-5), 1e-5), .55, 1.5)
    albedo = regions.srgb_to_linear(np.array([104, 113, 128]) / 255)
    repaint = srgb(np.clip(albedo * detail[..., None], 0, 1))
    result = image.copy()
    result[mask] = image[mask] * .6 + repaint[mask] * .4
    return result


report = {}
sets = {}
for suffix, layer, head in [('', 'UVMap', False), ('_head', 'HeadUV', True)]:
    job = p.parent / 'meshy' / ('head_retexture_v1' if head else 'body_retexture_v1')
    base = load(job / 'texture_urls_0_base_color.png')
    normal = load(job / 'texture_urls_0_normal.png')
    original_roughness = load(job / 'texture_urls_0_roughness.png', 'L')
    raster = np.load(p / f'work/uvraster_{layer}.npz')
    piece, position = raster['piece'], raster['pos']
    covered = piece >= 0
    hue, saturation, value = hsv(base)
    classes = np.zeros((size, size), np.uint8)
    classes[covered] = 1 if head else 8
    skin = covered.copy() if head else covered & (piece == 0)
    ivory = skin & (hue > 15) & (hue < 80) & (saturation < .4) & (value > .65)
    if head:
        eye = skin & (hue > 15) & (hue < 65) & (saturation > .5) & (value > .4)
        eye &= position[..., 2] > 1.72
        crest = skin & ((hue < 20) | (hue > 345)) & (saturation > .35) & (position[..., 2] > 1.88)
        ivory &= position[..., 2] < 1.9
    else:
        eye, crest = np.zeros_like(skin), np.zeros_like(skin)
    skin &= ~ivory & ~eye & ~crest
    classes[skin] = 1
    classes[ivory] = 5 if head else 4
    classes[eye] = 6
    classes[crest] = 4
    if not head:
        gold = covered & np.isin(piece, [2, 3, 4, 6]) & (hue > 15) & (hue < 80) & (saturation > .3)
        classes[gold] = 9
    graded = skin_grade(base, skin)
    if head:
        spill = covered & (hue > 70) & (hue < 170) & (saturation > .25)
        graded[spill] = np.array([104, 113, 128]) / 255
    ao = load(p / f'work/ao_{layer}.png', 'L')
    graded[covered] *= (.75 + .25 * np.maximum(ao[covered], .45))[:, None]
    specular = np.zeros((size, size))
    roughness = np.full((size, size), .85)
    for label, spec, rough in [(1, .2, .82), (4, .45, .5), (5, .5, .4), (6, .95, .2),
                               (8, .12, .88), (9, .75, .45)]:
        mask = classes == label
        specular[mask] = spec
        roughness[mask] = np.clip(rough + (original_roughness[mask] - .6) * .25, .15, .98)
    stem = 'm404' + suffix
    save(pad(np.clip(graded, 30 / 255, 243 / 255), covered), out / f'{stem}_basecolor_1k.png')
    save(pad(normal, covered), out / f'{stem}_normal_1k.png')
    save(np.stack([pad(specular, covered), pad(roughness, covered), np.zeros_like(specular)], -1),
         out / f'{stem}_metal_rough_1k.png')
    Image.fromarray(classes).save(out / f'{stem}_material_classes.png')
    mantle = covered & (piece == 1) & (hue > 65) & (hue < 170) & (saturation > .2) if not head else np.zeros_like(skin)
    if not head:
        assert mantle.sum() > 1000
    mask = ndimage.gaussian_filter(pad(mantle.astype(float), covered), .7)
    regions.write_mask([mask], out / f'{stem}_region_mask.png', size=size)
    sets[suffix] = {'base': graded, 'mantle': mantle, 'covered': covered, 'skin': skin}
    report[stem] = {'covered_texels': int(covered.sum()), 'skin_texels': int(skin.sum()),
                    'mantle_texels': int(mantle.sum()), 'class_counts': {
                        str(label): int((classes == label).sum()) for label in np.unique(classes)}}
# Both sets use the body's skin colour; the separate head keeps its own scale detail.
body_skin = sets['']['base'][sets['']['skin']]
head_skin = sets['_head']['base'][sets['_head']['skin']]
body_lum = np.median(regions.luminance(body_skin))
head_lum = np.median(regions.luminance(head_skin))
gain = float(np.clip(body_lum / max(head_lum, 1e-5), .7, 1.4))
head_base = load(out / 'm404_head_basecolor_1k.png')
head_mask = sets['_head']['skin']
head_base[head_mask] = srgb(np.clip(regions.srgb_to_linear(head_base[head_mask]) * gain, 0, 1))
save(pad(np.clip(head_base, 30 / 255, 243 / 255), sets['_head']['covered']), out / 'm404_head_basecolor_1k.png')
report['head_skin_linear_gain'] = gain
native = {variant: [] for variant in palettes}
for frame in ['m404sa0', 'm404sa1', 'm404sa2', 'm404sa3', 'm404sa4', 'm404aa0', 'm404wa0']:
    images = {variant: np.asarray(Image.open(p.parent / 'native_variants' / f'{frame}_{pal}.png').convert('RGB'),
                                  float) / 255 for variant, pal in palettes.items()}
    changed = ((np.abs(images['m404_a'] - images['m404_b']).sum(-1) > .03) |
               (np.abs(images['m404_a'] - images['m404_c']).sum(-1) > .03))
    native_hsv = np.asarray(Image.fromarray(np.uint8(images['m404_a'] * 255)).convert('HSV'), float) / 255
    changed &= (native_hsv[..., 0] > 65 / 360) & (native_hsv[..., 0] < 170 / 360) & (native_hsv[..., 1] > .25)
    for variant in palettes:
        colors = images[variant][changed]
        colors = colors[regions.luminance(colors) > .003]
        native[variant].append(colors)
lum = regions.luminance(sets['']['base'][sets['']['mantle']])
lo, hi = [float(v) for v in np.percentile(lum, [2, 98])]
assert 0 <= lo < hi <= 1
rank = np.sort(lum)
ramps = {}
for variant in palettes:
    colors = np.concatenate(native[variant])
    colors = colors[np.argsort(regions.luminance(colors))]
    stops = []
    for i in range(16):
        quantile = np.searchsorted(rank, lo + (hi - lo) * i / 15) / len(rank)
        color = colors[min(len(colors) - 1, round(quantile * (len(colors) - 1)))]
        stops.append(regions.srgb_to_linear(np.clip(color * 1.4, 0, 243 / 255)).tolist())
    ramps[variant] = [{'range': [lo, hi], 'colors': stops}]
config = {'variants': list(palettes), 'materials': [
    {'base': 'M404_A', 'prefix': 'M404', 'mask': 'm404_region_mask.png',
     'regions': ['mantle'], 'palettes': palettes, 'ramps': ramps},
    {'base': 'M404Head_A', 'prefix': 'M404Head', 'mask': 'm404_head_region_mask.png',
     'regions': ['mantle'], 'palettes': palettes, 'ramps': ramps}]}
(out / 'm404_ramps.json').write_text(json.dumps(config, indent=2))
(out / 'compose_report.json').write_text(json.dumps(report, indent=2))
print('TEXTURES', report)
