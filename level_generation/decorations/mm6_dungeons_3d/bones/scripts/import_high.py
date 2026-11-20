"""Import the full-detail Meshy pile (meshy/skullpile_hd_multiview_v1), ground it (base centre at the origin, min z 0,
height 153 units), squash it across to the sprite's width profile if WIDTH_RATIO is set, attach its Meshy PBR
texture set and save work/pile_high.blend. Usage: blender --background --python import_high.py -- [squash]"""
import os
import sys

import bmesh
import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blib  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
SQUASH = float(args[0]) if args else 1.0
JOB = os.path.join(blib.HERE, 'meshy', 'skullpile_hd_multiview_v1')
bpy.ops.wm.read_factory_settings(use_empty=True)
obj = blib.import_mesh(os.path.join(JOB, 'model_urls_glb.glb'), 'high')
mats = list(obj.data.materials)
blib.ground(obj, blib.u(153))
if SQUASH != 1.0:
    for v in obj.data.vertices:
        v.co.x *= SQUASH; v.co.y *= SQUASH
bm = bmesh.new(); bm.from_mesh(obj.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
bm.to_mesh(obj.data); bm.free()
co = np.array([v.co[:] for v in obj.data.vertices])
print('HIGH tris', sum(len(p.vertices) - 2 for p in obj.data.polygons), 'verts', len(co), 'materials',
      [m.name for m in mats], 'uv layers', len(obj.data.uv_layers),
      'size units', np.round((co.max(0) - co.min(0)) * blib.dl.UNITS_PER_METRE, 1).tolist())
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(blib.WORK, 'pile_high.blend'))
