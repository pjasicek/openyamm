#!/usr/bin/env python3
"""Material class map -> per-texel metallic, roughness and specular mask (docs/LIGHTING_AND_MATERIALS_ARCHITECTURE.md
section 7, CLAUDE_CREATURE_TEXTURES.md "Specular, material classes and AO").

Rewrites a runtime creature GLB's metallic-roughness texture from the project's material class map (8-bit L, labels
0-11, same UV layout as the base colour):
- B metallic: 1 on metal, 0 elsewhere (binary).
- G roughness: the class value plus the old roughness texture's fine variation (old minus its local mean inside the
  same class, DETAIL_SIGMA texels), limited to DETAIL_LIMIT and to the class band.
- R specular mask (engine: specular = R x openyamm_specular when openyamm_specular_mask is set): the class value. If
  the old R channel holds a baked AO (continuous values, no specular mask flag), the mask is multiplied by it, so the
  AO is kept as specular occlusion. An old specular mask or a constant R is replaced.
- Every material that uses the texture gets metallicFactor 1, roughnessFactor 1, openyamm_specular 1 and
  openyamm_specular_mask true, so the per-texel values apply. Region masks, ramps, KHR_materials_variants and every
  other image stay as they are.
Head sets: a material whose name contains "Head" with its own metallic-roughness texture takes the head map; a merged
body | 32 px gutter | head atlas (tools/merge_head_material.py) takes the body map on the left square and the head map
on the right part (the best-fitting placement is chosen). Texels outside the UV islands (label 0) and the gutter take
the nearest class.

Checks (in the JSON report): texel share per class, the UV raster of the GLB against the class map (texels inside the
UV islands without a class, class texels outside them; refused above MAX_UNLABELLED unless --force), old and new
factors, the old R channel, and the base colour of the metal texels after each variant's region ramps (fully metallic
texels have no diffuse term; Khronos iron is about sRGB 196, 199, 199).

Usage: material_classes_to_orm.py in.glb out.glb [--classes body_material_classes.png]
       [--head-classes head_material_classes.png] [--map MATCH=BODY[,HEAD] ...] [--keep-classes skin,...]
       [--report out.json] [--maps-dir DIR] [--force]
--map: for models with several metallic-roughness images (separate head, wings, cloak or LOD sets): the image whose
name or material names contain MATCH (case-insensitive; =NAME for an exact name) takes those class maps; the first
match wins, --classes and --head-classes then apply to the rest. Images without a class map are left unchanged.
--keep-classes (class names or labels): those texels keep the old specular and roughness (the old effective
values: red x openyamm_specular with the old mask, else openyamm_specular; green x roughnessFactor), for a look a
project tuned on purpose; metallic still comes from the class.
--maps-dir writes the new metallic-roughness image and a colour preview of the classes there."""
import argparse
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import region_variants as RV  # noqa: E402
import tier_textures as TT  # noqa: E402

GUTTER = 32  # tools/merge_head_material.py
NAMES = {0: 'empty', 1: 'skin', 2: 'fur', 3: 'membrane', 4: 'claw', 5: 'tooth', 6: 'eye', 7: 'mouth', 8: 'cloth',
         9: 'metal', 10: 'wood', 11: 'other'}
# label: (metallic, roughness, roughness band (lo, hi), specular mask). Specular "low" is 0.3, skin 0.25 (no grey
# sheen on skin, The Hive A/B 2026-10-08), "off" 0 (fur), "on" 1. The mouth interior is wet; "other" is matte.
TABLE = {
    1: (0, 0.80, (0.70, 0.90), 0.25),
    2: (0, 0.90, (0.80, 1.00), 0.0),
    3: (0, 0.85, (0.75, 0.95), 0.3),
    4: (0, 0.45, (0.35, 0.55), 1.0),
    5: (0, 0.35, (0.28, 0.45), 1.0),
    6: (0, 0.15, (0.10, 0.22), 1.0),
    7: (0, 0.45, (0.35, 0.55), 0.5),
    8: (0, 0.75, (0.65, 0.85), 0.3),
    9: (1, 0.38, (0.30, 0.45), 1.0),
    10: (0, 0.70, (0.60, 0.80), 0.3),
    11: (0, 0.70, (0.60, 0.80), 0.3),
}
DETAIL_SIGMA = 4.0      # texels at 1K: what counts as fine variation
DETAIL_GAIN = 1.0
DETAIL_LIMIT = 0.12
STRETCH = 25.0          # UV area per 3D area above this x the median: a stretched (collapsed seam) triangle
DARK_METAL, BRIGHT_METAL = 40, 230   # metal base colour flags (median sRGB luminance after the ramps)
MAX_UNLABELLED = 0.05   # share of UV-covered texels without a class above which the class map is refused
COMPONENTS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
TYPES = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
PREVIEW = {0: (0, 0, 0), 1: (230, 170, 130), 2: (120, 60, 20), 3: (200, 120, 200), 4: (240, 240, 120),
           5: (255, 255, 230), 6: (60, 200, 255), 7: (200, 40, 60), 8: (110, 140, 70), 9: (170, 180, 200),
           10: (140, 100, 40), 11: (255, 0, 255)}


