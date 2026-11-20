"""Inspect the MM9 source rig: bone heads, mesh symmetry (mirror x), per-clip max rotation per bone vs rest,
lowest point per clip. Args: <mm9 rig blend> <json out>"""
import bpy, sys, json, math
import numpy as np
from mathutils.kdtree import KDTree
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
arm = bpy.data.objects['MM9_Rig']
rep = {'bones': {b.name: [round(x, 4) for x in b.head_local] + [b.parent.name if b.parent else None] for b in arm.data.bones}}
P = []
for o in bpy.data.objects:
    if o.type == 'MESH':
        P += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
P = np.array(P)
k = KDTree(len(P))
for i, p in enumerate(P):
    k.insert(p, i)
k.balance()
d = np.array([k.find((-p[0], p[1], p[2]))[2] for p in P])
rep['mesh_bbox'] = [P.min(0).round(4).tolist(), P.max(0).round(4).tolist()]
rep['mirror_dist'] = {'mean': float(d.mean()), 'p95': float(np.percentile(d, 95)), 'max': float(d.max())}
sc = bpy.context.scene
fps = sc.render.fps / sc.render.fps_base
dg = bpy.context.evaluated_depsgraph_get()
rep['clips'] = {}
for act in bpy.data.actions:
    arm.animation_data_create(); arm.animation_data.action = act
    f0, f1 = act.frame_range
    worst = {}
    zmin = 9
    for f in np.linspace(f0, f1, 25):
        sc.frame_set(int(f), subframe=f - int(f))
        for pb in arm.pose.bones:
            q = pb.rotation_quaternion if pb.rotation_mode == 'QUATERNION' else pb.rotation_euler.to_quaternion()
            a = math.degrees(q.angle if q.angle <= math.pi else 2 * math.pi - q.angle)
            worst[pb.name] = max(worst.get(pb.name, 0), a)
        for o in bpy.data.objects:
            if o.type == 'MESH':
                me = o.evaluated_get(dg).to_mesh()
                zmin = min(zmin, min((o.matrix_world @ v.co).z for v in me.vertices))
                o.evaluated_get(dg).to_mesh_clear()
    rep['clips'][act.name] = {'frames': [f0, f1], 'sec': (f1 - f0) / fps, 'zmin': round(zmin, 4),
                              'rot': {b: round(v, 1) for b, v in sorted(worst.items(), key=lambda x: -x[1]) if v > 3}}
json.dump(rep, open(argv[1], 'w'), indent=1)
print('INSPECT', json.dumps({k: v for k, v in rep.items() if k in ('mesh_bbox', 'mirror_dist')}))
