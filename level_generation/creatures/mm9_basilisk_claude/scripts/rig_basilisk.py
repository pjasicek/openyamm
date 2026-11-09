"""Weight the fitted basilisk 'Body' to the MM9 skeleton (from ../mm9_lobber_claude/scripts/rig_body.py).

Args: <fit blend> <out blend> <report json>

- Labels: each vertex takes the bone of the nearest MM9 vertex (the MM9 skin is rigid, one bone per vertex). A leg
  vertex (fit attribute 'chain' 0-5) only considers its own leg's bones (chain + toe bones), a tail vertex (6) the
  tail bones, a core vertex only bones outside the legs and tail (chain roots allowed).
- Toes by connectivity: on every foot the Meshy toe tips (geodesic extremities from the ankle) are matched to the five
  MM9 toes (thumb + four fingers) by direction around the foot (exact assignment); each foot vertex within a toe's
  length of its nearest toe tip takes that toe's bones (the distal bone near the tip, blended to the proximal one),
  the rest of the foot the wrist bone. These labels are held during the first diffusion pass.
- Smooth along the mesh: weights diffuse (DIFFUSE iterations) with the jaw hinge and the toe labels held, then a
  short free pass. Small pieces (teeth, eyes, claws) are rigid with their nearest body vertex.
- At most four influences, normalised. The MM9 meshes are deleted; a 'bone' colour attribute shows the weights.
"""
import bpy, bmesh, sys, json, math, heapq, itertools
from mathutils import Vector
from mathutils.kdtree import KDTree
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
FIT, OUT, REP = argv
DIFFUSE = 10
HINGE = 2
LEGS = [['Xfrontpivot', 'Xfrontelbow', 'Xfrontarm'], ['Xfrontpivot01', 'Xfrontelbow01', 'Xfrontarm01'],
        ['Xmidbase', 'Xmidelbow', 'Xmidarm'], ['Xmidbase01', 'Xmidelbow01', 'Xmidarm01'],
        ['Xrearpivot', 'Xrearelbow', 'Xreararm', 'Xrearwrist'],
        ['Xrearpivot01', 'Xrearelbow01', 'Xreararm01', 'Xrearwrist01']]
TAIL = ['Xtailpiv', 'XtailA', 'XtailB', 'XtailC']
FIXED = {'Xjawpiv', 'Xjaw', 'Xhead', 'Xeye'}

bpy.ops.wm.open_mainfile(filepath=FIT)
arm = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
bones = [b.name for b in arm.data.bones]
bidx = {b: i for i, b in enumerate(bones)}
Jh = {b.name: Vector(b.head_local) for b in arm.data.bones}
Jt = {b.name: Vector(b.tail_local) for b in arm.data.bones}


def descendants(name):
    out = []
    st = list(arm.data.bones[name].children)
    while st:
        b = st.pop(); out.append(b.name); st += list(b.children)
    return out


CHAINS = [c + descendants(c[-1]) for c in LEGS] + [TAIL + descendants(TAIL[-1])]
mpos, mlab = [], []
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name == 'Body':
        continue
    for v in o.data.vertices:
        g = max(v.groups, key=lambda g: g.weight)
        mpos.append(o.matrix_world @ v.co)
        mlab.append(o.vertex_groups[g.group].name)
mlab = np.array(mlab)
chain_bones = set(b for c in CHAINS for b in c[1:])


def tree(ids):
    k = KDTree(len(ids))
    for j, i in enumerate(ids):
        k.insert(mpos[i], j)
    k.balance()
    return k, ids


trees = [tree([i for i in range(len(mpos)) if mlab[i] in c]) for c in CHAINS]
core_tree = tree([i for i in range(len(mpos)) if mlab[i] not in chain_bones])
me = body.data
n = len(me.vertices)
piece = np.array([d.value for d in me.attributes['piece'].data])
chain = np.array([d.value for d in me.attributes['chain'].data])
W = np.zeros((n, len(bones)))
for i, v in enumerate(me.vertices):
    k, ids = trees[chain[i]] if 0 <= chain[i] < len(CHAINS) else core_tree
    W[i, bidx[mlab[ids[k.find(v.co)[1]]]]] = 1

nbr = [[] for _ in range(n)]
elen = {}
for e in me.edges:
    a, b = e.vertices
    nbr[a].append(b); nbr[b].append(a)
    elen[(a, b)] = elen[(b, a)] = (me.vertices[a].co - me.vertices[b].co).length
body_v = piece == 0


def geodesic(src, allowed, limit=1e9):
    dist = {src: 0.0}
    pq = [(0.0, src)]
    while pq:
        d, i = heapq.heappop(pq)
        if d > dist[i] or d > limit:
            continue
        for j in nbr[i]:
            if j not in allowed:
                continue
            nd = d + elen[(i, j)]
            if nd < dist.get(j, 1e9):
                dist[j] = nd; heapq.heappush(pq, (nd, j))
    return dist