def accessor(doc, binary, index):
    acc = doc['accessors'][index]
    view = doc['bufferViews'][acc['bufferView']]
    dtype = np.dtype(TYPES[acc['componentType']])
    n = COMPONENTS[acc['type']]
    stride = view.get('byteStride', dtype.itemsize * n)
    start = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    raw = np.frombuffer(binary, np.uint8, count=stride * (acc['count'] - 1) + dtype.itemsize * n, offset=start)
    rows = np.lib.stride_tricks.as_strided(raw, (acc['count'], dtype.itemsize * n), (stride, 1))
    out = np.ascontiguousarray(rows).view(dtype).reshape(acc['count'], n).astype(np.float64)
    if acc.get('normalized'):
        out /= np.iinfo(dtype).max
    return out


def image_array(doc, binary, texture_index):
    image = doc['images'][doc['textures'][texture_index]['source']]
    view = doc['bufferViews'][image['bufferView']]
    start = view.get('byteOffset', 0)
    return Image.open(io.BytesIO(binary[start:start + view['byteLength']])), image


def material_variants(doc, primitive):
    found = {primitive.get('material')}
    for mapping in primitive.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
        found.add(mapping['material'])
    return found - {None}


def uv_coverage(doc, binary, materials, size):
    """UV triangles of the meshes that use one of the materials, as a W x H bool raster: the full-detail meshes (no
    LOD or Shadow in the name) when any of them use the materials, else the LOD meshes. Triangles stretched across the
    texture (UV area per 3D area above STRETCH x the median: collapsed seams) are left out and counted."""
    width, height = size
    canvas = Image.new('L', size, 0)
    draw = ImageDraw.Draw(canvas)
    users = [m for m in doc['meshes'] if 'Shadow' not in m.get('name', '')
             and any(material_variants(doc, p) & materials for p in m['primitives'])]
    full = [m for m in users if 'LOD' not in m.get('name', '')]
    stretched = 0
    for mesh in full or users:
        for primitive in mesh['primitives']:
            if not material_variants(doc, primitive) & materials or 'TEXCOORD_0' not in primitive['attributes']:
                continue
            uv = accessor(doc, binary, primitive['attributes']['TEXCOORD_0'])
            position = accessor(doc, binary, primitive['attributes']['POSITION'])
            if 'indices' in primitive:
                tris = accessor(doc, binary, primitive['indices']).astype(np.int64).reshape(-1, 3)
            else:
                tris = np.arange(len(uv)).reshape(-1, 3)
            t, p = uv[tris], position[tris]
            e1, e2 = t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]
            uv_area = 0.5 * np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0])
            area = 0.5 * np.linalg.norm(np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]), axis=1)
            ratio = uv_area / np.maximum(area, 1e-12)
            positive = ratio[uv_area > 0]
            keep = ratio <= STRETCH * (np.median(positive) if positive.size else 1.0)
            stretched += int((~keep).sum())
            points = np.stack([uv[:, 0] * width, uv[:, 1] * height], 1)
            for tri in points[tris[keep]]:
                draw.polygon([tuple(q) for q in tri], fill=255)
    return np.asarray(canvas) > 0, stretched


