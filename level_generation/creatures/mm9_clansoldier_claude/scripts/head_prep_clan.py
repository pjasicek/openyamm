"""Head-only Meshy model (face, ears, neck, helmet and nape curtain in one shell, plus eyes) -> objects Face, Eyes in metres, head-local, symmetric (figure's right half mirrored).
Hidden faces inside the helmet and behind the curtain go; reduced with the face protected. Args: <head glb> <out blend>"""
import bpy, bmesh, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
S = 0.31
TRIS = int(os.environ.get('HEAD_TRIS', 6500))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=IN)
o = next(x for x in bpy.data.objects if x.type == 'MESH')
Mw = o.matrix_world.copy()
for x in list(bpy.data.objects):
    if x is not o: bpy.data.objects.remove(x)
o.parent = None; o.matrix_world = Mw; o.name = 'Raw'
bpy.context.view_layer.objects.active = o; o.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = o.data; me.materials.clear()
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.to_mesh(me); bm.free()
P = np.array([tuple(v.co) for v in me.vertices]) * S
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
order = np.argsort(-np.bincount(comp))
print('COMPS', [int((comp == c).sum()) for c in order])
ids = {'Face': [order[0]], 'Eyes': [order[1], order[2]]}
for k, cs in ids.items():
    d = o.copy(); d.data = me.copy(); d.name = k; bpy.context.scene.collection.objects.link(d)
    bm = bmesh.new(); bm.from_mesh(d.data); bm.verts.ensure_lookup_table()
    keep = np.isin(comp, cs)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep[v.index]], context='VERTS')
    bm.to_mesh(d.data); bm.free()
bpy.data.objects.remove(o)
# Meshy's dome and brim have tears where they cross, so the helmet is rebuilt: rings of the raw shell's radius about the vertical axis, right half mirrored.
Fc = bpy.data.objects['Face']
bvr = BVHTree.FromObject(Fc, bpy.context.evaluated_depsgraph_get())
ZCUT = 0.0148
NT = 36
RINGS = [(.1485, .1475, 0), (.142, .142, 0), (.1345, .1345, 0), (.125, .125, 0), (.11, .11, 0), (.095, .095, 0), (.08, .08, 0), (.065, .065, 0), (.054, .054, 0),
         (.0485, .05, 0), (.0475, .0425, 0.001), (.044, .0405, 0.001), (.03, .03, 0.001), (.0195, .0215, 0.001), (.0165, .0205, 0.0), (.0155, .0205, -0.03)]   # height, sample height, radial offset
TH = np.arange(NT) * 2 * np.pi / NT
def radius(th, z):
    d = Vector((-abs(np.sin(th)), np.cos(th), 0)); o_ = Vector((0, 0, z))           # the figure's right half
    loc, *_ = bvr.ray_cast(d * 0.6 + o_, -d, 0.7)
    return (loc - o_).length if loc is not None else 0.0
R = np.array([[radius(t, zs) + off for t in TH] for z, zs, off in RINGS])
for j in range(len(RINGS)):                                      # one step of smoothing round the ring, no steps from the raw triangles
    R[j] = 0.25 * np.roll(R[j], 1) + 0.5 * R[j] + 0.25 * np.roll(R[j], -1)
bm = bmesh.new()
top = bm.verts.new((0, 0, 0.1545))
vs = [[bm.verts.new((np.sin(t) * R[j, i], np.cos(t) * R[j, i], RINGS[j][0])) for i, t in enumerate(TH)] for j in range(len(RINGS))]
for i in range(NT):
    k = (i + 1) % NT
    bm.faces.new((top, vs[0][i], vs[0][k]))
    for j in range(len(RINGS) - 1):
        bm.faces.new((vs[j][i], vs[j + 1][i], vs[j + 1][k], vs[j][k]))
