"""Accessories follow their carrier (mm9_sven, 2026-11-02; detached_parts_audit.py: belt studs, the chest medallion and
necklace pieces floated up to 1.3 cm off the belt/chest in Death and AttackMelee, fit_rig.py had labelled them from the
sparse MM9 mesh). Every small loose body part (no head/hand faces, at most MAXV vertices) takes, per vertex, the weights
of the nearest vertex of the large parts (the carrier surface under it): the playbook rule "accessories copy the skin
under them". Second pass: the tiny parts (at most TINY vertices: belt studs) copy again from every larger part, so a stud
follows the belt it sits on rather than the vest under the belt. Weights only. Args (Blender): -- <in blend> <out blend>
[maxv 120] [tiny 15]"""
import bpy, bmesh, sys
import numpy as np
from mathutils.kdtree import KDTree
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]; MAXV = int(a[2]) if len(a) > 2 else 120; TINY = int(a[3]) if len(a) > 3 else 15
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
lh, lk = bm.faces.layers.int['hand'], bm.faces.layers.int['head']
comp = -np.ones(len(bm.verts), np.int32); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0:
        continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0:
                comp[y.index] = cid; st.append(y)
    cid += 1
headish = set()
for f in bm.faces:
    if f[lh]:                     # mm9_greenman: the hands stay; small head-set leaves (the hood, beard) are accessories too
        headish.add(comp[f.verts[0].index])
# the staff (weighted to Bone01) is neither a target nor a carrier
staff_g = body.vertex_groups.get('Bone01')
staff = set()
if staff_g is not None:
    for v in me.vertices:
        if any(g.group == staff_g.index and g.weight > 0.5 for g in v.groups):
            staff.add(comp[v.index])
headish |= staff
bm.free()
size = np.bincount(comp)
small = [c for c in range(cid) if size[c] <= MAXV and c not in headish]
gname = {g.index: g.name for g in body.vertex_groups}
BONES = {b.name for b in rig.data.bones}
W = [{gname[g.group]: g.weight for g in v.groups if gname[g.group] in BONES} for v in me.vertices]
changed = 0
for target in (small, [c for c in small if size[c] <= TINY]):
    carrier = np.where(~np.isin(comp, list(target) + sorted(staff)))[0]
    tree = KDTree(len(carrier))
    for n, i in enumerate(carrier):
        tree.insert(me.vertices[i].co, n)
    tree.balance()
    for c in target:
        for i in np.where(comp == c)[0]:
            _, j, _ = tree.find(me.vertices[i].co)
            W[i] = dict(W[carrier[j]]); changed += 1
groups = {g.name: g for g in body.vertex_groups}
idx = [int(i) for c in small for i in np.where(comp == c)[0]]
for g in body.vertex_groups:
    if g.name in BONES:
        g.remove(idx)
for i in idx:
    for n, w in W[i].items():
        groups[n].add([i], w, 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('ACCESSORY_WEIGHTS', {'parts': len(small), 'sizes': sorted(int(size[c]) for c in small), 'verts': changed})
