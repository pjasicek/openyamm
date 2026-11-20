"""Edge stretch straight from a GLB (the original project's outliers.py on the exported mesh node): per clip, the
largest posed/rest edge length ratio over every frame, with the rest position and top weights of the worst vertex.
Usage: blender -b -P glb_stretch.py -- <glb> [node, default M382]"""
import bpy, os, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]; glb = a[0]; NODE = a[1] if len(a) > 1 else 'M382'
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
body = bpy.data.objects[NODE]; me = body.data; rig = next(m.object for m in body.modifiers if m.type == 'ARMATURE')
E = np.array([tuple(e.vertices) for e in me.edges])
rest = np.array([tuple(v.co) for v in me.vertices]); L0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
ok = L0 > 2e-4                                                            # ignore near-zero edges
for A in bpy.data.actions:
    rig.animation_data.action = A
    if len(A.slots):
        rig.animation_data.action_slot = A.slots[0]
    f0, f1 = map(int, A.frame_range); worst = (0, None, None)
    for f in range(f0, f1 + 1):
        bpy.context.scene.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        P = np.array([tuple(v.co) for v in m.vertices]); ev.to_mesh_clear()
        r = np.where(ok, np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / np.maximum(L0, 1e-6), 0)
        i = int(np.argmax(r))
        if r[i] > worst[0]:
            worst = (float(r[i]), f, int(E[i, 0]))
    v = worst[2]; grp = sorted(((g.weight, body.vertex_groups[g.group].name) for g in me.vertices[v].groups), reverse=True)[:3]
    print('STRETCH', A.name, round(worst[0], 2), 'frame', worst[1], 'rest', np.round(rest[v], 3), [(n, round(w, 2)) for w, n in grp])
