"""Refine the torso weights of the rigged sheep 'Body' (weight_refine.py, from the wolf; 2026-10-30, the flank and elbow
folds in Running). Positions, UVs, topology and attributes are unchanged: no untangle, the rest mesh has no folds outside
the mouth cavity, and the cavity must stay as built. The mirrored half carries the +X chain ids from Blender Symmetrize,
so they are set by side first (no mixing between limbs depends on them).

Args: <in blend (uv_v3b)> <out blend (uv_v3c)> <report json> [positions npz from armpit_rebuild.py: its P replaces
the untangle step]
"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import weight_refine as R

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv[:3]
POS = argv[3] if len(argv) > 3 else None
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
arm = bpy.data.objects['MM9_Rig']
me = body.data
mw = body.matrix_world
co = np.array([tuple(mw @ v.co) for v in me.vertices])
me.calc_loop_triangles()
tris = np.array([tuple(t.vertices) for t in me.loop_triangles])
bones = [b.name for b in arm.data.bones]
parents = [b.parent.name if b.parent else '' for b in arm.data.bones]
heads = np.array([tuple(arm.matrix_world @ b.head_local) for b in arm.data.bones])
bidx = {b: i for i, b in enumerate(bones)}
gname = {g.index: g.name for g in body.vertex_groups}
W = np.zeros((len(co), len(bones)))
for v in me.vertices:
    for g in v.groups:
        W[v.index, bidx[gname[g.group]]] = g.weight
piece = np.array([d.value for d in me.attributes['piece'].data])
chain = np.array([d.value for d in me.attributes['chain'].data])

if POS:
    P = np.load(POS)['P']
    assert P.shape == co.shape, 'positions npz does not match the mesh'
    urep = {'positions': os.path.basename(POS)}
else:
    P, urep = co, {'skipped': True}
chain = np.where(np.isin(chain, (0, 1)), np.where(co[:, 0] > 0, 0, 1), chain)
chain = np.where(np.isin(chain, (2, 3)), np.where(co[:, 0] > 0, 2, 3), chain)
W2, wrep = R.refine(P, tris, W, bones, heads, parents, chain, piece)
# mirror the result exactly: -X vertices take the +X weights with L/R bones swapped
from mathutils.kdtree import KDTree
from mathutils import Vector as _V
pos = np.nonzero(co[:, 0] >= -1e-5)[0]
kd = KDTree(len(pos))
for j, i in enumerate(pos):
    kd.insert(_V(tuple(co[i])), j)
kd.balance()
found = [kd.find(_V((-c[0], c[1], c[2]))) for c in co]
near = np.array([f[1] for f in found]); dist = np.array([f[2] for f in found])
swap = np.arange(len(bones))
for b, i in bidx.items():
    if b.endswith('01') and b[:-2] in bidx:
        swap[i], swap[bidx[b[:-2]]] = bidx[b[:-2]], i
neg = co[:, 0] < -1e-5
W2[neg] = W2[pos[near[neg]]][:, swap]
wrep['mirror_max_dist'] = float(dist[neg].max())

inv = mw.inverted()
from mathutils import Vector
for i, v in enumerate(me.vertices):
    v.co = inv @ Vector(tuple(P[i]))
me.update()
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
for j, b in enumerate(bones):
    if (W2[:, j] > 0).any():
        g = body.vertex_groups.new(name=b)
        for i in np.nonzero(W2[:, j])[0]:
            g.add([int(i)], float(W2[i, j]), 'REPLACE')
rep = {'untangle': urep, 'weights': wrep, 'unweighted': int((W2.sum(1) == 0).sum())}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('REFINE ' + json.dumps(rep))
