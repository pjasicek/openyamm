"""G3: the queen's armature, weights and the rock, in actor space (origin = the native ground pivot under the rock).

Placement (work/placement.json, from compose_check.py): the queen mesh and every joint move by queen_location, the
rock stays put relative to her; then both move back by her depth (SHIFT_Y) so she stands at the actor's position.
Bones:
  Root (origin) -> Rock (the rock alcove, rigid; its own leaf so the collapse can scale it)
  Root -> Abdomen1..6 (tail tip in the niche -> waist; ring-marched centreline) -> B_Pelvis (waist)
  -> B_Spine/Spine1/Spine2 -> B_Neck -> B_Head; B_Spine2 -> B_*_Clavicle -> UpperArm -> Forearm -> Hand -> fingers.
Upper-body frames follow the humanoid set (bar1 rule): rest frame R = q @ R_src, q the minimal swing of the source
segment onto ours; B_Pelvis keeps the source frame; hands from the mesh (finger direction + knuckle line, index ->
pinky); fingers from work/fingers_fit.json, each the minimal swing on top of its hand's swing. scene['rig_offsets']
holds q and R_src per bone for the Mixamo retarget. Sockets: Socket_Palm_L/R (non-deforming leaves on the hands, on
the palm surface).
Weights: geodesic labels from bone seeds (bone heat fails on the grafted head and the separate pieces), smoothed over
six edge rings; the axial share then redistributed by height along the abdomen-spine-neck chain; then (1) every separate piece (horns, spikes, fangs, breast hooks, studs)
copies the weights of the nearest main-skin vertex, (2) every finger piece goes wholly to its own finger chain (nearest
two joints along it), (3) skin above the jaw line carries only head weight.
Writes work/rig_v1.blend (objects 'Queen', 'Rock', 'Rig') and work/rig.json."""
import bpy, bmesh, sys, json, math
import numpy as np
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion
from mathutils.kdtree import KDTree
P = Path(__file__).resolve().parents[1]
SRC = json.loads((P / 'work' / 'source_rest.json').read_text())
JJ = json.loads((P / 'work' / 'joints.json').read_text())
FIT = json.loads((P / 'work' / 'fingers_fit.json').read_text())
PLACE = json.loads((P / 'work' / 'placement.json').read_text())
# The engine draws the native sprite as a plane at the actor's position, so the queen herself stands there: the whole
# model moves back by her placement depth (SHIFT_Y), the rock filling the space behind her toward the end wall.
# Without it the rock's front came 380 units nearer the camera than the sprite plane and read twice its size.
SHIFT_Y = -PLACE['queen_location'][1]
OFF = Vector(PLACE['queen_location']) + Vector((0.0, SHIFT_Y, 0.0))
J = {k: Vector(v) + OFF for k, v in JJ['joints'].items()}
ABD = 6
NAME = {'B_Pelvis': 'Pelvis', 'B_Spine': 'Spine', 'B_Spine1': 'Spine1', 'B_Spine2': 'Spine2', 'B_Neck': 'Neck',
        'B_Head': 'Head'}
for s in ('L', 'R'):
    for b in ('Clavicle', 'UpperArm', 'Forearm', 'Hand'):
        NAME[f'B_{s}_{b}'] = f'{s}_{b}'
FINGER = ['thumb', 'index', 'middle', 'ring', 'pinky']


def chain_names(s, i):
    if s == 'R' and i == 0:
        return ['B_R_Finger0', 'B_R_Finger0.001', 'B_R_Finger0.002']
    return [f'B_{s}_Finger{i}', f'B_{s}_Finger{i}1', f'B_{s}_Finger{i}2']


bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'step3.blend'))
queen = bpy.data.objects['Queen']
queen.data.transform(Matrix.Translation(OFF)); queen.data.update()
with bpy.data.libraries.load(str(P / 'work' / 'rock.blend')) as (data_from, data_to):
    data_to.objects = ['Rock']
rock = data_to.objects[0]
bpy.context.scene.collection.objects.link(rock)
rock.data = rock.data.copy()
# ROCK_BACK: extra room behind her (rock_gate.py: 5 cm left no room for leaning back or swinging an arm behind her)
ROCK_BACK = 0.25
rock.data.transform(Matrix.Translation((0.0, SHIFT_Y + ROCK_BACK, 0.0))); rock.data.update()

