"""Prepare a Meshy Smart Topology return of a statue (statues_hd/<name>/meshy/) for its retexture: import, drop crumbs,
turn (rot_z degrees) so the statue faces Blender -y, ground (base centre at the origin, min z = 0), triangulate,
Smart UV Project + pack, then save work/hd_<name>_uv.blend and the neutral upload statues_hd/<name>/upload.glb.
Helpers: the MM6 bones batch's blib (read only).
Usage: blender --background --python hd_prep.py -- <name> <smart topology glb> [rot_z degrees]"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlib  # noqa: E402

sys.path.insert(0, os.path.join(dlib.DECO, 'mm6_dungeons_3d', 'bones', 'scripts'))
import blib  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
name, source = args[0], args[1]
turn = float(args[2]) if len(args) > 2 else 0.0
HD = os.path.join(dlib.HERE, 'statues_hd', name)
bpy.ops.wm.read_factory_settings(use_empty=True)
obj = blib.import_mesh(source, name)
obj.data.materials.clear()
pieces, dropped = blib.drop_small_pieces(obj, keep_fraction=0.004)
if turn:
    obj.rotation_euler = (0, 0, math.radians(turn))
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
    bpy.ops.object.transform_apply(rotation=True)
blib.ground(obj, 1.0)
blib.triangulate(obj)
blib.smart_uv(obj, angle=1.15, margin=0.004)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(dlib.WORK, f'hd_{name}_uv.blend'))
blib.export_neutral(obj, os.path.join(HD, 'upload.glb'))
print('PREP', name, 'pieces', pieces, 'dropped', dropped, 'tris', len(obj.data.polygons),
      'dims', [round(d, 3) for d in obj.dimensions])
