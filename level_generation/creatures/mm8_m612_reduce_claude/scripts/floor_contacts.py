"""Rest positions (model space, Z up) of LOD0 vertices that come within REA_FLOOR_EPS (default 6 mm) of the floor in
any Death/Dead frame -> work/floor_contacts.json, for build_lods.py protected_points (the LOD3 collapse otherwise
pushed the Phoenix's landed body 3.7 mm through the floor). Usage: blender -b -P floor_contacts.py"""
import json, os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'work', 'r71_lod0.glb'))
sc = bpy.context.scene; o = bpy.data.objects[os.environ.get('REA_NODE', 'Body')]; rig = next(m.object for m in o.modifiers if m.type == 'ARMATURE')
rest = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices]); low = set()
eps = float(os.environ.get('REA_FLOOR_EPS', '0.006'))
for name in ('Death', 'Dead'):
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
        sc.frame_set(f); ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
        z = np.array([(ev.matrix_world @ v.co).z for v in me.vertices]); ev.to_mesh_clear()
        low |= set(np.where(z < eps)[0].tolist())
pts = np.unique(np.round(rest[sorted(low)], 6), axis=0)
json.dump(pts.tolist(), open(os.path.join(HERE, 'work', 'floor_contacts.json'), 'w'))
print('CONTACTS', len(low), 'vertices,', len(pts), 'points')
