"""Hydra rig (quadruped playbook + multi-headed notes; after mm7_m278_claude/scripts/rig_manticore.py and
mm6_hyd_claude/scripts/rig_hyd.py). Forward -Y, up +Z, character left +X; necks numbered 1..5 from the hydra's right
to its left (x ascending), as the HD masters number the heads.
Joints: work/joints_med.json (draft from leg/neck sections, refined onto the medial axis by medial.py).
Bones: Spine1 (hips, root) - Spine2 - Spine3 (chest); Tail1..8 (Spine1); per side UpperArm/ForeArm/FrontPaw (Spine3) and
Thigh/Shin/HindPaw (Spine1); per neck Neck<k>_00.. and Head<k> (the last HEAD_LEN m of the chain), parented to Spine3.
Cleanup first: the old heads' loose pieces (crest spikes, teeth, fins and the long sliver webs between the heads;
work/old_head_pieces.json) are deleted; the graft replaces the heads.
Weights:
- skin (piece 0) and neck 1 (piece 1, a separate shell): heat weights on a hole-filled voxel proxy of both, Data
  Transfer back;
- every vertex then keeps only bones of its own chain group: a vertex owned (geodesically, from seeds on each neck's
  upper half and on the body) by neck k keeps neck k + Spine3; body vertices drop all neck bones except the lowest two
  of each neck (heat weights leak between the five tightly packed necks);
- loose pieces (dorsal and tail spikes) copy the skin under them, averaged half per piece (rigid-ish).
Writes work/rig_v1.blend (Rig, Body) and work/rig.json (chains: [body placeholder, neck 1..5, ...]; names, joints,
radius, parent) for graft_heads.py and the clips. Args: none (env VOXEL)"""
import bpy, bmesh, os, sys, math, json, heapq
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOXEL = float(os.environ.get('VOXEL', '0.022'))
HEAD_LEN = 0.16
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'step1.blend'))
body = bpy.data.objects['Body']; me = body.data
J = json.load(open(os.path.join(HERE, 'work', 'joints_med.json')))['chains']
DROP = set(json.load(open(os.path.join(HERE, 'work', 'old_head_pieces.json')))['old_head_pieces'])

