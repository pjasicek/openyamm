"""Back hair to MM9's volume (mm9_markel, orchestrator review 2026-11-02: "the back hair is a big bulbous mass sticking out behind
the head and down the upper back ... MM9's Markel has nape-length hair hugging the skull"). Smart Topology's hair shell hung 13-15
cm behind the neck down to the shoulder blades (hair_probe.py). Bind pose, Blender coordinates (+y is the back):
1. hair-shell faces whose vertices all lie below Z_CUT (the nape, inside the raised fur collar, which reaches z 0.71) are deleted;
2. every remaining hair vertex further than T(z) from the skull/neck shells (face shell + neck shell, BVH) moves radially onto
   that offset: T = T_TOP above z 0.80 easing to T_NAPE at Z_CUT (the sunk bald crown, already inside the skull, is untouched);
3. SMOOTH Laplacian passes over the moved vertices, re-enforcing at least 0.6 T from the skull (no creases from the low-poly skull);
4. every hair vertex takes the weights of the nearest skull/neck vertex (MM9's Ponytail-free hair follows the head; the old tail
   carried Spine2/Neck weights from fit_rig.py and swung into the collar).
UVs and attributes of the kept faces are unchanged (the paid paint stays valid). Args: -- <in blend> <out blend>
[z_cut 0.665] [t_top 0.015] [t_nape 0.008] [smooth 4]"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
Z_CUT, T_TOP, T_NAPE, SMOOTH = (float(a[2]) if len(a) > 2 else 0.665, float(a[3]) if len(a) > 3 else 0.015,
                                 float(a[4]) if len(a) > 4 else 0.008, int(a[5]) if len(a) > 5 else 4)
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lk = bm.faces.layers.int['head']
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
CO = np.array([v.co[:] for v in bm.verts])
hparts = {comp[f.verts[0].index] for f in bm.faces if f[lk]}
big = sorted(hparts, key=lambda k: -(comp == k).sum())
hair = max(big, key=lambda k: CO[comp == k][:, 1].max())
face = big[0] if big[0] != hair else big[1]
neck = [k for k in big if k not in (hair, face) and (comp == k).sum() > 100]
skull_parts = [face] + neck
print('PARTS hair', int(hair), 'skull', [int(k) for k in skull_parts])
sf = [f for f in bm.faces if comp[f.verts[0].index] in skull_parts]
sv = sorted({v.index for f in sf for v in f.verts}); rm = {v: i for i, v in enumerate(sv)}
bvh = BVHTree.FromPolygons([bm.verts[i].co.copy() for i in sv], [[rm[v.index] for v in f.verts] for f in sf])
kd = KDTree(len(sv))
for n_, i in enumerate(sv):
    kd.insert(bm.verts[i].co, n_)
kd.balance()
# 1. cut the tail
dele = [f for f in bm.faces if comp[f.verts[0].index] == hair and all(v.co.z < Z_CUT for v in f.verts)]
bmesh.ops.delete(bm, geom=dele, context='FACES')
bm.verts.ensure_lookup_table()
# the hair set after the delete (indices changed): vertices at the old hair part's positions
bm.verts.index_update(); bm.faces.ensure_lookup_table()
old = {tuple(np.round(CO[i], 6)) for i in np.where(comp == hair)[0]}
hairverts = [v for v in bm.verts if tuple(np.round(np.array(v.co[:]), 6)) in old]
loose = [v for v in bm.verts if not v.link_faces]
bmesh.ops.delete(bm, geom=loose, context='VERTS')
hairverts = [v for v in hairverts if v.is_valid]
def T(z):
    k = np.clip((z - Z_CUT) / (0.80 - Z_CUT), 0, 1)
    return T_NAPE + (T_TOP - T_NAPE) * k
# 2. onto the offset surface
moved = set(); mx = 0.0
for v in hairverts:
    loc, nor, _, dist = bvh.find_nearest(v.co)
    if loc is None:
        continue
    d = v.co - loc
    inside = d.dot(nor) < 0
    if inside:
        continue
    t = T(v.co.z)
    if d.length > t:
        mx = max(mx, d.length - t)
        v.co = loc + d.normalized() * t
        moved.add(v)
# 3. smooth the moved vertices, keep them outside 0.6 T
for _ in range(SMOOTH):
    new = {}
    for v in moved:
        nb = [e.other_vert(v).co for e in v.link_edges]
        if nb:
            new[v] = v.co * 0.5 + sum(nb, Vector()) / len(nb) * 0.5
    for v, c in new.items():
        v.co = c
        loc, nor, _, _ = bvh.find_nearest(v.co)
        d = v.co - loc; t = T(v.co.z) * 0.6
        if d.dot(nor) < 0 or d.length < t:
            v.co = loc + nor.normalized() * t
bm.to_mesh(me); bm.free(); me.update()
# 4. weights from the nearest skull/neck vertex (indices in the new mesh)
name = {g.index: g.name for g in body.vertex_groups}
# skull/neck vertices are unmoved: find them by position in the edited mesh and read their deform weights
pos_now = {tuple(np.round(np.array(v.co[:]), 6)): v.index for v in me.vertices}
src = {}
for i in sv:
    k = tuple(np.round(CO[i], 6))
    if k in pos_now:
        vi = pos_now[k]
        src[vi] = {name[g.group]: g.weight for g in me.vertices[vi].groups if name[g.group] in rig.data.bones}
kd2 = KDTree(len(src)); keys = list(src)
for n_, vi in enumerate(keys):
    kd2.insert(me.vertices[vi].co, n_)
kd2.balance()
bm2 = bmesh.new(); bm2.from_mesh(me); bm2.verts.ensure_lookup_table()
comp2 = -np.ones(len(bm2.verts), np.int32); cid = 0
for v in bm2.verts:
    if comp2[v.index] >= 0:
        continue
    st = [v]; comp2[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp2[y.index] < 0:
                comp2[y.index] = cid; st.append(y)
    cid += 1
CO2 = np.array([v.co[:] for v in bm2.verts]); bm2.free()
# the hair part of the edited mesh: the large head-height part reaching furthest back
hk = max(set(comp2.tolist()), key=lambda k: CO2[comp2 == k][:, 1].max() if (comp2 == k).sum() > 300 and CO2[comp2 == k][:, 2].min() > 0.4 else -9)
hair_idx = np.where(comp2 == hk)[0]
bones = [b.name for b in rig.data.bones]
for vi in hair_idx:
    _, n_, _ = kd2.find(me.vertices[vi].co)
    w = src[keys[n_]]
    for g in list(me.vertices[vi].groups):
        if name[g.group] in bones:
            body.vertex_groups[name[g.group]].remove([int(vi)])
    for bn, wt in w.items():
        body.vertex_groups[bn].add([int(vi)], wt, 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('HAIR_RESHAPE deleted faces', len(dele), 'moved', len(moved), 'max_in_mm', round(mx * 1000, 1), 'hair verts now', len(hair_idx),
      'extent', CO2[hair_idx].min(0).round(3).tolist(), CO2[hair_idx].max(0).round(3).tolist())