# ---------------------------------------------------------------- upper-body frames (source-frame rule)
upper = [n for n in SRC if n.startswith('B_') and 'Thigh' not in n and 'Calf' not in n and 'Foot' not in n
         and 'Toe' not in n]
order = []
def visit(n):
    if n in upper:
        order.append(n)
    for c in [k for k, v in SRC.items() if v['parent'] == n]:
        visit(c)
visit('B_Pelvis')
head, rot, swing = {}, {}, {}
for n in order:
    if n in NAME:
        head[n] = J[NAME[n]].copy()
for n in order:
    s_ = SRC[n]
    c = s_['child']
    if c and n in NAME and c in NAME and n != 'B_Pelvis':
        q = Vector(s_['seg']).rotation_difference(head[c] - head[n])
    elif s_['parent'] in swing:
        q = swing[s_['parent']]
    else:
        q = Quaternion()
    swing[n] = q
    rot[n] = q.to_matrix() @ Matrix([Vector(r) for r in s_['rot']])
fj = {}
for sd in ('L', 'R'):
    hn = f'B_{sd}_Hand'
    pts = {f: [Vector(p) + OFF for p in FIT[sd][f]] for f in FINGER}
    wr = head[hn]
    f_our = (pts['middle'][0] - wr).normalized()
    t_our = pts['index'][0] - pts['pinky'][0]
    h0 = np.array(SRC[hn]['head'])
    f_src = np.array(SRC[f'B_{sd}_Finger2']['head']) - h0; f_src /= np.linalg.norm(f_src)
    t_src = np.array(SRC[f'B_{sd}_Finger1']['head']) - np.array(SRC[f'B_{sd}_Finger4']['head'])
    def basis(f, t):
        f = np.array(f); t = np.array(t); t = t - f * (t @ f); t /= np.linalg.norm(t)
        return np.column_stack([f, t, np.cross(f, t)])
    Rq = basis(f_our, t_our) @ basis(f_src, t_src).T
    swing[hn] = Matrix(Rq.tolist()).to_quaternion()
    rot[hn] = swing[hn].to_matrix() @ Matrix([Vector(r) for r in SRC[hn]['rot']])
    for i, f in enumerate(FINGER):
        names = chain_names(sd, i)
        for k, n in enumerate(names):
            head[n] = pts[f][k]
            tgt = pts[f][k + 1]
            sseg = Vector(SRC[n]['seg']) if SRC[n]['seg'] else (Vector(SRC[n]['head']) - Vector(SRC[SRC[n]['parent']]['head']))
            qh = swing[hn]
            q = (qh @ sseg).rotation_difference(tgt - head[n]) @ qh
            swing[n] = q
            rot[n] = q.to_matrix() @ Matrix([Vector(r) for r in SRC[n]['rot']])
            fj[n] = (head[n], tgt)

# ---------------------------------------------------------------- armature
ad = bpy.data.armatures.new('Rig'); rig = bpy.data.objects.new('Rig', ad)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = ad.edit_bones.new('Root'); eb.head = (0, 0, 0); eb.tail = (0, 0, 0.3)
eb = ad.edit_bones.new('Rock'); eb.head = (0, 0, 0); eb.tail = (0, 0, 0.5); eb.parent = ad.edit_bones['Root']
prev = 'Root'
for i in range(1, ABD + 1):
    eb = ad.edit_bones.new(f'Abdomen{i}')
    eb.head = J[f'Abdomen{i - 1:02d}']; eb.tail = J[f'Abdomen{i:02d}']
    eb.parent = ad.edit_bones[prev]; eb.use_connect = i > 1
    prev = f'Abdomen{i}'
for n in order:
    eb = ad.edit_bones.new(n)
    R = rot[n]
    c = SRC[n]['child']
    if n in fj:
        L = (fj[n][1] - fj[n][0]).length
    elif c in head and (head[c] - head[n]).length > 1e-4:
        L = (head[c] - head[n]).length
    else:
        L = 0.08
    eb.head = head[n]; eb.tail = head[n] + R.col[1] * L
    eb.align_roll(R.col[2])
