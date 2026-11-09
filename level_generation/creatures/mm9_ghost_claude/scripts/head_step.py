"""The floating head: Meshy's head-only model, cleaned for a see-through body and reduced. Interior faces (the hollow behind the shell) removed, the neck opening capped, scraps dropped,
decimated to TRIS, scaled onto MM9's head piece (bind). Weight 1 on Xhead. No neck: MM9's head flies free of the body in its clips (up to 49 cm, turning 180 deg).
Args: <in blend> <head glb> <out blend>"""
import bpy, bmesh, sys, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
A = sys.argv[sys.argv.index('--') + 1:]
IN, GLB, OUT = A
TRIS = 3000
MM9MIN, MM9MAX = np.array([-0.081, -0.2821, 0.4871]), np.array([0.081, -0.0802, 0.7333])
bpy.ops.wm.open_mainfile(filepath=IN)
old = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB)
new = [o for o in bpy.data.objects if o not in old]
h = next(o for o in new if o.type == 'MESH')
mat = h.matrix_world.copy(); h.parent = None; h.matrix_world = mat
for o in new:
    if o is not h:
        bpy.data.objects.remove(o)
for o in bpy.data.objects:
    o.select_set(o == h)
bpy.context.view_layer.objects.active = h
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = h.data
co = np.array([v.co[:] for v in me.vertices])
F = [list(p.vertices) for p in me.polygons]
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
bvh = BVHTree.FromPolygons([Vector(c.tolist()) for c in co], F)
g = np.pi * (3 - 5 ** 0.5); n = 80; kk = np.arange(n) + 0.5; zz = 1 - 2 * kk / n; rr = np.sqrt(1 - zz ** 2)
DIRS = [Vector((rr[i] * math.cos(g * i), rr[i] * math.sin(g * i), zz[i])) for i in range(n)]
dele = []
for f in bm.faces:
    N = f.normal; o = f.calc_center_median() + N * 1e-4
    vis = 0
    for d in DIRS:
        if d.dot(N) < 0.3:
            continue
        hit = bvh.ray_cast(o, d, 3.0)
        if hit[0] is None:
            vis += 1
    if vis == 0:
        dele.append(f)
print('INTERIOR faces', len(dele), 'of', len(bm.faces))
bmesh.ops.delete(bm, geom=dele, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
# keep the largest piece
bm.verts.ensure_lookup_table(); seen = set(); parts = []
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
print('PIECES', [len(p) for p in parts[:6]])
bmesh.ops.delete(bm, geom=[v for p in parts[1:] for v in p], context='VERTS')
# boundary loops: fill each
left = set(e for e in bm.edges if e.is_boundary)
loops = []
while left:
    e = left.pop(); cur = {e}; st = [e]
    while st:
        x = st.pop()
        for v in x.verts:
            for y in v.link_edges:
                if y in left:
                    left.discard(y); cur.add(y); st.append(y)
    loops.append(cur)
loops.sort(key=len, reverse=True)
print('LOOPS', [len(l) for l in loops[:8]])
for l in loops:
    if len(l) < 3:
        continue
    r = bmesh.ops.holes_fill(bm, edges=list(l), sides=0)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bm.to_mesh(me); bm.free(); me.update()
dm = h.modifiers.new('D', 'DECIMATE'); dm.ratio = TRIS / len(me.polygons); dm.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier=dm.name)
co = np.array([v.co[:] for v in me.vertices])
lo, hi = co.min(0), co.max(0)
s = (MM9MAX[2] - MM9MIN[2]) / (hi[2] - lo[2])
c0 = 0.5 * (lo + hi); c1 = 0.5 * (MM9MIN + MM9MAX)
print('HEAD raw', lo, hi, 'scale', s, 'x width', (hi - lo)[0] * s, 'mm9', (MM9MAX - MM9MIN)[0], 'y', (hi - lo)[1] * s, (MM9MAX - MM9MIN)[1])
for v, c in zip(me.vertices, co):
    v.co = Vector(((c - c0) * s + c1).tolist())
me.update()
h.name = 'Head'; me.name = 'Head'
for p in me.polygons:
    p.use_smooth = True
arm = bpy.data.objects['MM9_Rig']
for n in [b.name for b in arm.data.bones]:
    h.vertex_groups.new(name=n)
h.vertex_groups['Xhead'].add(list(range(len(me.vertices))), 1.0, 'REPLACE')
h.parent = arm
mod = h.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('HEAD', len(me.vertices), len(me.polygons))
