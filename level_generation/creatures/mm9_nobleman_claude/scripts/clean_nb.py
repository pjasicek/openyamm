"""Clean and reduce the Meshy return: scale to MM9's height on MM9's floor, keep the figure's right half (x < 0; Meshy's other collar edge
is jagged), label pieces, fill pin holes, reduce per garment with the joints protected, mirror (MM9 is exactly symmetric). The rig
and weights are deterministic from positions, so reducing before them keeps the mesh exactly symmetric.
Args: <meshy glb> <mm9 true glb> <out blend> <report json>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
MESHY, MM9, OUT, REP = a
rep = {}
BELT_LO, BELT_HI, SHOE_Z = 0.235, 0.31, -0.74
NAMES = {1: 'torso', 2: 'neck', 4: 'hand', 5: 'legs', 6: 'shoe', 7: 'skirt', 8: 'mantle', 9: 'belt', 10: 'buckle', 15: 'drop'}
RATIO = {1: 0.72, 2: 1.0, 4: 1.0, 5: 0.62, 6: 0.6, 7: 0.9, 8: 0.72, 9: 0.75, 10: 0.5, 15: 1.0}
JOINTS = [(-.205, .0, .60), (-.27, .0, .31), (-.335, .05, .07), (-.09, .0, .0), (-.165, .0, -.40), (-.19, .0, -.74)]   # kept dense


def label(q):
    lo, hi = q.min(0), q.max(0); e = hi - lo
    if lo[2] > 0.6:
        return 2 if lo[2] < 0.72 and e[2] > 0.2 and len(q) > 500 else 15   # old face + neck (its neck stays); hair, beads, brooches are replaced or painted
    if e[0] > 0.3 and lo[2] > 0.4: return 8                     # mantle
    if e[0] > 0.38: return 1                                     # doublet, sleeves, skirt (split below)
    if hi[2] < 0.3 and lo[2] < -0.8: return 5                   # legs with the shoes (split below)
    if abs(q[:, 0].mean()) > 0.25: return 4                     # hands
    return 15                                                   # brooch, chain, pendant: painted


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=MM9)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE'); arm.name = 'MM9_Rig'
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
mesh_b = next(o for o in sc.objects if o.type == 'MESH' and o.name.startswith('nobleman'))
mp = np.array([mesh_b.matrix_world @ v.co for v in mesh_b.data.vertices])
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MESHY)
new = [o for o in bpy.data.objects if o not in before]
o = next(x for x in new if x.type == 'MESH')
M = o.matrix_world.copy(); o.parent = None; o.matrix_world = M
for x in new:
    if x is not o: bpy.data.objects.remove(x)
for x in list(bpy.data.objects):
    if x.type == 'MESH' and x is not o: bpy.data.objects.remove(x)
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
o.name = 'Body'; o.data.name = 'Body'; o.data.materials.clear()
me = o.data
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=2e-5)
co = np.array([v.co for v in bm.verts])
s = np.ptp(mp[:, 2]) / np.ptp(co[:, 2])
t = np.array([-(co[:, 0].min() + co[:, 0].max()) / 2 * s, 0.0, mp[:, 2].min() - co[:, 2].min() * s])
for v in bm.verts:
    v.co = Vector(np.array(v.co) * s + t)
rep['scale'] = float(s)
# Meshy's central pieces sit up to 1 cm off the bbox centre (scripts: symmetry search, no yaw): each piece on its own mid-plane
bm.verts.ensure_lookup_table()
seen = set()
for v in bm.verts:
    if v in seen: continue
    st = [v]; seen.add(v); cur = []
    while st:
        x = st.pop(); cur.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen: seen.add(y); st.append(y)
    q = np.array([x.co for x in cur]); lo, hi = q.min(0), q.max(0)
    if lo[0] < 0 < hi[0] and len(cur) > 100:    # doublet, legs, mantle, neck: each on the mid-plane of its own central band
        if lo[2] > 0.6 and hi[2] > 0.7: band = (q[:, 2] > 0.66) & (q[:, 2] < 0.75)
        elif lo[2] > 0.4: band = np.ones(len(q), bool)
        elif np.ptp(q[:, 0]) > 0.6: band = (np.abs(q[:, 0]) < 0.24) & (q[:, 2] > 0.06) & (q[:, 2] < 0.45)
        elif hi[2] < 0.3 and lo[2] < -0.5: band = (q[:, 2] > -0.05) & (q[:, 2] < 0.1)
        else: band = np.ones(len(q), bool)
        dx = -(q[band, 0].min() + q[band, 0].max()) / 2
        print('MIDPLANE', len(cur), round(float(dx), 4))
        for x in cur: x.co.x += dx
geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True, clear_inner=False, dist=1e-5)
for v in bm.verts:
    if abs(v.co.x) < 2e-5: v.co.x = 0
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); bm.free()
# pin holes (Meshy's triangular pockets, a bowtie boundary defeats holes_fill): walk the short boundary cycles, fan from a centre
bm = bmesh.new(); bm.from_mesh(me)
filled = 0
for _ in range(3):
    used = set()
    bedges = [e for e in bm.edges if e.is_boundary]
    for e0 in bedges:
        if e0 in used: continue
        cyc = [e0]; start = e0.verts[0]; cur = e0.verts[1]; ok = False
        while len(cyc) < 10:
            nxt = [e for e in cur.link_edges if e.is_boundary and e not in cyc and e not in used]
            if not nxt: break
            cyc.append(nxt[0]); cur = nxt[0].other_vert(cur)
            if cur is start: ok = True; break
        for e in cyc: used.add(e)
        if not ok: continue
        vs = [start]; x = start
        for e in cyc[:-1]:
            x = e.other_vert(x); vs.append(x)
        if all(abs(v.co.x) < 1e-4 for v in vs) or sum(1 for v in vs if abs(v.co.x) < 1e-4) > 1: continue
        c = sum((v.co for v in vs), Vector()) / len(vs)
        nv = bm.verts.new(c)
        for a_, b_ in zip(vs, vs[1:] + vs[:1]):
            try:
                bm.faces.new((a_, b_, nv))
            except ValueError:
                pass
        filled += 1
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
rep['holes'] = filled
bm.verts.ensure_lookup_table()
seen = set(); pieces = []
for v in bm.verts:
    if v in seen: continue
    st = [v]; seen.add(v); cur = []
    while st:
        x = st.pop(); cur.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen: seen.add(y); st.append(y)
    pieces.append(cur)
lay = bm.faces.layers.int.new('part')
info = []
eyes = []
for cur in pieces:
    q = np.array([v.co for v in cur]); lb = label(q)
    if lb == 15:
        eyes.extend(cur)
    info.append((NAMES[lb], len(cur), q.min(0).round(3).tolist(), q.max(0).round(3).tolist()))
    for f in {f for v in cur for f in v.link_faces}:
        f[lay] = lb
bmesh.ops.delete(bm, geom=eyes, context='VERTS')
bm.to_mesh(me); bm.free()
for i in sorted(info, key=lambda x: -x[1]): print('PIECE', i)
# reduce per garment
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
objs = []
for lb in sorted(set(fp.tolist())):
    x = o.copy(); x.data = me.copy(); sc.collection.objects.link(x)
    bm = bmesh.new(); bm.from_mesh(x.data); bm.faces.ensure_lookup_table()
    lay = bm.faces.layers.int['part']
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[lay] != lb], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(x.data); bm.free()
    n0 = len(x.data.polygons)
    if RATIO[lb] < 1:
        g = x.vertex_groups.new(name='keep')
        for v in x.data.vertices:
            d = min(((np.abs(np.array(v.co)) - np.abs(np.array(j))) ** 2).sum() ** 0.5 for j in JOINTS)
            w = float(np.clip(1 - (d - 0.06) / 0.08, 0.0, 1.0))
            if abs(v.co.x) < 1e-5: w = 1.0
            g.add([v.index], w, 'REPLACE')
        dm = x.modifiers.new('D', 'DECIMATE'); dm.ratio = RATIO[lb]; dm.vertex_group = 'keep'; dm.invert_vertex_group = True; dm.vertex_group_factor = 3.0; dm.use_collapse_triangulate = True
        bpy.ops.object.select_all(action='DESELECT'); x.select_set(True); bpy.context.view_layer.objects.active = x
        bpy.ops.object.modifier_apply(modifier='D')
        x.vertex_groups.clear()
    x.data.attributes['part'].data.foreach_set('value', [lb] * len(x.data.polygons))
    if lb in (1, 7, 8, 9):                         # Meshy's sawtooth rims, relaxed along the rim
        bm = bmesh.new(); bm.from_mesh(x.data)
        for _ in range(3):
            mv = {}
            for v in bm.verts:
                nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
                if len(nb) == 2 and abs(v.co.x) > 1e-4:
                    mv[v] = v.co * 0.5 + (nb[0].co + nb[1].co) * 0.25
            for v, c in mv.items(): v.co = c
        bm.to_mesh(x.data); bm.free()
    rep.setdefault('reduce', {})[NAMES[lb]] = [n0, len(x.data.polygons)]
    objs.append(x)
bpy.ops.object.select_all(action='DESELECT')
bpy.data.objects.remove(o)
for x in objs: x.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.join()
o = objs[0]; o.name = 'Body'; o.data.name = 'Body'; me = o.data
bm = bmesh.new(); bm.from_mesh(me)
for v in bm.verts:
    if abs(v.co.x) < 3e-4: v.co.x = 0
geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
bmesh.ops.mirror(bm, geom=geom, axis='X', merge_dist=3e-4)
# small boundary cycles: pin holes the halves share, T-junction slits on the seam, closed by a fan
filled = 0
for _ in range(3):
    used = set()
    for e0 in [e for e in bm.edges if e.is_boundary]:
        if e0 in used: continue
        cyc = [e0]; start = e0.verts[0]; cur = e0.verts[1]; ok = False
        while len(cyc) < 22:
            nxt = [e for e in cur.link_edges if e.is_boundary and e not in cyc and e not in used]
            if not nxt: break
            cyc.append(nxt[0]); cur = nxt[0].other_vert(cur)
            if cur is start: ok = True; break
        used.update(cyc)
        if not ok: continue
        vs = [start]; x = start
        for e in cyc[:-1]:
            x = e.other_vert(x); vs.append(x)
        q = np.array([v.co for v in vs])
        if np.ptp(q, axis=0).max() > 0.04: continue
        nv = bm.verts.new(Vector(q.mean(0)))
        made = None
        for a_, b_ in zip(vs, vs[1:] + vs[:1]):
            try:
                made = bm.faces.new((a_, b_, nv))
                pv = a_.link_faces[0] if a_.link_faces else None
                if pv is not None and pv is not made:
                    made[bm.faces.layers.int['part']] = pv[bm.faces.layers.int['part']]
            except ValueError:
                pass
        filled += 1
rep['cycles_filled'] = filled
# what the walk cannot follow (bowties, zero-width seam slits): weld slits, fan by boundary component
for _ in range(2):
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
        vs = list({v for e in cur for v in e.verts})
        q = np.array([v.co for v in vs])
        ext = np.ptp(q, axis=0)
        if len(cur) <= 6 and np.sort(ext)[1] < 0.003:
            bmesh.ops.pointmerge(bm, verts=vs, merge_co=Vector(q.mean(0)))
            filled += 1
        elif len(cur) <= 20 and ext.max() < 0.04:
            r = bmesh.ops.holes_fill(bm, edges=cur, sides=len(cur))
            filled += 1
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bmesh.ops.triangulate(bm, faces=bm.faces)
rep['cycles_filled'] = filled
# new faces take their neighbour's garment; the pits Meshy left (collar, gauntlet, boot) are ironed out
bm.faces.ensure_lookup_table()
lay = bm.faces.layers.int['part']
for _ in range(6):
    for f in bm.faces:
        if f[lay] == 0:
            nb = [g[lay] for e in f.edges for g in e.link_faces if g is not f and g[lay]]
            if nb: f[lay] = nb[0]
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); bm.free()
# parts split by geometry only now: split before the reduction leaves loose strips whose normals flip (the belt)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); lay = bm.faces.layers.int['part']
for f in bm.faces:
    c = f.calc_center_median()
    if f[lay] == 1:
        if c.z < BELT_LO and abs(c.x) < 0.26: f[lay] = 7
        elif c.z < BELT_HI and abs(c.x) < 0.2: f[lay] = 9
    elif f[lay] == 5 and c.z < SHOE_Z: f[lay] = 6
# the placket: Meshy left holes, folded sheets and pits under the dropped brooches and pendant. The band is paint, so it is rebuilt: a smooth chest surface y = f(x, z), robust against
# the pits, and a fresh constrained Delaunay patch on it
from mathutils import geometry
def in_band(x, z): return abs(x) < 0.08 and 0.37 < z < 0.60 + 0.4 * abs(x)
Qc = np.array([v.co[:] for v in bm.verts if abs(v.co.x) < 0.15 and 0.3 < v.co.z < 0.63 and v.co.y < 0.0 and all(f[lay] == 1 for f in v.link_faces) and not in_band(v.co.x, v.co.z)])
def feat(x, z):
    x = x / 0.15; z = (z - 0.465) / 0.165; x2 = x * x
    return np.c_[np.ones_like(x), x2, x2 * x2, z, z * z, z ** 3, x2 * z, x2 * z * z]
ok = np.ones(len(Qc), bool)
for _ in range(6):
    co, *_r = np.linalg.lstsq(feat(Qc[ok, 0], Qc[ok, 2]), Qc[ok, 1], rcond=None)
    r = Qc[:, 1] - feat(Qc[:, 0], Qc[:, 2]) @ co
    ok = r < 0.004
dead = [f for f in bm.faces if f[lay] == 1 and f.calc_center_median().y < 0.0 and in_band(f.calc_center_median().x, f.calc_center_median().z)]
print('CHEST band faces', len(dead))
bmesh.ops.delete(bm, geom=dead, context='FACES')
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
inb = [c_ for c_ in comps if max(abs(v.co.x) for e in c_ for v in e.verts) < 0.12 and all(v.co.y < 0.0 and 0.33 < v.co.z < 0.68 for e in c_ for v in e.verts)]
ring = max(inb, key=len)
print('CHEST ring', len(ring), 'others', [len(c_) for c_ in inb if c_ is not ring])
# order the ring
rv = [ring[0].verts[0]]; used = set()
while True:
    nxt = [e for e in rv[-1].link_edges if e.is_boundary and e not in used and e in ring]
    if not nxt: break
    used.add(nxt[0]); w = nxt[0].other_vert(rv[-1])
    if w is rv[0]: break
    rv.append(w)
print('CHEST ordered', len(rv))
pts = [Vector((v.co.x, v.co.z)) for v in rv]; poly = list(range(len(rv)))
lat = []
for z in np.arange(0.38, 0.66, 0.03):
    for x in np.arange(-0.066, 0.0661, 0.033):
        if in_band(x, z) and abs(x) < 0.07 and 0.385 < z < 0.585 + 0.4 * abs(x): lat.append(Vector((float(x), float(z))))
cv, ce, cf, ov, oe, of = geometry.delaunay_2d_cdt(pts + lat, [], [poly], 1, 1e-5)
new = {}
for i, c_ in enumerate(cv):
    src = [k for k in ov[i]]
    if src and src[0] < len(rv): new[i] = rv[src[0]]
    else:
        y = float((feat(np.array([c_.x]), np.array([c_.y])) @ co)[0]); new[i] = bm.verts.new(Vector((c_.x, y, c_.y)))
made = 0
for f in cf:
    try:
        g = bm.faces.new([new[i] for i in f]); g[lay] = 1; made += 1
    except ValueError: pass
print('CHEST patch', made, 'lattice', len(lat))
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
for c_ in comps:
    if len(c_) <= 12 and max(abs(v.co.x) for e in c_ for v in e.verts) < 0.12 and all(v.co.y < 0.0 and 0.33 < v.co.z < 0.68 for e in c_ for v in e.verts):
        print('CHEST left', len(c_)); r = bmesh.ops.holes_fill(bm, edges=c_, sides=len(c_))
        for f in r['faces']: f[lay] = 1
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
# the patch's edge against Meshy's surface
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
sm = [v for v in bm.verts if abs(v.co.x) < 0.115 and 0.35 < v.co.z < 0.625 and v.co.y < -0.03 and all(f[lay] == 1 for f in v.link_faces) and not any(e.is_boundary for e in v.link_edges)]
for it in range(5):
    mv = {v: sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges) for v in sm}
    for v, c in mv.items(): v.co = v.co * 0.4 + c * 0.6
print('CHEST boundary left', [(round(e.verts[0].co.x, 3), round(e.verts[0].co.y, 3), round(e.verts[0].co.z, 3)) for e in bm.edges if e.is_boundary and abs(e.verts[0].co.x) < 0.1 and 0.33 < e.verts[0].co.z < 0.64 and e.verts[0].co.y < 0][:12])
print('CHEST back facing', [[round(c, 3) for c in f.calc_center_median()] for f in bm.faces if abs(f.calc_center_median().x) < 0.1 and 0.33 < f.calc_center_median().z < 0.64 and f.calc_center_median().y < -0.02 and f.normal.y > 0 and f[lay] == 1][:12])
bm.to_mesh(me); bm.free()
# the mirror seam (a slight V on the chin and chest) and Meshy's star creases on the tunic: light Laplacian on y, z near x = 0, all
# directions on the tunic's inside, rims and boots untouched
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lay = bm.faces.layers.int['part']
vp = {v: {f[lay] for f in v.link_faces} for v in bm.verts}
for it in range(3):
    mv = {}
    for v in bm.verts:
        if any(e.is_boundary for e in v.link_edges) and abs(v.co.x) > 1e-5: continue
        nb = [e.other_vert(v).co for e in v.link_edges]
        if not nb: continue
        c = sum(nb, Vector()) / len(nb)
        if abs(v.co.x) < 0.012 and vp[v] & {1, 2, 5, 6, 7, 8, 9}:
            mv[v] = Vector((v.co.x, v.co.y * 0.4 + c.y * 0.6, v.co.z * 0.4 + c.z * 0.6))
        elif vp[v] == {1} and it < 2:
            mv[v] = v.co * 0.7 + c * 0.3
    for v, c in mv.items(): v.co = c
bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
if 'UVMap' not in me.uv_layers: me.uv_layers.new(name='UVMap')
bm = bmesh.new(); bm.from_mesh(me)
rep['boundary'] = sum(1 for e in bm.edges if e.is_boundary); rep['over2'] = sum(1 for e in bm.edges if len(e.link_faces) > 2)
bm.free()
rep['tris'] = len(me.polygons); rep['verts'] = len(me.vertices)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=0)
print('CLEAN', json.dumps(rep)[:900])
