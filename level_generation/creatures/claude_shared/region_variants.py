#!/usr/bin/env python3
"""Colour tiers as one shared skin + region mask + per-tier ramps (CLAUDE_CREATURE_TEXTURES.md).

Library:
  fit_ramps(base_srgb, tier_srgb, weight)  -> ramp dict for one region (least squares, matches the shader's lookup)
  write_mask(weights, path, size)          -> RGBA mask PNG, channel i = region i
  tint_ramp(base_srgb, weight, tint)       -> ramp reproducing the old openyamm_tint (luminance * tint)

CLI (runtime GLB step, replaces per-project add_variants.py):
  region_variants.py in.glb out.glb ramps.json [--extra NAME_PREFIX KEY=VALUE ...]
  --extra sets a material extra on every output material whose name starts with NAME_PREFIX, e.g.
  `--extra Rat openyamm_specular=0` (creature skin without the grey specular sheen; values are JSON). A key
  `pbr.<name>` sets pbrMetallicRoughness.<name> instead: with specular off, also pass `pbr.metallicFactor=0`,
  because a metallic texel has no diffuse term and would render black (studs, hoops, buckles keep their base colour).
  A key `material.<name>` sets the material's own top-level <name> (one tier see-through:
  `--extra Dagrell_C material.alphaMode='"BLEND"'`; the engine resolves materials per variant, so only that tier draws
  blended).

ramps.json:
  {"variants": ["gob_a", "gob_b", "gob_c"],
   "materials": [{"base": "<material name in in.glb>", "prefix": "Goblin", "mask": "<png, relative to ramps.json>",
                  "ramps": {"gob_a": [<region ramp>, ...], ...}}]}
  region ramp = {"range": [lo, hi], "colors": [[r, g, b] x 16]} (linear luminance and linear RGB).

The tool keeps each listed base material's textures, makes one copy per variant carrying only
openyamm_region_mask / openyamm_region_ramps extras, maps every primitive that uses the base material (or any of
its old variants) to the copies, drops materials/textures/images nothing references any more (old baked tier
textures) and compacts the binary buffer.
"""
import copy
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

STOPS = 16
LUMA = np.array([0.2126, 0.7152, 0.0722])


def srgb_to_linear(value):
    value = np.asarray(value, dtype=np.float64)
    return np.where(value <= 0.04045, value / 12.92, ((value + 0.055) / 1.055) ** 2.4)


def load_srgb(path, size=None):
    image = Image.open(path).convert('RGB')
    if size is not None and image.size != (size, size):
        image = image.resize((size, size), Image.LANCZOS)
    return np.asarray(image, dtype=np.float64) / 255.0


def luminance(srgb):
    return srgb_to_linear(srgb) @ LUMA


def _range(lum, core):
    values = lum[core]
    lo, hi = np.percentile(values, 0.5), np.percentile(values, 99.5)
    if hi - lo < 1e-3:
        hi = lo + 1e-3
    return float(max(lo, 0.0)), float(min(hi, 1.0))


def _hat_weights(t):
    """Linear interpolation weights of the 16 stops at positions t in 0..1 (as the shader samples the ramp row)."""
    x = np.clip(t, 0, 1) * (STOPS - 1)
    i0 = np.minimum(np.floor(x).astype(int), STOPS - 2)
    f = x - i0
    return i0, f


