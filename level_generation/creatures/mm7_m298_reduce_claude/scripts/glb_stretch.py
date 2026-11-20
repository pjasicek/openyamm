"""Edge stretch straight from a GLB (the original project's outliers.py gate, on the exported LOD0): per clip, the
largest posed/rest edge-length ratio over every 2nd frame (edges under 1 mm at rest ignored) and where it is.
Usage: blender -b -P glb_stretch.py -- <glb> <mesh node>"""
import bpy, os, sys
import numpy as np
glb, node = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
body = bpy.data.objects[node]; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); me = body.data
E = np.array([tuple(e.vertices) for e in me.edges]); rest = np.array([tuple(v.co) for v in me.vertices])
L0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1); ok = L0 > 1e-3
for A in sorted(bpy.data.actions, key=lambda a: a.name):
    rig.animation_data.action = A
    if len(A.slots):
        rig.animation_data.action_slot = A.slots[0]
    f0, f1 = map(int, A.frame_range); worst = (0, None, None)
    for f in range(f0, f1 + 1, 2):
        bpy.context.scene.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        P = np.array([tuple(v.co) for v in m.vertices]); ev.to_mesh_clear()
        r = np.where(ok, np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / np.maximum(L0, 1e-6), 0)
        i = int(np.argmax(r))
        if r[i] > worst[0]:
            worst = (float(r[i]), f, int(E[i, 0]))
    print('STRETCH', A.name, round(worst[0], 2), 'frame', worst[1], 'rest', np.round(rest[worst[2]], 3))
