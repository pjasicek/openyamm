"""Weight refinement of the rigged pig (after rig_body.py; same mesh).

Args: <rig blend> <out blend> <report json>

1. Ears: MM9's ears are large low-poly flaps; ours are thin Meshy flaps ~5 cm further forward, so nearest-MM9-vertex
   labels gave them to the head. Ear vertices are found as thin head surface (BVH ray thickness along the inward
   normal below EAR_THICK) away from the mid-plane, one connected flap per side. Rotating our flap about MM9's ear
   pivot 5 cm away swung it off the head and shredded it, so each flap gets a helper bone EarRoot / EarRoot01 at
   its own root (child of Xhead, same rest orientation as Xearpiv: build_export.py copies Xearpiv's rotation
   keys onto it, so the ear turns exactly as MM9's, about our hinge). From the root (the flap's border with the
   head), geodesic distance ramps the weights head -> EarRoot over EAR_PIV. MM9's Xear (held 44 deg off its bind in
   every clip, even static_model) crumpled our flap and is not used (EAR_SHARE 0).
2. Mirror: MM9's pig is mirror-symmetric (joints within 3 mm), so every vertex on the left (+X) copies the weights of
   its mirror vertex on the right with the bone renamed (X... <-> X...01).
3. At most four influences, normalised.
"""
import bpy, bmesh, sys, json, math, os, heapq
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv
EAR_THICK = float(os.environ.get('EAR_THICK', '0.012'))
EAR_PIV = (0.0, 0.010)
EAR_EAR = (0.006, 0.022)
# MM9 holds Xear 44 deg off its bind in every clip (even static_model); on our flap, which sits ~5 cm in front of
# MM9's ear, that twist crumpled the ear, so the flap follows Xearpiv (the flap's swing) and only EAR_SHARE of Xear
EAR_SHARE = float(os.environ.get('EAR_SHARE', '0.0'))
bpy.ops.wm.open_mainfile(filepath=IN)
arm = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
me = body.data
bones = [b.name for b in arm.data.bones]
bidx = {b: i for i, b in enumerate(bones)}
J = {b.name: np.array(arm.matrix_world @ b.head_local) for b in arm.data.bones}
n = len(me.vertices)
W = np.zeros((n, len(bones)))
gname = {g.index: g.name for g in body.vertex_groups}
for v in me.vertices:
    for g in v.groups:
        W[v.index, bidx[gname[g.group]]] = g.weight
P = np.array([tuple(v.co) for v in me.vertices])
N = np.array([tuple(v.normal) for v in me.vertices])
piece = np.array([d.value for d in me.attributes['piece'].data])
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
bvh = BVHTree.FromBMesh(bm)
nbr = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
elen = {}
rep = {}
headw = W[:, [bidx[b] for b in ('Xhead', 'Xnose', 'Xearpiv', 'Xear', 'Xearpiv01', 'Xear01')]].sum(1)
thick = np.full(n, 9.0)
for i in np.nonzero((headw > 0.5) & (piece == 0))[0]:
    o = Vector(P[i]) - Vector(N[i]) * 1e-4
    hit = bvh.ray_cast(o, -Vector(N[i]), 0.1)
    if hit[0] is not None:
        thick[i] = hit[3]