bmesh.ops.triangulate(bm, faces=bm.faces)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
hm_ = bpy.data.meshes.new('Helm'); bm.to_mesh(hm_); bm.free()
Hm = bpy.data.objects.new('Helm', hm_); bpy.context.scene.collection.objects.link(Hm)
for p in hm_.polygons: p.use_smooth = True
print('HELM rings', len(RINGS), 'tris', len(hm_.polygons), 'r', np.round(R[:, 0], 3).tolist())
# a closed solid: Meshy's shell has hundreds of boundary edges and crossed layers, and every decimation tore there. Right half mirrored, all holes filled, voxel level set (enclosed layers vanish), relaxed.
bm = bmesh.new(); bm.from_mesh(Fc.data)
bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True, dist=1e-5)
for v in bm.verts:
    if abs(v.co.x) < 1e-4: v.co.x = 0
bmesh.ops.mirror(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], axis='X', merge_dist=2e-4)
bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
print('SOLID boundary left', sum(1 for e in bm.edges if e.is_boundary), 'faces', len(bm.faces))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(Fc.data); bm.free()
for x in bpy.data.objects: x.select_set(x is Fc)
bpy.context.view_layer.objects.active = Fc
rm = Fc.modifiers.new('R', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = float(os.environ.get('VOXEL', 0.0013)); rm.use_smooth_shade = True
bpy.ops.object.modifier_apply(modifier='R')
print('SOLID voxel', len(Fc.data.vertices), len(Fc.data.polygons))
bm = bmesh.new(); bm.from_mesh(Fc.data); bm.verts.ensure_lookup_table()
seen = set(); comps = []
for v in bm.verts:
    if v in seen: continue
    st = [v]; seen.add(v); cur = []
    while st:
        x = st.pop(); cur.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen: seen.add(y); st.append(y)
    comps.append(cur)
comps.sort(key=len, reverse=True)
print('SOLID comps', [len(c) for c in comps[:6]])
for c in comps[1:]: bmesh.ops.delete(bm, geom=c, context='VERTS')
bm.to_mesh(Fc.data); bm.free()
sm = Fc.modifiers.new('S', 'SMOOTH'); sm.factor = 0.5; sm.iterations = 2
bpy.ops.object.modifier_apply(modifier='S')
HT = {'Face': TRIS, 'Eyes': 160}
for ob in [Fc, bpy.data.objects['Eyes']]:
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True, dist=1e-5)
    for v in bm.verts:
        if abs(v.co.x) < 1e-4: v.co.x = 0
    bm.to_mesh(ob.data); bm.free()
    bpy.context.view_layer.objects.active = ob
    for x in bpy.data.objects: x.select_set(x is ob)
    g = ob.vertex_groups.new(name='keep')
    Zmax = max(v.co.z for v in ob.data.vertices)
    for v in ob.data.vertices:
        face = 0.55 if (v.co.y < -0.02 and v.co.z < 0.02) else 0.0        # the face and ears keep their detail; dome and curtain are smooth
        if v.co.y < 0.06 and abs(v.co.x) > 0.06 and v.co.z < 0.02: face = 0.55
        g.add([v.index], 1.0 if abs(v.co.x) < 1e-5 else face, 'REPLACE')
    bmx = bmesh.new(); bmx.from_mesh(ob.data); bmesh.ops.triangulate(bmx, faces=bmx.faces); bmx.to_mesh(ob.data); bmx.free()
    tri_now = len(ob.data.polygons)
    while tri_now > 40000:                                                  # a million voxel faces in stages, or the collapse tears
        st = ob.modifiers.new('St', 'DECIMATE'); st.ratio = 0.3; st.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier='St')
        tri_now = len(ob.data.polygons); print('VOXEL stage', tri_now)
    d = ob.modifiers.new('D', 'DECIMATE'); d.ratio = min(1.0, HT[ob.name] / 2 / len(ob.data.polygons)); d.use_collapse_triangulate = True
    d.vertex_group = 'keep'; d.invert_vertex_group = True; d.vertex_group_factor = float(os.environ.get('HEAD_GROUP', 2.5))
    bpy.ops.object.modifier_apply(modifier='D')
    ob.vertex_groups.clear()
    bm = bmesh.new(); bm.from_mesh(ob.data)
    for v in bm.verts:
        if abs(v.co.x) < 2e-4: v.co.x = 0
    bmesh.ops.mirror(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], axis='X', merge_dist=3e-4)
    bmesh.ops.remove_doubles(bm, verts=[v for v in bm.verts if v.co.x == 0], dist=2e-3)
    for _ in range(3):
        seen = set(); comps = []
        for e in [e for e in bm.edges if e.is_boundary]:
            if e in seen: continue
            st = [e]; seen.add(e); cur = []
            while st:
                x = st.pop(); cur.append(x)
                for v in x.verts:
                    for y in v.link_edges:
                        if y.is_boundary and y not in seen: seen.add(y); st.append(y)
            comps.append(cur)
        for cur in comps:
            if len(cur) <= 16: bmesh.ops.holes_fill(bm, edges=cur, sides=len(cur))
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    print('OBJ', ob.name, 'boundary loops edges', sum(1 for e in bm.edges if e.is_boundary))
    bm.to_mesh(ob.data); bm.free()
