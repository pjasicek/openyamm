#!/usr/bin/env python3
"""Add ramp-only skins (KHR_materials_variants) to an accepted actor GLB, keeping every existing variant.

Usage: add_variants.py <in.glb> <out.glb> <spec.json>

spec.json:
  {"variants": [{"name": "xboy_ginger",
                 "materials": {"<default LOD0 material name>": {"from": "<existing LOD0 material to copy>",
                                                               "ramps": [<region ramp> ...] | null,
                                                               "mask": "<png path>" | null}}}]}

For every primitive whose default material (name without `_LOD<n>`) is listed, the variant maps to a new material
`<default>_<variant>` (a copy of `from`, at LOD2/LOD3 a copy of `from_LOD<n>` named `<default>_<variant>_LOD<n>`)
with the given ramps and, where `mask` is set, a new region mask image. A listed default with "ramps": null keeps
`from`'s extras. Primitives whose default is not listed map the variant to their default material. Far LOD copies
keep their far maps; run lod_repair_claude/scripts/fix_variant_maps.py afterwards so a variant whose LOD0 maps
differ from the default's (another head picture, its own mask) gets far maps of its own.
"""
import copy
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared'))
from region_variants import read_glb, write_glb  # noqa: E402

LOD = re.compile(r'^(.*)_LOD(\d)$')


def add_png(doc, binary, name, path, sampler=0):
    data = Path(path).read_bytes()
    binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
    binary.extend(data)
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': name})
    doc['textures'].append({'source': len(doc['images']) - 1, 'sampler': sampler})
    return len(doc['textures']) - 1


def main():
    source, out, spec_path = sys.argv[1:4]
    spec = json.loads(Path(spec_path).read_text())
    doc, binary = read_glb(source)
    binary = bytearray(binary)
    ext = doc['extensions']['KHR_materials_variants']['variants']
    names = {m['name']: i for i, m in enumerate(doc['materials'])}
    for variant in spec['variants']:
        vname = variant['name']
        if any(v['name'] == vname for v in ext):
            raise SystemExit(f'variant {vname} exists already')
        ext.append({'name': vname})
        vindex = len(ext) - 1
        made = {}
        masks = {}

        def material_for(default_lod0, level):
            key = (default_lod0, level)
            if key in made:
                return made[key]
            entry = variant['materials'][default_lod0]
            src_name = entry['from'] + (f'_LOD{level}' if level else '')
            if src_name not in names:
                raise SystemExit(f'no material {src_name}')
            material = copy.deepcopy(doc['materials'][names[src_name]])
            material['name'] = f'{default_lod0}_{vname}' + (f'_LOD{level}' if level else '')
            extras = material.setdefault('extras', {})
            if entry.get('ramps') is not None:
                extras['openyamm_region_ramps'] = entry['ramps']
                if entry.get('mask'):
                    if default_lod0 not in masks:
                        masks[default_lod0] = add_png(doc, binary, f'{default_lod0}_{vname}_mask', entry['mask'])
                    extras['openyamm_region_mask'] = {'index': masks[default_lod0]}
                elif 'openyamm_region_mask' not in extras:
                    raise SystemExit(f'{src_name}: ramps without a mask')
            doc['materials'].append(material)
            names[material['name']] = len(doc['materials']) - 1
            made[key] = len(doc['materials']) - 1
            return made[key]

        for mesh in doc['meshes']:
            for primitive in mesh['primitives']:
                mappings = primitive.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings')
                if mappings is None:
                    continue
                default_name = doc['materials'][primitive['material']]['name']
                match = LOD.match(default_name)
                base, level = (match.group(1), int(match.group(2))) if match else (default_name, 0)
                if base in variant['materials']:
                    target = material_for(base, level)
                else:
                    target = primitive['material']
                mappings.append({'material': target, 'variants': [vindex]})
    write_glb(out, doc, bytes(binary))
    print('wrote', out, 'variants', [v['name'] for v in ext])


if __name__ == '__main__':
    main()