# ---------------- toes by connectivity
toe_hold = np.zeros(n, bool)
toe_report = {}
for li, c in enumerate(LEGS):
    wrist = c[-1]
    fingers = [b.name for b in arm.data.bones[wrist].children]          # proximal toe bones
    toes = []
    for f in fingers:
        kids = [b.name for b in arm.data.bones[f].children]
        dist = kids[0] if kids else f
        pts = np.array([tuple(mpos[i]) for i in range(len(mpos)) if mlab[i] == dist])
        tipm = Vector(tuple(pts[np.argmax(np.linalg.norm(pts - np.array(tuple(Jh[f])), axis=1))])) if len(pts) else Jt[dist]
        toes.append((f, dist, tipm, (tipm - Jh[f]).length))
    foot = set(i for i in range(n) if chain[i] == li and body_v[i] and me.vertices[i].co.z < 0.13)
    if not foot:
        continue
    fc = sum((me.vertices[i].co for i in foot), Vector()) / len(foot)
    ankle = max(foot, key=lambda i: me.vertices[i].co.z - 0.5 * Vector((me.vertices[i].co - fc).xy).length)
    g = geodesic(ankle, foot)
    ext = []
    for i, d in sorted(g.items(), key=lambda x: -x[1]):
        if d < 0.06:
            break
        if all(g.get(j, 0) <= d for j in nbr[i]) and all((me.vertices[i].co - me.vertices[e].co).length > 0.05
                                                         for e in ext):
            ext.append(i)
            if len(ext) == 7:
                break
    wc = Jh[wrist]
    az = lambda p, c0: math.atan2(p.y - c0.y, p.x - c0.x)
    best = (1e9, None)
    nt = min(len(ext), len(toes))
    for rows in itertools.permutations(range(len(ext)), nt):
        cost = 0.0
        for j, r in enumerate(rows):
            da = abs((az(me.vertices[ext[r]].co, fc) - az(toes[j][2], wc) + math.pi) % (2 * math.pi) - math.pi)
            cost += da
        if cost < best[0]:
            best = (cost, rows)
    tips = {}
    for j, r in enumerate(best[1]):
        tips[j] = ext[r]
    gts = {j: geodesic(t, foot, 0.4) for j, t in tips.items()}
    for i in foot:
        cand = [(gts[j].get(i, 1e9), j) for j in tips]
        d, j = min(cand)
        f, dist_b, _, L = toes[j]
        L = max(L, 0.06)
        W[i] = 0
        if d < L:
            u = d / L                      # 0 at the tip .. 1 at the toe base
            wd = 1.0 - min(1.0, max(0.0, (u - 0.35) / 0.3))
            W[i, bidx[dist_b]] += wd
            W[i, bidx[f]] += 1 - wd
        else:
            W[i, bidx[wrist]] = 1
        toe_hold[i] = True
    toe_report[wrist] = {'foot_verts': len(foot), 'meshy_tips': len(ext), 'matched': len(tips),
                         'azimuth_cost_deg': round(math.degrees(best[0]), 1)}

fixed = np.array([body_v[i] and any(W[i, bidx[b]] > 0 for b in FIXED if b in bidx) for i in range(n)]) | toe_hold


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

body_ids = np.nonzero(body_v)[0]
kb = KDTree(len(body_ids))
for j, i in enumerate(body_ids):
    kb.insert(me.vertices[i].co, j)
kb.balance()
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
seen = set(); pieces = 0
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
    pieces += 1

order = np.argsort(-W, axis=1)
for i in range(n):
    keep = order[i, :4]
    row = np.zeros(len(bones)); row[keep] = W[i, keep]
    row[row < 0.02] = 0
    W[i] = row / row.sum()
for b in bones:
    body.vertex_groups.new(name=b)
for i in range(n):
    for j in np.nonzero(W[i])[0]:
        body.vertex_groups[bones[j]].add([i], float(W[i, j]), 'REPLACE')
for g in list(body.vertex_groups):
    if not np.any(W[:, bidx[g.name]] > 0):
        body.vertex_groups.remove(g)
body.parent = arm
body.matrix_parent_inverse = arm.matrix_world.inverted()
mod = body.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
col = me.color_attributes.new('bone', 'FLOAT_COLOR', 'POINT')
rng = np.random.default_rng(7)
pal = rng.uniform(0.15, 1.0, (len(bones), 3))
for i in range(n):
    col.data[i].color = (*(W[i, :, None] * pal).sum(0), 1.0)
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name != 'Body':
        bpy.data.objects.remove(o)
usage = {bones[j]: int((W[:, j] > 0.5).sum()) for j in range(len(bones)) if (W[:, j] > 0).any()}
rep = {'verts': n, 'pieces_rigid': pieces, 'toes': toe_report, 'dominant_counts': usage,
       'max_influences': int((W > 0).sum(1).max()), 'unweighted': int((W.sum(1) == 0).sum())}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('RIG ' + json.dumps({k: v for k, v in rep.items() if k != 'dominant_counts'}))
