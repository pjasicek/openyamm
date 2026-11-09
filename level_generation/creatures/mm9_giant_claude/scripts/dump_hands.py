"""Rest vertices of both hands with their dominant bone, vertex normals and the armature's bone frames (Blender world) to work/hands_dump.npz,
for the offline grip solve (third pass). Args: <blend> <out npz>"""
import bpy, sys, numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
gid = {g.index: g.name for g in body.vertex_groups}
Wm = np.array(rig.matrix_world)
idx, names, co, nr = [], [], [], []
for v in me.vertices:
    if not v.groups: continue
    g = max(v.groups, key=lambda x: x.weight); n = gid[g.group]
    if (' R ' in n or ' L ' in n) and any(k in n for k in ('Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Forearm')):
        idx.append(v.index); names.append(n); co.append(tuple(body.matrix_world @ v.co)); nr.append(tuple(v.normal))
BR = {b.name: (Wm[:3, :3] @ np.array(b.matrix_local)[:3, :3]).tolist() for b in rig.data.bones}
import json
np.savez(OUT, idx=np.array(idx), names=np.array(names), co=np.array(co), nr=np.array(nr), br=json.dumps(BR))
print('DUMP', len(idx))
