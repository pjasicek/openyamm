"""Behemoth skin weights (replaces the Meshy weight transfer of the gob2/natm route).
1. Heat weights on a watertight proxy: the skin piece (piece 0) voxel-remeshed (VOXEL m; 0.015 and 0.03 made the heat solver fail for every vertex, 0.022 solves) and bound with Blender's
   automatic weights to the deforming bones (fingers set non-deforming: the claws ride on the hand), copied back to
   the skin by Data Transfer (nearest face interpolated). Meshy meshes have open seams that make heat weights fail on
   the original surface (cockatrice, mm6_ckt_claude).
2. Hands: every skin vertex distal to the wrist plane that is connected (through the mesh, inside 0.8 m and on that
   side) to the hand is 100 % on B_<s>_Hand, so no claw tip takes leg weight from the nearby knees.
3. Other pieces (scripts/inspect_mesh.py lists them): small pieces in the face (teeth, tusks, eyes) are rigid on
   B_Head; everything else (mane shingles) copies the skin under it (4 nearest skin vertices, inverse distance) with
   the arm share capped at 0.25 (excess to the clavicle) and is then averaged per piece so no shingle tears.
4. At most 4 influences, normalised.
Args: -- <in blend> <out blend>"""
import bpy, bmesh, sys, os
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
src, out = sys.argv[sys.argv.index('--') + 1:]
VOXEL = float(os.environ.get('VOXEL', '0.022'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
skin = np.where(pv == 0)[0]

# ---------------------------------------------------------------- 1. proxy heat weights
pm = me.copy(); proxy = bpy.data.objects.new('Proxy', pm); bpy.context.scene.collection.objects.link(proxy)
proxy.matrix_world = body.matrix_world.copy()
bm = bmesh.new(); bm.from_mesh(pm)
lay = bm.verts.layers.int.get('piece')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[lay] != 0], context='VERTS')
bmesh.ops.holes_fill(bm, edges=bm.edges, sides=0)                 # 9 open edges stop the voxel remesh
bm.to_mesh(pm); bm.free()
pm.attributes.remove(pm.attributes['piece']) if 'piece' in pm.attributes else None
proxy.vertex_groups.clear(); proxy.modifiers.clear()
r = proxy.modifiers.new('Remesh', 'REMESH'); r.mode = 'VOXEL'; r.voxel_size = VOXEL; r.adaptivity = 0.0
deps = bpy.context.evaluated_depsgraph_get()
rm = bpy.data.meshes.new_from_object(proxy.evaluated_get(deps))
proxy.modifiers.clear(); proxy.data = rm; pm = rm
print('WEIGHTS proxy verts', len(pm.vertices), 'voxel', VOXEL)
deform = {}
for b in rig.data.bones:
    deform[b.name] = b.use_deform
    b.use_deform = 'Finger' not in b.name