def load_labels(path, size):
    image = Image.open(path)
    if image.mode not in ('L', 'P', 'I'):
        raise ValueError(f'{path}: class map must be single channel, got {image.mode}')
    image = image.convert('L')
    if image.size != size:
        image = image.resize(size, Image.NEAREST)
    labels = np.asarray(image, np.uint8)
    bad = set(np.unique(labels).tolist()) - set(NAMES)
    if bad:
        raise ValueError(f'{path}: unknown labels {sorted(bad)}')
    return labels


def layouts(size, materials, has_head):
    """Candidate placements of the class maps on a texture: lists of (part, x0, y0, x1, y1). A head-only material
    (every name contains "Head") takes the head map over the whole texture; a texture wider than tall with a head map
    is tried as tools/merge_head_material.py's body | gutter | head atlas (body square on the left, head square at the
    top right, gutter 32 texels or 32 scaled to a reduced LOD texture); otherwise the body map covers the texture."""
    width, height = size
    if has_head and all('Head' in m.get('name', '') for m in materials):
        return [[('head', 0, 0, width, height)]]
    found = []
    if has_head and width > height:
        for gutter in sorted({GUTTER, max(1, round(GUTTER * height / 1024))}):
            head = width - height - gutter
            if 0 < head <= height:
                found.append([('body', 0, 0, height, height), ('head', height + gutter, 0, width, head)])
    return found + [[('body', 0, 0, width, height)]]


def fill_nearest(labels):
    known = labels > 0
    if not known.any():
        raise ValueError('class map has no labelled texels')
    index = ndimage.distance_transform_edt(~known, return_distances=False, return_indices=True)
    return labels[tuple(index)]


def roughness_map(labels, old, scale):
    """Class roughness plus the old map's fine variation inside each class."""
    sigma = DETAIL_SIGMA * scale
    new = np.zeros(labels.shape)
    for label in np.unique(labels):
        m = labels == label
        _, base, (lo, hi), _ = TABLE[int(label)]
        weight = ndimage.gaussian_filter(m.astype(np.float64), sigma)
        local = ndimage.gaussian_filter(np.where(m, old, 0.0), sigma) / np.maximum(weight, 1e-6)
        detail = np.clip((old - local) * DETAIL_GAIN, -DETAIL_LIMIT, DETAIL_LIMIT)
        new[m] = np.clip(base + detail[m], lo, hi)
    return new


def r_channel_kind(r, specular_mask):
    values = np.unique(r)
    if values.size == 1:
        return 'constant'
    if specular_mask:
        return 'specular_mask'
    return 'ao' if values.size > 32 else 'unknown_steps'


def metal_colour(doc, binary, material, labels_full, covered, mr_size):
    """sRGB statistics of the metal texels' base colour (inside the UV islands) after this material's region ramps."""
    metal = (labels_full == 9) & covered
    if not metal.any():
        return None
    pbr = material.get('pbrMetallicRoughness', {})
    factor = np.asarray(pbr.get('baseColorFactor', [1, 1, 1, 1])[:3])
    if 'baseColorTexture' in pbr:
        base_image, _ = image_array(doc, binary, pbr['baseColorTexture']['index'])
        base = np.asarray(base_image.convert('RGB').resize(mr_size, Image.BOX), np.float64) / 255
    else:
        base = np.ones(mr_size[::-1] + (3,))
    base = TT.linear_to_srgb(TT.srgb_to_linear(base) * factor)
    extras = material.get('extras', {})
    if 'openyamm_region_mask' in extras and extras.get('openyamm_region_ramps'):
        mask_image, _ = image_array(doc, binary, extras['openyamm_region_mask']['index'])
        bands = mask_image.convert('RGBA').split()
        mask = np.stack([np.asarray(b.resize(mr_size, Image.BILINEAR) if b.size != mr_size else b, np.float64) / 255
                         for b in bands], -1)
        base = TT.apply(base, mask, extras['openyamm_region_ramps'])
    rgb = base[metal] * 255
    lum_srgb = TT.linear_to_srgb(TT.srgb_to_linear(base[metal]) @ TT.LUMA) * 255
    median_lum = float(np.median(lum_srgb))
    return {'median_srgb': np.round(np.median(rgb, 0)).astype(int).tolist(),
            'luminance_srgb_p10_p50_p90': np.round(np.percentile(lum_srgb, [10, 50, 90])).astype(int).tolist(),
            'share_below_srgb_30': round(float((lum_srgb < 30).mean()), 4),
            'share_below_srgb_90': round(float((lum_srgb < 90).mean()), 4),
            'flag': 'very dark' if median_lum < DARK_METAL else 'very bright' if median_lum > BRIGHT_METAL else None,
            'verdict': ('very dark (engine phase 2 diffuse floor needed)' if median_lum < 90 else
                        'below the Khronos metal range (about sRGB 180-250)' if median_lum < 170 else
                        'very bright' if median_lum > BRIGHT_METAL else 'plausible')}