def fit_ramps(base_srgb, tier_srgb, weight, core_threshold=0.9, smooth=1e-3):
    """Fit one region's ramps. base_srgb: shared skin (HxWx3, sRGB 0..1); tier_srgb: {variant: HxWx3 sRGB} = the
    approved look per tier; weight: HxW region weight 0..1. Returns ({variant: ramp}, error report)."""
    lum = luminance(base_srgb)
    core = weight >= core_threshold
    if core.sum() < 100:
        raise ValueError('region has too few core texels')
    lo, hi = _range(lum, core)
    t = (lum[core] - lo) / (hi - lo)
    i0, f = _hat_weights(t)
    basis = np.zeros((len(t), STOPS))
    basis[np.arange(len(t)), i0] = 1 - f
    basis[np.arange(len(t)), i0 + 1] = f
    second = np.zeros((STOPS - 2, STOPS))
    for row in range(STOPS - 2):
        second[row, row:row + 3] = (1, -2, 1)
    normal = basis.T @ basis + smooth * len(t) * second.T @ second + 1e-9 * np.eye(STOPS)
    ramps, report = {}, {}
    for variant, srgb in tier_srgb.items():
        target = srgb_to_linear(srgb[core])
        colors = np.clip(np.linalg.solve(normal, basis.T @ target), 0, 1)
        ramps[variant] = {'range': [round(lo, 6), round(hi, 6)], 'colors': np.round(colors, 6).tolist()}
        fitted = basis @ colors
        encode = lambda v: np.where(v <= 0.0031308, v * 12.92, 1.055 * np.maximum(v, 0) ** (1 / 2.4) - 0.055)
        error = np.abs(encode(fitted) - srgb[core]) * 255
        report[variant] = {'mean_abs_8bit': round(float(error.mean()), 2),
                           'p95_abs_8bit': round(float(np.percentile(error, 95)), 2)}
    report['core_texels'] = int(core.sum())
    return ramps, report


def tint_ramp(base_srgb, weight, tint):
    """Exact equivalent of the old single tint (colour = luminance * tint) over the region's luminance range."""
    lum = luminance(base_srgb)
    values = lum[weight > 0.01]
    lo, hi = float(values.min()), float(values.max())
    if hi - lo < 1e-3:
        hi = lo + 1e-3
    stops = lo + (hi - lo) * np.arange(STOPS) / (STOPS - 1)
    colors = np.clip(stops[:, None] * np.asarray(tint)[None, :], 0, 1)
    return {'range': [round(lo, 6), round(hi, 6)], 'colors': np.round(colors, 6).tolist()}


def recover_weight(base, mapped, recoloured, min_change=4 / 255):
    """Per-texel blend weight w of a compose step recoloured = base * (1 - w) + mapped * w, solved by least squares
    over all tiers. base: HxWx3; mapped / recoloured: lists of HxWx3 (same colour space as the compose step)."""
    numerator = np.zeros(base.shape[:2])
    denominator = np.zeros(base.shape[:2])
    for target, actual in zip(mapped, recoloured):
        change = target - base
        numerator += ((actual - base) * change).sum(-1)
        denominator += (change * change).sum(-1)
    weight = np.where(denominator > 3 * min_change ** 2, numerator / np.maximum(denominator, 1e-12), 0.0)
    return np.clip(weight, 0, 1)


def write_mask(weights, path, size=1024):
    """weights: list of HxW arrays (one per region, at most four), area-averaged to size x size RGBA (size may also
    be a (width, height) pair for non-square textures)."""
    if not 1 <= len(weights) <= 4:
        raise ValueError('one to four regions')
    dims = tuple(size) if isinstance(size, (tuple, list)) else (size, size)
    channels = []
    for index in range(4):
        if index < len(weights):
            image = Image.fromarray(np.clip(weights[index] * 255 + 0.5, 0, 255).astype(np.uint8), 'L')
            channels.append(image.resize(dims, Image.BOX))
        else:
            channels.append(Image.new('L', dims, 0))
    Image.merge('RGBA', channels).save(path, optimize=True)


# ---------------------------------------------------------------------------------------------------- GLB rewrite

def read_glb(path):
    raw = Path(path).read_bytes()
    length = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + length]), bytes(raw[28 + length:])


def write_glb(path, doc, binary):
    binary = bytearray(binary)
    binary += b'\0' * (-len(binary) % 4)
    doc['buffers'][0]['byteLength'] = len(binary)
    encoded = json.dumps(doc, separators=(',', ':')).encode()
    encoded += b' ' * (-len(encoded) % 4)
    Path(path).write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(encoded) + len(binary))
                           + struct.pack('<II', len(encoded), 0x4e4f534a) + encoded
                           + struct.pack('<II', len(binary), 0x004e4942) + binary)


