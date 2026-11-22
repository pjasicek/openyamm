#!/usr/bin/env python3
"""Xeen colour tiers on a reused installed model (lane S): copy an installed GLB that already carries the shared skin,
region mask and ramps (CLAUDE_CREATURE_TEXTURES.md), and add new KHR_materials_variants whose materials are copies of
an existing tier's materials with recoloured ramps. Nothing else changes (mesh, clips, LODs, images), so a tier costs a
material and a ramp per region. The copy is installed into the Xeen world (tools/install_model.py --world xeen) and the
Xeen bindings name the new skins; the source world's model is untouched.

    xeen_tiers.py <installed source.glb> <out.glb> <spec.json>

spec.json:
  {"variants": {"<new skin>": {"from": "<existing skin>",
                               "regions": {"<region index>": {"hue": deg | null, "sat": k, "val": k, "rgb": [r,g,b],
                                                              "mid": "#rrggbb", "contrast": k, "lift": l,
                                                              "shadow": "#rrggbb", "highlight": "#rrggbb"}}}}}
Keys starting with "_" (notes such as "_follows") are ignored. A model whose materials number their regions differently
(the sprite's body and wings) gives `"by_material": {"<material name prefix>": {"<region index>": {...}}}`: a material
whose name starts with a listed prefix takes those regions instead of `regions`.
A region's 16 ramp stops are converted to HSV: `hue` replaces the hue (null keeps it), `sat` and `val` scale saturation
and value; or `rgb` (linear 0..1) re-tints the stops to that colour at their own luminance; or `mid` ("#rrggbb", sRGB,
picked from the sprite) gives the region its average colour: every stop becomes `mid` scaled by its luminance relative
to the mean luminance that the region's texels (mask channel above 0.5 in the LOD0 base colour) show through the
source ramp, so the region averages to `mid` (`contrast` k raises the ratio to the power k: below 1 flattens, above 1
deepens; `lift` l in 0..1 blends the ratio towards 1 as l + (1 - l) * ratio, for a source tier whose dark stops are
black, such as the MM6 ogre's black horns; optional `shadow`/`highlight` give the dark and light stops their own hue at
mid's luminance, as in add_region.py).
Regions not listed keep
the source tier's ramp. The materials of every LOD (Name_A, Name_A_LOD2 ...) are copied alike; attachments are separate
GLBs and need the same skin names (run this on them too)."""
import colorsys
import copy
import io
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def read(path):
    raw = Path(path).read_bytes()
    n = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20 + n])
    rest = raw[20 + n:]
    binary = b''
    if len(rest) >= 8:
        blen, btype = struct.unpack_from('<II', rest, 0)
        binary = rest[8:8 + blen]
    return doc, binary


def write(path, doc, binary):
    js = json.dumps(doc, separators=(',', ':')).encode()
    js += b' ' * ((4 - len(js) % 4) % 4)
    binary += b'\0' * ((4 - len(binary) % 4) % 4)
    out = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + (8 + len(binary) if binary else 0))
    out += struct.pack('<II', len(js), 0x4E4F534A) + js
    if binary:
        out += struct.pack('<II', len(binary), 0x004E4942) + binary
    Path(path).write_bytes(out)


