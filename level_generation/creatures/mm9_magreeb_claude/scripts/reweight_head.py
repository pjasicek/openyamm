"""Magreeb: re-weight the head of the UV'd body without touching its geometry or UVs (the retexture stays valid;
from mm9_lobber_claude/scripts/reweight_head.py).

Args: <uv blend> <mm9 source blend> <out blend> <report json>

MM9's lower jaw (Bone01 -> Bone02) hangs below the skull in the bind pose, where our head has its throat, so
nearest-vertex labels gave most of our head to the jaw and it tore when Hattack1/2 swing the jaw open. Head vertices
(dominant weight on a head bone) in front of the jaw hinge (Bone01 head) are split by the plane through the hinge and
the mouth centre (centroid of the small mouth/eye pieces) containing the lateral axis: above -> skull and horn bones,
below -> jaw bones; behind the hinge -> skull, horn and neck bones only. Each takes the bone of the nearest MM9 vertex
of its group, then the head weights diffuse (other vertices held), at most four influences, normalised.
"""
import bpy, sys, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
argv = sys.argv[sys.argv.index('--') + 1:]
UV, SRC, OUT, REP = argv
UPPER = ['Bone09', 'Bone36', 'Bone04', 'Bone05', 'Bone06', 'Bone07']
LOWER = ['Bone01', 'Bone02']
NECK = ['Bone35']
DIFFUSE = 6

bpy.ops.wm.open_mainfile(filepath=SRC)
dg = bpy.context.evaluated_depsgraph_get()
mpos, mlab = [], []
for o in bpy.data.objects:
    if o.type == 'MESH':
        for v in o.data.vertices:
            g = max(v.groups, key=lambda g: g.weight)
            mpos.append((o.matrix_world @ v.co).copy()); mlab.append(o.vertex_groups[g.group].name)
hinge = Vector(bpy.data.objects['MM9_Rig'].data.bones['Bone01'].head_local)
bpy.ops.wm.open_mainfile(filepath=UV)
ob = bpy.data.objects['Body']; me = ob.data
piece = np.array([d.value for d in me.attributes['piece'].data])
mouth = sum((me.vertices[i].co for i in np.nonzero(piece == 2)[0]), Vector()) / int((piece == 2).sum())
mouth.x = 0.0
ax = Vector((1, 0, 0))
nrm = ax.cross(mouth - hinge).normalized()
if nrm.z < 0:
    nrm = -nrm


def tree(names):
    ids = [i for i, l in enumerate(mlab) if l in names]
    k = KDTree(len(ids))
    for j, i in enumerate(ids):
        k.insert(mpos[i], j)
    k.balance()
    return k, ids


tu, tl, ta = tree(UPPER), tree(LOWER), tree(UPPER + NECK)
names = [g.name for g in ob.vertex_groups]
for b in UPPER + LOWER + NECK:
    if b not in names:
        ob.vertex_groups.new(name=b); names.append(b)
gi = {n: i for i, n in enumerate(names)}
n = len(me.vertices)
W = np.zeros((n, len(names)))
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
headset = [gi[b] for b in UPPER + LOWER]
head = (piece == 0) & (W[:, headset].sum(1) > 0.5)
moved = {'upper': 0, 'lower': 0, 'behind': 0}
for i in np.nonzero(head)[0]:
    p = me.vertices[i].co
    if p.y < hinge.y:
        side = 'upper' if (p - hinge).dot(nrm) > 0 else 'lower'
        k, ids = tu if side == 'upper' else tl
    else:
        side = 'behind'
        k, ids = ta
    row = np.zeros(len(names)); row[gi[mlab[ids[k.find(p)[1]]]]] = 1
    W[i] = row
    moved[side] += 1
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices
    nbr[a].append(b); nbr[b].append(a)
for _ in range(DIFFUSE):
    avg = np.array([W[nb].mean(0) if nb else W[i] for i, nb in enumerate(nbr)])
    W = np.where(head[:, None], 0.5 * W + 0.5 * avg, W)
# mouth pieces keep following their nearest head vertex rigidly
body_ids = np.nonzero(piece == 0)[0]
kb = KDTree(len(body_ids))
for j, i in enumerate(body_ids):
    kb.insert(me.vertices[i].co, j)
kb.balance()
import bmesh
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
seen = set()
for v in bm.verts:
    if piece[v.index] != 2 or v.index in seen:
        continue
    comp, st = [], [v]; seen.add(v.index)
    while st:
        x = st.pop(); comp.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); st.append(y)
    best = min(comp, key=lambda i: kb.find(me.vertices[i].co)[2])
    W[comp] = W[body_ids[kb.find(me.vertices[best].co)[1]]]
order = np.argsort(-W, axis=1)
for i in range(n):
    row = np.zeros(len(names)); keep = order[i, :4]; row[keep] = W[i, keep]
    row[row < 0.02] = 0; W[i] = row / row.sum()
for g in ob.vertex_groups:
    g.remove(list(range(n)))
for i in range(n):
    for j in np.nonzero(W[i])[0]:
        ob.vertex_groups[names[j]].add([i], float(W[i, j]), 'REPLACE')
rep = {'hinge': list(hinge), 'mouth_centre': list(mouth), 'plane_normal': list(nrm), 'head_vertices': moved}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('REWEIGHT ' + json.dumps(rep))
