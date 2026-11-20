#!/usr/bin/env python3
"""Glowing ("energy") parts of a creature GLB: glTF emission, per colour tier, with creature bloom
(engine/render/MODEL_RENDERING.md, "Emission and bloom"; recipe in ../CLAUDE_CREATURE_TEXTURES.md).

  emission.py in.glb out.glb --material PREFIX [--mask mask.png] [--color r,g,b | --color VARIANT=r,g,b ...]
              [--strength S] [--gamma G] [--pulse AMPLITUDE,PERIOD] [--no-bloom]

Every material whose name starts with PREFIX gets emissiveFactor = colour x strength (linear RGB; the colour of the
tier variant that material draws, so tiers can glow differently), and with --mask an emissiveTexture: the mask (any
PNG; its luminance, raised to --gamma, stored as an sRGB grey image the size of the mask) embedded once and shared by
all of them. The glow is then factor x texture, added unlit to the shaded colour and drawn into the bloom view.
Without --mask the whole material emits (a separate lens, cell or vent material); it is given
`openyamm_bloom: true`, because a creature material blooms only with an emissive texture or that flag.
--pulse sets `openyamm_pulse: [amplitude, period seconds]` (emission x 1 + a sin(2 pi t / period)).
Colours: a single --color for every tier, or one per KHR_materials_variants name. Run it last in the runtime build
(after region_variants.py, split_attachment.py and merge_head_material.py), on the body and on any attachment.
"""
import argparse
import io
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

GLB_MAGIC, CHUNK_JSON, CHUNK_BIN = 0x46546C67, 0x4E4F534A, 0x004E4942


def read_glb(path):
    data = Path(path).read_bytes()
    magic, _, _ = struct.unpack_from('<III', data, 0)
    if magic != GLB_MAGIC:
        sys.exit(f'{path}: not a GLB')
    offset, document, binary = 12, None, b''
    while offset < len(data):
        length, kind = struct.unpack_from('<II', data, offset)
        chunk = data[offset + 8:offset + 8 + length]
        if kind == CHUNK_JSON:
            document = json.loads(chunk)
        elif kind == CHUNK_BIN:
            binary = bytes(chunk)
        offset += 8 + length
    return document, bytearray(binary)


def write_glb(path, document, binary):
    encoded = json.dumps(document, separators=(',', ':')).encode()
    encoded += b' ' * (-len(encoded) % 4)
    binary = bytes(binary) + b'\0' * (-len(binary) % 4)
    total = 12 + 8 + len(encoded) + (8 + len(binary) if binary else 0)
    out = struct.pack('<III', GLB_MAGIC, 2, total) + struct.pack('<II', len(encoded), CHUNK_JSON) + encoded
    if binary:
        out += struct.pack('<II', len(binary), CHUNK_BIN) + binary
    Path(path).write_bytes(out)


def variant_of_material(document):
    """Material index -> variant name, from the primitives' KHR_materials_variants mappings."""
    names = [v['name'] for v in document.get('extensions', {}).get('KHR_materials_variants', {}).get('variants', [])]
    result = {}
    for mesh in document.get('meshes', []):
        for primitive in mesh.get('primitives', []):
            for mapping in primitive.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                for variant in mapping['variants']:
                    result.setdefault(mapping['material'], names[variant])
    return result


def parse_color(text):
    values = [float(v) for v in text.split(',')]
    if len(values) != 3 or not all(0.0 <= v <= 1.0 for v in values):
        sys.exit(f'colour {text}: three linear values in 0..1')
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('input')
    parser.add_argument('output')
    parser.add_argument('--material', required=True, help='material name prefix')
    parser.add_argument('--mask', help='emission mask PNG (luminance), UV0 of the material')
    parser.add_argument('--color', action='append', default=[], help='r,g,b or VARIANT=r,g,b (linear 0..1)')
    parser.add_argument('--strength', type=float, default=1.0)
    parser.add_argument('--gamma', type=float, default=1.0, help='mask luminance exponent (>1 narrows the glow)')
    parser.add_argument('--pulse', help='amplitude,period: openyamm_pulse')
    parser.add_argument('--no-bloom', action='store_true', help='emit without drawing into the bloom view')
    args = parser.parse_args()

    document, binary = read_glb(args.input)
    colors, default = {}, None
    for entry in args.color:
        if '=' in entry:
            name, value = entry.split('=', 1)
            colors[name] = parse_color(value)
        else:
            default = parse_color(entry)
    variants = variant_of_material(document)
    targets = [i for i, m in enumerate(document.get('materials', [])) if m.get('name', '').startswith(args.material)]
    if not targets:
        sys.exit(f'no material starts with {args.material}')

    texture_index = None
    if args.mask:
        grey = np.asarray(Image.open(args.mask).convert('L'), dtype=np.float64) / 255.0
        grey = np.clip(grey ** args.gamma, 0.0, 1.0)
        image = Image.fromarray(np.round(grey * 255).astype(np.uint8), 'L').convert('RGB')
        png = io.BytesIO()
        image.save(png, 'PNG', optimize=True)
        binary += b'\0' * (-len(binary) % 4)
        views = document.setdefault('bufferViews', [])
        views.append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(png.getvalue())})
        binary += png.getvalue()
        if not document.get('buffers'):
            document['buffers'] = [{}]
        document['buffers'][0]['byteLength'] = len(binary)
        images = document.setdefault('images', [])
        images.append({'name': Path(args.mask).stem + '_emission', 'mimeType': 'image/png',
                       'bufferView': len(views) - 1})
        # The base colour's sampler (same UVs, same filtering).
        base = document['materials'][targets[0]].get('pbrMetallicRoughness', {}).get('baseColorTexture')
        texture = {'source': len(images) - 1}
        if base is not None and 'sampler' in document['textures'][base['index']]:
            texture['sampler'] = document['textures'][base['index']]['sampler']
        document.setdefault('textures', []).append(texture)
        texture_index = len(document['textures']) - 1

    for index in targets:
        material = document['materials'][index]
        color = colors.get(variants.get(index), default)
        if color is None:
            sys.exit(f'material {material.get("name")} (variant {variants.get(index)}): no --color for it')
        factor = [round(min(max(c * args.strength, 0.0), 1.0), 6) for c in color]
        material['emissiveFactor'] = factor
        extras = material.setdefault('extras', {})
        if texture_index is not None:
            material['emissiveTexture'] = {'index': texture_index}
            extras.pop('openyamm_bloom', None)
            if args.no_bloom:
                extras['openyamm_bloom'] = False
        else:
            material.pop('emissiveTexture', None)
            extras['openyamm_bloom'] = not args.no_bloom
        if args.pulse:
            amplitude, period = (float(v) for v in args.pulse.split(','))
            extras['openyamm_pulse'] = [amplitude, period]
        print(f'EMISSION {material.get("name")} variant={variants.get(index)} factor={factor}'
              f'{" texture" if texture_index is not None else ""}')
    write_glb(args.output, document, binary)


if __name__ == '__main__':
    main()
