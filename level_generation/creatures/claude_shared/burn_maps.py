#!/usr/bin/env python3
"""Engine burn deaths (actors.yml death_effect: burn): embed one burn map per base material in a creature GLB.

A burn map is a linear PNG in the material's UV space: red orders the surface for the burn (0 first, 1 last), green
drives the glowing cracks of the charred band (fs_model.sc). Each listed material gets
extras.openyamm_burn_map = {"index": <texture>}; run this before region_variants.apply_variants, whose tier copies
keep the extra. Every skinned material of a burning creature needs one (the engine rejects the binding otherwise).
The model cook (tools/cook_models.py) bakes the red channel per vertex (_BURN_ORDER) and compresses the map; install
with tools/install_model.py, since an uncooked burning model fails its binding.

CLI: burn_maps.py in.glb out.glb MATERIAL=map.png [MATERIAL=map.png ...]
"""
import sys
from pathlib import Path

from region_variants import read_glb, write_glb


def add_burn_maps(source, destination, maps):
    """maps: {material name (Blender's numeric suffix allowed): burn map PNG path}."""
    doc, binary = read_glb(source)
    binary = bytearray(binary)
    names = [material.get('name', '') for material in doc['materials']]
    for name, path in maps.items():
        matches = [index for index, value in enumerate(names) if value == name or value.startswith(name + '.')]
        if len(matches) != 1:
            raise ValueError(f'burn map material {name}: {len(matches)} matches')
        data = Path(path).read_bytes()
        binary += b'\0' * (-len(binary) % 4)
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
        binary += data
        doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png',
                              'name': Path(path).stem})
        doc['textures'].append({'source': len(doc['images']) - 1})
        doc['materials'][matches[0]].setdefault('extras', {})['openyamm_burn_map'] = {
            'index': len(doc['textures']) - 1}
    write_glb(destination, doc, binary)


if __name__ == '__main__':
    add_burn_maps(sys.argv[1], sys.argv[2], dict(arg.split('=', 1) for arg in sys.argv[3:]))