for n in order:
    p = SRC[n]['parent']
    ad.edit_bones[n].parent = ad.edit_bones[p] if p in SRC and p in order else ad.edit_bones[f'Abdomen{ABD}']
# palm sockets: on the palm surface (the side the fingers curl toward), between the knuckles and the wrist
co = np.array([tuple(v.co) for v in queen.data.vertices])
for sd in ('L', 'R'):
    hn = f'B_{sd}_Hand'
    wr = head[hn]; mid = (Vector(FIT[sd]['index'][0]) + Vector(FIT[sd]['pinky'][0])) / 2 + OFF
    centre = (wr + mid) / 2
    curl = (Vector(FIT[sd]['middle'][2]) + OFF) - (Vector(FIT[sd]['middle'][0]) + OFF)
    axis = (mid - wr).normalized()
    palm_n = (curl - axis * curl.dot(axis)).normalized()
    near = co[np.linalg.norm(co - np.array(centre), axis=1) < 0.06]
    depth = max(0.0, float(((near - np.array(centre)) @ np.array(palm_n)).max())) if len(near) else 0.0
    eb = ad.edit_bones.new(f'Socket_Palm_{sd}')
    eb.head = centre + palm_n * depth; eb.tail = eb.head + palm_n * 0.04
    eb.parent = ad.edit_bones[hn]; eb.use_deform = False
for n in ('Root',):
    ad.edit_bones[n].use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
err = max(math.degrees((rig.data.bones[n].matrix_local.to_3x3().to_quaternion()).rotation_difference(
    rot[n].to_quaternion()).angle) for n in order)
print('RIG bones', len(rig.data.bones), 'max source-frame error deg', round(err, 3))

# ---------------------------------------------------------------- weights
deform = [b.name for b in rig.data.bones if b.use_deform and b.name not in ('Rock', 'Root')
          and not b.name.startswith('Socket')]
me = queen.data
NV = len(me.vertices)
co = np.array([tuple(v.co) for v in me.vertices])
col = {n: k for k, n in enumerate(deform)}
# Geodesic labels. Seeds: each vertex seeds its nearest bone that it can SEE (the straight line to the bone's closest
# point stays inside the body: no other surface crossed), within SEED_MAX - the bone-heat visibility rule, which
# keeps the abdomen beside a hanging hand from seeding the hand. A multi-source Dijkstra over mesh edges then labels
# every vertex with the bone of its nearest seed, so skin only takes bones it is connected to.
import heapq
from mathutils.bvhtree import BVHTree
SEED_MAX = 0.45
segs = []
for n in deform:
    b = rig.data.bones[n]
    segs.append((np.array(b.head_local), np.array(b.tail_local)))
def seg_point(p, a, b):
    d = b - a; t = np.clip(((p - a) @ d) / max(d @ d, 1e-12), 0, 1)
    return a + t[:, None] * d
CP = np.stack([seg_point(co, a, b) for a, b in segs], axis=1)            # (NV, bones, 3)
D = np.linalg.norm(CP - co[:, None, :], axis=2)
bmt = bmesh.new(); bmt.from_mesh(me); tree = BVHTree.FromBMesh(bmt); bmt.free()
nrm = np.array([tuple(v.normal) for v in me.vertices])
near = D.argmin(1); dmin = D.min(1)
seed = np.full(NV, -1)
for i in range(NV):
    for k in np.argsort(D[i])[:3]:
        if D[i, k] > SEED_MAX:
            break
        start = Vector(co[i] - nrm[i] * 1e-3)
        to = Vector(CP[i, k]) - start
        hit = tree.ray_cast(start, to.normalized(), to.length)
        if hit[0] is None:
            seed[i] = k
            break
adj = [[] for _ in range(NV)]
for e in me.edges:
    a, b = e.vertices
    L = float(np.linalg.norm(co[a] - co[b]))
    adj[a].append((b, L)); adj[b].append((a, L))
geo = np.full(NV, np.inf); lab = np.full(NV, -1)
heap = []
for i in np.where(seed >= 0)[0]:
    geo[i] = 0.0; lab[i] = seed[i]; heap.append((0.0, int(i)))
