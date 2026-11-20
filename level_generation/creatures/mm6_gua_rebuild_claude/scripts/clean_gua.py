"""MM6 guard on the MM9 GUARD skeleton (Yrsa route): clean and reduce the coif-repaired Smart Topology parts of mm6_gua_claude
(work/st1r_parts.blend, same gated MM6 HD master): scale to MM9's height on MM9's floor, label garments in MM9 guard numbering,
keep the figure's right half (x < 0) and mirror, fill pin holes, reduce per garment with the joints protected.
Labels: 1 mail shirt + blue sleeves, 2 face + coif (attribute `garm` 16 tells the coif), 3 helmet + nasal, 4 fist (replaced by the
graft), 5 trousers, 6 shoes, 7 mail skirt below the belt, 9 belt, 17 bare forearm.
Args: <st1r blend> <mm9 true glb> <out blend> <report json>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
SRC, MM9, OUT, REP = a
rep = {}
NAMES = {1: 'shirt', 2: 'face', 3: 'helmet', 4: 'hand', 5: 'pants', 6: 'shoe', 7: 'skirt', 9: 'belt', 17: 'forearm'}
RATIO = {0: 0.62, 1: 0.5, 2: 0.75, 3: 0.9, 4: 0.8, 5: 0.8, 6: 0.55, 8: 1.0}     # per source piece (labels cross pieces' seams)
JOINTS = [(-.20, .08, .475), (-.42, .07, .29), (-.60, .03, .17), (-.10, .03, -.02), (-.14, .02, -.40), (-.19, .05, -.82), (-.10, .05, .6)]
ARM_AX = np.array([-0.804, -0.179, -0.567]); SH = np.array([-0.215, 0.04, 0.505])   # right arm axis from the slice probe
SLEEVE_END, WRIST = 0.29, 0.49                                                      # along ARM_AX from SH (scaled frame)
BELT = (0.01, 0.105); HEM_TOP = 0.01; SHOE_TOP = -0.815
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=MM9)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE'); arm.name = 'MM9_Rig'
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
mesh_b = next(o for o in sc.objects if o.type == 'MESH' and o.name.startswith('guard'))
mp = np.array([mesh_b.matrix_world @ v.co for v in mesh_b.data.vertices])
for x in list(bpy.data.objects):
    if x.type == 'MESH': bpy.data.objects.remove(x)
with bpy.data.libraries.load(SRC) as (src_, dst_):
    dst_.objects = [n for n in src_.objects if n.startswith('P')]
objs = []
for x in dst_.objects:
    sc.collection.objects.link(x); x.data = x.data.copy()
    x.data.attributes.new('srcp', 'INT', 'FACE').data.foreach_set('value', [int(x.name[1:])] * len(x.data.polygons))
    objs.append(x)
bpy.ops.object.select_all(action='DESELECT')
for x in objs: x.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.join()
o = objs[0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
o.name = 'Body'; o.data.name = 'Body'; o.data.materials.clear()
me = o.data
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=2e-5)
co = np.array([v.co for v in bm.verts])
s = np.ptp(mp[:, 2]) / np.ptp(co[:, 2])
t = np.array([0.0, 0.0, mp[:, 2].min() - co[:, 2].min() * s])
for v in bm.verts:
    v.co = Vector(np.array(v.co) * s + t)
rep['scale'] = float(s)
# central pieces on their own mid-plane (Meshy's head sits ~7 mm off), then the figure's right half
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
    if lo[0] < 0 < hi[0]:
        dx = -(lo[0] + hi[0]) / 2
        for x in cur: x.co.x += dx
geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True, clear_inner=False, dist=1e-5)
for v in bm.verts:
    if abs(v.co.x) < 2e-5: v.co.x = 0
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
# garment labels per face
sl = bm.faces.layers.int['srcp']
lay = bm.faces.layers.int.new('part'); gl = bm.faces.layers.int.new('garm')
for f in bm.faces:
    c = np.array(f.calc_center_median()); p = f[sl]; lb = 1; g = 0
    if p in (6, 8): lb = 3
    elif p == 3: lb = 2
    elif p == 2: lb, g = 2, 16
    elif p == 1: lb = 6 if c[2] < SHOE_TOP else 5
    elif p == 0:
        lb = 7 if c[2] < HEM_TOP else 9 if BELT[0] <= c[2] < BELT[1] else 1
    elif p in (4, 5):
        al = (c * [-1 if c[0] > 0 else 1, 1, 1] - SH) @ ARM_AX
        lb = 1 if al < SLEEVE_END else 17 if al < WRIST else 4
    f[lay] = lb; f[gl] = g or lb
bm.to_mesh(me); bm.free()
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
rep['labels'] = {NAMES[k]: int((fp == k).sum()) for k in NAMES}
# reduce per garment
fp = np.zeros(len(me.polygons), int); me.attributes['srcp'].data.foreach_get('value', fp)
objs = []
for lb in sorted(set(fp.tolist())):
    x = o.copy(); x.data = me.copy(); sc.collection.objects.link(x)
    bm = bmesh.new(); bm.from_mesh(x.data); bm.faces.ensure_lookup_table()
    lay = bm.faces.layers.int['srcp']
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
    if lb in (0, 2, 6):                             # Meshy's sawtooth rims, relaxed along the rim
        bm = bmesh.new(); bm.from_mesh(x.data)
        for _ in range(3):
            mv = {}
            for v in bm.verts:
                nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
                if len(nb) == 2 and abs(v.co.x) > 1e-4:
                    mv[v] = v.co * 0.5 + (nb[0].co + nb[1].co) * 0.25
            for v, c in mv.items(): v.co = c
        bm.to_mesh(x.data); bm.free()
    rep.setdefault('reduce', {})['P%02d' % lb] = [n0, len(x.data.polygons)]
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
PITS = []
for it in range(8):
    mv = {}
    for v in bm.verts:
        q = np.array([abs(v.co.x), v.co.y, v.co.z])
        if PITS and min(np.linalg.norm(q - np.array(c)) for c in PITS) < 0.03:
            nb = [e.other_vert(v).co for e in v.link_edges]
            mv[v] = sum(nb, Vector()) / len(nb)
    for v, c in mv.items(): v.co = c
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
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
        if abs(v.co.x) < 0.012 and vp[v] & {1, 2, 7}:
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
