"""Shared paths and helpers for the MM8 rocks batch. Blender helpers come from the MM6 outdoor props library
(../../../mm6_new_sorpigal_3d/props/scripts/props_lib.py, read only). SCANS maps a short key to a Poly Haven CC0 scan
(glTF path, mesh node name or None for the whole file): the MM6 rock sources are read in place (read only), the
new ones live in ../source/ (scripts/fetch_scans.py)."""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
DECO = os.path.join(REPO, 'level_generation', 'decorations')
sys.path.insert(0, os.path.join(DECO, 'mm6_new_sorpigal_3d', 'props', 'scripts'))
import props_lib as pl  # noqa: E402

WORK = os.path.join(HERE, 'work')
REVIEW = os.path.join(HERE, 'review')
X2 = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2')
# the MM8 decoration sprites were retired from the runtime on 2026-10-16; their archive is read only
X2_ARCHIVE = os.path.join(REPO, 'assets_legacy', 'decorations_x2_mm8_20261016')


def sprite_path(name):
    """A native x2 sprite file: the runtime copy, else the retirement archive."""
    live = os.path.join(X2, name)
    return live if os.path.exists(live) else os.path.join(X2_ARCHIVE, name)
UNITS_PER_METRE = 81.7
MM6_ROCKS = os.path.join(DECO, 'mm6_new_sorpigal_3d', 'rocks', 'source')
MM6_ROCK = os.path.join(DECO, 'mm6_new_sorpigal_3d', 'rock', 'source')
SRC = os.path.join(HERE, 'source')


def units(value):
    return value / UNITS_PER_METRE


SCANS = {
    'boulder_01': (os.path.join(MM6_ROCKS, 'boulder_01', 'boulder_01_2k.gltf'), None),
    'nb03': (os.path.join(MM6_ROCK, 'namaqualand_boulder_03', 'namaqualand_boulder_03_2k.gltf'), None),
    'nb04': (os.path.join(MM6_ROCK, 'namaqualand_boulder_04', 'namaqualand_boulder_04_2k.gltf'), None),
    'nb05': (os.path.join(MM6_ROCKS, 'namaqualand_boulder_05', 'namaqualand_boulder_05_2k.gltf'), None),
    'nb06': (os.path.join(MM6_ROCKS, 'namaqualand_boulder_06', 'namaqualand_boulder_06_2k.gltf'), None),
    'nbs01a': (os.path.join(MM6_ROCKS, 'namaqualand_boulders_01', 'namaqualand_boulders_01_a_2k.gltf'), None),
    'nbs01b': (os.path.join(MM6_ROCKS, 'namaqualand_boulders_01', 'namaqualand_boulders_01_b_2k.gltf'), None),
    'rock_09': (os.path.join(MM6_ROCKS, 'rock_09', 'rock_09_2k.gltf'), None),
}
for i in range(1, 7):
    SCANS[f'ms1_{i}'] = (os.path.join(SRC, 'rock_moss_set_01', 'rock_moss_set_01_2k.gltf'), f'rock_moss_set_01_rock0{i}')
for i in range(7, 14):
    SCANS[f'ms2_{i}'] = (os.path.join(SRC, 'rock_moss_set_02', 'rock_moss_set_02_2k.gltf'), f'rock_moss_set_02_rock{i:02d}')
for c in 'abcd':
    SCANS[f'nr_{c}'] = (os.path.join(SRC, 'namaqualand_rocks_01', 'namaqualand_rocks_01_2k.gltf'), f'namaqualand_rocks_02_{c}')
for c in 'abcde':
    SCANS[f'ns_{c}'] = (os.path.join(SRC, 'namaqualand_stones_01', 'namaqualand_stones_01_2k.gltf'), f'namaqualand_stones_01_{c}')


def import_scan(key):
    """Import one scan (only its named mesh node for a set); returns the mesh objects, other imports removed."""
    import bpy
    path, node = SCANS[key]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    keep = [o for o in new if o.type == 'MESH' and (node is None or o.name == node or o.data.name == node
                                                     or o.name.startswith(node))]
    if not keep:
        raise RuntimeError(f'{key}: node {node} not found in {[o.name for o in new]}')
    for o in keep:                               # keep world transforms when the importer's parents go
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o not in keep:
            bpy.data.objects.remove(o)
    return keep
