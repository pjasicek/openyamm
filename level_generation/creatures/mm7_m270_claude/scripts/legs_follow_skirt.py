"""The m270 legs (garment 4) under the chain skirt (garment 3) take the skirt's weights: the hem reaches the floor all
round (z 0.026-0.038), so only the shoes show, but the skinned skirt (85 % leg at the hem, less above) lags the legs
and the striding thighs poked through it (11 cm in the walk, 21 cm in the run, 24 cm in the death). Every leg vertex
above the shoes now takes the inverse-distance mean of the final weights (skirt bones included) of its 4 nearest
skirt vertices, so it moves with the cloth around it; the shoes keep their own weights, blended over z 0.05-0.15.
Runs after skirt_bones.py; on the textured master (rig_v6, weights not re-synced) once, guarded by an object property.
Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
from mathutils.kdtree import KDTree
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
if body.get('legs_follow_skirt'):
    print('LEGSKIRT already applied')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out)); sys.exit(0)
Z0, Z1 = 0.05, 0.15
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices]); nv = len(co)
gv = np.zeros(nv, np.int32); me.attributes['garment'].data.foreach_get('value', gv)
names = [g.name for g in body.vertex_groups]
Wt = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        Wt[v.index, e.group] = e.weight
sk = np.where(gv == 3)[0]
kd = KDTree(len(sk))
for k, i in enumerate(sk):
    kd.insert(co[i], k)
kd.balance()
legs = np.where((gv == 4) & (co[:, 2] > Z0))[0]
for i in legs:
    nb = kd.find_n(co[i], 4)
    w = np.array([1.0 / max(h[2], 1e-3) for h in nb]); w /= w.sum()
    ws = sum(wk * Wt[sk[h[1]]] for wk, h in zip(w, nb))
    t = np.clip((co[i, 2] - Z0) / (Z1 - Z0), 0, 1); t = t * t * (3 - 2 * t)
    Wt[i] = (1 - t) * Wt[i] + t * ws
for i in legs:
    r = np.argsort(Wt[i])[::-1]
    Wt[i, r[4:]] = 0
    Wt[i] /= max(Wt[i].sum(), 1e-9)
for j, n in enumerate(names):
    g = body.vertex_groups[n]
    g.remove([int(i) for i in legs])
    for i in legs[Wt[legs, j] > 1e-4]:
        g.add([int(i)], float(Wt[i, j]), 'REPLACE')
body['legs_follow_skirt'] = True
print('LEGSKIRT leg vertices on the skirt weights', len(legs), 'of', int((gv == 4).sum()))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