heapq.heapify(heap)
while heap:
    d, v = heapq.heappop(heap)
    if d > geo[v]:
        continue
    for w, L in adj[v]:
        nd = d + L
        if nd < geo[w]:
            geo[w] = nd; lab[w] = lab[v]; heapq.heappush(heap, (nd, w))
unseeded = lab < 0
lab[unseeded] = near[unseeded]                    # islands without seeds: straight nearest bone (pieces fixed below)
W = np.zeros((NV, len(deform)))
W[np.arange(NV), lab] = 1.0
# soft joints: smooth the labels over the mesh (each pass mixes a vertex with its edge neighbours)
nbr = [np.array([w for w, _ in a], dtype=int) for a in adj]
for _ in range(6):
    W2 = W.copy()
    for v in range(NV):
        if len(nbr[v]):
            W2[v] = 0.5 * W[v] + 0.5 * W[nbr[v]].mean(0)
    W = W2
# Torso: the axial share of each vertex (abdomen, pelvis, spine, neck bones) is redistributed by its height along the
# joint chain (linear between neighbouring joints), so the torso bends smoothly; arm and clavicle shares are kept.
AXIAL = [f'Abdomen{i}' for i in range(1, ABD + 1)] + ['B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck']
ax_idx = [col[n] for n in AXIAL]
heads = [np.array(rig.data.bones[n].head_local) for n in AXIAL]
tails = [np.array(rig.data.bones[n].tail_local) for n in AXIAL]
share = W[:, ax_idx].sum(1)
torso = (share > 0.05) & (np.isin(np.arange(NV), np.where(W[:, ax_idx].argmax(1) >= 0)[0]))
# parameter along the chain: nearest point on the polyline of bone segments, as a fractional bone index
best = np.full(NV, np.inf); param = np.zeros(NV)
for k, (a, b) in enumerate(zip(heads, tails)):
    d = b - a; tt = np.clip(((co - a) @ d) / max(d @ d, 1e-12), 0, 1)
    dist = np.linalg.norm(co - a - tt[:, None] * d, axis=1)
    m = dist < best; best[m] = dist[m]; param[m] = k + tt[m]
axial = np.zeros((NV, len(AXIAL)))
# each bone owns its segment; blend across a joint over the last/first 30 % of the neighbouring segments
for i in range(NV):
    k = min(int(param[i]), len(AXIAL) - 1); f_ = param[i] - k
    if f_ > 0.7 and k + 1 < len(AXIAL):
        w2 = (f_ - 0.7) / 0.6; axial[i, k] = 1 - w2; axial[i, k + 1] = w2
    elif f_ < 0.3 and k > 0:
        w2 = (0.3 - f_) / 0.6; axial[i, k] = 1 - w2; axial[i, k - 1] = w2
    else:
        axial[i, k] = 1.0
W[np.ix_(torso, ax_idx)] = axial[torso] * share[torso, None]
torso_redistributed = int(torso.sum())
# Rigid armour (user review 2026-10-13: the steel cups crushed with the arm swing): breastplate cups, studs and the
# chest strap (work/rigid_mask.json from the textured master) are wholly on B_Spine2; the skin within FEATHER of them
# blends from that toward its own weights, so the cups move as one plate without tearing at their edges.
FEATHER = 0.03
rigid_path = P / 'work' / 'rigid_mask.json'
rigid_count = 0
if rigid_path.exists():
    RM = json.loads(rigid_path.read_text())
    rid = np.array(RM['metal'] + RM['strap'], dtype=int)
    rkd = KDTree(len(rid))
    for k, i in enumerate(rid):
        rkd.insert(co[i], k)
    rkd.balance()
    chest = np.zeros(len(deform)); chest[col['B_Spine2']] = 1.0
    is_rigid = np.zeros(NV, bool); is_rigid[rid] = True
    for i in range(NV):
        if is_rigid[i]:
            W[i] = chest; continue
        _, _, d = rkd.find(co[i])
        if d < FEATHER:
            f_ = d / FEATHER
            W[i] = W[i] * f_ + chest * (1 - f_)
    rigid_count = int(is_rigid.sum())
    # straps over the shoulder tops: chest, blending by height into that side's clavicle (never the upper arm, which
    # dragged the strap across the chest when the arm crossed in front)
    strap_top = np.array(RM.get('strap_top', []), dtype=int)
    for i in strap_top:
        f_ = float(np.clip((co[i, 2] - RM['top_z']) / 0.08, 0, 1))
        side = 'L' if co[i, 0] > OFF.x else 'R'
        W[i] = chest * (1 - f_); W[i, col[f'B_{side}_Clavicle']] += f_
    is_rigid[strap_top] = False
