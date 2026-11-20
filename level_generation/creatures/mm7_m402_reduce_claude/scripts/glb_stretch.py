"""Edge-stretch gate of the original project (mm7_m402_claude/scripts/outliers.py) on a GLB: per clip, the largest
posed/rest edge-length ratio over every 2nd frame for each colour LOD mesh. Usage: blender -b -P glb_stretch.py -- <glb> <label>"""
import bpy, sys, os
import numpy as np
glb, label = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for name in ('M402', 'M402_LOD1', 'M402_LOD2', 'M402_LOD3'):
    body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.data.name.split('.')[0] == name or o.name == name)
    me = body.data
    E = np.array([tuple(e.vertices) for e in me.edges])
    rest = np.array([tuple(v.co) for v in me.vertices]); L0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
    out = {}
    for A in bpy.data.actions:
        rig.animation_data.action = A
        if len(A.slots):
            rig.animation_data.action_slot = A.slots[0]
        f0, f1 = map(int, A.frame_range); worst = 0
        for f in range(f0, f1 + 1, 2):
            bpy.context.scene.frame_set(f)
            ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
            P = np.array([tuple(v.co) for v in m.vertices]); ev.to_mesh_clear()
            worst = max(worst, float((np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / np.maximum(L0, 1e-6)).max()))
        out[A.name.split('_')[0]] = round(worst, 2)
    print('STRETCH', label, name, len(me.polygons), out)
