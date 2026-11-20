"""Textured workbench views (front, three-quarter, side, back, top) of a single prop GLB, centred and fitted.
Args: -- <glb> <out prefix>"""
import bpy, sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
glb, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
ms = [o for o in bpy.data.objects if o.type == 'MESH' and 'LOD' not in o.name and 'Shadow' not in o.name]
for o in bpy.data.objects:
    if o.type == 'MESH' and o not in ms:
        o.hide_render = True
co = np.array([tuple(o.matrix_world @ v.co) for o in ms for v in o.data.vertices])
c = (co.max(0) + co.min(0)) / 2; size = float(np.ptp(co, axis=0).max())
sc = bpy.context.scene; common.workbench_clay(sc, textured=True)
print('PROPGLB tris', sum(len(p.vertices) - 2 for o in ms for p in o.data.polygons), 'size', np.round(np.ptp(co, axis=0), 3))
common.render_views(out, float(c[2]), size * 1.15, views=('front', 'three_quarter', 'left', 'back'), resolution=(500, 500),
                    target=(float(c[0]), float(c[1])))
