"""lod_check.py's stretched-face test on one lodcheck GLB and clip, printing each stretched face (Blender import, evaluated mesh,
every frame): rest/posed area, rest centroid, material. Usage: blender -b -P stretch_where.py -- <glb> <clip>"""
import bpy, bmesh, sys
import numpy as np
glb, clip = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=glb); o = bpy.data.objects['ClanSoldier']
rig = next(m.object for m in o.modifiers if m.type == 'ARMATURE'); rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
def state():
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world); b.faces.ensure_lookup_table()
    out = np.array([f.calc_area() for f in b.faces]), np.array([f.calc_center_median()[:] for f in b.faces]), np.array([f.material_index for f in b.faces]); b.free(); return out
a0, c0, m0 = state()
act = bpy.data.actions[clip]; rig.animation_data.action = act
if act.slots: rig.animation_data.action_slot = act.slots[0]
seen = {}
for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
    sc.frame_set(f); a1, _, _ = state()
    for i in np.where((a1 > 1e-6) & (a1 > 20 * (a0 + 1e-9)))[0]:
        seen[i] = max(seen.get(i, 0), a1[i])
for i, a in seen.items():
    print('STRETCH face', i, 'mat', o.data.materials[m0[i]].name, 'rest mm2', round(a0[i] * 1e6, 4), 'max posed mm2', round(a * 1e6, 2), 'rest centre', np.round(c0[i], 3))
