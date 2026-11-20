"""Where a G6 forearm/hand 'inside' hit lands: per side at one action frame, the deepest forearm samples, the face
they are behind (rest centroid) and that face's dominant weights. Args: -- <blend> <action> <frame>"""
import bpy, sys, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); act, fr = a[1], float(a[2])
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
names = [g.name for g in body.vertex_groups]; nv = len(me.vertices)
W = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups: W[v.index, e.group] = e.weight
gar = np.zeros(nv, np.int32); me.attributes['garment'].data.foreach_get('value', gar)
rest = np.array([tuple(v.co) for v in me.vertices])
part = lambda s, keys: W[:, [i for i, n in enumerate(names) if n.startswith(f'B_{s}_') and any(k in n for k in keys)]].sum(1)
A = bpy.data.actions[act]; rig.animation_data.action = A; rig.animation_data.action_slot = A.slots[0]
bpy.context.scene.frame_set(int(fr), subframe=fr - int(fr))
ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
P = [body.matrix_world @ v.co for v in m.vertices]; ev.to_mesh_clear()
faces = [tuple(p.vertices) for p in me.polygons]
for s in 'LR':
    keep = part(s, ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger')) <= 0.2
    fl = [f for f in faces if all(keep[i] for i in f) and gar[f[0]] == 0]
    tree = BVHTree.FromPolygons(P, fl)
    fa = np.where(part(s, ('Forearm',)) > 0.5)[0]; hits = []
    for i in fa:
        loc, nrm, idx, d = tree.find_nearest(P[i], 0.06)
        if loc is not None and (P[i] - loc).dot(nrm) < -0.7 * d:
            hits.append((d, i, idx))
    hits.sort(reverse=True)
    print('PROBE', s, 'inside samples', len(hits), 'of', len(fa))
    for d, i, idx in hits[:4]:
        f = fl[idx]; c = rest[list(f)].mean(0); w = W[list(f)].mean(0); top = np.argsort(-w)[:3]
        print('PROBE', s, f'depth {d*100:.1f} cm sample rest {np.round(rest[i],3).tolist()} face rest {np.round(c,3).tolist()}', [(names[t], round(float(w[t]), 2)) for t in top])
