"""Manticore rig (quadruped playbook; adapted from mm7_m258_claude/scripts/rig_griffin.py): joints measured on the mesh
(work/joints.json: leg sections, tail-piece junctions), forward -Y, up +Z, character left +X.
Bones: Spine1 (hips, root) - Spine2 - Spine3 (chest) - Neck1 - Head; Tail1..6 (Spine1; Tail1 = the skin tail base,
Tail2..6 = the five chitin segment pieces, stinger last); per side UpperArm/ForeArm/FrontPaw (Spine3) and
Thigh/Shin/HindPaw (Spine1).
Weights:
- body skin: heat weights on a hole-filled voxel proxy of the skin (Tail2..6 non-deforming), Data Transfer back;
- tail segments: each chitin piece 100 % on its own bone (exoskeleton rule, mm6_spi1_claude), Tail1 on the skin;
- mane shingles copy the skin under them (4 nearest skin vertices, inverse distance), averaged half per shingle;
- claws and other small pieces copy the skin under them; teeth and eyes in the face are rigid on Head.
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
skin = np.where(pv == 0)[0]


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
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[lay] != 0], context='VERTS')
bmesh.ops.holes_fill(bm, edges=bm.edges, sides=0)
bm.to_mesh(pm); bm.free()
r = proxy.modifiers.new('Remesh', 'REMESH'); r.mode = 'VOXEL'; r.voxel_size = VOXEL
deps = bpy.context.evaluated_depsgraph_get()
rm = bpy.data.meshes.new_from_object(proxy.evaluated_get(deps)); proxy.modifiers.clear(); proxy.data = rm
for b in ad.bones:
    b.use_deform = b.name not in J['tail_pieces']
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
W[pv != 0] = 0
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


# ---------------------------------------------------------------- pieces
kd = KDTree(len(skin))
for i, sv in enumerate(skin):
    kd.insert(co[sv], i)
kd.balance()
TP = {v: k for k, v in J['tail_pieces'].items()}
hj = np.array(CH['Head'][0])
nmane = 0
for p in range(1, pv.max() + 1):
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
