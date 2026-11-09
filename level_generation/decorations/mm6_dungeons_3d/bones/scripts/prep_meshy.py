"""Prepare a Meshy Smart Topology return for its retexture: import, drop crumbs, ground (base centre at the origin,
optionally scaled to a height), Smart UV Project + pack, then save work/<name>_uv.blend and the neutral upload
texturing/<name>_upload.glb.
Usage: blender --background --python prep_meshy.py -- <name> <meshy model.glb> [height metres] [rot_z degrees]"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blib  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
name, source = args[0], args[1]
height = float(args[2]) if len(args) > 2 and args[2] != '-' else None
turn = float(args[3]) if len(args) > 3 else 0.0
bpy.ops.wm.read_factory_settings(use_empty=True)
obj = blib.import_mesh(source, name)
for slot in list(obj.data.materials):
    obj.data.materials.clear()
pieces, dropped = blib.drop_small_pieces(obj)
if turn:
    obj.rotation_euler = (0, 0, math.radians(turn))
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
    bpy.ops.object.transform_apply(rotation=True)
blib.ground(obj, height)
blib.triangulate(obj)
blib.smart_uv(obj)
os.makedirs(blib.WORK, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(blib.WORK, f'{name}_uv.blend'))
blib.export_neutral(obj, os.path.join(blib.HERE, 'texturing', f'{name}_upload.glb'))
dims = obj.dimensions
print('PREP', name, 'pieces', pieces, 'dropped', dropped, 'tris', len(obj.data.polygons),
      'dims', [round(d, 3) for d in dims])
