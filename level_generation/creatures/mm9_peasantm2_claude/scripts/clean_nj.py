"""Clean and reduce the Meshy return (after mm9_nobleman_claude/scripts/clean_nb.py): scale to MM9's height on MM9's floor, keep the
figure's LEFT half (x > 0: the right chest has two pin-hole tears), label pieces, fill pin holes, reduce per garment with the joints
protected, mirror (MM9 is symmetric). Head, hair, eyes, brooches and pendant go (head graft; the jewellery is paint); the buckle stays.
Parts: 1 coat (body, sleeves; skirt 7 and belt band 9 split by height afterwards), 4 hands (replaced by the MPFB graft), 5 hose,
6 boots, 10 buckle. Args: <meshy glb> <mm9 src glb> <out blend> <report json>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
MESHY, MM9, OUT, REP = a
rep = {}
NAMES = {1: 'coat', 4: 'hand', 5: 'hose', 6: 'boot', 10: 'buckle', 15: 'drop'}
RATIO = {1: 0.62, 4: 1.0, 5: 0.55, 6: 0.55, 10: 0.5, 15: 1.0}
# joints kept dense, figure's left (x > 0), Meshy's A-pose: shoulder, elbow, wrist, hip, knee, ankle
JOINTS = [(.21, .0, .53), (.33, .0, .35), (.43, .0, .19), (.09, .0, .0), (.12, .0, -.40), (.15, .0, -.72)]


def label(q):
    lo, hi = q.min(0), q.max(0); e = hi - lo
    if lo[2] > 0.6: return 15                               # head, hair, eyes
    if e[0] > 0.35 and hi[2] > 0.5: return 1                  # coat with sleeves and skirt (half width after the bisect)
    if e[2] > 0.5 and lo[2] < -0.3 and hi[2] > 0.1: return 5   # hose
    if hi[2] < -0.3: return 6                               # boots
    if abs(q[:, 0].mean()) > 0.38 and hi[2] < 0.25: return 4   # hands (and Meshy's loose thumb piece)
    if hi[2] < 0.3 and lo[2] > 0.15 and e[1] < 0.03: return 10  # buckle
    return 15                                               # pendant, brooches: painted


def components(bm):
    bm.verts.ensure_lookup_table()
    seen = set(); out = []
    for v in bm.verts:
        if v in seen: continue
        st = [v]; seen.add(v); cur = []
        while st:
            x = st.pop(); cur.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y not in seen: seen.add(y); st.append(y)
        out.append(cur)
    return out


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


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=MM9)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE'); arm.name = 'MM9_Rig'
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
mesh_b = next(o for o in sc.objects if o.type == 'MESH' and o.name.startswith('njam'))
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
# each central piece on its own mid-plane (Meshy's pieces sit up to 1 cm off the bbox centre)
for cur in components(bm):
    q = np.array([x.co for x in cur]); lo, hi = q.min(0), q.max(0)
    if lo[0] < 0 < hi[0] and len(cur) > 100:
        if np.ptp(q[:, 0]) > 0.6: band = (np.abs(q[:, 0]) < 0.24) & (q[:, 2] > 0.06) & (q[:, 2] < 0.45)
        elif hi[2] < 0.3 and lo[2] < -0.3: band = (q[:, 2] > -0.05) & (q[:, 2] < 0.15)
        else: band = np.ones(len(q), bool)
        dx = -(q[band, 0].min() + q[band, 0].max()) / 2
        print('MIDPLANE', len(cur), round(float(dx), 4))
        for x in cur: x.co.x += dx
geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=False, clear_inner=True, dist=1e-5)
for v in bm.verts:
    if abs(v.co.x) < 2e-5: v.co.x = 0
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
# pin holes (short boundary cycles off the mid-plane): fan from the centre
filled = 0
for _ in range(3):
    used = set()
    for e0 in [e for e in bm.edges if e.is_boundary]:
        if e0 in used: continue
        cyc = [e0]; start = e0.verts[0]; cur = e0.verts[1]; ok = False
        while len(cyc) < 10:
            nxt = [e for e in cur.link_edges if e.is_boundary and e not in cyc and e not in used]
            if not nxt: break
            cyc.append(nxt[0]); cur = nxt[0].other_vert(cur)
            if cur is start: ok = True; break
        used.update(cyc)
        if not ok: continue
        vs = [start]; x = start
        for e in cyc[:-1]:
            x = e.other_vert(x); vs.append(x)
        if sum(1 for v in vs if abs(v.co.x) < 1e-4) > 1: continue
        c = sum((v.co for v in vs), Vector()) / len(vs)
        nv = bm.verts.new(c)
        for a_, b_ in zip(vs, vs[1:] + vs[:1]):
            try: bm.faces.new((a_, b_, nv))
            except ValueError: pass
        filled += 1
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
rep['holes'] = filled
lay = bm.faces.layers.int.new('part')
info = []; drop = []
for cur in components(bm):
    q = np.array([v.co for v in cur]); lb = label(q)
    if lb == 15: drop.extend(cur)
    info.append((NAMES[lb], len(cur), q.min(0).round(3).tolist(), q.max(0).round(3).tolist()))
    for f in {f for v in cur for f in v.link_faces}: f[lay] = lb
bmesh.ops.delete(bm, geom=drop, context='VERTS')
bm.to_mesh(me); bm.free()
for i in sorted(info, key=lambda x: -x[1]): print('PIECE', i)
# reduce per garment, joints protected
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
            d = min(((np.array(v.co) - np.array(j)) ** 2).sum() ** 0.5 for j in JOINTS)
            w = float(np.clip(1 - (d - 0.06) / 0.08, 0.0, 1.0))
            if abs(v.co.x) < 1e-5: w = 1.0
            g.add([v.index], w, 'REPLACE')
        dm = x.modifiers.new('D', 'DECIMATE'); dm.ratio = RATIO[lb]; dm.vertex_group = 'keep'; dm.invert_vertex_group = True; dm.vertex_group_factor = 3.0; dm.use_collapse_triangulate = True
        bpy.ops.object.select_all(action='DESELECT'); x.select_set(True); bpy.context.view_layer.objects.active = x
        bpy.ops.object.modifier_apply(modifier='D')
        x.vertex_groups.clear()
    x.data.attributes['part'].data.foreach_set('value', [lb] * len(x.data.polygons))
    if lb in (1, 6):                                  # Meshy's sawtooth rims (hem, coat front, cuffs, boot tops), relaxed along the rim
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
bmesh.ops.mirror(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], axis='X', merge_dist=3e-4)
filled = 0
for _ in range(2):
    for cur in boundary_comps(bm):
        vs = list({v for e in cur for v in e.verts})
        q = np.array([v.co for v in vs]); ext = np.ptp(q, axis=0)
        if len(cur) <= 6 and np.sort(ext)[1] < 0.003:
            bmesh.ops.pointmerge(bm, verts=vs, merge_co=Vector(q.mean(0))); filled += 1
        elif len(cur) <= 20 and ext.max() < 0.04:
            bmesh.ops.holes_fill(bm, edges=cur, sides=len(cur)); filled += 1
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bmesh.ops.triangulate(bm, faces=bm.faces)
rep['seam_filled'] = filled
bm.faces.ensure_lookup_table()
lay = bm.faces.layers.int['part']
for _ in range(6):
    for f in bm.faces:
        if f[lay] == 0:
            nb = [g[lay] for e in f.edges for g in e.link_faces if g is not f and g[lay]]
            if nb: f[lay] = nb[0]
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
# skirt and belt band split from the coat by height (the buckle's height marks the belt)
BELT_LO, BELT_HI = 0.19, 0.275
for f in bm.faces:
    c = f.calc_center_median()
    if f[lay] == 1 and abs(c.x) < 0.26:
        if c.z < BELT_LO: f[lay] = 7
        elif c.z < BELT_HI: f[lay] = 9
# mirror seam: light Laplacian on y, z near x = 0
vp = {v: {f[lay] for f in v.link_faces} for v in bm.verts}
for it in range(3):
    mv = {}
    for v in bm.verts:
        if any(e.is_boundary for e in v.link_edges) and abs(v.co.x) > 1e-5: continue
        nb = [e.other_vert(v).co for e in v.link_edges]
        if not nb: continue
        c = sum(nb, Vector()) / len(nb)
        if abs(v.co.x) < 0.012 and vp[v] & {1, 5, 7, 9}:
            mv[v] = Vector((v.co.x, v.co.y * 0.4 + c.y * 0.6, v.co.z * 0.4 + c.z * 0.6))
    for v, c in mv.items(): v.co = c
bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
if 'UVMap' not in me.uv_layers: me.uv_layers.new(name='UVMap')
bm = bmesh.new(); bm.from_mesh(me)
rep['boundary'] = sum(1 for e in bm.edges if e.is_boundary); rep['over2'] = sum(1 for e in bm.edges if len(e.link_faces) > 2)
rep['boundary_rings'] = sorted([len(c) for c in boundary_comps(bm)], reverse=True)[:20]
bm.free()
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
rep['parts'] = {int(k): int((fp == k).sum()) for k in np.unique(fp)}
rep['tris'] = len(me.polygons); rep['verts'] = len(me.vertices)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=0)
print('CLEAN', json.dumps(rep)[:900])
