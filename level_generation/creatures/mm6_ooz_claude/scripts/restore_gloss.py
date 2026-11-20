#!/usr/bin/env python3
"""Restore the user-reviewed wet-slime material on the installed ooze, nothing else (2026-10-30).

The 2026-10-16 material pass flattened the ooze: openyamm_specular 0.7 with a per-texel crease mask and roughness 0.5
became 1.0 with a flat mask of 0.30 and roughness 0.7. material_pass/revert.sh cannot be used: its backup predates the
far-LOD repair and would bring the broken far LODs back. This keeps the installed GLB and changes only the factors and
the metal/roughness maps: LOD0's from the backup, and the far LODs' re-derived from it per texel with the far-LOD
repair's own transfer_textures.py, because far textures do not follow LOD0 (see lod_repair_claude/README.md).

Usage: restore_gloss.py <installed source glb> <backup glb> <output glb>
"""
import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'level_generation/creatures/lod_repair_claude/scripts'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
from build_lods import source_faces  # noqa: E402
from splice_lods import floats  # noqa: E402
from transfer_textures import transfer  # noqa: E402

LOD0_MAP = 'ooz_metal_rough_1k'
FAR_MAPS = {'Ooze_LOD2': 'Ooze_A_lod2_mr', 'Ooze_LOD3': 'Ooze_A_lod3_mr'}
SPECULAR = 0.7


def image_view(doc, name):
    source = next(entry for entry in doc['images'] if entry.get('name') == name)
    return source['bufferView']


def view_bytes(doc, binary, view_index):
    view = doc['bufferViews'][view_index]
    start = view.get('byteOffset', 0)
    return binary[start:start + view['byteLength']]


def replaced(doc, binary, payloads):
    """The binary with the given bufferViews' bytes swapped, every view repacked in its old order."""
    packed = bytearray()
    for index in sorted(range(len(doc['bufferViews'])), key=lambda i: doc['bufferViews'][i].get('byteOffset', 0)):
        data = payloads.get(index, view_bytes(doc, binary, index))
        packed += b'\0' * (-len(packed) % 4)
        doc['bufferViews'][index]['byteOffset'] = len(packed)
        doc['bufferViews'][index]['byteLength'] = len(data)
        packed += data
    return bytes(packed)


def far_map(doc, binary, mesh_name):
    """Metal/roughness of one far LOD from LOD0's current map (same transfer as the far-LOD repair)."""
    mesh = next(entry for entry in doc['meshes'] if entry['name'] == mesh_name)
    lod0 = next(entry for entry in doc['meshes'] if entry['name'] == 'Ooze')
    primitive = mesh['primitives'][0]
    faces = source_faces(doc, binary, primitive)
    corner_uv = floats(doc, binary, primitive['attributes']['TEXCOORD_0'])[faces]
    size = Image.open(io.BytesIO(view_bytes(doc, binary, image_view(doc, FAR_MAPS[mesh_name])))).size[0]
    maps, _ = transfer(doc, binary, lod0['primitives'][0], primitive, faces, corner_uv, size)
    return maps['mr']


def main():
    source, backup, output = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    doc, binary = read_glb(source)
    backup_doc, backup_binary = read_glb(backup)

    # The far maps from the installed LOD0 must reproduce the installed far maps, or the UVs are read wrongly.
    for mesh_name, map_name in FAR_MAPS.items():
        current = np.asarray(Image.open(io.BytesIO(view_bytes(doc, binary, image_view(doc, map_name)))).convert('RGB'))
        rebuilt = np.asarray(far_map(doc, binary, mesh_name).convert('RGB'))
        difference = np.abs(current.astype(int) - rebuilt.astype(int)).mean()
        print(f'{mesh_name}: transfer reproduces the installed map within {difference:.2f}/255')
        if difference > 2.0:
            raise SystemExit('far map transfer does not match the installed map')

    lod0_view = image_view(doc, LOD0_MAP)
    binary = replaced(doc, binary, {lod0_view: view_bytes(backup_doc, backup_binary, image_view(backup_doc, LOD0_MAP))})
    payloads = {}
    for mesh_name, map_name in FAR_MAPS.items():
        out = io.BytesIO()
        far_map(doc, binary, mesh_name).save(out, 'PNG')
        payloads[image_view(doc, map_name)] = out.getvalue()
    binary = replaced(doc, binary, payloads)

    for material in doc['materials']:
        material['extras']['openyamm_specular'] = SPECULAR
        material['pbrMetallicRoughness']['metallicFactor'] = 0
    write_glb(output, doc, binary)


if __name__ == '__main__':
    main()
