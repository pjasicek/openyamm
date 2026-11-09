"""Rig edits after the UVs (no vertex moved): the MM9 hand sockets LHand1 / RHand1 sit on the palm of our hands.
Args: in blend, out blend"""
import bpy, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
SKULL_SCALE, MARGIN = 0.95, 0.018
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
b = bpy.data.objects['Body']; rig = b.parent; me = b.data
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
co = np.array([b.matrix_world @ v.co for v in me.vertices])
pos = {}
for s, sock in (('L', 'LHand1'), ('R', 'RHand1')):
    gi = b.vertex_groups[f'Bip01 {s} Hand'].index
    w = np.array([next((g.weight for g in v.groups if g.group == gi), 0.0) for v in me.vertices])
    c = co[w > 0.6].mean(0)
    hand = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {s} Hand'].head_local)
    # the fingers' mean base, for the palm's forward direction
    tip = rig.data.bones[f'Bip01 {s} Finger2'].head_local
    pos[sock] = c + (np.array(rig.matrix_world @ tip) - hand) * 0.25
# the skull's crown poked through the hood: skull a little smaller, hood pushed out where it stays closer than the margin
part = np.zeros(len(me.polygons), np.int32); me.attributes['part'].data.foreach_get('value', part)
F = np.array([list(p.vertices) for p in me.polygons])
sk = np.unique(F[part == 30])
cen = co[sk].mean(0)
co[sk] = cen + (co[sk] - cen) * SKULL_SCALE
top = np.unique(F[np.isin(part, (2, 40))])
hood = top[co[top, 2] > 1.42]
tree = BVHTree.FromPolygons([Vector(x) for x in co], [list(t) for t in F[part == 30]])
push = np.zeros(len(co)); dirs = np.zeros((len(co), 3))
inside = 0
for i in hood:
    loc, nrm, fi, dist = tree.find_nearest(Vector(co[i]))
    out = co[i] - np.array(loc)
    ins = out @ np.array(nrm) < 0
    d = -dist if ins else dist
    inside += ins
    if d < MARGIN:
        push[i] = MARGIN - d
        dirs[i] = np.array(nrm)
adj = {int(i): set() for i in hood}
for t in F:
    for a, b_ in ((0, 1), (1, 2), (2, 0)):
        if int(t[a]) in adj and int(t[b_]) in adj:
            adj[int(t[a])].add(int(t[b_])); adj[int(t[b_])].add(int(t[a]))
for _ in range(4):
    new = push.copy(); nd = dirs.copy()
    for i, nb in adj.items():
        if nb:
            l = [j for j in nb]
            new[i] = max(push[i], 0.5 * push[l].mean() + 0.5 * push[i]) if push[i] > 0 else 0.5 * push[l].mean()
            nd[i] = dirs[i] if push[i] > 0 else dirs[l].sum(0)
    push, dirs = new, nd
nrmz = np.maximum(np.linalg.norm(dirs, axis=1, keepdims=True), 1e-6)
co = co + dirs / nrmz * push[:, None]
print('SOCKETS hood', 'verts inside the skull', int(inside), 'pushed', int((push > 1e-4).sum()), 'max cm', round(float(push.max() * 100), 2))
M = np.array(b.matrix_world.inverted())
loc = co @ M[:3, :3].T + M[:3, 3]
for v, c in zip(me.vertices, loc):
    v.co = Vector(c)
for o in bpy.data.objects:
    o.select_set(o is rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
Mi = rig.matrix_world.inverted()
for sock, p in pos.items():
    eb = rig.data.edit_bones[sock]
    d = Mi @ Vector(p) - eb.head
    eb.head += d; eb.tail += d
bpy.ops.object.mode_set(mode='OBJECT')
# rear robe chain: the panel hangs 30 cm behind the legs, so on her back it would stab through the floor and lift the
# corpse. Three bones under the pelvis, at rest in every clip; floor_fix.py bends them flat in Death and Dead only.
ROBE = [(0.95, 'XRobe1'), (0.70, 'XRobe2'), (0.45, 'XRobe3')]
yr = {}
Fr = F[np.isin(part, (8, 41))]
rv = np.unique(Fr)
rear = rv[co[rv, 1] > 0.0]
for z0, name in ROBE:
    m = rear[np.abs(co[rear, 2] - z0) < 0.1]
    yr[name] = (0.0, float(np.median(co[m, 1])) if len(m) else 0.12, z0)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
Mi0 = rig.matrix_world.inverted()
par = rig.data.edit_bones['Bip01 Pelvis']
for z0, name in ROBE:
    eb = rig.data.edit_bones.new(name)
    h = Vector(yr[name]); eb.head = Mi0 @ h; eb.tail = Mi0 @ (h - Vector((0, 0, 0.2)))
    eb.parent = par; eb.use_connect = False
    par = eb
bpy.ops.object.mode_set(mode='OBJECT')
zs = np.array([r[0] for r in ROBE])
for v_i in rv:
    y = co[v_i, 1]; z = co[v_i, 2]
    k = np.clip((y - (-0.03)) / 0.09, 0, 1); k = k * k * (3 - 2 * k)
    k *= np.clip((0.98 - z) / 0.1, 0, 1)
    if k <= 0:
        continue
    v = me.vertices[int(v_i)]
    rest = {g.group: g.weight * (1 - k) for g in v.groups}
    for gid, w in rest.items():
        b.vertex_groups[gid].add([int(v_i)], w, 'REPLACE')
    # between the two nearest chain joints (falls with height)
    t = np.clip((zs[0] - z) / (zs[0] - zs[-1]), 0, 0.999) * (len(zs) - 1)
    i = int(t); f = t - i
    for name, w in ((ROBE[i][1], (1 - f) * k), (ROBE[min(i + 1, 2)][1], f * k)):
        g = b.vertex_groups.get(name) or b.vertex_groups.new(name=name)
        g.add([int(v_i)], float(w), 'ADD')
print('SOCKETS', {k: np.round(v, 3).tolist() for k, v in pos.items()})
bpy.ops.wm.save_as_mainfile(filepath=argv[1])