def _texture_indices(material):
    found = []

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == 'index' and isinstance(value, int) and node is not material:
                    found.append(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for key in ('pbrMetallicRoughness', 'normalTexture', 'occlusionTexture', 'emissiveTexture', 'extras'):
        if key in material:
            walk(material[key])
    return found


def _compact(doc, binary):
    """Drop unreferenced materials, textures, images and buffer views; repack the binary buffer."""
    used_materials = set()
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            if 'material' in primitive:
                used_materials.add(primitive['material'])
            for mapping in primitive.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                used_materials.add(mapping['material'])
    material_map = {old: new for new, old in enumerate(sorted(used_materials))}
    doc['materials'] = [doc['materials'][old] for old in sorted(used_materials)]
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            if 'material' in primitive:
                primitive['material'] = material_map[primitive['material']]
            for mapping in primitive.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                mapping['material'] = material_map[mapping['material']]

    used_textures = sorted({index for material in doc['materials'] for index in _texture_indices(material)})
    texture_map = {old: new for new, old in enumerate(used_textures)}

    def remap(node, owner):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == 'index' and isinstance(value, int) and node is not owner:
                    node[key] = texture_map[value]
                else:
                    remap(value, owner)
        elif isinstance(node, list):
            for value in node:
                remap(value, owner)

    for material in doc['materials']:
        for key in ('pbrMetallicRoughness', 'normalTexture', 'occlusionTexture', 'emissiveTexture', 'extras'):
            if key in material:
                remap(material[key], material)
    doc['textures'] = [doc['textures'][old] for old in used_textures]

    used_images = sorted({texture['source'] for texture in doc['textures']})
    image_map = {old: new for new, old in enumerate(used_images)}
    doc['images'] = [doc['images'][old] for old in used_images]
    for texture in doc['textures']:
        texture['source'] = image_map[texture['source']]
    if 'samplers' in doc:
        used_samplers = sorted({texture['sampler'] for texture in doc['textures'] if 'sampler' in texture})
        sampler_map = {old: new for new, old in enumerate(used_samplers)}
        doc['samplers'] = [doc['samplers'][old] for old in used_samplers]
        for texture in doc['textures']:
            if 'sampler' in texture:
                texture['sampler'] = sampler_map[texture['sampler']]
        if not doc['samplers']:
            del doc['samplers']

    used_views = set()
    for accessor in doc.get('accessors', []):
        if 'bufferView' in accessor:
            used_views.add(accessor['bufferView'])
        sparse = accessor.get('sparse')
        if sparse:
            used_views.add(sparse['indices']['bufferView'])
            used_views.add(sparse['values']['bufferView'])
    for image in doc['images']:
        if 'bufferView' in image:
            used_views.add(image['bufferView'])
    view_map, packed = {}, bytearray()
    views = []
    for old in sorted(used_views):
        view = copy.deepcopy(doc['bufferViews'][old])
        start = view.get('byteOffset', 0)
        data = binary[start:start + view['byteLength']]
        packed += b'\0' * (-len(packed) % 4)
        view['byteOffset'] = len(packed)
        packed += data
        view_map[old] = len(views)
        views.append(view)
    doc['bufferViews'] = views
    for accessor in doc.get('accessors', []):
        if 'bufferView' in accessor:
            accessor['bufferView'] = view_map[accessor['bufferView']]
        sparse = accessor.get('sparse')
        if sparse:
            sparse['indices']['bufferView'] = view_map[sparse['indices']['bufferView']]
            sparse['values']['bufferView'] = view_map[sparse['values']['bufferView']]
    for image in doc['images']:
        if 'bufferView' in image:
            image['bufferView'] = view_map[image['bufferView']]
    return doc, bytes(packed)


def apply_variants(source, destination, config_path, material_extras=()):
    config_path = Path(config_path)
    config = json.loads(config_path.read_text())
    doc, binary = read_glb(source)
    binary = bytearray(binary)
    variants = config['variants']
    names = [material.get('name', '') for material in doc['materials']]
    replaced = {}
    for entry in config['materials']:
        # Blender may add a numeric suffix ("Rat_A.001") when the material name already exists in the file.
        base = next(index for index, name in enumerate(names)
                    if name == entry['base'] or name.startswith(entry['base'] + '.'))
        mask = (config_path.parent / entry['mask']).read_bytes()
        binary += b'\0' * (-len(binary) % 4)
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(mask)})
        binary += mask
        doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png',
                              'name': Path(entry['mask']).stem})
        mask_texture = {'source': len(doc['images']) - 1}
        base_texture = doc['materials'][base].get('pbrMetallicRoughness', {}).get('baseColorTexture')
        if base_texture is not None and 'sampler' in doc['textures'][base_texture['index']]:
            mask_texture['sampler'] = doc['textures'][base_texture['index']]['sampler']
        doc['textures'].append(mask_texture)
        copies = []
        for variant in variants:
            material = copy.deepcopy(doc['materials'][base])
            material['name'] = f"{entry['prefix']}_{variant.split('_')[-1].upper()}"
            extras = material.setdefault('extras', {})
            extras.pop('openyamm_tint', None)
            extras['openyamm_region_mask'] = {'index': len(doc['textures']) - 1}
            extras['openyamm_region_ramps'] = entry['ramps'][variant]
            doc['materials'].append(material)
            copies.append(len(doc['materials']) - 1)
        replaced[base] = copies
    existing = [variant['name'] for variant in
                doc.get('extensions', {}).get('KHR_materials_variants', {}).get('variants', [])]
    mapped = 0
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            default = primitive.get('material')
            extension = primitive.get('extensions', {}).get('KHR_materials_variants')
            if default not in replaced:
                # Other variant materials (e.g. separate irises) stay as they are when the variant list is unchanged.
                if extension is not None and existing != variants:
                    raise ValueError(f'primitive with material {default} has variants not covered by ramps.json')
                continue
            copies = replaced[default]
            primitive['material'] = copies[0]
            primitive.setdefault('extensions', {})['KHR_materials_variants'] = {
                'mappings': [{'material': copies[index], 'variants': [index]} for index in range(len(variants))]}
            mapped += 1
    doc.setdefault('extensionsUsed', [])
    if 'KHR_materials_variants' not in doc['extensionsUsed']:
        doc['extensionsUsed'].append('KHR_materials_variants')
    doc.setdefault('extensions', {})['KHR_materials_variants'] = {'variants': [{'name': name} for name in variants]}
    for prefix, key, value in material_extras:
        matched = [m for m in doc['materials'] if m.get('name', '').startswith(prefix)]
        if not matched:
            raise ValueError(f'--extra {prefix}: no material name starts with it')
        for material in matched:
            if key.startswith('pbr.'):
                material.setdefault('pbrMetallicRoughness', {})[key[4:]] = value
            elif key.startswith('material.'):
                material[key[len('material.'):]] = value
            else:
                material.setdefault('extras', {})[key] = value
    doc, binary = _compact(doc, bytes(binary))
    write_glb(destination, doc, binary)
    print(f'{destination}: {len(variants)} variants on {mapped} primitives, {len(doc["images"])} images, '
          f'{len(binary) / 1e6:.1f} MB buffer')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument('source')
    parser.add_argument('destination')
    parser.add_argument('config')
    parser.add_argument('--extra', nargs=2, action='append', default=[], metavar=('NAME_PREFIX', 'KEY=VALUE'))
    options = parser.parse_args()
    parsed = [(prefix, *assignment.split('=', 1)) for prefix, assignment in options.extra]
    apply_variants(options.source, options.destination, options.config,
                   [(prefix, key, json.loads(value)) for prefix, key, value in parsed])
