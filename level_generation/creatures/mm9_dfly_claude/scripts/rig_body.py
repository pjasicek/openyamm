"""Weight the fitted body 'Dfly' to the MM9 skeleton.

Args: <fit blend> <out blend> <report json>

- Labels: each body vertex takes the bone of the nearest MM9 body vertex (the MM9 skin is rigid, one bone per vertex);
  eyes (piece 1) are rigid on Xheadpiv; teeth and jaw pieces (piece 2) take the final weights of their nearest body
  vertex, rigidly per piece.
- Smooth along the chains: weights diffuse over the mesh (DIFFUSE iterations), with the jaw/snout labels (Xjawpiv,
  Xhead) held fixed so the mouth keeps a clean hinge; a final short pass softens the hinge.
- At most four influences, normalised. The MM9 meshes and the two dummy pieces are deleted.
"""
import bpy, bmesh, sys, json
from mathutils.kdtree import KDTree
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
FIT, OUT, REP = argv
DIFFUSE = 14
HINGE = 3
FIXED = {'Xjawpiv', 'Xhead'}

bpy.ops.wm.open_mainfile(filepath=FIT)
arm = bpy.data.objects['MM9_Rig']
mm9 = bpy.data.objects['d_body.mesh']
body = bpy.data.objects['Dfly']

# MM9 vertex labels (bind pose)
mpos, mlab = [], []
for v in mm9.data.vertices:
    g = max(v.groups, key=lambda g: g.weight)
    mpos.append(mm9.matrix_world @ v.co)
    mlab.append(mm9.vertex_groups[g.group].name)
kd = KDTree(len(mpos))
for i, p in enumerate(mpos):
    kd.insert(p, i)
kd.balance()

bones = [b.name for b in arm.data.bones]
bidx = {b: i for i, b in enumerate(bones)}
me = body.data
n = len(me.vertices)
piece = np.array([me.attributes['piece'].data[i].value for i in range(n)])
W = np.zeros((n, len(bones)))
for i, v in enumerate(me.vertices):
    if piece[i] == 1:
        W[i, bidx['Xheadpiv']] = 1
    else:
        W[i, bidx[mlab[kd.find(v.co)[1]]]] = 1

# adjacency
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices
    nbr[a].append(b)
    nbr[b].append(a)
fixed = np.array([piece[i] == 0 and any(W[i, bidx[b]] > 0 for b in FIXED) for i in range(n)])
body_v = piece == 0


def diffuse(W, iters, hold):
    for _ in range(iters):
        avg = np.array([W[nb].mean(0) if nb else W[i] for i, nb in enumerate(nbr)])
        new = 0.5 * W + 0.5 * avg
        keep = hold | ~body_v
        new[keep] = W[keep]
        W = new
    return W


W = diffuse(W, DIFFUSE, fixed)
W = diffuse(W, HINGE, np.zeros(n, bool))

# pieces (teeth, jaw parts): rigid with their nearest body vertex
bm = bmesh.new()
bm.from_mesh(me)
bm.verts.ensure_lookup_table()
kd_body = KDTree(int(body_v.sum()))
body_ids = np.nonzero(body_v)[0]
for k, i in enumerate(body_ids):
    kd_body.insert(me.vertices[i].co, k)
kd_body.balance()
seen = set()
pieces = 0
for v in bm.verts:
    if piece[v.index] != 2 or v.index in seen:
        continue
    comp, stack = [], [v]
    seen.add(v.index)
    while stack:
        x = stack.pop()
        comp.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index)
                stack.append(y)
    cen = sum((me.vertices[i].co for i in comp), me.vertices[comp[0]].co * 0) / len(comp)
    best = min(comp, key=lambda i: kd_body.find(me.vertices[i].co)[2])
    src = body_ids[kd_body.find(me.vertices[best].co)[1]]
    W[comp] = W[src]
    pieces += 1

# four influences
order = np.argsort(-W, axis=1)
for i in range(n):
    keep = order[i, :4]
    row = np.zeros(len(bones))
    row[keep] = W[i, keep]
    row[row < 0.02] = 0
    W[i] = row / row.sum()

for b in bones:
    body.vertex_groups.new(name=b)
for i in range(n):
    for j in np.nonzero(W[i])[0]:
        body.vertex_groups[bones[j]].add([i], float(W[i, j]), 'REPLACE')
# drop empty groups
for g in list(body.vertex_groups):
    if not np.any(W[:, bidx[g.name]] > 0):
        body.vertex_groups.remove(g)
body.parent = arm
body.matrix_parent_inverse = arm.matrix_world.inverted()
mod = body.modifiers.new('Armature', 'ARMATURE')
mod.object = arm

# debug colours: dominant bone
col = me.color_attributes.new('bone', 'FLOAT_COLOR', 'POINT')
rng = np.random.default_rng(7)
palette = rng.uniform(0.15, 1.0, (len(bones), 3))
for i in range(n):
    c = (W[i, :, None] * palette).sum(0)
    col.data[i].color = (*c, 1.0)

for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name != 'Dfly':
        bpy.data.objects.remove(o)
usage = {bones[j]: int((W[:, j] > 0.5).sum()) for j in range(len(bones)) if (W[:, j] > 0).any()}
rep = {'verts': n, 'pieces_rigid': pieces, 'dominant_counts': usage,
       'max_influences': int((W > 0).sum(1).max()), 'unweighted': int((W.sum(1) == 0).sum())}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('RIG ' + json.dumps(rep))
