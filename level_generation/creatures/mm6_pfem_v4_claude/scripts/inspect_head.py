"""Inspect the head-only Meshy model: normalised as graft_head_parts.py does (unit height, centred, neck/bust bottom
at z 0), textured and clay renders front/left/back, and a height profile of the
mesh width (x extent) and depth per 0.025 band, to choose where the invented bust is cut. Args: -- [glb]"""
import bpy, bmesh, sys, os
import numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
glb = args[0] if args else os.path.join(common.PROJECT, 'meshy', 'head_v1', 'model_urls_glb.glb')
common.clear_scene()
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
head = max((o for o in bpy.data.objects if o.type == 'MESH'), key=lambda o: len(o.data.vertices))
head.parent = None
for o in bpy.context.view_layer.objects:
    o.select_set(o is head)
bpy.context.view_layer.objects.active = head
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([tuple(v.co) for v in head.data.vertices]); lo, hi = co.min(0), co.max(0)
bm = bmesh.new(); bm.from_mesh(head.data)
bm.transform(Matrix.Scale(1.0 / (hi[2] - lo[2]), 4) @ Matrix.Translation(Vector((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]))))
bm.to_mesh(head.data); bm.free()
co = np.array([tuple(v.co) for v in head.data.vertices])
print('HEADMESH verts', len(co), 'tris', sum(len(p.vertices) - 2 for p in head.data.polygons), 'raw size', [round(float(x), 3) for x in hi - lo],
      'y', round(float(co[:, 1].min()), 3), round(float(co[:, 1].max()), 3))
for z in np.arange(0, 1.0001, 0.025):
    m = (co[:, 2] >= z) & (co[:, 2] < z + 0.025)
    if m.any():
        print('BAND z %.3f  x %.3f..%.3f  y %.3f..%.3f  n %d' % (z, co[m, 0].min(), co[m, 0].max(), co[m, 1].min(), co[m, 1].max(), m.sum()))
scene = bpy.context.scene
common.workbench_clay(scene, textured=True)
common.render_views(os.path.join(common.REVIEW, 'head_v1_raw_tex'), 0.5, 1.1, views=('front', 'left', 'back', 'right'), resolution=(500, 500))
common.workbench_clay(scene)
common.render_views(os.path.join(common.REVIEW, 'head_v1_raw_clay'), 0.5, 1.1, views=('front', 'left', 'back'), resolution=(500, 500))