# Meshy's pits on the cheek: spikes of the umbrella operator relaxed
bm = bmesh.new(); bm.from_mesh(Fc.data)
for it in range(6):
    mv = {}
    for v in bm.verts:
        if v.is_boundary or abs(v.co.x) < 1e-5 or v.co.z > ZCUT: continue
        nb = [e.other_vert(v).co for e in v.link_edges]
        c_ = sum(nb, Vector()) / len(nb); dd = (c_ - v.co).length
        if dd > 0.0022 and v.co.y < 0.04 and abs(v.co.z) < 0.09: mv[v] = c_
    for v, c_ in mv.items(): v.co = c_
    print('HIDDEN relax', it, len(mv))
bm.to_mesh(Fc.data); bm.free()
# the shell seen from outside, after the reduction so that the layers cross cleanly under each other: a face stays if some ray from a sphere of directions reaches it first, plus two rings. A voxel level set wraps this open shell in a double skin.
Fc = bpy.data.objects['Face']
bm = bmesh.new(); bm.from_mesh(Fc.data)
bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, ZCUT), plane_no=(0, 0, 1), clear_outer=True, dist=1e-5)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.to_mesh(Fc.data); bm.free()
bm = bmesh.new(); bm.from_mesh(Fc.data); bm.faces.ensure_lookup_table()
keep = {f.index for f in bm.faces}
seen_f = keep
dead = [f for f in bm.faces if f.index not in keep]
print('HIDDEN', len(dead), 'of', len(bm.faces), 'seen', len(seen_f))
bmesh.ops.delete(bm, geom=dead, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
seen = set(); filled = 0
for e0 in [e for e in bm.edges if e.is_boundary]:
    if e0 in seen: continue
    st = [e0]; seen.add(e0); cur = []
    while st:
        x = st.pop(); cur.append(x)
        for v in x.verts:
            for y in v.link_edges:
                if y.is_boundary and y not in seen: seen.add(y); st.append(y)
    q = np.array([v.co[:] for e in cur for v in e.verts])
    if (len(cur) <= 14 and q[:, 2].max() < ZCUT - 0.004 and np.ptp(q, axis=0).max() < 0.03) or (len(cur) <= 90 and q[:, 1].max() < -0.05 and q[:, 2].max() < -0.02):
        bmesh.ops.holes_fill(bm, edges=cur, sides=len(cur)); filled += 1
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
print('HIDDEN holes filled', filled)
bm.to_mesh(Fc.data); bm.free()
for ob in bpy.data.objects:
    for p in ob.data.polygons: p.use_smooth = True
    print('OBJ', ob.name, len(ob.data.vertices), len(ob.data.polygons), np.round(np.min([v.co[:] for v in ob.data.vertices], 0), 3), np.round(np.max([v.co[:] for v in ob.data.vertices], 0), 3))
c = np.array([v.co[:] for v in Fc.data.vertices])
for z in np.arange(-0.16, -0.08, 0.01):
    m = np.abs(c[:, 2] - z) < 0.006
    if m.any(): print('OBJ section', round(float(z), 3), np.round(c[m].min(0), 3).tolist(), np.round(c[m].max(0), 3).tolist())
bpy.ops.wm.save_as_mainfile(filepath=OUT)