def parse_classes(text):
    labels = set()
    for item in filter(None, (part.strip() for part in (text or '').split(','))):
        by_name = {name: label for label, name in NAMES.items()}
        if item.isdigit() and int(item) in TABLE:
            labels.add(int(item))
        elif item in by_name and by_name[item] in TABLE:
            labels.add(by_name[item])
        else:
            raise ValueError(f'unknown class {item!r}: use 1-11 or one of {sorted(NAMES.values())[1:]}')
    return labels


def assess(labels_by_part, covered):
    """UV fit of each placed class map: shares of island texels without a class (all, and over 2 texels from one)."""
    out = {}
    for name, (x0, y0, x1, y1), labels in labels_by_part:
        cov = covered[y0:y1, x0:x1]
        near = ndimage.binary_dilation(cov, iterations=2)
        distance = ndimage.distance_transform_edt(labels == 0)
        out[name] = {'uv_covered_texels': int(cov.sum()),
                     'uv_covered_without_class': round(float((cov & (labels == 0)).sum() / max(cov.sum(), 1)), 4),
                     'uv_covered_without_class_far': round(float((cov & (distance > 2)).sum() / max(cov.sum(), 1)), 4),
                     'class_texels_outside_uv': round(float(((labels > 0) & ~near).sum()
                                                           / max((labels > 0).sum(), 1)), 4)}
    return out


def matches(matcher, image_entry, materials):
    """'' matches everything, '=NAME' an exact image or material name, anything else a case-insensitive substring."""
    names = [image_entry.get('name', '')] + [m.get('name', '') for m in materials]
    if matcher.startswith('='):
        return matcher[1:] in names
    return matcher == '' or any(matcher.lower() in n.lower() for n in names)