for o in bpy.data.objects:
    o.select_set(o in (proxy, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
pw = np.zeros(len(pm.vertices))
for v in pm.vertices:
    pw[v.index] = sum(g.weight for g in v.groups)
print('WEIGHTS proxy unweighted verts', int((pw < 1e-6).sum()), 'of', len(pw))
for b in rig.data.bones:
    b.use_deform = deform[b.name]
names = [b.name for b in rig.data.bones]
body.vertex_groups.clear()
for n in names:
    body.vertex_groups.new(name=n)
dt = body.modifiers.new('DT', 'DATA_TRANSFER'); dt.object = proxy
dt.use_vert_data = True; dt.data_types_verts = {'VGROUP_WEIGHTS'}; dt.vert_mapping = 'POLYINTERP_NEAREST'
dt.layers_vgroup_select_src = 'ALL'; dt.layers_vgroup_select_dst = 'NAME'
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects:
    o.select_set(o == body)
while body.modifiers[0].name != 'DT':
    bpy.ops.object.modifier_move_up(modifier='DT')
bpy.ops.object.modifier_apply(modifier='DT')
gi = {g.name: g.index for g in body.vertex_groups}
W = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight
W[pv != 0] = 0.0                                               # only the skin takes the proxy weights
J = lambda n: np.array(rig.data.bones[n].head_local)

# ---------------------------------------------------------------- 2. hands (connected, distal to the wrist)
adj = [[] for _ in range(nv)]
for e in me.edges:
    a, b = e.vertices; adj[a].append(b); adj[b].append(a)
for s in ('L', 'R'):
    wr, el = J(f'B_{s}_Hand'), J(f'B_{s}_Forearm')
    ax = (wr - el) / np.linalg.norm(wr - el)
    cand = np.zeros(nv, bool)
    cand[skin] = (((co[skin] - wr) @ ax) > 0.0) & (np.linalg.norm(co[skin] - wr, axis=1) < 0.8)
    seed = skin[np.argmin(np.linalg.norm(co[skin] - (wr + ax * 0.08), axis=1))]
    hand = np.zeros(nv, bool); hand[seed] = True; stack = [seed]
    while stack:
        x = stack.pop()
        for y in adj[x]:
            if cand[y] and not hand[y]:
                hand[y] = True; stack.append(y)
    # blend band: 3 cm on either side of the wrist plane keeps the proxy's forearm/hand mix
    d = (co[hand] - wr) @ ax
    k = np.clip((d - 0.0) / 0.04, 0, 1)[:, None]
    tgt = np.zeros(len(names)); tgt[gi[f'B_{s}_Hand']] = 1.0
    W[hand] = W[hand] * (1 - k) + tgt * k
    legw = W[hand][:, [gi[n] for n in names if any(t in n for t in ('Thigh', 'Calf', 'Foot', 'Toe'))]].sum()
    print('WEIGHTS hand', s, 'verts', int(hand.sum()), 'max reach m', round(float(d.max()), 3),
          'residual leg weight', round(float(legw), 4))

# ---------------------------------------------------------------- 2b. head skin: head/neck only (gob2 rule: no clavicle or
# arm weight on the jaw; the ears stick out toward the shoulders and took clavicle weight: a 100x edge stretch)
hj0 = J('B_Head')
hd = skin[(co[skin][:, 1] < hj0[1] + 0.02) & (co[skin][:, 2] > 1.15)]
keep = [gi['B_Head'], gi['B_Neck']]
share = W[np.ix_(hd, keep)].sum(1)
newW = np.zeros((len(hd), len(names)))
newW[:, keep] = np.where(share[:, None] > 0.05, W[np.ix_(hd, keep)] / np.maximum(share[:, None], 1e-9), [1.0, 0.0])
moved = float((1 - share).clip(0).sum())
W[hd] = newW
print('WEIGHTS head region verts', len(hd), 'non-head weight removed (vertex sum)', round(moved, 1))
# ---------------------------------------------------------------- 3. other pieces
kd = KDTree(len(skin))
for i, sv in enumerate(skin):
    kd.insert(co[sv], i)
kd.balance()
head = gi['B_Head']; hj = J('B_Head')
ARMS = [gi[n] for n in names if any(t in n for t in ('UpperArm', 'Forearm', 'Hand'))]
npieces = pv.max() + 1
rigid_head = 0; mane = 0
for p in range(1, npieces):
    idx = np.where(pv == p)[0]
    c = co[idx].mean(0); size = (co[idx].max(0) - co[idx].min(0)).max()
    # teeth, tusks, eyes: small and in front of the skull base
    if size < 0.2 and c[1] < hj[1] + 0.05 and abs(c[2] - hj[2]) < 0.35:
        W[idx] = 0; W[idx, head] = 1; rigid_head += 1
        continue
    acc = np.zeros(len(names))
    for i in idx:
        hits = kd.find_n(co[i], 4)
        w = np.array([1.0 / max(h[2], 1e-4) for h in hits])
        W[i] = (w[:, None] * W[[skin[h[1]] for h in hits]]).sum(0) / w.sum()
    for side in ('L', 'R'):
        arm = [gi[n] for n in names if f'B_{side}_' in n and any(t in n for t in ('UpperArm', 'Forearm', 'Hand'))]
        cl = gi[f'B_{side}_Clavicle']
        sh = W[np.ix_(idx, arm)].sum(1)
        ex = np.clip(sh - 0.25, 0, None)
        f = np.where(sh > 0, (sh - ex) / np.maximum(sh, 1e-9), 1)
        W[np.ix_(idx, arm)] *= f[:, None]; W[idx, cl] += ex
    # per piece: half its own copy, half the piece mean (no shingle tears, still bends with the back)
    W[idx] = 0.5 * W[idx] + 0.5 * W[idx].mean(0)
    mane += 1
print('WEIGHTS pieces rigid on head', rigid_head, 'copied from skin', mane)

# ---------------------------------------------------------------- 4. limit + normalise + write
lost = np.where(W.sum(1) < 0.5)[0]                               # the proxy's few unsolved spots
good = np.where(W.sum(1) >= 0.5)[0]
if len(lost):
    kg = KDTree(len(good))
    for i, g in enumerate(good):
        kg.insert(co[g], i)
    kg.balance()
    for i in lost:
        W[i] = W[good[kg.find(co[i])[1]]]
top = np.argsort(-W, 1)[:, :4]
W2 = np.zeros_like(W); rows = np.arange(nv)[:, None]
W2[rows, top] = W[rows, top]
W2 /= np.maximum(W2.sum(1, keepdims=True), 1e-9)
print('WEIGHTS unweighted body verts', int((W2.sum(1) < 0.5).sum()))
for g in body.vertex_groups:
    g.remove(list(range(nv)))
for j, n in enumerate(names):
    nz = np.nonzero(W2[:, j] > 1e-4)[0]
    g = body.vertex_groups[n]
    for i in nz:
        g.add([int(i)], float(W2[i, j]), 'REPLACE')
bpy.data.objects.remove(proxy, do_unlink=True)
if not any(m.type == 'ARMATURE' for m in body.modifiers):
    m = body.modifiers.new('Armature', 'ARMATURE'); m.object = rig
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
