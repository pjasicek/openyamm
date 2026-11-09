"""Head-only Meshy model -> parts in final coordinates. Meshy's head is a doubled shell, with hair strips over a real neck: only faces that can be seen from outside stay
(plus the mouth pocket), the near half (x < 0) is mirrored, ears are brought in to MM9's span, and the hair becomes one voxel-closed mass. Objects Face, Teeth, Eyes, Hair.
Args: <head glb> <out blend>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
S = 0.42; XOFF = -0.005; CROWN = 0.945; NOSE_Y = -0.178; EAR_K = 0.82; VOX = 0.0042
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=IN)
o = next(x for x in bpy.data.objects if x.type == 'MESH')
Mw = o.matrix_world.copy()
for x in list(bpy.data.objects):
    if x is not o:
        o.parent = None
        bpy.data.objects.remove(x)
o.matrix_world = Mw; o.name = 'Raw'
bpy.context.view_layer.objects.active = o; o.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = o.data; me.materials.clear()
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bmesh.ops.triangulate(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
R = np.array([tuple(v.co) for v in me.vertices])
n = len(R)
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
sz = np.bincount(comp); main = int(np.argmax(sz))
kind = {}
for c in range(c_):
    q = R[comp == c]; cen = q.mean(0); ext = np.ptp(q, 0)
    if c == main: kind[c] = 'Face'
    elif cen[1] < -0.2 and -0.3 < cen[2] < -0.05: kind[c] = 'Teeth'            # teeth, gums, tongue plate
    elif cen[1] < -0.2 and -0.05 < cen[2] < 0.15: kind[c] = 'Eyes'
    else: kind[c] = 'Hair'
print('KINDS', {k: sum(1 for v in kind.values() if v == k) for k in ('Face', 'Teeth', 'Eyes', 'Hair')})
# placement, in final metres
P = R.copy(); P[:, 0] += XOFF
crown = R[(np.abs(R[:, 0]) < 0.12), 2].max()
P *= S
P[:, 2] += CROWN - crown * S
P[:, 1] += NOSE_Y - P[np.abs(R[:, 0]) < 0.05, 1].min()
print('crown raw', crown, 'chin z', P[(np.abs(R[:, 0]) < 0.1) & (R[:, 1] < -0.2), 2].min(), 'nose y', P[:, 1].min())
ear = np.abs(P[:, 0]) > 0.125
P[ear, 0] = np.sign(P[ear, 0]) * (0.125 + (np.abs(P[ear, 0]) - 0.125) * EAR_K)
for v, p in zip(me.vertices, P): v.co = Vector(p)
me.update()
# outer faces: from any of 96 directions a ray leaves the head. Rays from both sides of a face.
bvh = BVHTree.FromPolygons([tuple(p) for p in P], [tuple(p.vertices) for p in me.polygons])
k = np.arange(96) + 0.5; g = np.pi * (3 - 5 ** 0.5); zz = 1 - 2 * k / 96; rr = np.sqrt(1 - zz ** 2)
dirs = [Vector((rr[i] * np.cos(g * k[i]), rr[i] * np.sin(g * k[i]), zz[i])) for i in range(96)]
vis = np.zeros(len(me.polygons), bool)
fv = np.array([p.vertices[:] for p in me.polygons])
cen = P[fv].mean(1)
for p in me.polygons:
    c = Vector(cen[p.index]); nm = p.normal
    hit_ = False
    for s in (1, -1):
        org = c + nm * (s * 2e-4)
        for d in dirs:
            if d.dot(nm) * s <= 0.02: continue
            if bvh.ray_cast(org, d, 1.0)[0] is None:
                hit_ = True; break
        if hit_: break
    vis[p.index] = hit_
mouth = (np.abs(cen[:, 0]) < 0.08) & (cen[:, 1] < -0.02) & (cen[:, 2] > 0.63) & (cen[:, 2] < 0.76)
fk = comp[fv[:, 0]]
isface = fk == main
print('VISIBLE', int(vis[isface].sum()), 'of', int(isface.sum()), 'mouth kept', int((~vis & mouth & isface).sum()))
vis |= mouth
kindf = np.array([kind[c] for c in fk])
objs = {}
for nm in ('Face', 'Teeth', 'Eyes', 'Hair'):
    d = o.copy(); d.data = me.copy(); d.name = nm; bpy.context.scene.collection.objects.link(d)
    bm = bmesh.new(); bm.from_mesh(d.data); bm.faces.ensure_lookup_table()
    keep = (kindf == nm) & (vis if nm in ('Face', 'Hair') else np.ones(len(vis), bool))
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not keep[f.index]], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(d.data); bm.free(); objs[nm] = d
bpy.data.objects.remove(o)
# the outer skin of the back of the head goes to the hair volume with the strips
sol = objs['Hair'].copy(); sol.data = objs['Hair'].data.copy(); sol.name = 'HairSolid'; bpy.context.scene.collection.objects.link(sol)
fc = objs['Face'].copy(); fc.data = objs['Face'].data.copy(); bpy.context.scene.collection.objects.link(fc)
bm = bmesh.new(); bm.from_mesh(fc.data)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not (v.co.y > -0.03 and v.co.z < 0.86)], context='VERTS')
bm.to_mesh(fc.data); bm.free()
bpy.ops.object.select_all(action='DESELECT'); sol.select_set(True); fc.select_set(True); bpy.context.view_layer.objects.active = sol
bpy.ops.object.join()
m = sol.modifiers.new('s', 'SOLIDIFY'); m.thickness = 0.012; m.offset = -1
bpy.ops.object.modifier_apply(modifier='s')
r = sol.modifiers.new('r', 'REMESH'); r.mode = 'VOXEL'; r.voxel_size = VOX; r.use_smooth_shade = True
bpy.ops.object.modifier_apply(modifier='r')
bpy.data.objects.remove(objs['Hair']); sol.name = 'Hair'; objs['Hair'] = sol
print('VOXEL verts', len(sol.data.vertices))
# mirror the near half of the skin parts
for nm in ('Face', 'Teeth', 'Eyes'):
    ob = objs[nm]
    bm = bmesh.new(); bm.from_mesh(ob.data)
    g = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True, dist=1e-5)
    for v in bm.verts:
        if abs(v.co.x) < 1e-4: v.co.x = 0
    bmesh.ops.mirror(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), axis='X', merge_dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data); bm.free()
for ob in bpy.data.objects:
    for p in ob.data.polygons: p.use_smooth = True
    c = np.array([v.co[:] for v in ob.data.vertices])
    print('OBJ', ob.name, len(c), len(ob.data.polygons), c.min(0).round(3), c.max(0).round(3))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
