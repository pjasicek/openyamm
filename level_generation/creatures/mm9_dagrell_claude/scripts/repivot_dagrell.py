"""Dagrell joints (2026-10-30): re-pivot the MM9 skeleton onto the Meshy bone pieces so no piece leaves its joint.

Args: <uv blend (Body on MM9_Rig, action FitPose)> <out blend> <report json>

Why: fit_dagrell.py only ROTATED the MM9 skeleton onto Meshy's pieces; the bones kept MM9's lengths, so their pivots
sat 3-30 cm away from where Meshy's pieces meet (Meshy's neck is short, its tail and limbs are proportioned
differently). A rigid piece turns about its bone's pivot, so every MM9 rotation of a joint swung the piece's end away
from its neighbour by about (pivot offset) x (angle): the head, tail blade and limbs flew 10-33 cm apart in the attack.
Several pieces also rode the wrong bone (the right humerus on XbackB, the pelvis on XtailA, a forearm on the wrist
bone, a second claw on an occupied digit), and the left arm lacked a humerus.

What it does (in the FitPose, i.e. on Meshy's own geometry, where the pieces touch):
1. Structural pieces get their bone: the spine (split along its length at the XbackA / XbackB / Xneckbase pivots, the
   front of it is the chest, Xneckbase, that carries the neck and the shoulders as in MM9), the neck vertebra
   (XneckB), skull and mandible (kept from the fit), the tail vertebrae and blade (kept), the right humerus
   (Xarmpiv), forearm (Xarm, its hand end Xarmlow), the two separate claws (one digit pivot each, matched by
   direction), femur (Xlegpiv) and the shin+metatarsal+toes piece (split Xleg / Xleglow / Xfoot at the knee, hock
   and ankle). The left femur and shin are labelled the same way (they are replaced below).
2. Every other piece (ribs, spikes, pelvis, girdle, spurs, toe claws, small claws) is an attachment: it takes, as a
   whole, the skin weights of the host vertex its root touches (the torso when it touches it within CORE_REACH,
   else the nearest assigned piece), so it moves with the exact point it grows from.
3. Pivots: each bone's head goes to the interface with its parent's geometry (the mean of the closest vertex pairs
   between the two), and every geometry-less bone between them to the same point; split pivots lie on the piece's
   axis. New rest heads keep each bone's rest orientation, so the MM9 rotation keys play unchanged.
4. Unpose: every vertex goes to the new rest by the inverse of its blended FitPose matrices.
5. Left limbs: deleted and replaced by mirrored copies (rest space, about the spine's mid-plane) of the right arm and
   right hind leg, bones and pieces alike; UVs are carried (the mirrored limbs sample the right limbs' texels).
"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv
CORE_REACH = 0.03     # an attachment within this of the torso grows from the torso
CONTACT_BAND = 0.01   # interface: closest vertex pairs within (min + band)
DIFFUSE = 4           # smoothing passes of split-piece weights along edges
CHEST_BACK = 0.05     # the chest (Xneckbase) starts this far behind the shoulder girdle's root on the spine
WRIST_BACK = 0.06     # the wrist pivot sits this far up the forearm from the claw roots
TORSO = ('XCENTER', 'XbackA', 'XbackB', 'Xneckbase')
TAIL = ('XtailA', 'XtailB', 'XtailC', 'XtailD', 'XtailF', 'Xtail')
HEAD = ('Xheadpiv', 'Xjawpiv')
DIGITS_R = ('Xfinpiv', 'Xfinpiv01', 'Xfinpiv02')
DIGIT_TIP = {'Xfinpiv': 'Xfmid', 'Xfinpiv01': 'Xfmid01', 'Xfinpiv02': 'Xfmid02'}

bpy.ops.wm.open_mainfile(filepath=IN)
sc = bpy.context.scene
rig = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
assert rig.matrix_world == Matrix.Identity(4) and body.matrix_world == Matrix.Identity(4)
bones = [b.name for b in rig.data.bones]
bidx = {b: i for i, b in enumerate(bones)}
NB = len(bones)
parent = {b.name: (b.parent.name if b.parent else None) for b in rig.data.bones}
ML = {b.name: b.matrix_local.copy() for b in rig.data.bones}


def depth(name):
    d = 0
    while parent[name]:
        name = parent[name]; d += 1
    return d


def ancestors(name):
    out = []
    while parent[name]:
        name = parent[name]; out.append(name)
    return out


# ---------------- FitPose positions and current weights
fp = bpy.data.actions['FitPose']
rig.animation_data_create(); rig.animation_data.action = fp
try:
    rig.animation_data.action_slot = fp.slots[0]
except Exception:
    pass
sc.frame_set(0); bpy.context.view_layer.update()
BASIS = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
POSE_OLD = {pb.name: pb.matrix.copy() for pb in rig.pose.bones}
dg = bpy.context.evaluated_depsgraph_get()
ev = body.evaluated_get(dg).to_mesh()
P = np.array([tuple(v.co) for v in ev.vertices])
body.evaluated_get(dg).to_mesh_clear()
me = body.data
n = len(me.vertices)
gname = {g.index: g.name for g in body.vertex_groups}
W0 = np.zeros((n, NB))
for v in me.vertices:
    for g in v.groups:
        W0[v.index, bidx[gname[g.group]]] = g.weight

# ---------------- pieces
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = np.full(n, -1)
pieces = []
for v in bm.verts:
    if comp[v.index] >= 0:
        continue
    st = [v]; comp[v.index] = len(pieces); c = []
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0:
                comp[y.index] = len(pieces); st.append(y)
    pieces.append(np.array(sorted(c)))
nbr = [[] for _ in range(n)]
for e in bm.edges:
    a, b = e.verts[0].index, e.verts[1].index
    nbr[a].append(b); nbr[b].append(a)
NP = len(pieces)
dom = [bones[int(np.argmax(W0[c].sum(0)))] for c in pieces]
cen = [P[c].mean(0) for c in pieces]
ext = [float(np.linalg.norm(P[c].max(0) - P[c].min(0))) for c in pieces]
cur_bones = [set(bones[j] for j in np.nonzero(W0[c].sum(0) > 1e-6)[0]) for c in pieces]
# mirror pairs by mirrored MM9 rest head (the MM9 skeleton is symmetric in its bind pose)
head0 = {b.name: b.head_local.copy() for b in rig.data.bones}
MIRROR = {}
for b in bones:
    h = head0[b]
    if h.x > 0.01:
        t = Vector((-h.x, h.y, h.z))
        m = min(bones, key=lambda o: (head0[o] - t).length)
        assert (head0[m] - t).length < 1e-4, (b, m)
        MIRROR[b] = m
RIGHT_LIMB = set(MIRROR)
LEFT_LIMB = set(MIRROR.values())
LEFT_ARM = {MIRROR[b] for b in RIGHT_LIMB if b == 'Xarmpiv' or 'Xarmpiv' in ancestors(b)}


def pdist(a, b):
    """min distance between vertex sets a and b (indices) and the closest pair."""
    A, B = P[a], P[b]
    best = (1e9, None, None)
    for k in range(0, len(A), 256):
        d = np.linalg.norm(A[k:k + 256, None, :] - B[None, :, :], axis=2)
        i, j = np.unravel_index(np.argmin(d), d.shape)
        if d[i, j] < best[0]:
            best = (float(d[i, j]), a[k + i], b[j])
    return best


def interface(a, b):
    """Mean midpoint of the closest vertex pairs between vertex sets a and b."""
    A, B = P[a], P[b]
    d = np.linalg.norm(A[:, None, :] - B[None, :, :], axis=2)
    j = np.argmin(d, axis=1); dm = d[np.arange(len(a)), j]
    sel = dm <= dm.min() + CONTACT_BAND
    return (A[sel] + B[j[sel]]).mean(0) / 2, float(dm.min())


def axis_point(c, q, radius=0.045):
    """Centroid of the piece's vertices within radius of q (a point on the piece's medial axis)."""
    d = np.linalg.norm(P[c] - q, axis=1)
    sel = d < radius
    if sel.sum() < 4:
        sel = d <= np.sort(d)[min(5, len(d) - 1)]
    return P[c][sel].mean(0)


def bone_head_fit(b):
    return np.array(tuple(POSE_OLD[b].translation))


report = {'pieces': NP}
W = np.zeros((n, NB))
kind = ['attach'] * NP   # 'struct', 'attach', 'drop'


def set_rigid(k, b):
    W[pieces[k]] = 0; W[pieces[k], bidx[b]] = 1.0; kind[k] = 'struct'


def pick(cond, what, largest=True, single=False):
    ks = [k for k in range(NP) if cond(k)]
    assert ks, what
    if single:
        assert len(ks) == 1, (what, ks)
    return max(ks, key=lambda k: len(pieces[k])) if largest else ks


# ---- the left arm copies (mirror_left_arm.py) are replaced by new mirrors of the right arm
for k in range(NP):
    if cur_bones[k] <= LEFT_ARM:
        kind[k] = 'drop'
# ---- head: skull pieces and the mandible keep their fit labels
for k in range(NP):
    if kind[k] != 'drop' and dom[k] in HEAD:
        set_rigid(k, dom[k])
# ---- tail vertebrae and blade (behind the pelvis) keep theirs
for k in range(NP):
    if kind[k] != 'drop' and dom[k] in TAIL and cen[k][1] > 0.28:
        set_rigid(k, dom[k])
# ---- neck: the vertebra between spine and skull
k_neck = pick(lambda k: dom[k] == 'XneckB', 'neck', single=True)
set_rigid(k_neck, 'XneckB')
# ---- spine: one long piece, split along y at the pivots
k_sp = pick(lambda k: dom[k] in TORSO and ext[k] > 0.6, 'spine', single=True)
sp = pieces[k_sp]
kind[k_sp] = 'struct'
# ---- right limbs
k_hum = pick(lambda k: dom[k] == 'XbackB' and cen[k][0] > 0.1 and ext[k] > 0.3, 'right humerus')  # the longest bone there
set_rigid(k_hum, 'Xarmpiv')
k_fa = pick(lambda k: dom[k] == 'Xarmlow', 'right forearm')
kind[k_fa] = 'struct'
k_fem = pick(lambda k: dom[k] == 'Xlegpiv', 'right femur')
set_rigid(k_fem, 'Xlegpiv')
k_shin = pick(lambda k: dom[k] in ('Xleg', 'Xleglow', 'Xfoot') and cen[k][0] > 0, 'right shin')
kind[k_shin] = 'struct'
# left hind leg (Meshy's own): labelled like the right one so the pieces growing from it are found and replaced
k_fem_l = pick(lambda k: dom[k] == 'Xlegpiv01' and kind[k] != 'drop', 'left femur')
set_rigid(k_fem_l, 'Xlegpiv01')
k_shin_l = pick(lambda k: dom[k] in ('Xleg01', 'Xleglow01', 'Xfoot01') and cen[k][0] < 0, 'left shin')
set_rigid(k_shin_l, 'Xleglow01')
# ---- claws: groups of touching claw pieces; the large ones ride a digit pivot each, small spurs are attachments
claw = [k for k in range(NP) if dom[k] in DIGITS_R and kind[k] != 'drop']
groups = []
for k in claw:
    for g in groups:
        if any(pdist(pieces[k], pieces[o])[0] < 0.01 for o in g):
            g.append(k); break
    else:
        groups.append([k])
fa = pieces[k_fa]
main = []
for g in groups:
    vs = np.concatenate([pieces[k] for k in g])
    d, i_root, _ = pdist(vs, fa)
    if len(vs) >= 30 and d < 0.012:
        root = P[i_root]
        tip = P[vs[np.argmax(np.linalg.norm(P[vs] - root, axis=1))]]
        main.append((g, vs, root, (tip - root) / np.linalg.norm(tip - root)))
free = list(DIGITS_R)
claw_rep = []
for g, vs, root, dvec in sorted(main, key=lambda m: -len(m[1])):
    def cosine(dg_):
        v = bone_head_fit(DIGIT_TIP[dg_]) - bone_head_fit(dg_)
        return float(dvec @ v / np.linalg.norm(v))
    dg_ = max(free, key=cosine)
    free.remove(dg_)
    for k in g:
        set_rigid(k, dg_)
    claw_rep.append({'pieces': g, 'digit': dg_, 'cos': round(cosine(dg_), 2)})
report['claws'] = claw_rep

# ---------------- explicit pivots (FitPose world): spine axis, wrist, hock/ankle, jaw hinge
pivot = {}
# spine: XbackA / XbackB at the MM9 heads' y, on the axis; the chest (Xneckbase) begins just behind the girdle root
girdle = [k for k in range(NP) if kind[k] == 'attach' and abs(cen[k][0]) < 0.08 and ext[k] > 0.2
          and -0.55 < cen[k][1] < -0.35 and cen[k][2] < 1.0 and pdist(pieces[k], pieces[k_hum])[0] < 0.02]
assert girdle, 'shoulder girdle'
k_gird = min(girdle, key=lambda k: pdist(pieces[k], sp)[0])
_, _, i_sp = pdist(pieces[k_gird], sp)
y_chest = P[i_sp][1] + CHEST_BACK
for b, y in (('XbackA', bone_head_fit('XbackA')[1]), ('XbackB', bone_head_fit('XbackB')[1]), ('Xneckbase', y_chest)):
    sel = np.abs(P[sp][:, 1] - y) < 0.03
    pivot[b] = P[sp][sel].mean(0)
order = sorted(('XbackA', 'XbackB', 'Xneckbase'), key=lambda b: -pivot[b][1])  # back to front
ys = [pivot[b][1] for b in order]
for i in sp:
    y = P[i][1]
    lab = 'XCENTER' if y > ys[0] else 'XbackA' if y > ys[1] else 'XbackB' if y > ys[2] else 'Xneckbase'
    W[i, bidx[lab]] = 1.0
report['girdle_piece'] = int(k_gird)
# forearm: Xarm, the hand end (beyond the wrist) Xarmlow; the wrist WRIST_BACK up the forearm from the claw roots
roots = np.array([m[2] for m in main])
r0 = roots.mean(0)
elbow_side = P[fa][np.argmax(np.linalg.norm(P[fa] - r0, axis=1))]
u = (elbow_side - r0) / np.linalg.norm(elbow_side - r0)
pivot['Xarmlow'] = axis_point(fa, r0 + u * WRIST_BACK)
s_w = (P[fa] - pivot['Xarmlow']) @ u
for i, s in zip(fa, s_w):
    W[i, bidx['Xarm' if s > 0 else 'Xarmlow']] = 1.0
# shin+metatarsal+toes: knee (contact with the femur, below), hock and ankle at the MM9 heads moved onto the axis
sh = pieces[k_shin]
pivot['Xleglow'] = axis_point(sh, bone_head_fit('Xleglow'))
pivot['Xfoot'] = axis_point(sh, bone_head_fit('Xfoot'))
knee, _ = interface(sh, pieces[k_fem])
knee = axis_point(sh, knee)
toe_c = P[sh][P[sh][:, 2] < pivot['Xfoot'][2] - 0.05].mean(0)
segs = {'Xleg': (knee, pivot['Xleglow']), 'Xleglow': (pivot['Xleglow'], pivot['Xfoot']), 'Xfoot': (pivot['Xfoot'], toe_c)}


def seg_d(p, a, b):
    ab = b - a
    t = np.clip((p - a) @ ab / (ab @ ab), 0, 1)
    return np.linalg.norm(p - (a + t[:, None] * ab), axis=1)


D = np.stack([seg_d(P[sh], *segs[b]) for b in segs], 1)
for i, j in zip(sh, np.argmin(D, 1)):
    W[i, bidx[list(segs)[j]]] = 1.0
# smooth the split pieces' weights a little along their edges (a short blend about each pivot)
for c in (sp, fa, sh):
    cs = set(int(i) for i in c)
    for _ in range(DIFFUSE):
        avg = np.array([W[[j for j in nbr[i] if j in cs]].mean(0) if nbr[i] else W[i] for i in c])
        W[c] = 0.5 * W[c] + 0.5 * avg
# jaw hinge: the mouth corners, i.e. the rear end of the seam where fit_dagrell.py cut the mandible off the skull (a
# hinge at the mandible's rear top let the jaw slide 7 cm off the skull when MM9 opens it 50 degrees)
jaw_ks = [k for k in range(NP) if kind[k] == 'struct' and dom[k] == 'Xjawpiv']
k_mand = max(jaw_ks, key=lambda k: len(pieces[k]))
mand = pieces[k_mand]
skull = np.concatenate([pieces[k] for k in range(NP) if kind[k] == 'struct' and dom[k] == 'Xheadpiv'])
dj = np.array([np.linalg.norm(P[skull] - P[i], axis=1).min() for i in mand])
seam = mand[dj < 0.003]
corner = seam[P[seam][:, 1] > P[seam][:, 1].max() - 0.02]
pivot['Xjawpiv'] = P[corner].mean(0)
report['jaw_seam_verts'] = int(len(seam))
# pieces the fit's head/jaw vote put on the jaw but that lie behind the hinge (throat, cheek) belong to the skull
behind = [k for k in jaw_ks if k != k_mand and P[pieces[k]][:, 1].min() > pivot['Xjawpiv'][1] - 0.01]
for k in behind:
    set_rigid(k, 'Xheadpiv')
report['jaw_pieces_to_skull'] = [int(k) for k in behind]

# ---------------- attachments (Prim order: nearest to the assigned geometry first)
assigned = np.zeros(n, bool)
for k in range(NP):
    if kind[k] == 'struct':
        assigned[pieces[k]] = True
pending = [k for k in range(NP) if kind[k] == 'attach']
att_rep = {}
while pending:
    A = np.nonzero(assigned)[0]
    core = A[np.all(W[A][:, [bidx[b] for b in bones if b not in TORSO]] < 1e-6, axis=1)]
    best = None
    for k in pending:
        d_any, _, h_any = pdist(pieces[k], A)
        if best is None or d_any < best[0]:
            best = (d_any, k, h_any)
    _, k, host = best
    d_core, i_core, h_core = pdist(pieces[k], core)
    if d_core < CORE_REACH:
        host = h_core
    W[pieces[k]] = W[host]
    assigned[pieces[k]] = True
    pending.remove(k)
    att_rep[int(k)] = {'host_piece': int(comp[host]), 'bones': sorted(bones[j] for j in np.nonzero(W[host] > 0.01)[0])}
report['attachments'] = att_rep

# 4 influences, normalised
for i in range(n):
    row = W[i].copy()
    keep = np.argsort(-row)[:4]
    r2 = np.zeros(NB); r2[keep] = row[keep]; r2[r2 < 0.02] = 0
    W[i] = r2 / r2.sum()


def wbones(c):
    return set(bones[j] for j in np.nonzero(W[c].sum(0) > 1e-6)[0])


for k in range(NP):
    if kind[k] != 'drop' and wbones(pieces[k]) <= LEFT_LIMB:
        kind[k] = 'drop'
mirror_set = [k for k in range(NP) if kind[k] != 'drop' and wbones(pieces[k]) <= RIGHT_LIMB]
report['dropped_pieces'] = [int(k) for k in range(NP) if kind[k] == 'drop']
report['mirrored_pieces'] = [int(k) for k in mirror_set]

# ---------------- interfaces -> pivots (right side and centre)
geo = {b: np.nonzero(W[:, bidx[b]] > 0.5)[0] for b in bones}
struct_v = np.zeros(n, bool)
for k in range(NP):
    if kind[k] == 'struct':
        struct_v[pieces[k]] = True
live = np.ones(n, bool)
for k in range(NP):
    if kind[k] == 'drop':
        live[pieces[k]] = False
piv_rep = {}
for b in sorted(bones, key=depth):
    if b in LEFT_LIMB:
        continue
    own = geo[b][struct_v[geo[b]] & live[geo[b]]]
    if len(own) == 0:
        continue
    path = []
    a = parent[b]
    while a is not None and len(geo[a][live[geo[a]]]) == 0:
        path.append(a); a = parent[a]
    if a is None:
        continue
    if b in pivot:
        p = pivot[b]; how = 'axis'
        gap = None
    else:
        pa = geo[a][live[geo[a]]]
        p, gap = interface(own, pa); how = 'contact'
        pivot[b] = p
    for x in path:
        if x in pivot and np.linalg.norm(pivot[x] - p) > 1e-6:
            report.setdefault('path_conflicts', []).append([x, b])
        pivot[x] = p
    piv_rep[b] = {'geo_parent': a, 'path': path, 'how': how, 'gap': None if gap is None else round(gap, 4),
                  'moved': round(float(np.linalg.norm(bone_head_fit(b) - p)), 4)}
report['pivots'] = piv_rep
# the first tail vertebra: MM9 translates XtailA (up to 3.5 cm; its own BACK01 skin stretches over it), so a rigid
# vertebra opened 2-4 cm at the tail root. Blend it from XCENTER at the spine end to XtailA at the far end, as MM9's
# skin does.
ta = [k for k in range(NP) if kind[k] == 'struct' and dom[k] == 'XtailA']
if ta:
    k_ta = min(ta, key=lambda k: np.linalg.norm(cen[k] - pivot['XtailA']))
    c = pieces[k_ta]
    far = P[c][np.argmax(np.linalg.norm(P[c] - pivot['XtailA'], axis=1))]
    ax = far - pivot['XtailA']
    t = np.clip((P[c] - pivot['XtailA']) @ ax / (ax @ ax), 0, 1)
    t = t * t * (3 - 2 * t)
    W[c] = 0
    W[c, bidx['XtailA']] = t
    W[c, bidx['XCENTER']] = 1 - t
    report['tail_root_blend_piece'] = int(k_ta)

# ---------------- new rest heads (bone rest orientations unchanged)
NEW_ML = {}
NEW_POSE = {}
for b in sorted(bones, key=depth):
    a = parent[b]
    ml = ML[b].copy()
    if a is None:
        NEW_ML[b] = ml; NEW_POSE[b] = POSE_OLD[b].copy(); continue
    A_ = NEW_POSE[a] @ NEW_ML[a].inverted()
    target = Vector(pivot[b]) if (b in pivot and b not in LEFT_LIMB) else POSE_OLD[b].translation
    R = ml.to_3x3()
    lb = BASIS[b].translation
    h = (A_.inverted() @ target) - R @ lb
    ml.translation = h
    NEW_ML[b] = ml
    NEW_POSE[b] = A_ @ ml @ BASIS[b]
DEF = {b: NEW_POSE[b] @ NEW_ML[b].inverted() for b in bones}
rest = np.zeros((n, 3))
for i in range(n):
    if not live[i]:
        continue
    M = Matrix(((0.0,) * 4,) * 4)
    for j in np.nonzero(W[i])[0]:
        M = M + DEF[bones[j]] * float(W[i, j])
    rest[i] = tuple(M.inverted() @ Vector(P[i]))
x_c = float(np.median(rest[sp][:, 0]))
report['mirror_plane_x'] = round(x_c, 4)
for r_, l_ in MIRROR.items():
    h = NEW_ML[r_].translation
    NEW_ML[l_].translation = Vector((2 * x_c - h.x, h.y, h.z))

# ---------------- write the rig
bpy.context.view_layer.objects.active = rig
rig.animation_data.action = None
bpy.ops.object.mode_set(mode='EDIT')
for eb in rig.data.edit_bones:
    d = eb.tail - eb.head
    eb.head = NEW_ML[eb.name].translation
    eb.tail = eb.head + d
bpy.ops.object.mode_set(mode='OBJECT')
for b in bones:
    err = (rig.data.bones[b].matrix_local - NEW_ML[b])
    assert max(abs(err[r][c]) for r in range(4) for c in range(4)) < 1e-4, b

# ---------------- write the mesh: rest positions, mirrored right limbs, dropped left limbs, weights
src = bm.verts.layers.int.new('src_tmp')
mir = bm.verts.layers.int.new('mir_tmp')  # layers before any element reference is held (adding one reallocates)
bm.verts.ensure_lookup_table()
for v in bm.verts:
    v[src] = v.index
    v.co = Vector(rest[v.index]) if live[v.index] else v.co
mv = [bm.verts[i] for k in mirror_set for i in pieces[k]]
mset = set(mv)
geom = mv + list({e for v in mv for e in v.link_edges}) + list({f for v in mv for f in v.link_faces})
res = bmesh.ops.duplicate(bm, geom=geom)
new_verts = [g for g in res['geom'] if isinstance(g, bmesh.types.BMVert)]
new_faces = [g for g in res['geom'] if isinstance(g, bmesh.types.BMFace)]
for v in new_verts:
    v.co.x = 2 * x_c - v.co.x
    v[mir] = 1
bmesh.ops.reverse_faces(bm, faces=new_faces)
new_set = set(new_faces)
flipped = 0
seen_f = set()
for f0 in new_faces:
    if f0 in seen_f:
        continue
    comp_f, st = [], [f0]; seen_f.add(f0)
    while st:
        f = st.pop(); comp_f.append(f)
        for e in f.edges:
            for g in e.link_faces:
                if g in new_set and g not in seen_f:
                    seen_f.add(g); st.append(g)
    vol = 0.0
    for f in comp_f:
        vs = [v.co for v in f.verts]
        for k in range(1, len(vs) - 1):
            vol += vs[0].dot(vs[k].cross(vs[k + 1])) / 6.0
    if vol < 0:
        bmesh.ops.reverse_faces(bm, faces=comp_f); flipped += 1
report['mirror_flipped_inverted'] = flipped
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[mir] == 0 and not live[v[src]]], context='VERTS')
bm.verts.ensure_lookup_table()
ROW = []
for v in bm.verts:
    w = W[v[src]]
    if v[mir]:
        w2 = np.zeros(NB)
        for j in np.nonzero(w)[0]:
            w2[bidx[MIRROR.get(bones[j], bones[j])]] += w[j]
        w = w2
    ROW.append(w)
bm.verts.layers.int.remove(src); bm.verts.layers.int.remove(mir)
dl = bm.verts.layers.deform.verify()
for v in bm.verts:
    v[dl].clear()
bm.to_mesh(me); me.update()
bm.free()
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
ROW = np.array(ROW)
for j, b in enumerate(bones):
    idx = np.nonzero(ROW[:, j] > 0)[0]
    if len(idx) == 0:
        continue
    g = body.vertex_groups.new(name=b)
    for i in idx:
        g.add([int(i)], float(ROW[i, j]), 'REPLACE')

# ---------------- check: the FitPose reproduces Meshy's pieces (right side and centre)
rig.animation_data.action = fp
sc.frame_set(1); sc.frame_set(0); bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
ev = body.evaluated_get(dg).to_mesh()
Q = np.array([tuple(v.co) for v in ev.vertices])
body.evaluated_get(dg).to_mesh_clear()
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
n_live = int(live.sum())
report['fitpose_err_max'] = float(np.abs(Q[:n_live] - P[live]).max())
report['verts'] = len(me.vertices)
report['tris'] = sum(len(p.vertices) - 2 for p in me.polygons)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(report, open(REP, 'w'), indent=1, default=str)
print('REPIVOT ' + json.dumps({k: report.get(k) for k in ('pieces', 'verts', 'tris', 'mirror_plane_x', 'claws',
                                                           'girdle_piece', 'mirror_flipped_inverted', 'fitpose_err_max',
                                                           'path_conflicts')}, default=str))
print('REPIVOT pivots ' + json.dumps(piv_rep, default=str))
