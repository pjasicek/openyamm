"""Reduce the root skirt (Treant): Smart Topology spent 6.6k of 17k triangles on the root tendrils lying on the ground
(face centre below z 0.35 m). Edit-mode collapse decimation of those faces only (ratio RATIO), UVs and weights
interpolated by the collapse; trunk, face, teeth, eyes and crown untouched. work/rig_v2.blend -> work/rig_v3.blend.
Args: none   env RATIO (default 0.5)"""
import bpy, os, bmesh
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RATIO = float(os.environ.get('RATIO', '0.5'))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v2.blend'))
body = bpy.data.objects['Body']; me = body.data
before = sum(len(p.vertices) - 2 for p in me.polygons)
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(me)
pa = bm.verts.layers.int.get('part')
for f in bm.faces:
    f.select = f.calc_center_median().z < 0.35 and all(v[pa] == 0 for v in f.verts)
bmesh.update_edit_mesh(me)
bpy.ops.mesh.decimate(ratio=RATIO)
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.quads_convert_to_tris()
bpy.ops.object.mode_set(mode='OBJECT')
# keep the root tendrils on the floor
co = np.array([tuple(v.co) for v in me.vertices])
print('REDUCE tris', before, '->', sum(len(p.vertices) - 2 for p in me.polygons), 'min z', round(float(co[:, 2].min()), 4))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v3.blend'))
