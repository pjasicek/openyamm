"""Review of the barrel's state overlays with back faces culled (as the engine draws single-sided materials): each
liquid in mm8_deco_barrel's LOD0 from three-quarter above, the empty barrel, LOD1 and LOD2 with the red liquid, and
the barrel from below. Writes review/barrel_liquids/*.png; sheet with sheet_liquids (below, run with python3).
Usage: blender --background --python review_liquids.py"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm8lib as ml  # noqa: E402

pl = ml.pl
OUT = os.path.join(ml.HERE, 'review', 'barrel_liquids')
COLOURS = ['red', 'yellow', 'blue', 'orange', 'green', 'purple', 'white']


def load(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before and o.type == 'MESH']


def main():
    os.makedirs(OUT, exist_ok=True)
    pl.reset()
    barrel = sorted(load(os.path.join(ml.WORK, 'barrel_export.glb')), key=lambda o: o.name)   # unlinked LODs
    liquids = {c: load(os.path.join(ml.WORK, 'liquids', f'mm8_deco_barrel_liquid_{c}.glb'))[0] for c in COLOURS}
    for m in bpy.data.materials:
        m.use_backface_culling = True
        if m.name.startswith('liquid_'):
            m.surface_render_method = 'BLENDED'
    pl.setup_render((420, 420))
    bpy.context.scene.eevee.taa_render_samples = 8
    everything = barrel + list(liquids.values())

    def shot(objects, name, view):
        for o in everything:
            o.hide_render = o not in objects
        pl.render_views(objects, OUT, name, views=(view,))
    lod0 = barrel[0]
    for c in COLOURS:
        shot([lod0, liquids[c]], f'a_{COLOURS.index(c)}_{c}', (35, 45))
    shot([lod0], 'b_empty', (35, 45))
    shot([barrel[1], liquids['red']], 'c_lod1_red', (35, 45))
    shot([barrel[2], liquids['red']], 'd_lod2_red', (35, 45))
    shot([lod0, liquids['blue']], 'e_low_blue', (200, 15))
    shot([lod0], 'f_below', (35, -50))


main()
