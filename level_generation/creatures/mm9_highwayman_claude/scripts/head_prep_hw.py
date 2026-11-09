"""Head-only Meshy model -> objects Face (with neck), Eyes, Hair in metres, head-local, symmetric (from mm9_thrall_claude/scripts/head_prep.py). Teeth shell removed: MM9 has no jaw bone, the mouth stays closed.
The hair is a helmet-sized mushroom: shrunk onto the skull and neck by a soft cap on its shell thickness, hidden skull under it removed. The neck's flared base goes: the face stops above it at NECK_CUT
and a straight neck runs down into the collar. Args: <head glb> <out blend>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
S = 0.315
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
ids = {'Face': [order[0]], 'Hair': [order[1]], 'Eyes': [order[2], order[3]]}
print('COMPS', [int((comp == c).sum()) for c in order])
for k, cs in ids.items():
    d = o.copy(); d.data = me.copy(); d.name = k; bpy.context.scene.collection.objects.link(d)
    bm = bmesh.new(); bm.from_mesh(d.data); bm.verts.ensure_lookup_table()
    keep = np.isin(comp, cs)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep[v.index]], context='VERTS')
    # symmetric: the figure's right half (x < 0) mirrored. The pin holes of Meshy's hair go with a fill of small boundaries below
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True, dist=1e-5)
    for v in bm.verts:
        if abs(v.co.x) < 1e-4: v.co.x = 0
    bmesh.ops.mirror(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], axis='X', merge_dist=2e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # pin holes
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
            if len(cur) <= 24:
                bmesh.ops.holes_fill(bm, edges=cur, sides=len(cur))
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(d.data); bm.free()
bpy.data.objects.remove(o)
Fc, Hr = bpy.data.objects['Face'], bpy.data.objects['Hair']
dg = bpy.context.evaluated_depsgraph_get()
bv = BVHTree.FromObject(Fc, dg)
H = np.array([v.co[:] for v in Hr.data.vertices]); m = len(H)
Q = np.zeros((m, 3)); Nn = np.zeros((m, 3)); D = np.zeros(m)
for i, p in enumerate(H):
    loc, nor, idx, dist = bv.find_nearest(Vector(p))
    Q[i] = loc; Nn[i] = nor; D[i] = dist
back = np.clip((H[:, 1] + 0.01) / 0.09, 0, 1); back = back * back * (3 - 2 * back)
dmax = 0.036 + 0.040 * back
Dn = dmax * np.tanh(D / dmax)
rim = (D < 0.007) & (H[:, 1] < 0.02)
dr = np.linalg.norm(H[:, None] - H[rim][None], axis=2).min(1) if rim.any() else np.ones(m)
front = np.clip((0.03 - H[:, 1]) / 0.05, 0, 1)
Dn = np.minimum(Dn, 0.003 + 0.5 * dr + 0.2 * (1 - front))
dsp = (Q - H) * (1 - Dn / np.maximum(D, 1e-6))[:, None]
hn = [[] for _ in range(m)]
for e in Hr.data.edges:
    a, b = e.vertices; hn[a].append(b); hn[b].append(a)
for _ in range(10):
    dsp = 0.5 * dsp + 0.5 * np.array([dsp[nb].mean(0) if nb else dsp[i] for i, nb in enumerate(hn)])
H2 = H + dsp
for v, p in zip(Hr.data.vertices, H2): v.co = Vector(p)
Hr.data.update(); dg.update()
print('HAIR before', np.round(H.min(0), 3), np.round(H.max(0), 3), 'after', np.round(H2.min(0), 3), np.round(H2.max(0), 3))
# the hair as one clean shell: Meshy's has lumps, pin holes and a deep parting. A polar grid about the head's centre takes the shrunk shell's radius per direction, low-passed; where the ray misses the hair
# (the face) the grid runs just under the skin, so the hairline is the intersection and no gap opens at the temples. Below the rim it closes to the neck, a closed rounded lower edge like MM9's.
def gaussian2(A, st, sp):
    kt = np.exp(-0.5 * (np.arange(-6, 7) / st) ** 2); kt /= kt.sum()
    kp = np.exp(-0.5 * (np.arange(-5, 6) / sp) ** 2); kp /= kp.sum()
    O = np.zeros_like(A)
    for k, w in zip(range(-6, 7), kt): O += w * np.roll(A, k, axis=0)
    Pd = np.pad(O, ((0, 0), (5, 5)), mode='edge')
    Q = np.zeros_like(O)
    for k, w in zip(range(-5, 6), kp): Q += w * Pd[:, 5 + k:O.shape[1] + 5 + k]
    return Q
dg = bpy.context.evaluated_depsgraph_get()
bvH = BVHTree.FromObject(Hr, dg); bvF = BVHTree.FromObject(Fc, dg)
C0 = Vector((0, 0.0, 0.03))
NT, NP = 96, 48
TH = np.arange(NT) * 2 * np.pi / NT; PH = np.radians(np.linspace(1.0, 158.0, NP))
def outer(bv, d):
    far = C0 + d * 0.5
    loc, nor, idx, dist = bv.ray_cast(far, -d, 0.5)
    return None if loc is None else (loc - C0).length
Rh = np.full((NT, NP), np.nan); Rs = np.full((NT, NP), np.nan)
for i, t in enumerate(TH):
    for j, p in enumerate(PH):
        d = Vector((np.sin(p) * np.sin(t), np.sin(p) * np.cos(t), np.cos(p)))
        a_ = outer(bvH, d); b_ = outer(bvF, d)
        if a_ is not None: Rh[i, j] = a_
        if b_ is not None: Rs[i, j] = b_
Rs = np.where(np.isnan(Rs), 0.05, Rs)
hairy = ~np.isnan(Rh) & (np.nan_to_num(Rh) > Rs + 0.002)
# the lower rim is level at the sides and back: the shell's ragged lower edge is replaced by a clean closed one
Rt = np.where(hairy, np.nan_to_num(Rh), Rs - 0.006)
Rt = 0.5 * (Rt + np.roll(Rt[::-1], 1, axis=0))
hm = 0.5 * (hairy.astype(float) + np.roll(hairy[::-1].astype(float), 1, axis=0))
Rt = gaussian2(Rt, 2.4, 1.5)
Rt = np.maximum(Rt, np.where(hm > 0.5, Rs + 0.005, 0))
bm = bmesh.new()
vs = [[None] * NP for _ in range(NT)]
for i, t in enumerate(TH):
    for j, p in enumerate(PH):
        d = np.array([np.sin(p) * np.sin(t), np.sin(p) * np.cos(t), np.cos(p)])
        q = np.array(C0[:]) + d * Rt[i, j]
        vs[i][j] = bm.verts.new(Vector(q))
top = bm.verts.new(C0 + Vector((0, 0, float(Rt[:, 0].mean()))))
bot = bm.verts.new(C0 + Vector((0, 0, -0.06)))
for i in range(NT):
    k = (i + 1) % NT
    bm.faces.new((top, vs[i][0], vs[k][0]))
    bm.faces.new((bot, vs[k][-1], vs[i][-1]))
    for j in range(NP - 1):
        bm.faces.new((vs[i][j], vs[i][j + 1], vs[k][j + 1], vs[k][j]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bmesh.ops.triangulate(bm, faces=bm.faces)
# faces under the skin in front of the hairline go
keep = np.ones(0)
inside = {}
for i in range(NT):
    for j in range(NP): inside[vs[i][j]] = hm[i, j] < 0.05 and Rt[i, j] < Rs[i, j] - 0.001
dead = [f for f in bm.faces if all(inside.get(v, False) for v in f.verts) and f.calc_center_median().y < 0.02]
bmesh.ops.delete(bm, geom=dead, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(Hr.data); bm.free(); Hr.data.update()
print('HAIR grid hairy', int(hairy.sum()), 'of', hairy.size, 'r', np.round(Rt.min(), 3), np.round(Rt.max(), 3), 'tris', len(Hr.data.polygons))
# skull faces hidden under the closed hair
dg = bpy.context.evaluated_depsgraph_get()
bh = BVHTree.FromObject(Hr, dg)
bm = bmesh.new(); bm.from_mesh(Fc.data); bm.faces.ensure_lookup_table()
dead = set()
for f in bm.faces:
    c = f.calc_center_median(); hits = 0; tot = 0
    for dd in (f.normal, (f.normal + Vector((0.2, 0.1, 0.3))).normalized(), (f.normal + Vector((-0.2, 0.1, 0.3))).normalized(), (f.normal + Vector((0, 0.3, -0.1))).normalized()):
        loc, *_ = bh.ray_cast(c + dd * 1e-4, dd, 0.09); tot += 1; hits += loc is not None
    if hits == tot and c.z > -0.05: dead.add(f)
for _ in range(3):
    dead -= {f for f in dead if any(g not in dead for e in f.edges for g in e.link_faces)}
print('SKULL hidden faces', len(dead), 'of', len(bm.faces))
bmesh.ops.delete(bm, geom=list(dead), context='FACES')
bm.to_mesh(Fc.data); bm.free()
TRIS = {'Face': 2500, 'Hair': 1500, 'Eyes': 160}
for ob in bpy.data.objects:
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True, dist=1e-5)
    for v in bm.verts:
        if abs(v.co.x) < 1e-4: v.co.x = 0
    bm.to_mesh(ob.data); bm.free()
    bpy.context.view_layer.objects.active = ob
    for x in bpy.data.objects: x.select_set(x is ob)
    g = ob.vertex_groups.new(name='keep')
    for v in ob.data.vertices: g.add([v.index], 1.0 if abs(v.co.x) < 1e-5 else 0.0, 'REPLACE')
    d = ob.modifiers.new('D', 'DECIMATE'); d.ratio = min(1.0, TRIS[ob.name] / 2 / len(ob.data.polygons)); d.vertex_group = 'keep'; d.invert_vertex_group = True; d.vertex_group_factor = 10.0; d.use_collapse_triangulate = True
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
            if len(cur) <= 30: bmesh.ops.holes_fill(bm, edges=cur, sides=len(cur))
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data); bm.free()
for ob in bpy.data.objects:
    for p in ob.data.polygons: p.use_smooth = True
    print('OBJ', ob.name, len(ob.data.vertices), len(ob.data.polygons), np.round(np.min([v.co[:] for v in ob.data.vertices], 0), 3), np.round(np.max([v.co[:] for v in ob.data.vertices], 0), 3))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