# pieces
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
label = np.full(NV, -1); sizes = []
for v in bm.verts:
    if label[v.index] >= 0:
        continue
    k = len(sizes); st = [v]; label[v.index] = k; n_ = 0
    while st:
        x = st.pop(); n_ += 1
        for e in x.link_edges:
            w = e.other_vert(x)
            if label[w.index] < 0:
                label[w.index] = k; st.append(w)
    sizes.append(n_)
bm.free()
main = {int(np.argmax(sizes))}
# the head mesh is its own large piece (part = 1); both big pieces count as skin
big = sorted(range(len(sizes)), key=lambda k: -sizes[k])[:2]
skin = np.isin(label, big)
skin_ids = np.where(skin)[0]
kd = KDTree(len(skin_ids))
for k, i in enumerate(skin_ids):
    kd.insert(co[i], k)
kd.balance()
copied = 0
for i in np.where(~skin)[0]:
    _, k, _ = kd.find(co[i])
    W[i] = W[skin_ids[k]]; copied += 1
# the rigid armour again: studs are separate pieces that copied the nearest skin, which may lie outside the plate
if rigid_path.exists():
    W[is_rigid] = chest
    for i in strap_top:
        f_ = float(np.clip((co[i, 2] - RM['top_z']) / 0.08, 0, 1))
        side = 'L' if co[i, 0] > OFF.x else 'R'
        W[i] = chest * (1 - f_); W[i, col[f'B_{side}_Clavicle']] += f_
# fingers: piece vertices wholly on their own chain, by position along it
finger_verts = 0
for sd in ('L', 'R'):
    for i, f in enumerate(FINGER):
        names = chain_names(sd, i)
        pts = [np.array(p) + np.array(OFF) for p in FIT[sd][f]]
        for v in FIT[sd]['vertices'][f]:
            p = co[v]
            best = None
            for k in range(3):
                a, b = pts[k], pts[k + 1]
                d = b - a; t = float(np.clip((p - a) @ d / (d @ d), 0, 1))
                dist = float(np.linalg.norm(p - a - t * d))
                if best is None or dist < best[0]:
                    best = (dist, k, t)
            _, k, t = best
            W[v] = 0
            # blend into the next phalanx over the last quarter of a segment
            if t > 0.75 and k < 2:
                f2 = (t - 0.75) / 0.25 * 0.5
                W[v, col[names[k]]] = 1 - f2; W[v, col[names[k + 1]]] = f2
            else:
                W[v, col[names[k]]] = 1.0
            finger_verts += 1
# above the jaw: head only
z_jaw = float(J['Head'].z) + 0.0
headpart = np.array([0] * NV)
part_face = np.array([p.value for p in me.attributes['part'].data])
for p in me.polygons:
    if part_face[p.index] == 1:
        headpart[list(p.vertices)] = 1
cleared = 0
for i in np.where((headpart == 1) & (co[:, 2] > z_jaw))[0]:
    W[i] = 0; W[i, col['B_Head']] = 1.0; cleared += 1
