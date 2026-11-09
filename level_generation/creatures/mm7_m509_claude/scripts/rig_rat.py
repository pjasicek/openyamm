"""MM7 rat rig (quadruped playbook; adapted from mm7_m278_claude/scripts/rig_manticore.py, after mm6_rat_claude):
joints measured on the mesh (work/joints.json), forward -Y, up +Z, character left +X.
Bones: Spine1 (hips, root) - Spine2 - Spine3 (chest) - Neck1 - Head; Tail1..6 (Spine1); per side
UpperArm/ForeArm/FrontPaw (Spine3) and Thigh/Shin/HindPaw (Spine1).
Weights: heat weights on a hole-filled voxel proxy of the six large pieces (Smart Topology split the head, the body
shells, legs and tail into separate pieces; the voxel remesh fuses them), Data Transfer back (the naked tail is skin, so it
takes heat weights along its chain); fur cards and small pieces copy the skin under them; teeth and eyes in the
face are rigid on Head.
Writes work/rig_v1.blend (Rig, Body). Args: none"""
import bpy, bmesh, os, sys, math, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOXEL = float(os.environ.get('VOXEL', '0.022'))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'step1.blend'))
body = bpy.data.objects['Body']; me = body.data
V = Vector
J = json.load(open(os.path.join(HERE, 'work', 'joints.json')))
CH = {k: [V(p) for p in v] for k, v in J['chains'].items()}
NAMES = {'Spine': ['Spine1', 'Spine2', 'Spine3'], 'Neck': ['Neck1'], 'Head': ['Head'],
         'Tail': [f'Tail{i}' for i in range(1, 7)]}
PARENT = {'Spine': None, 'Neck': 'Spine3', 'Head': 'Neck1', 'Tail': 'Spine1'}
for s in 'LR':
    NAMES[f'Front_{s}'] = [f'UpperArm_{s}', f'ForeArm_{s}', f'FrontPaw_{s}']; PARENT[f'Front_{s}'] = 'Spine3'
    NAMES[f'Hind_{s}'] = [f'Thigh_{s}', f'Shin_{s}', f'HindPaw_{s}']; PARENT[f'Hind_{s}'] = 'Spine1'
