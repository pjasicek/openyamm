"""Skinned LOD0 of the school (imported as is) at every 1/24 s of every clip -> work/pose_<label>.npz
(per frame: vertex positions; triangles; per-vertex fish index from the dominant joint).
Usage: blender -b -P pose_dump.py -- <glb> <label>"""
import os, sys, bpy
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]; glb, label = a[0], a[1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=glb if os.path.isabs(glb) else os.path.join(HERE, glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
ob = bpy.data.objects['School']
me = ob.data; me.calc_loop_triangles()
tris = np.array([[l for l in t.vertices] for t in me.loop_triangles], np.int32)
names = [g.name for g in ob.vertex_groups]
fish = np.array([int(max(((g.weight, names[g.group]) for g in v.groups if names[g.group].startswith('Fish')),
                         default=(0, 'Fish-1'))[1][4:6].rstrip('_')) for v in me.vertices])
print('FISH VERTS', np.bincount(fish + 1))
out = {'tris': tris, 'fish': fish}
for act in bpy.data.actions:
    clip = act.name.split('|')[-1]; rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range; frames = np.arange(f0, f1 + 1e-6, 1.0)
    P = []
    for fr in frames:
        sc.frame_set(int(fr), subframe=float(fr - int(fr)))
        ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); ev.to_mesh_clear()
        P.append(co.reshape(-1, 3) @ np.array(ob.matrix_world)[:3, :3].T + np.array(ob.matrix_world)[:3, 3])
    out[f'clip_{clip}'] = np.array(P, np.float32)
np.savez(os.path.join(HERE, 'work', f'pose_{label}.npz'), **out); print('POSES', label, [k for k in out if k.startswith('clip_')], len(tris))
