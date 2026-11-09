"""Dagrell step 2: pose the MM9 skeleton onto the aligned Meshy skeleton, weight, and unpose to the MM9 bind pose.

Args: <align blend> <out blend> <report json>

The Meshy return is ~130 separate rigid pieces (limb bones, vertebrae, ribs, spikes, claws, teeth, skull, jaw) in
roughly the MM9 Stand pose (the pose of the HD masters; align_stand.py put it in that space). Bones do not bend, so
the Meshy geometry is not warped at all; instead the MM9 skeleton is posed to fit it:
1. Clean: the thin thread Meshy grew from the lower jaw to the left hand is cut (jaw-piece vertices with |x| > 0.12;
   its other part and any long, very thin piece are dropped).
2. Pose fit: starting from Stand frame 0, every MM9 bone below XCENTER (parents first) is rotated about its head
   by rigid ICP of its whole subtree's MM9 skin (-> nearest Meshy points, outliers > REJECT dropped, ITERS Kabsch
   steps, at most MAX_ROT degrees in total; a step is kept only if it lowers the subtree's mean distance).
   Children follow their parents and then refine themselves.
3. Weights (fitted pose): every Meshy vertex votes for the bone of its nearest MM9 skin vertex. A piece under 250
   vertices (250 after an earlier 120 stretched ribs and vertebrae across the spine joints), or with one bone >= 90 %
   of its votes, is rigid to its majority bone (spikes, ribs, claws, teeth,
   vertebrae). Other pieces (bones spanning a joint: Meshy's shin+foot, forearm+wrist) take per vertex the nearest
   bone segment (head -> child head) among the majority bone, its parent (and two more ancestors for pieces over
   0.3 m) and its children (one chain: never sibling fingers/toes), diffused along the piece. The skull (>= MAX_RIGID) keeps per-vertex skin labels, diffused. Four influences at most.
4. Unpose: every vertex goes to the MM9 rest pose by the inverse of its blended fitted-pose bone matrices; 'Body' is
   parented to MM9_Rig (armature modifier) in the rest pose and plays every MM9 clip.
Also saved: the fitted pose as action 'FitPose' (one frame), used to export the retexture upload in the Meshy pose.
Attributes: 'piece' (2 for pieces under 40 vertices: teeth and small spikes, kept out of decimation, else 0), 'chain' -1.
"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv
MAX_RIGID = 400
DIFFUSE = 6
REJECT = 0.15
ITERS = 12
MAX_ROT = 70.0   # degrees per bone: a fit needing more has locked onto the wrong piece

bpy.ops.wm.open_mainfile(filepath=IN)
sc = bpy.context.scene
arm = bpy.data.objects['MM9_Rig']
act = bpy.data.actions['Stand']
arm.animation_data_create(); arm.animation_data.action = act
try:
    arm.animation_data.action_slot = act.slots[0]
except Exception:
    pass
sc.frame_set(0); bpy.context.view_layer.update()
# freeze the Stand pose into the pose bones, then drop the action so edits stick
basis = {pb.name: pb.matrix_basis.copy() for pb in arm.pose.bones}
arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.rotation_mode = 'QUATERNION'
    pb.matrix_basis = basis[pb.name]
bpy.context.view_layer.update()
AW = arm.matrix_world.copy(); AWi = AW.inverted()

# MM9 skin vertices in armature rest space with their (rigid) bone
mv, ml = [], []
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name == 'Meshy':
        continue
    for v in o.data.vertices:
        g = max(v.groups, key=lambda g: g.weight)
        mv.append(AWi @ o.matrix_world @ v.co)
        ml.append(o.vertex_groups[g.group].name)
ml = np.array(ml)
by_bone = {b: [mv[i] for i in np.nonzero(ml == b)[0]] for b in set(ml)}


def deform(pb):
    return AW @ pb.matrix @ pb.bone.matrix_local.inverted() @ AWi


def posed_skin():
    out = []
    for i, b in enumerate(ml):
        out.append(deform(arm.pose.bones[b]) @ AW @ mv[i])
    return out


# ---------------- Meshy: components, clean the jaw thread
src = bpy.data.objects['Meshy']
bm = bmesh.new(); bm.from_mesh(src.data); bm.verts.ensure_lookup_table()


def components():
    comp = np.full(len(bm.verts), -1); comps = []
    for v in bm.verts:
        if comp[v.index] >= 0:
            continue
        st = [v]; comp[v.index] = len(comps); c = []
        while st:
            x = st.pop(); c.append(x.index)
            for e in x.link_edges:
                y = e.other_vert(x)
                if comp[y.index] < 0:
                    comp[y.index] = len(comps); st.append(y)
        comps.append(np.array(c))
    return comp, comps


comp, comps = components()
# the jaw piece: the component reaching furthest forward (-y) below the skull, i.e. holding the lower teeth line
skull_k = max(range(len(comps)), key=lambda k: len(comps[k]))
cand = [k for k in range(len(comps)) if k != skull_k and len(comps[k]) > 100]
jaw_k = min(cand, key=lambda k: min(bm.verts[i].co.y for i in comps[k]))
thread = [bm.verts[i] for i in comps[jaw_k] if abs(bm.verts[i].co.x) > 0.12]
report = {'jaw_piece_verts': int(len(comps[jaw_k])), 'thread_removed': len(thread)}
bmesh.ops.delete(bm, geom=thread, context='VERTS')
bm.verts.ensure_lookup_table()
comp, comps = components()
# drop leftover crumbs (< 8 verts) from the cut, and other thread artefacts: long (> 0.4 m), very thin pieces
def thread_like(c):
    if len(c) < 8:
        return True
    X = np.array([tuple(bm.verts[i].co) for i in c])
    sv = np.linalg.svd(X - X.mean(0), compute_uv=False) / np.sqrt(len(c))
    return float(np.linalg.norm(X.max(0) - X.min(0))) > 0.4 and sv[1] < 0.012


threads = [c for c in comps if len(c) >= 8 and thread_like(c)]
report['threads_removed'] = [int(len(c)) for c in threads]
crumbs = [bm.verts[i] for c in comps if thread_like(c) for i in c]
if crumbs:
    bmesh.ops.delete(bm, geom=crumbs, context='VERTS'); bm.verts.ensure_lookup_table()
    comp, comps = components()
P = [v.co.copy() for v in bm.verts]
n = len(P)
kP = KDTree(n)
for i, p in enumerate(P):
    kP.insert(p, i)
kP.balance()


# ---------------- pose fit, parents first
def depth(b):
    d = 0
    while b.parent:
        b = b.parent; d += 1
    return d


def subtree(bone):
    out = [bone.name]
    for c in bone.children:
        out += subtree(c)
    return out


fit_rep = {}
for pb in sorted(arm.pose.bones, key=lambda p: depth(p.bone)):
    if pb.parent is None or pb.parent.parent is None:
        continue  # the scene root and XCENTER stay where align_stand.py put them
    own = by_bone.get(pb.name, [])
    pts = [(b, p) for b in subtree(pb.bone) for p in by_bone.get(b, [])]  # each skin vertex with its own bone
    if len(own) < 8 and len(pts) < 8:
        continue
    def cost():
        X = [deform(arm.pose.bones[b]) @ AW @ p for b, p in pts]
        return float(np.mean([min(kP.find(x)[2], 0.3) for x in X]))

    tot = 0.0
    c0 = cost()
    start_cost = c0
    for it in range(ITERS):
        h = AW @ pb.head
        X = [deform(arm.pose.bones[b]) @ AW @ p for b, p in pts]
        pairs = []
        for x in X:
            q, j, d = kP.find(x)
            if d < REJECT:
                pairs.append((x - h, q - h))
        if len(pairs) < 6:
            break
        A = np.array([tuple(a) for a, _ in pairs]); B = np.array([tuple(b) for _, b in pairs])
        U, S_, Vt = np.linalg.svd(B.T @ A)
        Dg = np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))])
        R = U @ Dg @ Vt
        ang = math.degrees(math.acos(max(-1, min(1, (np.trace(R) - 1) / 2))))
        if tot + ang > MAX_ROT:
            break
        tot += ang
        Rm = Matrix(R.tolist()).to_4x4()
        Wm = Matrix.Translation(h) @ Rm @ Matrix.Translation(-h)
        keep = pb.matrix_basis.copy()
        pb.matrix = AWi @ Wm @ AW @ pb.matrix
        bpy.context.view_layer.update()
        c1 = cost()
        if c1 > c0:  # accept a step only when it brings the subtree closer to the Meshy pieces
            pb.matrix_basis = keep
            bpy.context.view_layer.update()
            tot -= ang
            break
        c0 = c1
        if ang < 0.05:
            break
    X = [deform(arm.pose.bones[b]) @ AW @ p for b, p in pts]
    fit_rep[pb.name] = {'rot_total_deg': round(tot, 1), 'cost_before': round(start_cost, 4), 'cost_after': round(c0, 4),
                        'mean_dist': round(float(np.mean([kP.find(x)[2] for x in X])), 4)}
report['pose_fit'] = fit_rep
fitted = {pb.name: pb.matrix_basis.copy() for pb in arm.pose.bones}
DEF = {pb.name: deform(pb) for pb in arm.pose.bones}

# ---------------- weights in the fitted pose
S = posed_skin()
kS = KDTree(len(S))
for i, p in enumerate(S):
    kS.insert(p, i)
kS.balance()
JAW = ('Xjawbase', 'Xjawpiv')
DIGITS = ('Xfin', 'Xfm', 'Xtoe')
# ---- cut the skull: Meshy fused the lower jaw to it. Head/jaw labels by the skin vote (majority-filtered over the
# mesh), faces labelled by their vertices, and the edges between head and jaw faces split, so the mandible is a
# separate rigid piece on Xjawpiv that opens about the MM9 hinge instead of stretching the mouth corners.
skull_set = set(int(i) for i in comps[max(range(len(comps)), key=lambda k: len(comps[k]))])
vl = {}
for i in skull_set:
    b_ = ml[kS.find(P[i])[1]]
    vl[i] = b_ in JAW
for _ in range(8):  # majority filter: a smoother lip line (4 passes left a ragged mandible edge)
    nv = {}
    for i in skull_set:
        v = bm.verts[i]
        ns = [e.other_vert(v).index for e in v.link_edges] + [i]
        nv[i] = sum(vl[j] for j in ns) * 2 > len(ns)
    vl = nv
face_jaw = {}
for f in bm.faces:
    if f.verts[0].index in skull_set:
        face_jaw[f] = sum(vl[v.index] for v in f.verts) * 2 > len(f.verts)
cut = [e for e in bm.edges if len(e.link_faces) == 2 and all(f in face_jaw for f in e.link_faces)
       and face_jaw[e.link_faces[0]] != face_jaw[e.link_faces[1]]]
report['skull_cut_edges'] = len(cut)
report['skull_jaw_faces'] = int(sum(face_jaw.values()))
bmesh.ops.split_edges(bm, edges=cut)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
vert_jaw = {}
for f, j in face_jaw.items():
    for v in f.verts:
        vert_jaw[v.index] = j
comp, comps = components()
P = [v.co.copy() for v in bm.verts]
n = len(P)
REMAP = {'Xnose': 'Xheadpiv'}  # the pose fit turned Xnose 57 deg on the snout; its votes go to the skull bone
kS_nojaw = KDTree(int(np.sum(~np.isin(ml, JAW))))
nojaw_ids = np.nonzero(~np.isin(ml, JAW))[0]
for j, i in enumerate(nojaw_ids):
    kS_nojaw.insert(S[i], j)
kS_nojaw.balance()
near = np.array([REMAP.get(ml[kS.find(p)[1]], ml[kS.find(p)[1]]) for p in P])
near_nojaw = np.array([REMAP.get(ml[nojaw_ids[kS_nojaw.find(p)[1]]], ml[nojaw_ids[kS_nojaw.find(p)[1]]]) for p in P])
hinge_y = (AW @ arm.pose.bones['Xjawpiv'].head).y
for c in comps:
    # jaw bones only bind pieces in front of the jaw hinge (a neck vertebra behind it voted for Xjawbase)
    if float(np.mean([P[i].y for i in c])) > hinge_y - 0.05:
        near[c] = near_nojaw[c]
near = np.where(near == 'Xjawbase', 'Xjawpiv', near)  # the jaw opens as one piece
for i, j in vert_jaw.items():
    near[i] = 'Xjawpiv' if j else 'Xheadpiv'
bones = [b.name for b in arm.data.bones]
bidx = {b: i for i, b in enumerate(bones)}
Wt = np.zeros((n, len(bones)))
nbr = [[] for _ in range(n)]
for e in bm.edges:
    a, b = e.verts[0].index, e.verts[1].index
    nbr[a].append(b); nbr[b].append(a)
# bone segments in the fitted pose: head -> its single child's head, else the posed tail
segs = {}
for pb in arm.pose.bones:
    if len(by_bone.get(pb.name, [])) < 8:
        continue
    kids = [c for c in pb.children]
    end = (AW @ kids[0].head) if len(kids) == 1 else (AW @ pb.tail)
    segs[pb.name] = (np.array(tuple(AW @ pb.head)), np.array(tuple(end)))
seg_names = list(segs)


def nearest_segment(p, names):
    best = (1e9, None)
    for name in names:
        a, b = segs[name]
        ab = b - a
        u = min(1.0, max(0.0, float((p - a) @ ab / max(ab @ ab, 1e-12))))
        d = float(np.linalg.norm(p - (a + u * ab)))
        if d < best[0]:
            best = (d, name)
    return best[1]


Pa = np.array([tuple(p) for p in P])
rigid = 0
split = 0
for c in comps:
    vals, cnt = np.unique(near[c], return_counts=True)
    frac = cnt / cnt.sum()
    # blend only along one chain: the majority bone, its parent and its children (never between sibling fingers or
    # toes, which would stretch a claw into a sheet when they move apart)
    major = vals[np.argmax(cnt)]
    pbm = arm.pose.bones[major]
    chain = {major} | {c_.name for c_ in pbm.children}
    if pbm.parent is not None:
        chain.add(pbm.parent.name)
    up = pbm.parent.parent if pbm.parent is not None else None
    long_piece = float(np.linalg.norm(Pa[c].max(0) - Pa[c].min(0))) > 0.3
    for _ in range(2 if long_piece else 0):  # Meshy's shin+foot piece votes for the dense MM9 toes; its shin needs Xleg
        if up is None or up.parent is None:
            break
        chain.add(up.name); up = up.parent
    cands = [b for b in chain if b in segs and b not in JAW]
    if long_piece and len(c) >= 250:
        # a long limb bone (Meshy forearm, shin+foot) sits where MM9's long fingers/toes are and outvotes the limb bone:
        # bind it to limb bones only (the claws are separate rigid pieces)
        limb = [b for b in cands if not b.startswith(DIGITS)]
        if limb:
            cands = limb
            major = max(limb, key=lambda b: (vals.tolist().index(b) if b in vals else -1, -depth(arm.data.bones[b])))
    if len(c) < 250 or frac.max() >= 0.9 or len(cands) < 2:
        bone = major if major in cands else vals[np.argmax(cnt)]
        # a claw/toe piece rides the digit's pivot (the knuckle at the wrist/foot): Meshy's claws are short and start
        # at the wrist, MM9's fingers are long, and their outer bones swing a claw off the hand
        pb_ = arm.pose.bones[bone]
        while bone.startswith(DIGITS) and 'piv' not in bone and pb_.parent is not None and pb_.parent.name.startswith(DIGITS):
            pb_ = pb_.parent; bone = pb_.name
        Wt[c, bidx[bone]] = 1.0
        rigid += 1
        continue
    # a bone piece spanning a joint (Meshy's shin+foot, forearm+wrist): per vertex the nearest bone segment among the
    # bones its skin vote supports, diffused along the piece
    split += 1
    lab = [nearest_segment(Pa[i], cands) for i in c]
    share = {b_: lab.count(b_) / len(lab) for b_ in set(lab)}
    kept = [b_ for b_ in cands if share.get(b_, 0) >= 0.2] or [max(share, key=share.get)]
    if len(kept) < len(set(lab)):  # a bone holding < 20 % of the piece only stretches it: relabel among the rest
        lab = [nearest_segment(Pa[i], kept) for i in c]
    for i, b_ in zip(c, lab):
        Wt[i, bidx[b_]] = 1.0
    for _ in range(DIFFUSE):
        avg = np.array([Wt[nbr[i]].mean(0) if nbr[i] else Wt[i] for i in c])
        Wt[c] = 0.5 * Wt[c] + 0.5 * avg
order = np.argsort(-Wt, axis=1)
for i in range(n):
    keep = order[i, :4]
    row = np.zeros(len(bones)); row[keep] = Wt[i, keep]; row[row < 0.02] = 0
    Wt[i] = row / row.sum()

# ---------------- unpose
Z = Matrix(((0.0,) * 4,) * 4)
for v in bm.verts:
    i = v.index
    M = Z.copy()
    for j in np.nonzero(Wt[i])[0]:
        M = M + DEF[bones[j]] * float(Wt[i, j])
    v.co = M.inverted() @ P[i]
pa = bm.verts.layers.int.new('piece'); ca = bm.verts.layers.int.new('chain')
comp_of = np.full(n, -1)
for k, c in enumerate(comps):
    comp_of[c] = k
for v in bm.verts:
    v[pa] = 2 if len(comps[comp_of[v.index]]) < 40 else 0  # small pieces (teeth, small spikes): not decimated
    v[ca] = -1
me = bpy.data.meshes.new('Body'); bm.to_mesh(me)
body = bpy.data.objects.new('Body', me); sc.collection.objects.link(body)
for p in me.polygons:
    p.use_smooth = True
for b in bones:
    body.vertex_groups.new(name=b)
for i in range(n):
    for j in np.nonzero(Wt[i])[0]:
        body.vertex_groups[bones[j]].add([i], float(Wt[i, j]), 'REPLACE')
for g in list(body.vertex_groups):
    if not np.any(Wt[:, bidx[g.name]] > 0):
        body.vertex_groups.remove(g)
# the fitted pose as a one-frame action (retexture upload in the Meshy pose)
fp = bpy.data.actions.new('FitPose'); fp.use_fake_user = True
arm.animation_data.action = fp
for pb in arm.pose.bones:
    pb.matrix_basis = fitted[pb.name]
    for f in (0, 1):
        pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)
        pb.keyframe_insert('scale', frame=f)
arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
body.parent = arm
body.matrix_parent_inverse = arm.matrix_world.inverted()
mod = body.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name != 'Body':
        bpy.data.objects.remove(o)
zs = [v.co.z for v in me.vertices]
report.update({'verts': n, 'tris': sum(len(p.vertices) - 2 for p in me.polygons), 'pieces': len(comps),
               'rigid_pieces': rigid, 'split_pieces': split, 'bind_zmin': float(min(zs)),
               'dominant': {bones[j]: int((Wt[:, j] > 0.5).sum()) for j in range(len(bones)) if (Wt[:, j] > 0).any()}})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(report, open(REP, 'w'), indent=1, default=str)
print('FIT ' + json.dumps({k: v for k, v in report.items() if k not in ('dominant', 'pose_fit')}, default=str))
