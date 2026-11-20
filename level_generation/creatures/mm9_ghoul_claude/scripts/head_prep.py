"""Head-only Meshy model -> parts: face skin (with neck), teeth, eyes, and a clean hair mass (voxel union of the shredded hair shells, keeping the clumps).
Output blend: objects Face, Teeth, Eyes, Hair in head-local metres, chin/crown placed by config. Args: <head glb> <out blend>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
S = 0.265             # metres per unit
BACK = 0.86           # depth compress behind the ears (the 3/4 master over-reads the skull depth)
VOX = 0.0035
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=IN)
o = next(x for x in bpy.data.objects if x.type == 'MESH')
Mw = o.matrix_world.copy()
for x in list(bpy.data.objects):
    if x is not o and x.type != 'MESH':
        o.parent = None
        bpy.data.objects.remove(x)
o.matrix_world = Mw; o.name = 'Raw'
bpy.context.view_layer.objects.active = o; o.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = o.data; me.materials.clear()
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.to_mesh(me); bm.free()
P = np.array([tuple(v.co) for v in me.vertices]) * S
# y: the face stays, the back of the skull compresses smoothly
y0 = -0.02
yy = P[:, 1]
P[:, 1] = np.where(yy > y0, y0 + (yy - y0) * BACK, yy)
for v, p in zip(me.vertices, P): v.co = Vector(p)
n = len(P)
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
comp = -np.ones(n, int); c_ = 0
for i in range(n):
    if comp[i] >= 0: continue
    st = [i]; comp[i] = c_
    while st:
        x = st.pop()
        for y in nbr[x]:
            if comp[y] < 0: comp[y] = c_; st.append(y)
    c_ += 1
sz = np.bincount(comp); face_c = int(np.argmax(sz))
# classify
kind = {}
for c in range(c_):
    q = P[comp == c]
    cen = q.mean(0); ext = np.ptp(q, 0)
    if c == face_c: kind[c] = 'Face'
    elif sz[c] > 100 and sz[c] < 140 and ext.max() < 0.035 and cen[1] < -0.06 and abs(cen[2] - 0.02) < 0.03: kind[c] = 'Eyes'
    elif ext.max() < 0.016 and cen[1] < -0.04 and cen[2] < -0.02 and abs(cen[0]) < 0.075: kind[c] = 'Teeth'
    else: kind[c] = 'Hair'
print('KINDS', {k: sum(1 for v in kind.values() if v == k) for k in set(kind.values())})
ids = {k: [c for c in range(c_) if kind[c] == k] for k in ('Face', 'Eyes', 'Teeth', 'Hair')}
for c in sorted(ids['Teeth'], key=lambda c: -sz[c])[:6]: print('tooth', sz[c], P[comp == c].mean(0).round(3))
for k, cs in ids.items():
    d = o.copy(); d.data = me.copy(); d.name = k; bpy.context.scene.collection.objects.link(d)
    bm = bmesh.new(); bm.from_mesh(d.data); bm.verts.ensure_lookup_table()
    keep = np.isin(comp, cs)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep[v.index]], context='VERTS')
    bm.to_mesh(d.data); bm.free()
bpy.data.objects.remove(o)
# hair: solid shells + skull -> voxel surface
hair, face = bpy.data.objects['Hair'], bpy.data.objects['Face']
sol = hair.copy(); sol.data = hair.data.copy(); sol.name = 'HairSolid'; bpy.context.scene.collection.objects.link(sol)
m = sol.modifiers.new('s', 'SOLIDIFY'); m.thickness = 0.006; m.offset = -1
bpy.context.view_layer.objects.active = sol
bpy.ops.object.modifier_apply(modifier='s')
fc = face.copy(); fc.data = face.data.copy(); bpy.context.scene.collection.objects.link(fc)
bpy.ops.object.select_all(action='DESELECT'); sol.select_set(True); fc.select_set(True); bpy.context.view_layer.objects.active = sol
bpy.ops.object.join()
r = sol.modifiers.new('r', 'REMESH'); r.mode = 'VOXEL'; r.voxel_size = VOX; r.use_smooth_shade = True
bpy.ops.object.modifier_apply(modifier='r')
bm = bmesh.new(); bm.from_mesh(sol.data); print('VOXEL verts', len(bm.verts))
# keep the voxel surface near the hair shells
hco = np.array([tuple(v.co) for v in hair.data.vertices])
bv = BVHTree.FromObject(hair, bpy.context.evaluated_depsgraph_get())
keepv = []
for v in bm.verts:
    loc, nor, idx, dist = bv.find_nearest(v.co, 0.012)
    keepv.append(loc is not None and dist < 0.007)
keepv = np.array(keepv)
bmesh.ops.delete(bm, geom=[v for i, v in enumerate(bm.verts) if not keepv[i]], context='VERTS')
# drop specks
seen = set(); comps = []
for v in bm.verts:
    if v in seen: continue
    st = [v]; seen.add(v); cc = [v]
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen: seen.add(y); st.append(y); cc.append(y)
    comps.append(cc)
comps.sort(key=len, reverse=True)
print('HAIR comps', [len(c) for c in comps[:8]])
for c in comps[1:]:
    if len(c) < 400: bmesh.ops.delete(bm, geom=c, context='VERTS')
bm.to_mesh(sol.data); bm.free()
bpy.data.objects.remove(hair); sol.name = 'Hair'
for ob in bpy.data.objects:
    for p in ob.data.polygons: p.use_smooth = True
    print('OBJ', ob.name, len(ob.data.vertices), len(ob.data.polygons), np.round(np.min([v.co[:] for v in ob.data.vertices], 0), 3), np.round(np.max([v.co[:] for v in ob.data.vertices], 0), 3))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
