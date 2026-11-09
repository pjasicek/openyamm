"""Half-rotation helper bones (cat and Mummy lessons): the skin over a joint follows an arc. Each helper is keyed half way by clips (half_keys). Args: <in blend> <out blend>"""
import bpy, sys
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
rig = bpy.data.objects['MM9_Rig']; body = bpy.data.objects['Body']; me = body.data
import bmesh
bm = bmesh.new(); bm.from_mesh(me); seen = set(); drop = []                    # specks of Meshy's old hand left beside the fingers
for v in bm.verts:
    if v in seen: continue
    st = [v]; seen.add(v); cur = []
    while st:
        x = st.pop(); cur.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen: seen.add(y); st.append(y)
    if len(cur) < 60 and abs(cur[0].co.x) > 0.7: drop += cur
bmesh.ops.delete(bm, geom=drop, context='VERTS')
print('HELPERS ngons', sum(1 for f in bm.faces if len(f.verts) > 3))
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.to_mesh(me); bm.free(); print('HELPERS dropped', len(drop))
B = 'Bip01 '
HELP = (('L Thigh', ('Pelvis',)), ('R Thigh', ('Pelvis',)), ('L Calf', ('L Thigh',)), ('R Calf', ('R Thigh',)), ('L Forearm', ('L UpperArm',)), ('R Forearm', ('R UpperArm',)),
        ('L UpperArm', ('L Clavicle', 'Spine3')), ('R UpperArm', ('R Clavicle', 'Spine3')), ('Head', ('Neck',)), ('Neck', ('Spine3',)))
parents = {b.name: (b.parent.name if b.parent else None) for b in rig.data.bones}
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
for c, ps in HELP:
    h = eb.new(B + c + '_h'); t = eb[B + c]
    h.head = t.head; h.tail = t.tail; h.roll = t.roll; h.parent = eb[parents[B + c]]; h.use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')
for g in list(body.vertex_groups):
    if g.name.startswith('MP_') or g.name not in rig.data.bones: body.vertex_groups.remove(g)
names = [g.name for g in body.vertex_groups]
for c, _ in HELP: names.append(B + c + '_h'); body.vertex_groups.new(name=B + c + '_h')
idx = {n: i for i, n in enumerate(names)}
n = len(me.vertices)
W = np.zeros((n, len(names)))
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp); pa = np.zeros(n, int)
for p in me.polygons:
    for v in p.vertices: pa[v] = max(pa[v], fp[p.index])
skin = np.isin(pa, (1, 2, 3, 5, 8, 13, 20, 21))
for c, ps in HELP:
    ci = idx[B + c]; pi = [idx[B + p] for p in ps if B + p in idx]; hi = idx[B + c + '_h']
    wc = W[:, ci]; wp = W[:, pi].sum(1); tot = wc + wp
    m = (wc > 1e-3) & (wp > 1e-3) & skin
    t = wc[m] / tot[m]
    scale = np.maximum(1 - 2 * t, 0)
    for p in pi: W[m, p] = W[m, p] * scale
    W[m, ci] = tot[m] * np.maximum(2 * t - 1, 0)
    W[m, hi] = tot[m] * (1 - np.abs(2 * t - 1))
order = np.argsort(-W, axis=1)
for i in range(n):
    keep = order[i, :4]; row = np.zeros(len(names)); row[keep] = W[i, keep]; row[row < 0.015] = 0
    W[i] = row / max(row.sum(), 1e-9)
for g in body.vertex_groups:
    j = idx[g.name]
    g.remove(list(range(n)))
    ids = np.nonzero(W[:, j])[0]
    for i in ids: g.add([int(i)], float(W[i, j]), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('HELPERS', len(HELP), 'bones', len(rig.data.bones))