# Neck seam: the grafted head's neck band and the body's neck top overlap as two surfaces; both take one weight by
# height (B_Neck below the cut, blending into B_Head up to the head joint), so they never part when the head turns.
CUT_W = json.loads((P / 'work' / 'graft_report.json').read_text())['cut_z'] + OFF.z
NECK_TOP = CUT_W + 0.06              # above this the head mesh is head-only (the chin and fangs sit just above)
band = (co[:, 2] > CUT_W - 0.09) & (co[:, 2] < NECK_TOP)
t = np.clip((co[:, 2] - (CUT_W - 0.03)) / (NECK_TOP - (CUT_W - 0.03)), 0, 1)
t = t * t * (3 - 2 * t)
# body vertices: the rule fades out radially (full within 9 cm of the neck axis, none beyond 14 cm), so it never
# cuts a hard edge across the base of the neck into the clavicles; the whole head mesh in the band takes it fully
radial = np.hypot(co[:, 0] - float(J['Neck'].x), co[:, 1] - float(J['Neck'].y))
f = np.where(headpart == 1, 1.0, np.clip((0.14 - radial) / 0.05, 0, 1) * band)
seam = np.zeros_like(W)
seam[:, col['B_Head']] = t; seam[:, col['B_Neck']] = 1 - t
W = W * (1 - f[:, None]) + seam * f[:, None]
sel = f > 0
seam_unified = int(sel.sum())
head_only = (headpart == 1) & ((co[:, 2] >= NECK_TOP) | ~skin)
W[head_only] = 0; W[head_only, col['B_Head']] = 1.0
cleared += int(head_only.sum())
# Upper-arm weight fades out medially over 7 cm inside the shoulder joint and clavicle weight toward the midline
# (playbook: a raised arm otherwise drags the sternum); the removed share goes to the chest (B_Spine2).
bled = 0
for sd, sg in (('L', 1), ('R', -1)):
    sx = float(J[f'{sd}_UpperArm'].x) * sg
    lat = co[:, 0] * sg
    f_up = np.clip((lat - (sx - 0.07)) / 0.07, 0, 1)
    f_cl = np.clip((lat - float(J['Spine2'].x) * sg) / 0.08, 0, 1)
    for name, f in ((f'B_{sd}_UpperArm', f_up), (f'B_{sd}_Clavicle', f_cl)):
        k = col[name]
        cut_w = W[:, k] * (1 - f)
        bled += int((cut_w > 0.05).sum())
        W[:, k] -= cut_w
        W[:, col['B_Spine2']] += cut_w
W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
queen.parent = rig
if not any(m.type == 'ARMATURE' for m in queen.modifiers):
    mm = queen.modifiers.new('Armature', 'ARMATURE'); mm.object = rig
for g in list(queen.vertex_groups):
    queen.vertex_groups.remove(g)
groups = {n: queen.vertex_groups.new(name=n) for n in deform}
for n, k in col.items():
    ids = np.where(W[:, k] > 1e-4)[0]
    for i in ids:
        groups[n].add([int(i)], float(W[i, k]), 'REPLACE')
# rock: rigid on its bone
rock.parent = rig
rock.vertex_groups.clear()
g = rock.vertex_groups.new(name='Rock'); g.add(list(range(len(rock.data.vertices))), 1.0, 'REPLACE')
m = rock.modifiers.new('Armature', 'ARMATURE'); m.object = rig
unweighted = int((W.sum(1) < 0.5).sum())
report_seed = {'seeded': int((geo == 0).sum()), 'unreached': int(unseeded.sum())}
report = {**report_seed, 'rigid_armour': rigid_count, 'torso_redistributed': torso_redistributed, 'neck_seam_unified': seam_unified, 'arm_bleed_moved_to_chest': bled, 'bones': len(rig.data.bones), 'frame_error_deg': err, 'pieces_copied': copied, 'finger_vertices': finger_verts,
          'head_only_above_jaw': cleared, 'unweighted': unweighted,
          'queen_triangles': sum(len(p.vertices) - 2 for p in me.polygons),
          'rock_triangles': sum(len(p.vertices) - 2 for p in rock.data.polygons)}
print('WEIGHTS', json.dumps(report))
(P / 'work' / 'rig.json').write_text(json.dumps(report, indent=1))
bpy.context.scene['rig_offsets'] = json.dumps({n: {'q': list(swing[n]), 'R_src': [list(r) for r in SRC[n]['rot']]}
                                              for n in order})
PLACE['queen_actor_location'] = list(OFF)
(P / 'work' / 'placement.json').write_text(json.dumps(PLACE, indent=1))
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work' / 'rig_v1.blend'))
