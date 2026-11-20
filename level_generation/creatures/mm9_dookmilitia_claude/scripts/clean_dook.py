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
NAMES = {1: 'tunic', 2: 'neck', 3: 'sleeve', 4: 'hand', 5: 'pants', 6: 'boot', 7: 'skirt', 8: 'mantle', 9: 'belt', 10: 'buckle', 13: 'cap', 15: 'drop'}
RATIO = {1: 0.82, 2: 1.0, 3: 0.85, 4: 1.0, 5: 0.66, 6: 0.55, 7: 0.85, 8: 0.7, 9: 0.75, 10: 0.45, 13: 0.85, 15: 1.0}
JOINTS = [(-.285, .065, .515), (-.545, .068, .385), (-.775, .01, .265), (-.095, .03, -.03), (-.175, .02, -.44), (-.24, .07, -.83), (-.13, .05, .56)]   # kept dense


def label(q):
    lo, hi = q.min(0), q.max(0); e = hi - lo
    if 0.5 < lo[2] < 0.69 and hi[2] > 0.9: return 2                  # old face + neck: the neck stays below the head job's cut
    if lo[2] > 0.69: return 15                                  # hood, cap, cheek straps, eyes, teeth, spikes: the head job replaces them
    if lo[2] < -0.9: return 5                                   # legs, pelvis, boots
    if lo[2] < -0.1 and hi[2] > 0.7: return 1                   # tunic with belt and skirt, split below
    if abs(q[:, 0].mean()) > 0.7: return 4                      # hands
    if e[0] > 0.4: return 3                                     # sleeves
    if hi[1] < -0.12 and hi[2] < 0.25: return 10                # belt buckle
    if lo[2] > 0.5 and e[1] > 0.25: return 8                    # mantle
    if lo[2] > 0.38 and hi[2] < 0.68 and abs(q[:, 0].mean()) > 0.25: return 13    # shoulder caps
    return 15                                                   # ankle rings: painted


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=MM9)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE'); arm.name = 'MM9_Rig'
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
mesh_b = next(o for o in sc.objects if o.type == 'MESH' and o.name.startswith('militiarev'))
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
    if lo[0] < 0 < hi[0] and len(cur) > 100:                    # tunic, pants, neck: each on the mid-plane of its own central band
        if lo[2] < -0.9: band = (q[:, 2] > 0.0) & (q[:, 2] < 0.12) & (np.abs(q[:, 0]) < 0.3)
        elif lo[2] < -0.1: band = (q[:, 2] > 0.2) & (q[:, 2] < 0.32)
        elif lo[2] > 0.5 and hi[2] > 0.9: band = (q[:, 2] > 0.6) & (q[:, 2] < 0.7)
        else: band = np.ones(len(q), bool)
        if not band.any(): continue
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
        if lb == 1:                                             # the skirt: below the belt's lower edge, not the arm
            c = f.calc_center_median()
            if c.z < 0.135: f[lay] = 7
            elif c.z < 0.245: f[lay] = 9
        if lb == 5 and f.calc_center_median().z < -0.495: f[lay] = 6   # boots: same shell as the legs
bmesh.ops.delete(bm, geom=eyes, context='VERTS')
bm.to_mesh(me); bm.free()
for i in sorted(info, key=lambda x: -x[1]): print('PIECE', i)
# reduce per garment
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
objs = []
GROUP = {7: 1, 9: 1, 6: 5}                                     # one shell in Meshy's model: reduced together, or the seams crack open
fp = np.array([GROUP.get(int(k), int(k)) for k in fp])
me.attributes['part'].data.foreach_set('value', fp.tolist())
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
    vals = [lb] * len(x.data.polygons)
    for i_, p_ in enumerate(x.data.polygons):
        zc = p_.center.z
        if lb == 1: vals[i_] = 7 if zc < 0.135 else 9 if zc < 0.245 else 1
        if lb == 5 and zc < -0.495: vals[i_] = 6
    x.data.attributes['part'].data.foreach_set('value', vals)
    if lb in (1, 3, 7, 8, 13):                         # Meshy's sawtooth rims, relaxed along the rim
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
# the mirror seam (a slight V on the chest) and Meshy's star creases on the tunic: light Laplacian on y, z near x = 0, all
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
        if abs(v.co.x) < 0.045 and vp[v] & {1, 2, 5, 7, 8}:
            w_ = 0.6 * (1 - abs(v.co.x) / 0.045)
            mv[v] = Vector((v.co.x, v.co.y * (1 - w_) + c.y * w_, v.co.z * (1 - w_) + c.z * w_))
        elif vp[v] == {1} and it < 2:
            mv[v] = v.co * 0.7 + c * 0.3
    for v, c in mv.items(): v.co = c
bm.to_mesh(me); bm.free()
# the mantle's strips hang in the air off the chest and over the shoulder (a slit to see through, shards when posed): laid on the tunic and caps, keeping a third of their relief
from mathutils.bvhtree import BVHTree
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lay = bm.faces.layers.int['part']
T_ = bmesh.new(); vm = {}
for f in bm.faces:
    if f[lay] in (1, 9, 13):
        for v in f.verts:
            if v not in vm: vm[v] = T_.verts.new(v.co)
        try: T_.faces.new([vm[v] for v in f.verts])
        except ValueError: pass
T_.normal_update()
bvt = BVHTree.FromBMesh(T_)
mv_ = {v for f in bm.faces if f[lay] == 8 for v in f.verts}
moved = 0.0
for v in mv_:
    loc, nor, idx, dist = bvt.find_nearest(v.co)
    if loc is None: continue
    side = (v.co - loc).dot(nor)
    nd = 0.006 + 0.33 * max(side, 0.0)
    new = loc + nor * nd
    moved = max(moved, (new - v.co).length); v.co = new
for _ in range(2):
    mv = {}
    for v in mv_:
        nb = [e.other_vert(v).co for e in v.link_edges]
        if nb: mv[v] = v.co * 0.6 + sum(nb, Vector()) / len(nb) * 0.4
    for v, c in mv.items(): v.co = c
rep['mantle_moved_max_cm'] = round(moved * 100, 1)
T_.free(); bm.to_mesh(me); bm.free()
# thighs under the skirt: hidden, so slimmer than Meshy's (they drove the skirt out in Walking); full width again below the hem
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lay = bm.faces.layers.int['part']
pv = {v for f in bm.faces if f[lay] == 5 for v in f.verts} - {v for f in bm.faces if f[lay] != 5 for v in f.verts}
def sst(x, a, b):
    t = min(1.0, max(0.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)
for v in pv:
    k = 1 - 0.2 * sst(v.co.z, -0.27, -0.15)
    sx = 1 if v.co.x > 0 else -1
    ax = abs(v.co.x); nx = 0.125 + (ax - 0.125) * k; t_ = min(1.0, ax / 0.05)
    v.co.x = sx * (ax * (1 - t_) + nx * t_); v.co.y = 0.02 + (v.co.y - 0.02) * k
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