for side, (piv, ear) in {-1: ('Xearpiv', 'Xear'), 1: ('Xearpiv01', 'Xear01')}.items():
    cand = (headw > 0.5) & (piece == 0) & (thick < EAR_THICK) & (np.sign(P[:, 0]) == side) & (np.abs(P[:, 0]) > 0.03)
    # connected flap nearest the MM9 ear joint
    seen = np.zeros(n, bool); comps = []
    for s0 in np.nonzero(cand)[0]:
        if seen[s0]:
            continue
        st, c = [s0], []
        seen[s0] = True
        while st:
            x = st.pop(); c.append(x)
            for y in nbr[x]:
                if cand[y] and not seen[y]:
                    seen[y] = True; st.append(y)
        comps.append(c)
    comps.sort(key=lambda c: -len(c))
    flap = max(comps[:3], key=lambda c: len(c) / (1 + 20 * np.linalg.norm(P[c].mean(0) - J[ear])))
    flap = np.array(flap)
    inflap = np.zeros(n, bool); inflap[flap] = True
    # close small gaps: grow by one ring where both neighbours are in the flap
    root = [i for i in flap if any(not inflap[y] for y in nbr[i])]
    tip = flap[np.argmax(np.linalg.norm(P[flap] - J[piv], axis=1))]
    # the root is the border toward the head (nearest the pivot), not the flap's free edge
    rootd = np.linalg.norm(P[root] - J[piv], axis=1)
    root = [r for r, d in zip(root, rootd) if d < np.percentile(rootd, 35)]
    dist = {i: 0.0 for i in root}
    pq = [(0.0, i) for i in root]
    while pq:
        d, i = heapq.heappop(pq)
        if d > dist[i]:
            continue
        for y in nbr[i]:
            if not inflap[y]:
                continue
            nd = d + float(np.linalg.norm(P[y] - P[i]))
            if nd < dist.get(y, 9):
                dist[y] = nd; heapq.heappush(pq, (nd, y))
    helper = 'EarRoot' if side < 0 else 'EarRoot01'
    rootc = P[root].mean(0)
    bpy.context.view_layer.objects.active = arm
    for o in bpy.data.objects:
        o.select_set(o == arm)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.data.edit_bones
    src = eb[piv]
    hb = eb.get(helper) or eb.new(helper)
    mw_inv = arm.matrix_world.inverted()
    hb.head = mw_inv @ Vector(rootc)
    hb.tail = hb.head + (src.tail - src.head)
    hb.roll = src.roll
    hb.parent = eb['Xhead']
    bpy.ops.object.mode_set(mode='OBJECT')
    if helper not in bidx:
        bones.append(helper); bidx[helper] = len(bones) - 1
        W = np.hstack([W, np.zeros((n, 1))])
    piv_w = helper
    for i in flap:
        d = dist.get(int(i), 0.0)
        a = np.clip((d - EAR_PIV[0]) / (EAR_PIV[1] - EAR_PIV[0]), 0, 1); a = a * a * (3 - 2 * a)
        b = np.clip((d - EAR_EAR[0]) / (EAR_EAR[1] - EAR_EAR[0]), 0, 1); b = b * b * (3 - 2 * b)
        new = np.zeros(len(bones)); new[bidx[piv_w]] = 1 - EAR_SHARE * b; new[bidx[ear]] = EAR_SHARE * b
        W[i] = (1 - a) * W[i] + a * new
    rep[ear] = {'helper': helper, 'root_centroid': np.round(rootc, 3).tolist(), 'flap_verts': int(len(flap)), 'root_verts': len(root), 'max_geodesic': float(max(dist.values())),
                'centroid': np.round(P[flap].mean(0), 3).tolist(), 'mm9_joint': np.round(J[ear], 3).tolist()}
# mirror (+X copies -X with renamed bones)
mirror = {}
for b in bones:
    m = b[:-2] if b.endswith('01') else b + '01'   # (EarRoot <-> EarRoot01 too)
    mirror[bidx[b]] = bidx[m] if m in bidx else bidx[b]
right = np.nonzero((P[:, 0] < -1e-5))[0]
kd = KDTree(len(right))
for j, i in enumerate(right):
    kd.insert((-P[i, 0], P[i, 1], P[i, 2]), j)
kd.balance()
mirrored, far = 0, []
for i in np.nonzero(P[:, 0] > 1e-5)[0]:
    co, j, d = kd.find(tuple(P[i]))
    if d > 3e-3:
        far.append(float(d)); continue
    m = right[j]
    row = np.zeros(len(bones))
    for k in np.nonzero(W[m])[0]:
        row[mirror[k]] += W[m, k]
    W[i] = row
    mirrored += 1
rep['mirrored'] = mirrored
rep['mirror_skipped'] = len(far)
order = np.argsort(-W, axis=1)
for i in range(n):
    keep = order[i, :4]
    row = np.zeros(len(bones)); row[keep] = W[i, keep]
    row[row < 0.02] = 0
    W[i] = row / row.sum()
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
for b in bones:
    body.vertex_groups.new(name=b)
for i in range(n):
    for j in np.nonzero(W[i])[0]:
        body.vertex_groups[bones[j]].add([i], float(W[i, j]), 'REPLACE')
for g in list(body.vertex_groups):
    if not np.any(W[:, bidx[g.name]] > 0):
        body.vertex_groups.remove(g)
rep['dominant_counts'] = {bones[j]: int((W[:, j] > 0.5).sum()) for j in range(len(bones)) if (W[:, j] > 0).any()}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('REFINE ' + json.dumps(rep))
