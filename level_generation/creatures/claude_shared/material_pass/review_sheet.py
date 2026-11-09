#!/usr/bin/env python3
"""Review sheet for the material pass: old and new GLB of one creature, rows old / new, columns sun front, sun
three-quarter, sun head close-up, indoor front, indoor three-quarter, indoor head close-up (Blender Eevee via
render_material_views.py). The base colour is baked for one tier with the shader's region-ramp maths
(tier_textures.py), since Blender does not apply the ramps.
Usage: review_sheet.py <old.glb> <new.glb> <out.png> [--variant N] [--front -y|+y] [--work DIR] [--size PX]"""
import argparse
import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import region_variants as RV  # noqa: E402
import tier_textures as TT  # noqa: E402

COLUMNS = [('sun', 'front'), ('sun', 'three_quarter'), ('sun', 'head'),
           ('indoor', 'front'), ('indoor', 'three_quarter'), ('indoor', 'head')]


def texture(doc, binary, index):
    image = doc['images'][doc['textures'][index]['source']]
    view = doc['bufferViews'][image['bufferView']]
    start = view.get('byteOffset', 0)
    return Image.open(io.BytesIO(binary[start:start + view['byteLength']]))


def prepare(glb, prefix, variant, front, size):
    doc, binary = RV.read_glb(glb)
    material_index = doc['meshes'][0]['primitives'][0].get('material', 0)
    names = [v['name'] for v in doc.get('extensions', {}).get('KHR_materials_variants', {}).get('variants', [])]
    for mapping in doc['meshes'][0]['primitives'][0].get('extensions', {}).get('KHR_materials_variants', {}).get(
            'mappings', []):
        if variant in mapping['variants']:
            material_index = mapping['material']
    material = doc['materials'][material_index]
    pbr = material.get('pbrMetallicRoughness', {})
    extras = material.get('extras', {})
    base = texture(doc, binary, pbr['baseColorTexture']['index']).convert('RGB')
    rgb = np.asarray(base, np.float64) / 255
    if extras.get('openyamm_region_ramps'):
        bands = texture(doc, binary, extras['openyamm_region_mask']['index']).convert('RGBA').split()
        mask = np.stack([np.asarray(b if b.size == base.size else b.resize(base.size, Image.BILINEAR), np.float64) / 255
                         for b in bands], -1)
        rgb = TT.apply(rgb, mask, extras['openyamm_region_ramps'])
    Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)).save(f'{prefix}_base.png')
    texture(doc, binary, pbr['metallicRoughnessTexture']['index']).convert('RGB').save(f'{prefix}_mr.png')
    texture(doc, binary, material['normalTexture']['index']).convert('RGB').save(f'{prefix}_normal.png')
    job = {'glb': str(Path(glb).resolve()), 'base': f'{prefix}_base.png', 'mr': f'{prefix}_mr.png',
           'normal': f'{prefix}_normal.png', 'metallic': pbr.get('metallicFactor', 1.0),
           'roughness': pbr.get('roughnessFactor', 1.0), 'specular': extras.get('openyamm_specular', 1.0),
           'specular_mask': bool(extras.get('openyamm_specular_mask', False)), 'out_prefix': prefix,
           'front': front, 'size': size}
    Path(f'{prefix}_job.json').write_text(json.dumps(job, indent=1))
    return job, (names[variant] if variant < len(names) else material['name'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('old')
    parser.add_argument('new')
    parser.add_argument('out')
    parser.add_argument('--variant', type=int, default=0)
    parser.add_argument('--front', default='-y')
    parser.add_argument('--work')
    parser.add_argument('--size', type=int, default=420)
    args = parser.parse_args()
    work = Path(args.work or Path(args.out).with_suffix('')).resolve()
    work.mkdir(parents=True, exist_ok=True)
    rows = []
    for label, glb in (('old', args.old), ('new', args.new)):
        prefix = str(work / label)
        job, tier = prepare(glb, prefix, args.variant, args.front, args.size)
        subprocess.run(['blender', '--background', '--python', str(HERE / 'render_material_views.py'), '--',
                        f'{prefix}_job.json'], check=True, stdout=subprocess.DEVNULL)
        rows.append((f"{label}: metallic x{job['metallic']:g}, roughness x{job['roughness']:g}, specular "
                     f"{job['specular']:g}{' masked' if job['specular_mask'] else ''} ({tier})", prefix))
    size, top = args.size, 18
    sheet = Image.new('RGB', (size * len(COLUMNS), (size + top) * len(rows) + top), (18, 18, 18))
    draw = ImageDraw.Draw(sheet)
    for c, (light, view) in enumerate(COLUMNS):
        draw.text((c * size + 4, 3), f'{light} {view}', fill=(200, 200, 200))
    for r, (text, prefix) in enumerate(rows):
        y = top + r * (size + top)
        draw.text((4, y + 3), text, fill=(255, 220, 120))
        for c, (light, view) in enumerate(COLUMNS):
            sheet.paste(Image.open(f'{prefix}_{light}_{view}.png').convert('RGB'), (c * size, y + top))
    sheet.save(args.out)
    print('WROTE', args.out)


if __name__ == '__main__':
    main()