# ---------------------------------------------------------------- cleanup: old head pieces
bm = bmesh.new(); bm.from_mesh(me); lay = bm.verts.layers.int.get('piece')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[lay] in DROP], context='VERTS')
bm.to_mesh(me); bm.free(); me.update()
co = np.array([tuple(v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
SKIN = np.isin(pv, (0, 1))
print('CLEAN dropped', len(DROP), 'pieces; verts', nv)


def resample(P, seg, head_len=0.0):
    P = np.array(P); arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    end = arc[-1] - head_len; n = max(1, int(round(end / seg)))
    s = np.linspace(0, end, n + 1)
    if head_len:
        s = np.append(s, arc[-1])
    return np.stack([np.interp(s, arc, P[:, i]) for i in range(3)], 1)


V = Vector
CH = {k: [np.array(p) for p in J[k]] for k in ('Spine', 'Tail', 'Front_L', 'Front_R', 'Hind_L', 'Hind_R')}
ST = np.load(os.path.join(HERE, 'work', 'step1_mesh.npz')); SKV = ST['co'][np.isin(ST['piece'], (0, 1))]
for k in range(1, 6):
    # the neck trace can climb into the old crest (neck 3): end every chain at the old snout (most forward skin
    # vertex near the trace's upper third), dropping trace points within HEAD_LEN of it or above it
    P = np.array(J[f'N{k}']); end = P[-max(3, len(P) // 3):]
    reg = SKV[np.min(np.linalg.norm(SKV[:, None] - end[None], axis=2), 1) < 0.2]
    reg = reg[reg[:, 2] > P[len(P) // 2, 2]]
    snout = reg[np.argmin(reg[:, 1])]
    keep = [i for i in range(len(P)) if np.linalg.norm(P[i] - snout) > HEAD_LEN and
            (i < len(P) // 2 or P[i, 2] < snout[2] + 0.1)]
    P = np.vstack([P[:keep[-1] + 1], snout])
    CH[f'N{k}'] = list(resample(P, 0.13, HEAD_LEN))
NAMES = {'Spine': ['Spine1', 'Spine2', 'Spine3'], 'Tail': [f'Tail{i}' for i in range(1, len(CH['Tail']))]}
PARENT = {'Spine': None, 'Tail': 'Spine1'}
for s in 'LR':
    NAMES[f'Front_{s}'] = [f'UpperArm_{s}', f'ForeArm_{s}', f'FrontPaw_{s}']; PARENT[f'Front_{s}'] = 'Spine3'
    NAMES[f'Hind_{s}'] = [f'Thigh_{s}', f'Shin_{s}', f'HindPaw_{s}']; PARENT[f'Hind_{s}'] = 'Spine1'
for k in range(1, 6):
    n = len(CH[f'N{k}']) - 1
    NAMES[f'N{k}'] = [f'Neck{k}_{i:02d}' for i in range(n - 1)] + [f'Head{k}']; PARENT[f'N{k}'] = 'Spine3'
ORDER = ['Spine', 'Tail', 'Front_L', 'Front_R', 'Hind_L', 'Hind_R'] + [f'N{k}' for k in range(1, 6)]

ad = bpy.data.armatures.new('Rig'); rig = bpy.data.objects.new('Rig', ad)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = ad.edit_bones
for key in ORDER:
    pts = CH[key]; prev = eb[PARENT[key]] if PARENT[key] else None
    for i, n in enumerate(NAMES[key]):
        b = eb.new(n); b.head = V(pts[i]); b.tail = V(pts[i + 1])
        b.align_roll(V((0, -1, 0)) if key.startswith(('Front', 'Hind')) else V((0, 0, 1)) if not key.startswith('N')
                     else V((1, 0, 0)))
        b.parent = prev; b.use_connect = False
        prev = b
bpy.ops.object.mode_set(mode='OBJECT')
names = [b.name for b in ad.bones]
gi = {n: i for i, n in enumerate(names)}

# ---------------------------------------------------------------- heat weights on a voxel proxy (skin + neck 1)
pm = me.copy(); proxy = bpy.data.objects.new('Proxy', pm); bpy.context.scene.collection.objects.link(proxy)
bm = bmesh.new(); bm.from_mesh(pm); lay = bm.verts.layers.int.get('piece')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[lay] not in (0, 1)], context='VERTS')
bmesh.ops.holes_fill(bm, edges=bm.edges, sides=0)
bm.to_mesh(pm); bm.free()
r = proxy.modifiers.new('Remesh', 'REMESH'); r.mode = 'VOXEL'; r.voxel_size = VOXEL
deps = bpy.context.evaluated_depsgraph_get()
rm = bpy.data.meshes.new_from_object(proxy.evaluated_get(deps)); proxy.modifiers.clear(); proxy.data = rm
for o in bpy.data.objects:
    o.select_set(o in (proxy, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
pw = np.array([sum(g.weight for g in v.groups) for v in rm.vertices])
print('RIG proxy verts', len(rm.vertices), 'unweighted', int((pw < 1e-6).sum()), 'voxel', VOXEL)
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
W = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight
W[~SKIN] = 0
bpy.data.objects.remove(proxy, do_unlink=True)

# ---------------------------------------------------------------- chain ownership (geodesic from seeds)
adj = [[] for _ in range(nv)]
for e in me.edges:
    a, b = e.vertices; adj[a].append(b); adj[b].append(a)
# neck 1 is its own shell: join it to the skin vertices it touches, so the geodesic flood can cross
sk = np.nonzero(pv == 0)[0]; kd0 = KDTree(len(sk))
for i, v in enumerate(sk):
    kd0.insert(co[v], i)
kd0.balance()
for v in np.nonzero(pv == 1)[0]:
    _, j, d = kd0.find(co[v])
    if d < 0.03:
        adj[v].append(int(sk[j])); adj[int(sk[j])].append(int(v))


def seg_dist(P, x):
    best = np.full(len(x), 1e9)
    for a, b in zip(P[:-1], P[1:]):
        d = b - a; t = np.clip(((x - a) @ d) / (d @ d), 0, 1)
        best = np.minimum(best, np.linalg.norm(x - (a + t[:, None] * d), axis=1))
    return best


seeds = []
for k in range(1, 6):
    P = np.array(CH[f'N{k}'])
    upper = P[len(P) // 3:]
    dk = seg_dist(upper, co)
    others = np.min([seg_dist(np.array(CH[f'N{j}'])[len(CH[f'N{j}']) // 3:], co) for j in range(1, 6) if j != k], 0)
    seeds.append(np.nonzero(SKIN & (dk < 0.16) & (dk < others - 0.02))[0])
seeds.insert(0, np.nonzero(SKIN & (co[:, 2] < 0.75) & (co[:, 1] > -0.4))[0])          # body: hips, belly, legs, tail
dist = np.full(nv, np.inf); owner = np.full(nv, -1); heap = []
for lab, s in enumerate(seeds):
    heap += [(0.0, int(v), lab) for v in s]
heapq.heapify(heap)
while heap:
    d, v, lab = heapq.heappop(heap)
    if d >= dist[v]:
        continue
    dist[v] = d; owner[v] = lab
    for b in adj[v]:
        nd = d + float(np.linalg.norm(co[b] - co[v]))
        if nd < dist[b]:
            heapq.heappush(heap, (nd, b, lab))
neck_of = {n: k for k in range(1, 6) for n in NAMES[f'N{k}']}
low_neck = {n for k in range(1, 6) for n in NAMES[f'N{k}'][:2]}
cols = np.array([neck_of.get(n, 0) for n in names])
for v in np.nonzero(SKIN)[0]:
    o = owner[v]
    if o > 0:
        W[v, (cols != o) & (cols != 0)] = 0                    # neck k vertex: only neck k and body bones
        W[v, (cols == 0) & ~np.isin(names, ['Spine3', 'Spine2'])] *= 0.0 if co[v, 2] > 1.0 else 1.0
    elif o == 0:
        keep = np.array([n in low_neck for n in names])
        W[v, (cols != 0) & ~keep] = 0
print('RIG owners', {lab: int((owner == lab).sum()) for lab in range(6)})

# ---------------------------------------------------------------- loose pieces copy the skin under them
skin_idx = np.nonzero(SKIN)[0]
kd = KDTree(len(skin_idx))
for i, sv in enumerate(skin_idx):
    kd.insert(co[sv], i)
kd.balance()
npieces = 0
for p in np.unique(pv[~SKIN]):
    idx = np.where(pv == p)[0]
    for i in idx:
        hits = kd.find_n(co[i], 4); w = np.array([1.0 / max(h[2], 1e-4) for h in hits])
        W[i] = (w[:, None] * W[[skin_idx[h[1]] for h in hits]]).sum(0) / w.sum()
    W[idx] = 0.5 * W[idx] + 0.5 * W[idx].mean(0); npieces += 1
good = np.where(W.sum(1) > 0.3)[0]; lost = np.where(W.sum(1) <= 0.3)[0]
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
    for i in np.nonzero(W2[:, j] > 1e-4)[0]:
        body.vertex_groups[n].add([int(i)], float(W2[i, j]), 'REPLACE')
print('RIG bones', len(names), 'pieces copied', npieces, 'filled', len(lost))
body.parent = rig
m = body.modifiers.new('Armature', 'ARMATURE'); m.object = rig
own_attr = me.attributes.new('chain_owner', 'INT', 'POINT'); own_attr.data.foreach_set('value', np.maximum(owner, 0).astype(np.int32))


# rig.json: chain list compatible with graft_heads.py (index k = neck k); radius = clearance per joint
def radius(P):
    out = []
    for p in P:
        dd = np.linalg.norm(co[SKIN] - p, axis=1); out.append(float(np.percentile(dd[dd < 0.4], 5)) if (dd < 0.4).any() else 0.05)
    return out


chains = [{'names': NAMES['Spine'], 'joints': np.array(CH['Spine']).round(5).tolist(), 'radius': radius(CH['Spine']),
           'parent': None}]
for k in range(1, 6):
    P = np.array(CH[f'N{k}'])
    chains.append({'names': NAMES[f'N{k}'], 'joints': P.round(5).tolist(), 'radius': radius(P), 'parent': 'Spine3'})
for key in ('Tail', 'Front_L', 'Front_R', 'Hind_L', 'Hind_R'):
    chains.append({'names': NAMES[key], 'joints': np.array(CH[key]).round(5).tolist(), 'radius': radius(CH[key]),
                   'parent': PARENT[key]})
json.dump({'chains': chains}, open(os.path.join(HERE, 'work', 'rig.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
print('SAVED rig_v1')