def convert(source, destination, assignments, force=False, maps_dir=None, keep=(), dry_run=False):
    """assignments: list of (matcher, body class map or None, head class map or None[, keep classes]); each
    metallic-roughness image takes the first assignment that matches its image or material names (see matches); an
    assignment's own keep classes replace `keep` for that image.
    Images without an assignment stay unchanged. dry_run: report only (fit and metal colour), nothing is written and
    a class map that does not fit is reported instead of refused."""
    doc, binary = RV.read_glb(source)
    binary = bytes(binary)
    groups = {}
    for index, material in enumerate(doc['materials']):
        texture = material.get('pbrMetallicRoughness', {}).get('metallicRoughnessTexture')
        if texture is not None:
            groups.setdefault(doc['textures'][texture['index']]['source'], []).append(index)
    if not groups:
        raise ValueError(f'{source}: no material has a metallic-roughness texture')
    report = {'source': str(source), 'output': str(destination),
              'assignments': [{'match': a[0], 'body': str(a[1]) if a[1] else None,
                               'head': str(a[2]) if a[2] else None} for a in assignments],
              'kept_classes': [NAMES[k] for k in sorted(keep)], 'textures': [], 'unchanged': []}
    for image_index, material_indices in sorted(groups.items()):
        materials = [doc['materials'][i] for i in material_indices]
        image_entry = doc['images'][image_index]
        assignment = next((a for a in assignments if matches(a[0], image_entry, materials)), None)
        if assignment is None or (assignment[1] is None and assignment[2] is None):
            report['unchanged'].append({'image': image_entry.get('name'), 'materials': [m['name'] for m in materials]})
            continue
        _, body_map, head_map = assignment[:3]
        image_keep = set(assignment[3]) if len(assignment) > 3 else set(keep)
        view = doc['bufferViews'][image_entry['bufferView']]
        start = view.get('byteOffset', 0)
        image = Image.open(io.BytesIO(binary[start:start + view['byteLength']]))
        size = image.size
        old = np.asarray(image.convert('RGB'), np.float64) / 255
        old_factors = {}
        for material in materials:
            pbr = material.get('pbrMetallicRoughness', {})
            extras = material.get('extras', {})
            old_factors[material['name']] = {
                'metallicFactor': pbr.get('metallicFactor', 1.0), 'roughnessFactor': pbr.get('roughnessFactor', 1.0),
                'openyamm_specular': extras.get('openyamm_specular', 1.0),
                'openyamm_specular_mask': extras.get('openyamm_specular_mask', False)}
        first = old_factors[materials[0]['name']]
        if any(f != first for f in old_factors.values()):
            raise ValueError(f'{image_entry.get("name")}: materials sharing it have different factors {old_factors}')
        old_rough = old[..., 1] * first['roughnessFactor']
        r_kind = r_channel_kind(np.asarray(image.convert('RGB'))[..., 0], first['openyamm_specular_mask'])
        covered, stretched = uv_coverage(doc, binary, set(material_indices), size)
        best = None
        for candidate in layouts(size, materials, head_map is not None):
            placed = []
            for name, x0, y0, x1, y1 in candidate:
                path = body_map if name == 'body' else head_map
                if path is None:
                    break
                placed.append((name, (x0, y0, x1, y1), load_labels(path, (x1 - x0, y1 - y0))))
            else:
                fit = assess(placed, covered)
                score = max(f['uv_covered_without_class_far'] for f in fit.values())
                if best is None or score < best[0]:
                    best = (score, candidate, placed, fit)
        if best is None:
            raise ValueError(f'{image_entry.get("name")}: no layout for the given class maps')
        score, candidate, placed, fit = best
        entry = {'image': image_entry.get('name'), 'size': list(size), 'materials': [m['name'] for m in materials],
                 'layout': [{'part': name, 'box': [x0, y0, x1, y1]} for name, x0, y0, x1, y1 in candidate],
                 'old_factors': first, 'old_r_channel': r_kind, 'stretched_uv_triangles': stretched,
                 'fit_ok': score <= MAX_UNLABELLED, 'parts': fit}
        if score > MAX_UNLABELLED and not force and not dry_run:
            raise ValueError(f'{image_entry.get("name")}: {score:.1%} of the UV-covered texels have no class within '
                             '2 texels (class map does not match the GLB UV layout); --force to override')
        composite = np.zeros(size[::-1], np.uint8)
        for name, (x0, y0, x1, y1), labels in placed:
            composite[y0:y1, x0:x1] = fill_nearest(labels)
            counts = np.bincount(composite[y0:y1, x0:x1][covered[y0:y1, x0:x1]], minlength=12)
            entry['parts'][name]['class_map'] = str(body_map if name == 'body' else head_map)
            entry['parts'][name]['class_share_in_uv'] = {NAMES[k]: round(float(counts[k] / max(counts.sum(), 1)), 4)
                                                         for k in range(1, 12) if counts[k]}
        filled = fill_nearest(composite)          # gutters and uncovered strips take the nearest class
        counts = np.bincount(filled[covered] if covered.any() else filled.ravel(), minlength=12)
        entry['class_share_total'] = {NAMES[k]: round(float(counts[k] / counts.sum()), 4)
                                      for k in range(1, 12) if counts[k]}
        metallic = np.vectorize(lambda k: TABLE[int(k)][0])(filled).astype(np.float64)
        specular = np.vectorize(lambda k: TABLE[int(k)][3])(filled).astype(np.float64)
        rough = roughness_map(filled, old_rough, min(size) / 1024)
        if r_kind == 'ao':
            specular *= old[..., 0]
        old_specular = first['openyamm_specular'] * (old[..., 0] if first['openyamm_specular_mask']
                                                     else np.ones(old.shape[:2]))
        kept = np.isin(filled, sorted(image_keep))
        entry['kept_classes'] = [NAMES[k] for k in sorted(image_keep)]
        if kept.any():
            specular = np.where(kept, old_specular, specular)
            rough = np.where(kept, old_rough, rough)
        entry['kept_texels'] = int((kept & covered).sum())
        present = np.unique(filled[covered]) if covered.any() else np.unique(filled)
        inside = covered if covered.any() else np.ones_like(covered)

        def by_class(values):
            return {NAMES[int(k)]: round(float(values[(filled == k) & inside].mean()), 3) for k in present}
        entry['old_specular_mean_by_class'] = by_class(old_specular)
        entry['new_specular_mean_by_class'] = by_class(specular)
        entry['new_roughness_mean_by_class'] = by_class(rough)
        entry['new_factors'] = {'metallicFactor': 1.0, 'roughnessFactor': 1.0, 'openyamm_specular': 1.0,
                                'openyamm_specular_mask': True}
        entry['metal_base_colour'] = {m['name']: metal_colour(doc, binary, m, filled, covered, size)
                                      for m in materials}
        report['textures'].append(entry)
        if dry_run:
            continue
        new = np.stack([specular, rough, metallic], -1)
        new_image = Image.fromarray((np.clip(new, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB')
        buffer = io.BytesIO()
        new_image.save(buffer, 'PNG', optimize=True)
        data = buffer.getvalue()
        binary += b'\0' * (-len(binary) % 4)
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
        binary += data
        image_entry['bufferView'] = len(doc['bufferViews']) - 1
        image_entry['mimeType'] = 'image/png'
        for material in materials:
            pbr = material.setdefault('pbrMetallicRoughness', {})
            pbr['metallicFactor'] = 1.0
            pbr['roughnessFactor'] = 1.0
            extras = material.setdefault('extras', {})
            extras['openyamm_specular'] = 1.0
            extras['openyamm_specular_mask'] = True
        pixels = np.asarray(new_image)
        entry['new_channels'] = {c: {'min': int(pixels[..., i].min()), 'max': int(pixels[..., i].max()),
                                     'mean': round(float(pixels[..., i].mean()), 1)} for i, c in enumerate('RGB')}
        if maps_dir:
            stem = Path(destination).stem
            Path(maps_dir).mkdir(parents=True, exist_ok=True)
            new_image.save(Path(maps_dir) / f'{stem}_{image_index}_mr.png')
            preview = np.zeros(filled.shape + (3,), np.uint8)
            for k, colour in PREVIEW.items():
                preview[filled == k] = colour
            preview[~covered] //= 3
            Image.fromarray(preview).save(Path(maps_dir) / f'{stem}_{image_index}_classes.png')
    if not report['textures']:
        raise ValueError(f'{source}: no metallic-roughness image matched an assignment')
    if not dry_run:
        doc, binary = RV._compact(doc, binary)
        RV.write_glb(destination, doc, binary)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('source')
    parser.add_argument('destination')
    parser.add_argument('--classes')
    parser.add_argument('--head-classes')
    parser.add_argument('--map', action='append', default=[], metavar='MATCH=BODY[,HEAD]')
    parser.add_argument('--keep-classes')
    parser.add_argument('--report')
    parser.add_argument('--maps-dir')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    assignments = []
    for item in args.map:
        matcher, _, paths = item.partition('=')
        body, _, head = paths.partition(',')
        assignments.append((matcher, body or None, head or None))
    if args.classes or args.head_classes:
        assignments.append(('', args.classes, args.head_classes))
    if not assignments:
        parser.error('give --classes and/or --head-classes, or --map')
    report = convert(args.source, args.destination, assignments, args.force, args.maps_dir,
                     parse_classes(args.keep_classes))
    text = json.dumps(report, indent=1)
    if args.report:
        Path(args.report).write_text(text + '\n')
    for entry in report['textures']:
        print('TEXTURE', entry['image'], 'r:', entry['old_r_channel'], 'old', entry['old_factors'])
        for part, info in entry['parts'].items():
            print(' ', part, 'uv without class', info['uv_covered_without_class'], 'far',
                  info['uv_covered_without_class_far'], 'class outside uv', info['class_texels_outside_uv'],
                  info.get('class_share_in_uv'))
        for name, metal in entry['metal_base_colour'].items():
            if metal:
                print('  metal', name, metal['median_srgb'], metal['luminance_srgb_p10_p50_p90'], metal['verdict'])
    for entry in report['unchanged']:
        print('UNCHANGED', entry['image'], entry['materials'][:3])
    print('WROTE', args.destination)


if __name__ == '__main__':
    main()
