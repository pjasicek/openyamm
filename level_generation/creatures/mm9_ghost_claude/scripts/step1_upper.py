"""Upper body from the Meshy return: scaled to MM9 size, cut at the belt, interior faces (shoulder discs, hems folded inside) removed,
x > 0 half mirrored (MM9 is mirror-symmetric), lace cuffs kept. Everything below the belt comes from robe_loft.py instead, the head from its own Meshy model.
Writes <out blend> with object Upper (part attr: 0 torso+arms, 2 cuff) and <out npz> with the whole posed Meshy sheets for the loft.
Args: <meshy glb> <out blend> <out npz> [report json]"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index('--') + 1:]
GLB, OUT, NPZ = argv[:3]
S, ZBELT_TOP = 1.5, 0.128          # Meshy units -> MM9 metres; belt top in Meshy units
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
sc = bpy.context.scene
o = next(x for x in sc.objects if x.type == 'MESH')
for x in list(sc.objects):
    if x is not o:
        m = o.matrix_world.copy(); o.parent = None; o.matrix_world = m; bpy.data.objects.remove(x)
for x in sc.objects:
    x.select_set(True)
bpy.context.view_layer.objects.active = o
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = o.data
co = np.array([v.co for v in me.vertices])
F = [list(p.vertices) for p in me.polygons]
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lab = np.full(len(bm.verts), -1, np.int32); k = 0; sizes = []
for v in bm.verts:
    if lab[v.index] >= 0:
        continue
    st = [v]; lab[v.index] = k; n = 0
    while st:
        x = st.pop(); n += 1
        for e in x.link_edges:
            y = e.other_vert(x)
            if lab[y.index] < 0:
                lab[y.index] = k; st.append(y)
    k += 1; sizes.append(n)
order = np.argsort(sizes)[::-1]
main = order[0]; head = order[1]
flab = np.array([lab[f[0]] for f in F])
fcen = np.array([co[f].mean(0) for f in F])
# waist centre: the main comp's vertices around the belt
band = (lab == main) & (np.abs(co[:, 2] - 0.10) < 0.03) & (np.abs(co[:, 0]) < 0.2)
yc = 0.5 * (co[band, 1].min() + co[band, 1].max())
TY = -0.0576 - yc * S          # waist on MM9's Xspine
TZ = 0.083 - 0.105 * S         # belt on MM9's Ydress height
print('WAIST y', yc, 'x', co[band, 0].min(), co[band, 0].max(), 'TY TZ', TY, TZ, 'parts', k)
W = co * S + np.array([0, TY, TZ])
for v, c in zip(bm.verts, W):
    v.co = Vector(c.tolist())
zcut = ZBELT_TOP * S + TZ
# blockers: the main shell and the head only (ornaments and hands would punch holes in the shell under them)
bvh = BVHTree.FromPolygons([Vector(c.tolist()) for c in W], [f for f, c in zip(F, flab) if c in (main, head)])
g = np.pi * (3 - 5 ** 0.5)
n = 48
kk = np.arange(n) + 0.5
zz = 1 - 2 * kk / n
rr = np.sqrt(1 - zz ** 2)
DIRS = [Vector((rr[i] * math.cos(g * i), rr[i] * math.sin(g * i), zz[i])) for i in range(n)]
keep = np.zeros(len(F), bool)
PART = np.zeros(len(F), np.int32)
fnor = np.array([np.cross(W[f[1]] - W[f[0]], W[f[2]] - W[f[0]]) for f in F])
fnor /= np.maximum(np.linalg.norm(fnor, axis=1, keepdims=True), 1e-12)
cuffs = [c for c in range(k) if 80 < sizes[c] < 120 and 0.3 < (co[lab == c, 0].mean()) and co[lab == c, 2].max() > 0.1]
print('CUFF comps', cuffs, [sizes[c] for c in cuffs])
for i, f in enumerate(F):
    cen = Vector(fcen[i] * S + np.array([0, TY, TZ]))
    if flab[i] in cuffs:
        keep[i] = fcen[i, 0] > 0; PART[i] = 2
        continue
    if flab[i] != main or cen.z < zcut or fcen[i, 0] < -0.04:
        continue
    N = Vector(fnor[i])
    org = cen + N * 1e-4
    seen = 0
    for d in DIRS:
        if d.dot(N) < 0.55:
            continue
        hit = bvh.ray_cast(org, d, 3.0)
        if hit[0] is None:
            seen += 1
    keep[i] = seen >= 1
print('KEPT', keep.sum(), 'main upper tested')
bmesh.ops.delete(bm, geom=[bm.faces[i] for i in np.where(~keep)[0]], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(me); bm.free()
me.update()
np.savez(NPZ, co=W, tris=np.array([t for f in F for t in ([f[0], f[j], f[j + 1]] for j in range(1, len(f) - 1))]), comp=lab, main=main, head=head, TY=TY, TZ=TZ, S=S, zcut=zcut)
# drop faces that became disconnected scraps
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
seen = set(); parts = []
for v in bm.verts:
    if v.index in seen:
        continue
    st = [v]; cur = [v]; seen.add(v.index)
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); st.append(y); cur.append(y)
    parts.append(cur)
parts.sort(key=len, reverse=True)
print('UPPER comps', [len(p) for p in parts[:12]])
drop = [v for p in parts if len(p) < 20 for v in p]
bmesh.ops.delete(bm, geom=drop, context='VERTS')
# mirror x > 0 onto x < 0, weld on the plane
bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=False, clear_inner=True, dist=1e-5)
for v in bm.verts:
    if abs(v.co.x) < 1e-3:
        v.co.x = 0
res = bmesh.ops.mirror(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], matrix=__import__('mathutils').Matrix.Identity(4), merge_dist=2e-4, axis='X')
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bmesh.ops.triangulate(bm, faces=bm.faces[:])
print('UPPER', len(bm.verts), len(bm.faces), 'boundary', sum(1 for e in bm.edges if e.is_boundary))
bm.to_mesh(me); bm.free()
o.name = 'Upper'; me.name = 'Upper'
bpy.ops.wm.save_as_mainfile(filepath=OUT)
