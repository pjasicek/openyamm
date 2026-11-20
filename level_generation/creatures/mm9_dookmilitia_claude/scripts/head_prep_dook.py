"""Head-only Meshy model -> objects Face (skin, ears, neck), Eyes, Helm (cap, coif, rim, cheek straps, spikes) in metres, head-local, exactly symmetric. The teeth pocket and the coif's loose inner sheet go
(MM9 has no jaw bone; linings come from finish_dook.py). Skull faces hidden under the helmet go. Args: <head glb> <out blend>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
S = 0.41
GROUPS = {'Face': [0], 'Eyes': [3, 4], 'Helm': [1, 5, 6, 7, 8, 9, 11, 12]}
TRIS = {'Face': 2400, 'Helm': 1500, 'Eyes': 160}
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
# the face's own mid-plane (the job's bbox is centred, the face was up to 1 cm off)
fq = P[comp == order[0]]; band = (fq[:, 2] < -0.03) & (fq[:, 2] > -0.16)
dx = -(fq[band, 0].min() + fq[band, 0].max()) / 2
print('MIDPLANE', round(float(dx), 4))
for v in me.vertices: v.co.x += dx
# the coif on its own mid-plane: Meshy guessed the back of the head from one view, up to 1 cm off the face's plane; cut there it leaves a ridge down the back
hc = np.isin(comp, [order[i] for i in GROUPS['Helm']]); Q = np.array([v.co[:] for v in me.vertices])
bk = hc & (Q[:, 2] < 0.05) & (Q[:, 2] > -0.15) & (Q[:, 1] > 0.02)
hdx = -(Q[bk, 0].min() + Q[bk, 0].max()) / 2
print('MIDPLANE helm', round(float(hdx), 4))
for i in np.nonzero(comp == order[1])[0]: me.vertices[int(i)].co.x += hdx


def boundary_comps(bm):
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
    return comps


def half(bm):
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True, dist=1e-5)
    for v in bm.verts:
        if abs(v.co.x) < 2e-4: v.co.x = 0


for k, ids in GROUPS.items():
    d = o.copy(); d.data = me.copy(); d.name = k; bpy.context.scene.collection.objects.link(d)
    bm = bmesh.new(); bm.from_mesh(d.data); bm.verts.ensure_lookup_table()
    keep = np.isin(comp, [order[i] for i in ids])
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep[v.index]], context='VERTS')
    half(bm)
    bmesh.ops.mirror(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], axis='X', merge_dist=3e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if k == 'Face':
        nf = 0
        for cur in boundary_comps(bm):
            q = np.array([v.co[:] for e in cur for v in e.verts])
            if q[:, 2].mean() > -0.17 or len(cur) < 26:          # everything but the neck's cut: the mouth pocket's opening, pin holes
                bmesh.ops.holes_fill(bm, edges=cur, sides=len(cur)); nf += 1
        print('FACE holes filled', nf)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(d.data); bm.free()
bpy.data.objects.remove(o)
Fc, Hm = bpy.data.objects['Face'], bpy.data.objects['Helm']
dg = bpy.context.evaluated_depsgraph_get()
bh = BVHTree.FromObject(Hm, dg)
bm = bmesh.new(); bm.from_mesh(Fc.data); bm.faces.ensure_lookup_table()
dead = set()
for f in bm.faces:
    c = f.calc_center_median(); hits = 0; tot = 0
    for dd in (f.normal, (f.normal + Vector((0.3, 0.1, 0.3))).normalized(), (f.normal + Vector((-0.3, 0.1, 0.3))).normalized(), (f.normal + Vector((0, 0.3, -0.1))).normalized()):
        loc, *_ = bh.ray_cast(c + dd * 1e-4, dd, 0.12); tot += 1; hits += loc is not None
    if hits == tot and c.z > -0.11 and not (abs(c.x) > 0.125 and -0.11 < c.z < 0.08): dead.add(f)         # the ears come out through the coif
for _ in range(3):
    dead -= {f for f in dead if any(g not in dead for e in f.edges for g in e.link_faces)}
print('SKULL hidden faces', len(dead), 'of', len(bm.faces))
bmesh.ops.delete(bm, geom=list(dead), context='FACES')
bm.to_mesh(Fc.data); bm.free()
for ob in bpy.data.objects:
    bpy.context.view_layer.objects.active = ob
    for x in bpy.data.objects: x.select_set(x is ob)
    if ob.name == 'Helm':                                      # symmetric decimation of the whole shell: a protected half-mesh seam comes out far denser than its neighbours and shades as a pit
        d = ob.modifiers.new('D', 'DECIMATE'); d.ratio = min(1.0, TRIS['Helm'] / len(ob.data.polygons)); d.use_symmetry = True; d.symmetry_axis = 'X'; d.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier='D')
    else:
        bm = bmesh.new(); bm.from_mesh(ob.data); half(bm); bm.to_mesh(ob.data); bm.free()
    g = ob.vertex_groups.new(name='keep') if ob.name != 'Helm' else None
    for v in (ob.data.vertices if g else []):
        w = 1.0 if abs(v.co.x) < 1e-5 else 0.0
        if ob.name == 'Face' and v.co.y < -0.06 and v.co.z > -0.13 and abs(v.co.x) < 0.075: w = max(w, 0.6)      # eyes, nose, mouth stay dense
        g.add([v.index], w, 'REPLACE')
    if g:
        d = ob.modifiers.new('D', 'DECIMATE'); d.ratio = min(1.0, TRIS[ob.name] / 2 / len(ob.data.polygons)); d.vertex_group = 'keep'; d.invert_vertex_group = True; d.vertex_group_factor = 10.0; d.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier='D')
        ob.vertex_groups.clear()
    bm = bmesh.new(); bm.from_mesh(ob.data)
    for v in bm.verts:
        if abs(v.co.x) < 2e-4: v.co.x = 0
    if ob.name != 'Helm':
        bmesh.ops.mirror(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], axis='X', merge_dist=3e-4)
        bmesh.ops.remove_doubles(bm, verts=[v for v in bm.verts if v.co.x == 0], dist=2e-3)
    if ob.name == 'Face':
        for v in bm.verts:                                      # MM9's ears stand well out of the coif; Meshy's sit against it behind the strap
            ax = abs(v.co.x)
            if ax > 0.12: v.co.x = (1 if v.co.x > 0 else -1) * (0.12 + (ax - 0.12) * 1.6)
        for cur in boundary_comps(bm):
            q = np.array([v.co[:] for e in cur for v in e.verts])
            if q[:, 2].mean() > -0.17 and q[:, 1].mean() < 0.0 and np.ptp(q[:, 0]) < 0.1: bmesh.ops.holes_fill(bm, edges=cur, sides=len(cur))
    if ob.name == 'Helm':                                      # the mirror seam: pin holes on it, then a crease down the crown and the coif's back
        for cur in boundary_comps(bm):
            q = np.array([v.co[:] for e in cur for v in e.verts])
            if len(cur) <= 12 and np.abs(q[:, 0]).max() < 0.03: bmesh.ops.holes_fill(bm, edges=cur, sides=len(cur))
        for _ in range(3):
            mv = {}
            for v in bm.verts:
                ax = abs(v.co.x)
                if ax > 0.07 or (v.co.y < -0.02 and v.co.z < 0.11): continue
                nb = [e.other_vert(v).co for e in v.link_edges]
                if not nb: continue
                c = sum(nb, Vector()) / len(nb); w = 0.6 * (1 - ax / 0.07)
                mv[v] = Vector((v.co.x, v.co.y * (1 - w) + c.y * w, v.co.z * (1 - w) + c.z * w))
            for v, c in mv.items(): v.co = c
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    print('PART', ob.name, 'tris', len(bm.faces), 'boundary comps', sorted(len(c) for c in boundary_comps(bm))[-6:], 'bbox', np.round(np.array([v.co[:] for v in bm.verts]).min(0), 3), np.round(np.array([v.co[:] for v in bm.verts]).max(0), 3))
    bm.free()
    for p in ob.data.polygons: p.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('HEAD saved')
