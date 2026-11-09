"""Griffin rig (quadruped playbook, flyer): joints measured on the mesh (grid_plot.py / hsections.py sections and the
wing leading edges, README "Rig"), forward -Y, up +Z, character left +X.
Bones: Spine1 (hips, root) - Spine2 - Spine3 (chest) - Neck1 - Neck2 - Head; Tail1..5 (Spine1);
per side UpperArm/ForeArm/FrontPaw (eagle leg, Spine3), Thigh/Shin/HindPaw (lion leg, Spine1),
Wing1/Wing2/Wing3 (humerus, forearm, hand + primaries; Spine3). Wing bones roll so their local Z is the wing sheet's
normal (the clips aim each wing by direction + sheet normal, so the asymmetric rest wings move as one pose).
Weights:
- body skin: heat weights on a hole-filled voxel proxy of the skin (wing bones non-deforming), Data Transfer back;
- wings (skin with |x| > WING_X and z > 1.12): by the closest point on the wing chain (shoulder-elbow-wrist-tip),
  blended over +-6 cm at each joint, faded into the body weights between |x| 0.42 and WING_X;
- eagle legs (separate pieces): rigid by the leg chain (ForeArm above the ankle, FrontPaw beyond, 4 cm blend);
- tail tuft pieces rigid on Tail5; eyes rigid on Head; other small pieces copy the nearest skin vertex.
Writes work/rig_v1.blend (Rig, Body). Args: none"""
import bpy, bmesh, os, sys, math, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOXEL = float(os.environ.get('VOXEL', '0.022'))
WING_X = 0.55
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'step1.blend'))
body = bpy.data.objects['Body']; me = body.data
V = Vector
J = json.load(open(os.path.join(HERE, 'work', 'joints.json')))
CH = {k: [V(p) for p in v] for k, v in J['chains'].items()}
NAMES = {'Spine': ['Spine1', 'Spine2', 'Spine3'], 'Neck': ['Neck1', 'Neck2'], 'Head': ['Head'],
         'Tail': [f'Tail{i}' for i in range(1, 6)]}
PARENT = {'Spine': None, 'Neck': 'Spine3', 'Head': 'Neck2', 'Tail': 'Spine1'}
for s in 'LR':
    NAMES[f'Front_{s}'] = [f'UpperArm_{s}', f'ForeArm_{s}', f'FrontPaw_{s}']; PARENT[f'Front_{s}'] = 'Spine3'
    NAMES[f'Hind_{s}'] = [f'Thigh_{s}', f'Shin_{s}', f'HindPaw_{s}']; PARENT[f'Hind_{s}'] = 'Spine1'
    NAMES[f'Wing_{s}'] = [f'Wing1_{s}', f'Wing2_{s}', f'Wing3_{s}']; PARENT[f'Wing_{s}'] = 'Spine3'
co = np.array([tuple(v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
skin = np.where(pv == 0)[0]


def sheet_normal(a, b):
    """normal of the wing sheet around segment a-b (PCA of the skin vertices within the segment's slab)"""
    a, b = np.array(a), np.array(b); d = (b - a) / np.linalg.norm(b - a)
    t = (co[skin] - a) @ d / np.linalg.norm(b - a)
    sel = co[skin][(t > 0) & (t < 1) & (np.linalg.norm(np.cross(co[skin] - a, d), axis=1) < 0.6)]
    c = sel.mean(0); n = np.linalg.svd(sel - c)[2][2]
    return V(n if n[2] > 0 else -n)


ad = bpy.data.armatures.new('Rig'); rig = bpy.data.objects.new('Rig', ad)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = ad.edit_bones
for key in ['Spine', 'Neck', 'Head', 'Tail', 'Front_L', 'Front_R', 'Hind_L', 'Hind_R', 'Wing_L', 'Wing_R']:
    pts = CH[key]; prev = eb[PARENT[key]] if PARENT[key] else None
    for i, n in enumerate(NAMES[key]):
        b = eb.new(n); b.head = pts[i]; b.tail = pts[i + 1]
        if key.startswith('Wing'):
            b.align_roll(sheet_normal(pts[i], pts[i + 1]))
        elif key in ('Spine', 'Neck', 'Head', 'Tail'):
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
    b.use_deform = not b.name.startswith('Wing')
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


# ---------------------------------------------------------------- wings
for s, sg in (('L', 1), ('R', -1)):
    pts = [np.array(p) for p in CH[f'Wing_{s}']]; bones = NAMES[f'Wing_{s}']
    m = (co[:, 0] * sg > 0.42) & (co[:, 2] > 1.12) & (pv == 0)
    n = 0
    for i in np.where(m)[0]:
        wv = np.zeros(len(names))
        wv[[gi[b] for b in bones]] = chain_weights(pts, bones, co[i], 0.06)
        f = np.clip((co[i, 0] * sg - 0.42) / (WING_X - 0.42), 0, 1)
        W[i] = W[i] * (1 - f) + wv * f; n += 1
    print('RIG wing', s, 'vertices', n)

# smoothing over mesh edges inside the wings: the closest-segment rule put neighbouring trailing feathers on different
# wing bones with no blend (a 20x edge stretch); 8 passes of neighbour averaging on the wing vertices
adj = [[] for _ in range(nv)]
for e in me.edges:
    a, b = e.vertices; adj[a].append(b); adj[b].append(a)
wing_v = np.where((np.abs(co[:, 0]) > 0.45) & (co[:, 2] > 1.12) & (pv == 0))[0]
for _ in range(8):
    W2s = W.copy()
    for i in wing_v:
        if adj[i]:
            W2s[i] = 0.5 * W[i] + 0.5 * W[adj[i]].mean(0)
    W = W2s
print('RIG wing weights smoothed on', len(wing_v), 'vertices')

# ---------------------------------------------------------------- pieces
kd = KDTree(len(skin))
for i, sv in enumerate(skin):
    kd.insert(co[sv], i)
kd.balance()
for p in range(1, pv.max() + 1):
    idx = np.where(pv == p)[0]; c = co[idx].mean(0); size = (co[idx].max(0) - co[idx].min(0)).max()
    W[idx] = 0
    if size > 0.3 and c[1] < -0.5 and c[2] < 1.1:                       # an eagle foreleg
        s = 'L' if c[0] > 0 else 'R'; pts = [np.array(x) for x in CH[f'Front_{s}']]
        bones = NAMES[f'Front_{s}']
        for i in idx:
            W[i, [gi[b] for b in bones]] = chain_weights(pts, bones, co[i], 0.04)
        print('RIG foreleg piece', p, s, len(idx))
    elif c[1] > 1.0:                                                      # tail tuft clumps
        W[idx, gi['Tail5']] = 1.0
    elif size < 0.05 and c[1] < -0.8 and c[2] > 1.5:                      # eyes
        W[idx, gi['Head']] = 1.0
    else:
        for i in idx:
            W[i] = W[skin[kd.find(co[i])[1]]]
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