def srgb_hex_to_linear(text):
    c = [int(text.lstrip('#')[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


def luminance(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def srgb_to_linear(v):
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def texture_image(doc, binary, texture):
    view = doc['bufferViews'][doc['images'][doc['textures'][texture]['source']]['bufferView']]
    start = view.get('byteOffset', 0)
    return Image.open(io.BytesIO(binary[start:start + view['byteLength']]))


def sample_ramp(colors, t):
    x = min(max(t, 0.0), 1.0) * 15
    i0 = int(x)
    i1 = min(i0 + 1, 15)
    f = x - i0
    return [colors[i0][c] * (1 - f) + colors[i1][c] * f for c in range(3)]


def region_reference(doc, binary, mat, region):
    """Mean luminance of what the region's texels show through the ramp (the shader's mapping), and their median t."""
    ex = mat['extras']
    ramp = ex['openyamm_region_ramps'][region]
    pbr = mat['pbrMetallicRoughness']
    base = np.asarray(texture_image(doc, binary, pbr['baseColorTexture']['index']).convert('RGB'), np.float64) / 255
    lin = srgb_to_linear(base) * np.array(pbr.get('baseColorFactor', [1, 1, 1, 1])[:3])
    band = texture_image(doc, binary, ex['openyamm_region_mask']['index']).convert('RGBA').split()[region]
    if band.size != (base.shape[1], base.shape[0]):
        band = band.resize((base.shape[1], base.shape[0]), Image.BILINEAR)
    weight = np.asarray(band, np.float64) / 255
    lum = lin @ np.array([0.2126, 0.7152, 0.0722])
    lo, hi = ramp['range']
    t = np.clip((lum[weight > 0.5] - lo) / max(hi - lo, 1e-4), 0, 1)
    if not t.size:
        return luminance(ramp['colors'][8]), 0.5
    stops = np.array([luminance(c) for c in ramp['colors']])
    shown = np.interp(t * 15, np.arange(16), stops)
    return float(shown.mean()), float(np.median(t))


def recolour(colors, rule, reference=None):
    if 'mid' in rule:
        mid = np.array(srgb_hex_to_linear(rule['mid']))
        shadow = np.array(srgb_hex_to_linear(rule.get('shadow', rule['mid'])))
        highlight = np.array(srgb_hex_to_linear(rule.get('highlight', rule['mid'])))
        ref = max(reference if reference is not None else luminance(colors[8]), 1e-5)
        contrast = rule.get('contrast', 1.0)
        lift = rule.get('lift', 0.0)
        out = []
        for i, c in enumerate(colors):
            # optional shadow/highlight hues (add_region.py's rule): stops 0-7 blend shadow -> mid, 8-15 mid ->
            # highlight, each at mid's luminance, so only the hue changes
            target = shadow + (mid - shadow) * (i / 8) if i < 8 else mid + (highlight - mid) * ((i - 8) / 7)
            target = target * (luminance(mid) / max(luminance(target), 1e-6))
            k = lift + (1 - lift) * (max(luminance(c), 0.0) / ref) ** contrast
            out.append([round(float(min(1.0, x * k)), 6) for x in target])
        return out
    out = []
    for r, g, b in colors:
        if 'rgb' in rule:
            lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
            tr, tg, tb = rule['rgb']
            tl = max(0.2126 * tr + 0.7152 * tg + 0.0722 * tb, 1e-6)
            k = lum / tl
            out.append([min(1.0, tr * k), min(1.0, tg * k), min(1.0, tb * k)])
            continue
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        if rule.get('hue') is not None:
            h = (rule['hue'] % 360) / 360.0
        s = min(1.0, s * rule.get('sat', 1.0)); v = min(1.0, v * rule.get('val', 1.0))
        out.append([round(x, 6) for x in colorsys.hsv_to_rgb(h, s, v)])
    return out


def main(src, dst, spec_path):
    doc, binary = read(src)
    spec = json.load(open(spec_path))
    ext = doc.setdefault('extensions', {}).setdefault('KHR_materials_variants', {'variants': []})
    names = [v['name'] for v in ext['variants']]
    references = {}  # (source skin, region) -> (reference luminance, median t), from the first (LOD0) material
    for new, rule in spec['variants'].items():
        if new.startswith('_'):
            continue
        if new in names:
            raise SystemExit(f'variant {new} exists')
        src_index = names.index(rule['from'])
        ext['variants'].append({'name': new}); names.append(new)
        new_index = len(names) - 1
        cloned = {}
        for mesh in doc['meshes']:
            for prim in mesh['primitives']:
                maps = prim.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', [])
                add = []
                for m in maps:
                    if src_index in m['variants']:
                        mi = m['material']
                        if mi not in cloned:
                            mat = copy.deepcopy(doc['materials'][mi])
                            mat['name'] = mat['name'] + '_' + new
                            ramps = mat.get('extras', {}).get('openyamm_region_ramps')
                            if ramps:
                                regions, prefix = rule.get('regions', {}), ''
                                for name, over in rule.get('by_material', {}).items():
                                    if doc['materials'][mi]['name'].startswith(name):
                                        regions, prefix = over, name
                                for idx, r in regions.items():
                                    if idx.startswith('_'):
                                        continue
                                    key = (rule['from'], prefix, idx)
                                    if 'mid' in r and key not in references:
                                        references[key] = region_reference(doc, binary, doc['materials'][mi], int(idx))
                                        print(f'  {key}: mean shown luminance {references[key][0]:.4f}, median texel t={references[key][1]:.2f}')
                                    ref = references[key][0] if 'mid' in r else None
                                    ramps[int(idx)]['colors'] = recolour(ramps[int(idx)]['colors'], r, ref)
                            doc['materials'].append(mat); cloned[mi] = len(doc['materials']) - 1
                        add.append({'material': cloned[mi], 'variants': [new_index]})
                maps.extend(add)
        print('VARIANT', new, 'from', rule['from'], 'materials', len(cloned))
    write(dst, doc, binary)
    print('WROTE', dst)


if __name__ == '__main__':
    main(*sys.argv[1:4])