co = np.array([tuple(v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
BIG = [int(p) for p in np.unique(pv) if (pv == p).sum() > int(os.environ.get('BIG_MIN', '150'))]   # m509: 1000 (one shell; eyes 150-190 verts)
skin = np.where(np.isin(pv, BIG))[0]


ad = bpy.data.armatures.new('Rig'); rig = bpy.data.objects.new('Rig', ad)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = ad.edit_bones
for key in ['Spine', 'Neck', 'Head', 'Tail', 'Front_L', 'Front_R', 'Hind_L', 'Hind_R']:
    pts = CH[key]; prev = eb[PARENT[key]] if PARENT[key] else None
    for i, n in enumerate(NAMES[key]):
        b = eb.new(n); b.head = pts[i]; b.tail = pts[i + 1]
        if key in ('Spine', 'Neck', 'Head', 'Tail'):
            b.align_roll(V((0, 0, 1)))
        else:
            b.align_roll(V((0, -1, 0)))
        b.parent = prev; b.use_connect = prev is not None and i > 0
        prev = b
bpy.ops.object.mode_set(mode='OBJECT')
names = [b.name for b in ad.bones]

# ---------------------------------------------------------------- body: heat weights on a voxel proxy
pm = me.copy(); proxy = bpy.data.objects.new('Proxy', pm); bpy.context.scene.collection.objects.link(proxy)
bm = bmesh.new(); bm.from_mesh(pm); lay = bm.verts.layers.int.get('piece')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[lay] not in BIG], context='VERTS')
bmesh.ops.holes_fill(bm, edges=bm.edges, sides=0)
bm.to_mesh(pm); bm.free()
r = proxy.modifiers.new('Remesh', 'REMESH'); r.mode = 'VOXEL'; r.voxel_size = VOXEL
deps = bpy.context.evaluated_depsgraph_get()
rm = bpy.data.meshes.new_from_object(proxy.evaluated_get(deps)); proxy.modifiers.clear(); proxy.data = rm
for b in ad.bones:
    b.use_deform = b.name not in J.get('tail_pieces', {})
for o in bpy.data.objects:
    o.select_set(o in (proxy, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
pw = np.array([sum(g.weight for g in v.groups) for v in rm.vertices])
print('RIG proxy verts', len(rm.vertices), 'unweighted', int((pw < 1e-6).sum()), 'voxel', VOXEL)
for b in ad.bones:
    b.use_deform = True
body.vertex_groups.clear()
for n in names:
    body.vertex_groups.new(name=n)
dt = body.modifiers.new('DT', 'DATA_TRANSFER'); dt.object = proxy
dt.use_vert_data = True; dt.data_types_verts = {'VGROUP_WEIGHTS'}; dt.vert_mapping = 'POLYINTERP_NEAREST'
dt.layers_vgroup_select_src = 'ALL'; dt.layers_vgroup_select_dst = 'NAME'
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.ops.object.modifier_apply(modifier='DT')
gi = {g.name: g.index for g in body.vertex_groups}
W = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight
W[~np.isin(pv, BIG)] = 0
bpy.data.objects.remove(proxy, do_unlink=True)


def chain_weights(pts, bones, p, blend):
    """weights along a polyline chain for point p: closest segment, blended across joints"""
    best = None
    for i in range(len(bones)):
        a, b = np.array(pts[i]), np.array(pts[i + 1]); L = np.linalg.norm(b - a)
        t = np.clip((p - a) @ (b - a) / L / L, 0, 1)
        d = np.linalg.norm(p - (a + (b - a) * t))
        if best is None or d < best[0]:
            best = (d, i, t * L, L)
    _, i, s, L = best
    w = np.zeros(len(bones)); w[i] = 1.0
    if i > 0 and s < blend:
        k = 0.5 * (1 - s / blend); w[i] -= k; w[i - 1] += k
    if i < len(bones) - 1 and s > L - blend:
        k = 0.5 * (1 - (L - s) / blend); w[i] -= k; w[i + 1] += k
    return w


# ---------------------------------------------------------------- lower legs by their own chain
# The 2.2 cm voxel proxy fuses the thin lower legs and feet (finer voxels made the heat solver fail): a left hind foot
# took right-shin weight (a 57x edge stretch). Below LOW_Z every skin vertex within 15 cm of a leg chain is weighted
# along that chain (closest segment, 3 cm joint blend), faded back into the heat weights between LOW_Z - 6 cm and LOW_Z.
LOW_Z = 0.28
LEGCH = {f'Front_{s}': [f'UpperArm_{s}', f'ForeArm_{s}', f'FrontPaw_{s}'] for s in 'LR'}
LEGCH.update({f'Hind_{s}': [f'Thigh_{s}', f'Shin_{s}', f'HindPaw_{s}'] for s in 'LR'})


def seg_dist(pts, p):
    best = 9.0
    for i in range(len(pts) - 1):
        a, b = np.array(pts[i]), np.array(pts[i + 1]); L2 = float((b - a) @ (b - a))
        t = np.clip((p - a) @ (b - a) / L2, 0, 1); best = min(best, float(np.linalg.norm(p - (a + (b - a) * t))))
    return best


nfix = 0
for i in skin:
    if co[i, 2] > LOW_Z:
        continue
    d = {k: seg_dist([np.array(x) for x in CH[k]], co[i]) for k in LEGCH}
    k = min(d, key=d.get)
    if d[k] > 0.15 or seg_dist([np.array(x) for x in CH['Tail']], co[i]) < d[k]:   # the tail lies beside the hind foot
        continue
    wv = np.zeros(len(names))
    wv[[gi[b] for b in LEGCH[k]]] = chain_weights([np.array(x) for x in CH[k]], LEGCH[k], co[i], 0.03)
    f = np.clip((LOW_Z - co[i, 2]) / 0.06, 0, 1)
    W[i] = W[i] * (1 - f) + wv * f; nfix += 1
print('RIG lower-leg vertices weighted by their chain', nfix)

# tail root: the naked tail grows out of the rump between the thighs and lies beside the left hock; its border with
# the thigh/shin weights stretched 12-14x when the tail swayed. 6 passes of neighbour averaging within 0.22 m of the
# tail root spread that border.
adj = [[] for _ in range(nv)]
for e in me.edges:
    a_, b_ = e.vertices; adj[a_].append(b_); adj[b_].append(a_)
root = np.array(CH['Tail'][1])
near = skin[np.linalg.norm(co[skin] - root, axis=1) < 0.22]
for _ in range(6):
    Ws = W.copy()
    for i in near:
        if adj[i]:
            Ws[i] = 0.5 * W[i] + 0.5 * W[adj[i]].mean(0)
    W = Ws
print('RIG tail-root weights smoothed on', len(near), 'vertices')

# ---------------------------------------------------------------- pieces
kd = KDTree(len(skin))
for i, sv in enumerate(skin):
    kd.insert(co[sv], i)
kd.balance()
TP = {v: k for k, v in J.get('tail_pieces', {}).items()}
hj = np.array(CH['Head'][0])
nmane = 0
for p in range(1, pv.max() + 1):
    if p in BIG:
        continue
    idx = np.where(pv == p)[0]; c = co[idx].mean(0); size = (co[idx].max(0) - co[idx].min(0)).max()
    W[idx] = 0
    if p in TP:                                                           # chitin tail segment: rigid
        W[idx, gi[TP[p]]] = 1.0
        continue
    if size < 0.06 and c[1] < hj[1] - 0.1 and c[2] > 0.85:                 # teeth, eyes in the face
        W[idx, gi['Head']] = 1.0
        continue
    for i in idx:
        hits = kd.find_n(co[i], 4); w = np.array([1.0 / max(h[2], 1e-4) for h in hits])
        W[i] = (w[:, None] * W[[skin[h[1]] for h in hits]]).sum(0) / w.sum()
    W[idx] = 0.5 * W[idx] + 0.5 * W[idx].mean(0)
    nmane += 1
print('RIG pieces copied from skin', nmane, 'tail pieces', len(TP))
# unweighted spots: nearest weighted vertex
good = np.where(W.sum(1) > 0.5)[0]; lost = np.where(W.sum(1) <= 0.5)[0]
if len(lost):
    kg = KDTree(len(good))
    for i, g in enumerate(good):
        kg.insert(co[g], i)
    kg.balance()
    for i in lost:
        W[i] = W[good[kg.find(co[i])[1]]]
top = np.argsort(-W, 1)[:, :4]; W2 = np.zeros_like(W); rows = np.arange(nv)[:, None]
W2[rows, top] = W[rows, top]; W2 /= np.maximum(W2.sum(1, keepdims=True), 1e-9)
for g in body.vertex_groups:
    g.remove(list(range(nv)))
for j, n in enumerate(names):
    nz = np.nonzero(W2[:, j] > 1e-4)[0]
    for i in nz:
        body.vertex_groups[n].add([int(i)], float(W2[i, j]), 'REPLACE')
print('RIG bones', len(names), 'filled spots', len(lost))
body.parent = rig
m = body.modifiers.new('Armature', 'ARMATURE'); m.object = rig
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
