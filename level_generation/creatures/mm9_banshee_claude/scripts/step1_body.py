"""Torso, arms and sleeves from the Meshy return: scaled onto MM9 (S = 1.6 puts hem, belt and crown on MM9's), cut at the waist under the belt (the dress is our lattice), at the neck base and at the wrist beyond the
ruffle (hands are ours), interior faces dropped, x > 0 mirrored. The arms are then re-posed onto MM9's bind direction and length, so MM9's clips reach where they do in MM9.
Writes work/upper.blend (object Upper) and work/upper.json. Args: <meshy glb> <out blend> <out json>"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
GLB, OUT, REP = sys.argv[sys.argv.index('--') + 1:]
S, T = 1.6, np.array([0, 0.15, -0.08])
ZWAIST, ZNECK, XWRIST = 0.122, 0.505, 0.574
# MM9 arm (+x side, 01 chain)
M_SH, M_EL, M_WR = np.array([0.1775, -0.119, 0.3898]), np.array([0.3996, -0.1284, 0.2361]), np.array([0.6022, -0.1447, 0.0799])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
o = next(x for x in bpy.context.scene.objects if x.type == 'MESH')
for x in list(bpy.context.scene.objects):
    if x is not o:
        m = o.matrix_world.copy(); o.parent = None; o.matrix_world = m; bpy.data.objects.remove(x)
bpy.context.view_layer.objects.active = o; o.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = o.data
for u in list(me.uv_layers):
    me.uv_layers.remove(u)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
# largest component
lab = {}; parts = []
for v in bm.verts:
    if v.index in lab:
        continue
    st = [v]; lab[v.index] = len(parts); cur = []
    while st:
        x = st.pop(); cur.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in lab:
                lab[y.index] = len(parts); st.append(y)
    parts.append(cur)
parts.sort(key=len, reverse=True)
print('PARTS', [len(p) for p in parts[:8]])
bmesh.ops.delete(bm, geom=[v for p in parts[1:] for v in p], context='VERTS')
for v in bm.verts:
    v.co = Vector((np.array(v.co[:]) * S + T).tolist())
bm.verts.ensure_lookup_table()
# the dress below the belt, the neck, the hands
bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=False, clear_inner=True, dist=1e-5)
bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
sel = [v for v in bm.verts if v.co.x < 0.42]
gm = list({f for v in sel for f in v.link_faces}) + list({e for v in sel for e in v.link_edges}) + sel
bmesh.ops.bisect_plane(bm, geom=gm, plane_co=(0, 0, ZWAIST), plane_no=(0, 0, 1), clear_outer=False, clear_inner=True, dist=1e-5)
bm.verts.ensure_lookup_table()
sel = [v for v in bm.verts if v.co.x < 0.2]
gm = list({f for v in sel for f in v.link_faces}) + list({e for v in sel for e in v.link_edges}) + sel
NECK_P, NECK_N = np.array([0, -0.13, ZNECK]), np.array([0, -0.6, 0.8])      # the neck leaves the chest forward and up, as MM9's
bmesh.ops.bisect_plane(bm, geom=gm, plane_co=NECK_P.tolist(), plane_no=NECK_N.tolist(), clear_outer=True, clear_inner=False, dist=1e-5)
# arm axis
bm.verts.ensure_lookup_table()
co = np.array([v.co[:] for v in bm.verts])
a = co[(co[:, 0] > 0.3) & (co[:, 0] < 0.585) & (co[:, 2] > -0.05)]
cs = np.array([0.5 * (a[np.abs(a[:, 0] - x) < 0.015].min(0) + a[np.abs(a[:, 0] - x) < 0.015].max(0)) for x in np.arange(0.33, 0.58, 0.04)])
u = np.linalg.svd(cs - cs.mean(0))[2][0]
u = u if u[0] > 0 else -u
sho = cs.mean(0) + u * ((0.18 - cs.mean(0)[0]) / u[0])
print('AXIS', u.round(4), 'SHOULDER', sho.round(3), cs.round(3).tolist())
# wrist cut, normal to the arm axis
wp = sho + u * ((XWRIST - sho[0]) / u[0])
sel = [v for v in bm.verts if v.co.x > 0.5]
gm = list({f for v in sel for f in v.link_faces}) + list({e for v in sel for e in v.link_edges}) + sel
bmesh.ops.bisect_plane(bm, geom=gm, plane_co=wp.tolist(), plane_no=u.tolist(), clear_outer=True, clear_inner=False, dist=1e-5)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
# scraps
seen = {}; parts = []
for v in bm.verts:
    if v.index in seen:
        continue
    st = [v]; seen[v.index] = 1; cur = []
    while st:
        x = st.pop(); cur.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen[y.index] = 1; st.append(y)
    parts.append(cur)
parts.sort(key=len, reverse=True)
print('AFTER CUT', [len(p) for p in parts[:8]])
bmesh.ops.delete(bm, geom=[v for p in parts[1:] for v in p], context='VERTS')
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
# interior faces
F = [[v.index for v in f.verts] for f in bm.faces]
W = np.array([v.co[:] for v in bm.verts])
bvh = BVHTree.FromPolygons([Vector(c.tolist()) for c in W], F)
g = np.pi * (3 - 5 ** 0.5); n = 64; kk = np.arange(n) + 0.5; zz = 1 - 2 * kk / n; rr = np.sqrt(1 - zz ** 2)
DIRS = [Vector((rr[i] * math.cos(g * i), rr[i] * math.sin(g * i), zz[i])) for i in range(n)]
dele = []
for f in bm.faces:
    N = f.normal; org = f.calc_center_median() + N * 1e-4; seen_ = 0
    for d in DIRS:
        if d.dot(N) < 0.3:
            continue
        if bvh.ray_cast(org, d, 3.0)[0] is None:
            seen_ += 1
    if seen_ == 0:
        dele.append(f)
print('INTERIOR', len(dele), 'of', len(bm.faces))
bmesh.ops.delete(bm, geom=dele, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
# what the wrist cut left of the thumb
bm.verts.ensure_lookup_table()
drop = [v for v in bm.verts if v.co.x > 0.5 and np.linalg.norm((np.array(v.co[:]) - sho) - u * ((np.array(v.co[:]) - sho) @ u)) > 0.075]
print('THUMB verts', len(drop))
bmesh.ops.delete(bm, geom=drop, context='VERTS')
# slits and pin holes on the +x half: every boundary loop that is not a cut (x = 0 plane, waist, neck, wrist)
bm.edges.ensure_lookup_table()
def is_cut(e):
    a, b = e.verts
    if abs(a.co.x) < 1e-4 and abs(b.co.x) < 1e-4:
        return True
    if abs(a.co.z - ZWAIST) < 1e-4 and abs(b.co.z - ZWAIST) < 1e-4:
        return True
    if abs((np.array(a.co[:]) - NECK_P) @ NECK_N) < 1e-4 and abs((np.array(b.co[:]) - NECK_P) @ NECK_N) < 1e-4:
        return True
    pa, pb = np.array(a.co[:]), np.array(b.co[:])
    return abs((pa - wp) @ u) < 1e-4 and abs((pb - wp) @ u) < 1e-4
rest = {e for e in bm.edges if e.is_boundary and not is_cut(e)}
loops = []
while rest:
    e = rest.pop(); cur = {e}; st = [e]
    while st:
        x = st.pop()
        for v in x.verts:
            for y in v.link_edges:
                if y in rest:
                    rest.discard(y); cur.add(y); st.append(y)
    loops.append(cur)
print('OPEN LOOPS', sorted([(len(l), [round(c, 2) for c in next(iter(l)).verts[0].co]) for l in loops], key=lambda t: -t[0])[:14])
for l in loops:
    if len(l) <= 40:
        try:
            bmesh.ops.holes_fill(bm, edges=list(l), sides=0)
        except Exception as ex:
            print('fill', ex)
# arm re-pose: rotate about the shoulder onto MM9's direction, stretch to MM9's length; deltoid blended
d9 = (M_WR - M_SH); L9 = float(np.linalg.norm(d9)); d9 /= L9
L = float((wp - sho) @ u)
stretch = L9 / L
axis = np.cross(u, d9); ang = math.asin(min(np.linalg.norm(axis), 1)); axis /= np.linalg.norm(axis)
R = np.array(Matrix.Rotation(ang, 3, Vector(axis.tolist())))
print('ARM length ours', round(L, 3), 'mm9', round(L9, 3), 'stretch', round(stretch, 3), 'rotate deg', round(math.degrees(ang), 1))


def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


for v in bm.verts:
    p = np.array(v.co[:])
    if p[0] < 0.1:
        continue
    al = (p - sho) @ u
    b = ss(-0.03, 0.14, al) * ss(0.1, 0.19, p[0])
    q = sho + R @ ((p - sho) + u * al * (stretch - 1))
    v.co = Vector((p * (1 - b) + q * b).tolist())
for v in bm.verts:
    if abs(v.co.x) < 1e-3:
        v.co.x = 0
bmesh.ops.mirror(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], matrix=Matrix.Identity(4), merge_dist=2e-4, axis='X')
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bmesh.ops.triangulate(bm, faces=bm.faces[:])
be = [e for e in bm.edges if e.is_boundary]
print('UPPER', len(bm.verts), len(bm.faces), 'boundary', len(be))
bm.to_mesh(me); bm.free()
o.name = 'Upper'; me.name = 'Upper'
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump({'shoulder': sho.tolist(), 'dir': d9.tolist(), 'length': L9, 'stretch': stretch}, open(REP, 'w'))
